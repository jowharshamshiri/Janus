#!/usr/bin/env python3
"""
Janus Cross-Platform Test Orchestrator
Comprehensive test suite for validating SOCK_DGRAM implementations across Go, Rust, Swift, and TypeScript
"""

import json
import subprocess
import sys
import os
import time
import threading
import signal
import argparse
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import logging

@dataclass
class TestResult:
    """Test result container"""
    name: str
    category: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    message: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class TestOrchestrator:
    """Main test orchestrator for cross-platform Janus testing"""
    
    def __init__(self, config_path: str = "test-spec.json", verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose
        self.config = self._load_config()
        self.results: List[TestResult] = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="janus_test_"))
        self.log_dir = Path(self.config["environment"]["log_directory"])
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logging()
        self.running_processes = []
        
        # Signal handling for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.DEBUG if self.verbose else logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.log_dir / "test_orchestrator.log")
            ]
        )
        self.logger = logging.getLogger("TestOrchestrator")
    
    def _load_config(self) -> Dict:
        """Load test configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle cleanup on interrupt"""
        self.logger.info("Received interrupt signal, cleaning up...")
        self.cleanup()
        sys.exit(130)
    
    def cleanup(self):
        """Cleanup running processes and temporary files"""
        self.logger.info("Cleaning up test environment...")
        
        # Terminate running processes
        for proc in self.running_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as e:
                self.logger.warning(f"Error terminating process: {e}")
        
        # Cleanup temporary files
        if self.config["environment"]["cleanup_on_exit"]:
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.warning(f"Error cleaning up temp directory: {e}")
    
    def run_command(self, cmd: List[str], cwd: Optional[str] = None, 
                   timeout: int = 30, capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a command with timeout and logging"""
        cmd_str = " ".join(cmd)
        self.logger.debug(f"Running command: {cmd_str} (cwd: {cwd})")
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, 
                    cwd=cwd, 
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                return result.returncode, result.stdout, result.stderr
            else:
                # For long-running processes like servers
                proc = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.running_processes.append(proc)
                return 0, "", ""  # Success for start, actual monitoring happens elsewhere
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            return 124, "", f"Timeout after {timeout}s"
        except FileNotFoundError:
            self.logger.error(f"Command not found: {cmd[0]}")
            return 127, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            self.logger.error(f"Error running command: {e}")
            return 1, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Check that all required tools are available"""
        self.logger.info("Checking prerequisites...")
        
        tools = {
            "go": ["go", "version"],
            "rust": ["cargo", "version"],
            "swift": ["swift", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "version"]
        }
        
        missing_tools = []
        for tool, cmd in tools.items():
            returncode, stdout, stderr = self.run_command(cmd, timeout=10)
            if returncode != 0:
                missing_tools.append(tool)
                self.logger.error(f"Missing tool: {tool}")
            else:
                version = stdout.strip().split('\n')[0] if stdout else "unknown"
                self.logger.info(f"Found {tool}: {version}")
        
        if missing_tools:
            self.logger.error(f"Missing required tools: {missing_tools}")
            return False
        
        return True
    
    def build_implementation(self, impl_name: str) -> TestResult:
        """Build a specific implementation"""
        impl = self.config["implementations"][impl_name]
        self.logger.info(f"Building {impl['name']}...")
        
        start_time = time.time()
        
        # Change to implementation directory
        impl_dir = Path(impl["directory"])
        if not impl_dir.exists():
            return TestResult(
                name=f"build_{impl_name}",
                category="build",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Implementation directory not found: {impl_dir}"
            )
        
        # Run build command
        returncode, stdout, stderr = self.run_command(
            impl["build_command"],
            cwd=str(impl_dir),
            timeout=impl.get("build_timeout", 60)
        )
        
        duration = time.time() - start_time
        
        if returncode == 0:
            self.logger.info(f"✅ {impl_name} build successful ({duration:.1f}s)")
            return TestResult(
                name=f"build_{impl_name}",
                category="build",
                status="PASS",
                duration=duration,
                message=f"Build successful",
                details={"stdout": stdout, "stderr": stderr}
            )
        else:
            self.logger.error(f"❌ {impl_name} build failed ({duration:.1f}s)")
            return TestResult(
                name=f"build_{impl_name}",
                category="build",
                status="FAIL",
                duration=duration,
                message=f"Build failed with code {returncode}",
                details={"stdout": stdout, "stderr": stderr}
            )
    
    def run_unit_tests(self, impl_name: str) -> TestResult:
        """Run unit tests for an implementation"""
        impl = self.config["implementations"][impl_name]
        self.logger.info(f"Running unit tests for {impl['name']}...")
        
        start_time = time.time()
        
        # Run test command
        returncode, stdout, stderr = self.run_command(
            impl["test_command"],
            cwd=impl["directory"],
            timeout=impl.get("test_timeout", 60)
        )
        
        duration = time.time() - start_time
        
        if returncode == 0:
            self.logger.info(f"✅ {impl_name} unit tests passed ({duration:.1f}s)")
            return TestResult(
                name=f"unit_tests_{impl_name}",
                category="unit_tests",
                status="PASS",
                duration=duration,
                message="All unit tests passed",
                details={"stdout": stdout, "stderr": stderr}
            )
        else:
            self.logger.error(f"❌ {impl_name} unit tests failed ({duration:.1f}s)")
            return TestResult(
                name=f"unit_tests_{impl_name}",
                category="unit_tests",
                status="FAIL",
                duration=duration,
                message=f"Unit tests failed with code {returncode}",
                details={"stdout": stdout, "stderr": stderr}
            )
    
    def start_server(self, impl_name: str, socket_path: str) -> Optional[subprocess.Popen]:
        """Start a server implementation"""
        impl = self.config["implementations"][impl_name]
        self.logger.info(f"Starting {impl_name} server on {socket_path}")
        
        # Clean up any existing socket
        try:
            os.unlink(socket_path)
        except FileNotFoundError:
            pass
        
        # Start server process
        try:
            cmd = impl["server_command"] + [socket_path]
            proc = subprocess.Popen(
                cmd,
                cwd=impl["directory"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.running_processes.append(proc)
            
            # Wait for server to start
            max_wait = 10
            for _ in range(max_wait * 10):  # Check every 100ms
                if os.path.exists(socket_path):
                    self.logger.info(f"✅ {impl_name} server started successfully")
                    return proc
                if proc.poll() is not None:
                    # Process exited
                    stdout, stderr = proc.communicate()
                    self.logger.error(f"❌ {impl_name} server failed to start")
                    self.logger.error(f"stdout: {stdout}")
                    self.logger.error(f"stderr: {stderr}")
                    return None
                time.sleep(0.1)
            
            # Timeout waiting for server
            self.logger.error(f"❌ {impl_name} server failed to create socket within {max_wait}s")
            proc.terminate()
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error starting {impl_name} server: {e}")
            return None
    
    def test_client_communication(self, server_impl: str, client_impl: str, 
                                 socket_path: str, test_cmd: Dict) -> TestResult:
        """Test client communication with server"""
        test_name = f"{client_impl}_to_{server_impl}_{test_cmd['command']}"
        self.logger.info(f"Testing {test_name}")
        
        start_time = time.time()
        
        # Prepare client command
        client_config = self.config["implementations"][client_impl]
        
        # Create test command JSON
        command_json = {
            "channel": test_cmd["channel"],
            "command": test_cmd["command"],
            "parameters": test_cmd["parameters"],
            "reply_to": f"/tmp/reply_{int(time.time() * 1000000)}.sock"
        }
        
        # Write command to temp file
        cmd_file = self.temp_dir / f"cmd_{test_name}.json"
        with open(cmd_file, 'w') as f:
            json.dump(command_json, f)
        
        # Run client
        client_cmd = client_config["client_command"] + [socket_path, str(cmd_file)]
        returncode, stdout, stderr = self.run_command(
            client_cmd,
            cwd=client_config["directory"],
            timeout=test_cmd.get("timeout", 10)
        )
        
        duration = time.time() - start_time
        
        # Analyze response
        if returncode == 0:
            try:
                response = json.loads(stdout.strip()) if stdout.strip() else {}
                expected = test_cmd.get("expected_response", {})
                
                # Basic validation
                if self._validate_response(response, expected):
                    self.logger.info(f"✅ {test_name} passed ({duration:.1f}s)")
                    return TestResult(
                        name=test_name,
                        category="integration",
                        status="PASS",
                        duration=duration,
                        message="Communication successful",
                        details={"response": response, "expected": expected}
                    )
                else:
                    self.logger.error(f"❌ {test_name} response validation failed")
                    return TestResult(
                        name=test_name,
                        category="integration",
                        status="FAIL",
                        duration=duration,
                        message="Response validation failed",
                        details={"response": response, "expected": expected, "stderr": stderr}
                    )
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ {test_name} invalid JSON response: {e}")
                return TestResult(
                    name=test_name,
                    category="integration",
                    status="FAIL",
                    duration=duration,
                    message=f"Invalid JSON response: {e}",
                    details={"stdout": stdout, "stderr": stderr}
                )
        else:
            self.logger.error(f"❌ {test_name} client failed with code {returncode}")
            return TestResult(
                name=test_name,
                category="integration",
                status="FAIL",
                duration=duration,
                message=f"Client failed with code {returncode}",
                details={"stdout": stdout, "stderr": stderr}
            )
    
    def _validate_response(self, response: Dict, expected: Dict) -> bool:
        """Validate response against expected structure"""
        for key, expected_value in expected.items():
            if key not in response:
                self.logger.debug(f"Missing key in response: {key}")
                return False
            
            if isinstance(expected_value, str) and expected_value == "string":
                if not isinstance(response[key], str):
                    self.logger.debug(f"Expected string for {key}, got {type(response[key])}")
                    return False
            elif isinstance(expected_value, (int, float, str, bool)):
                if response[key] != expected_value:
                    self.logger.debug(f"Value mismatch for {key}: expected {expected_value}, got {response[key]}")
                    return False
        
        return True
    
    def run_cross_platform_tests(self) -> List[TestResult]:
        """Run comprehensive cross-platform communication tests"""
        self.logger.info("Running cross-platform communication tests...")
        results = []
        
        # Test all combinations
        all_combinations = (
            self.config["test_matrix"]["self_communication"]["combinations"] +
            self.config["test_matrix"]["cross_communication"]["combinations"]
        )
        
        for combo in all_combinations:
            server_impl = combo["server"]
            client_impl = combo["client"]
            
            self.logger.info(f"\n=== Testing {server_impl} server with {client_impl} client ===")
            
            # Use implementation-specific socket path
            socket_path = f"/tmp/test_{server_impl}_server.sock"
            
            # Start server
            server_proc = self.start_server(server_impl, socket_path)
            if not server_proc:
                results.append(TestResult(
                    name=f"server_start_{server_impl}_for_{client_impl}",
                    category="integration",
                    status="FAIL",
                    duration=0.0,
                    message=f"Failed to start {server_impl} server"
                ))
                continue
            
            try:
                # Run test commands
                for cmd_name, test_cmd in self.config["test_commands"].items():
                    result = self.test_client_communication(
                        server_impl, client_impl, socket_path, test_cmd
                    )
                    results.append(result)
                    
                    # Short delay between tests
                    time.sleep(0.5)
                    
            finally:
                # Cleanup server
                try:
                    server_proc.terminate()
                    server_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_proc.kill()
                except Exception as e:
                    self.logger.warning(f"Error stopping server: {e}")
                
                # Remove socket file
                try:
                    os.unlink(socket_path)
                except FileNotFoundError:
                    pass
        
        return results
    
    def run_performance_tests(self) -> List[TestResult]:
        """Run performance benchmarks"""
        self.logger.info("Running performance tests...")
        results = []
        
        # TODO: Implement performance tests
        # For now, return placeholder
        results.append(TestResult(
            name="performance_tests",
            category="performance",
            status="SKIP",
            duration=0.0,
            message="Performance tests not yet implemented"
        ))
        
        return results
    
    def run_conformance_tests(self) -> List[TestResult]:
        """Run API specification conformance tests"""
        self.logger.info("Running conformance tests...")
        results = []
        
        # TODO: Implement conformance tests
        # For now, return placeholder
        for test in self.config["conformance_tests"]:
            results.append(TestResult(
                name=f"conformance_{test['name']}",
                category="conformance",
                status="SKIP",
                duration=0.0,
                message=f"Conformance test {test['name']} not yet implemented"
            ))
        
        return results
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        skipped = len([r for r in self.results if r.status == "SKIP"])
        errors = len([r for r in self.results if r.status == "ERROR"])
        
        total_duration = sum(r.duration for r in self.results)
        
        # Group results by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)
        
        report = []
        report.append("=" * 80)
        report.append("JANUS CROSS-PLATFORM TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Duration: {total_duration:.1f}s")
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tests:   {total_tests}")
        report.append(f"Passed:        {passed} ({passed/total_tests*100:.1f}%)" if total_tests > 0 else "Passed:        0")
        report.append(f"Failed:        {failed} ({failed/total_tests*100:.1f}%)" if total_tests > 0 else "Failed:        0")
        report.append(f"Skipped:       {skipped} ({skipped/total_tests*100:.1f}%)" if total_tests > 0 else "Skipped:       0")
        report.append(f"Errors:        {errors} ({errors/total_tests*100:.1f}%)" if total_tests > 0 else "Errors:        0")
        report.append("")
        
        # Results by category
        for category, results in by_category.items():
            cat_passed = len([r for r in results if r.status == "PASS"])
            cat_total = len(results)
            
            report.append(f"{category.upper()} TESTS ({cat_passed}/{cat_total} passed)")
            report.append("-" * 40)
            
            for result in results:
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌", 
                    "SKIP": "⏭️",
                    "ERROR": "💥"
                }.get(result.status, "❓")
                
                report.append(f"{status_icon} {result.name:<40} {result.duration:>6.1f}s  {result.message}")
            
            report.append("")
        
        # Failed test details
        failed_tests = [r for r in self.results if r.status in ["FAIL", "ERROR"]]
        if failed_tests:
            report.append("FAILURE DETAILS")
            report.append("-" * 40)
            for result in failed_tests:
                report.append(f"\n{result.name}:")
                report.append(f"  Status: {result.status}")
                report.append(f"  Duration: {result.duration:.1f}s")
                report.append(f"  Message: {result.message}")
                if result.details:
                    for key, value in result.details.items():
                        if isinstance(value, str) and len(value) > 200:
                            value = value[:200] + "..."
                        report.append(f"  {key}: {value}")
        
        return "\n".join(report)
    
    def run_all_tests(self, categories: List[str] = None) -> bool:
        """Run all test categories"""
        if categories is None:
            categories = ["build", "unit", "integration", "performance", "conformance"]
        
        self.logger.info(f"Starting comprehensive test suite for categories: {categories}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.logger.error("Prerequisites check failed")
            return False
        
        all_success = True
        
        try:
            # Build phase
            if "build" in categories:
                self.logger.info("\n" + "="*60 + " BUILD PHASE " + "="*60)
                for impl_name in self.config["implementations"].keys():
                    result = self.build_implementation(impl_name)
                    self.results.append(result)
                    if result.status != "PASS":
                        all_success = False
            
            # Unit tests phase
            if "unit" in categories:
                self.logger.info("\n" + "="*60 + " UNIT TESTS PHASE " + "="*60)
                for impl_name in self.config["implementations"].keys():
                    result = self.run_unit_tests(impl_name)
                    self.results.append(result)
                    if result.status != "PASS":
                        all_success = False
            
            # Integration tests phase
            if "integration" in categories:
                self.logger.info("\n" + "="*60 + " INTEGRATION TESTS PHASE " + "="*60)
                integration_results = self.run_cross_platform_tests()
                self.results.extend(integration_results)
                if any(r.status != "PASS" for r in integration_results):
                    all_success = False
            
            # Performance tests phase
            if "performance" in categories:
                self.logger.info("\n" + "="*60 + " PERFORMANCE TESTS PHASE " + "="*60)
                performance_results = self.run_performance_tests()
                self.results.extend(performance_results)
            
            # Conformance tests phase
            if "conformance" in categories:
                self.logger.info("\n" + "="*60 + " CONFORMANCE TESTS PHASE " + "="*60)
                conformance_results = self.run_conformance_tests()
                self.results.extend(conformance_results)
        
        finally:
            self.cleanup()
        
        return all_success

def main():
    parser = argparse.ArgumentParser(description="Janus Cross-Platform Test Orchestrator")
    parser.add_argument("--config", default="test-spec.json", help="Test configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--categories", nargs="+", 
                       choices=["build", "unit", "integration", "performance", "conformance"],
                       default=["build", "unit", "integration"],
                       help="Test categories to run")
    parser.add_argument("--report", default="test_report.txt", help="Output report file")
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = TestOrchestrator(args.config, args.verbose)
    
    try:
        # Run tests
        success = orchestrator.run_all_tests(args.categories)
        
        # Generate report
        report = orchestrator.generate_report()
        
        # Write report to file
        with open(args.report, 'w') as f:
            f.write(report)
        
        # Print summary
        print("\n" + report)
        print(f"\nDetailed report written to: {args.report}")
        print(f"Log files available in: {orchestrator.log_dir}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        orchestrator.logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
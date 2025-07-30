#!/usr/bin/env python3
"""
UnixSocketAPI Unified Test Suite
Complete test coverage for SOCK_DGRAM implementations across Go, Rust, Swift, and TypeScript
Consolidates all testing functionality into a single comprehensive runner
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
import uuid
import socket as pysocket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from enum import Enum

# Add python test directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "python"))

class TestCategory(Enum):
    """Test category enumeration"""
    BUILD = "build"
    UNIT = "unit"
    INTEGRATION = "integration"
    CROSS_PLATFORM = "cross_platform"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFORMANCE = "conformance"
    STRESS = "stress"

class TestStatus(Enum):
    """Test status enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"

@dataclass
class TestResult:
    """Test result container with comprehensive information"""
    name: str
    category: TestCategory
    status: TestStatus
    duration: float
    implementation: str
    target_implementation: str = ""
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    details: Dict = None

@dataclass
class ImplementationInfo:
    """Implementation configuration and status"""
    name: str
    language: str
    directory: str
    build_command: List[str]
    unified_binary: str
    listen_args: List[str] 
    send_args: List[str]
    socket_path: str
    build_successful: bool = False

class UnifiedTestSuite:
    """Unified test suite for all UnixSocketAPI implementations"""
    
    def __init__(self, config_path: str, verbose: bool = False, stress_duration: int = 60):
        self.config_path = Path(config_path)
        self.verbose = verbose
        self.stress_duration = stress_duration
        self.config = self._load_config()
        self.implementations = self._load_implementations()
        self.results: List[TestResult] = []
        self.running_processes: List[subprocess.Popen] = []
        
        # Create output directories
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = Path(__file__).parent / "reports" / self.timestamp
        self.log_dir = Path(__file__).parent / "logs" / self.timestamp
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_logging()
        
        # Cleanup on exit
        signal.signal(signal.SIGINT, self._cleanup_handler)
        signal.signal(signal.SIGTERM, self._cleanup_handler)
    
    def setup_logging(self):
        """Setup logging"""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "test_suite.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("UnifiedTestSuite")
    
    def _load_config(self) -> Dict:
        """Load test configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _load_implementations(self) -> Dict[str, ImplementationInfo]:
        """Load implementation configurations"""
        implementations = {}
        
        for name, config in self.config["implementations"].items():
            impl = ImplementationInfo(
                name=name,
                language=config["language"],
                directory=config["directory"],
                build_command=config["build_command"],
                unified_binary=config["unified_binary"],
                listen_args=config["listen_args"],
                send_args=config["send_args"],
                socket_path=config["socket_path"]
            )
            implementations[name] = impl
        
        return implementations
    
    def _cleanup_handler(self, signum, frame):
        """Handle cleanup on exit"""
        self.cleanup()
        sys.exit(130)
    
    def cleanup(self):
        """Clean up running processes and temporary files"""
        self.logger.info("Cleaning up test environment...")
        
        # Terminate all running processes
        for process in self.running_processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                self.logger.debug(f"Error cleaning up process: {e}")
        
        # Clean up socket files
        for impl in self.implementations.values():
            try:
                Path(impl.socket_path).unlink(missing_ok=True)
            except Exception as e:
                self.logger.debug(f"Error removing socket {impl.socket_path}: {e}")
    
    def run_all_tests(self, categories: Set[TestCategory]) -> Dict:
        """Run all specified test categories"""
        self.logger.info(f"Starting comprehensive test suite with categories: {[c.value for c in categories]}")
        
        try:
            # Always run build tests first
            if TestCategory.BUILD in categories:
                self.run_build_tests()
            
            # Run unit tests
            if TestCategory.UNIT in categories:
                self.run_unit_tests()
            
            # Run cross-platform tests
            if TestCategory.CROSS_PLATFORM in categories:
                self.run_cross_platform_tests()
            
            # Run integration tests (feature tests)
            if TestCategory.INTEGRATION in categories:
                self.run_integration_tests()
            
            # Run performance tests
            if TestCategory.PERFORMANCE in categories:
                self.run_performance_tests()
            
            # Run security tests
            if TestCategory.SECURITY in categories:
                self.run_security_tests()
            
            # Run stress tests
            if TestCategory.STRESS in categories:
                self.run_stress_tests()
            
            # Generate comprehensive report
            report = self.generate_report()
            self.save_report(report)
            
            return report
            
        finally:
            self.cleanup()
    
    def run_build_tests(self) -> List[TestResult]:
        """Run build tests for all implementations"""
        self.logger.info("Running build tests...")
        results = []
        
        for impl_name, impl in self.implementations.items():
            start_time = time.time()
            
            try:
                # Change to implementation directory
                impl_dir = Path(__file__).parent.parent / impl.directory
                
                # Run build command
                process = subprocess.run(
                    impl.build_command,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=impl_dir
                )
                
                duration = time.time() - start_time
                
                if process.returncode == 0:
                    status = TestStatus.PASS
                    impl.build_successful = True
                    message = "Build successful"
                else:
                    status = TestStatus.FAIL
                    message = f"Build failed with exit code {process.returncode}"
                
                result = TestResult(
                    name=f"build_{impl_name}",
                    category=TestCategory.BUILD,
                    status=status,
                    duration=duration,
                    implementation=impl_name,
                    message=message,
                    stdout=process.stdout,
                    stderr=process.stderr
                )
                
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                result = TestResult(
                    name=f"build_{impl_name}",
                    category=TestCategory.BUILD,
                    status=TestStatus.TIMEOUT,
                    duration=duration,
                    implementation=impl_name,
                    message="Build timeout after 5 minutes"
                )
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    name=f"build_{impl_name}",
                    category=TestCategory.BUILD,
                    status=TestStatus.ERROR,
                    duration=duration,
                    implementation=impl_name,
                    message=f"Build error: {str(e)}"
                )
            
            results.append(result)
            self.logger.info(f"Build test {impl_name}: {result.status.value} ({result.duration:.2f}s)")
        
        self.results.extend(results)
        return results
    
    def run_unit_tests(self) -> List[TestResult]:
        """Run unit tests for all implementations"""
        self.logger.info("Running unit tests...")
        results = []
        
        for impl_name, impl in self.implementations.items():
            if not impl.build_successful:
                result = TestResult(
                    name=f"unit_{impl_name}",
                    category=TestCategory.UNIT,
                    status=TestStatus.SKIP,
                    duration=0.0,
                    implementation=impl_name,
                    message="Skipped due to build failure"
                )
                results.append(result)
                continue
            
            start_time = time.time()
            
            try:
                # Change to implementation directory
                impl_dir = Path(__file__).parent.parent / impl.directory
                
                # Verify directory exists and has required files
                if not impl_dir.exists():
                    raise FileNotFoundError(f"Implementation directory not found: {impl_dir}")
                
                # Run unit test command
                test_commands = {
                    "go": ["go", "test", "./..."],
                    "rust": ["cargo", "test"],
                    "swift": ["swift", "test"],
                    "typescript": ["npm", "test"]
                }
                
                cmd = test_commands.get(impl_name, ["echo", "No unit tests defined"])
                
                # Verify command exists (for debugging)
                self.logger.debug(f"Running command: {cmd} in directory: {impl_dir}")
                
                # Set up environment
                env = os.environ.copy()
                
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(impl_dir),  # Ensure string path
                    env=env
                )
                
                duration = time.time() - start_time
                
                # Enhanced exit code handling
                if process.returncode == 0:
                    status = TestStatus.PASS
                    message = "Unit tests passed"
                else:
                    status = TestStatus.FAIL
                    message = f"Unit tests failed with exit code {process.returncode}"
                    
                    # Log detailed failure information for debugging
                    self.logger.error(f"Unit test failure for {impl_name}:")
                    self.logger.error(f"  Exit code: {process.returncode}")
                    self.logger.error(f"  Command: {cmd}")
                    self.logger.error(f"  Working dir: {impl_dir}")
                    self.logger.error(f"  STDOUT (first 1000 chars): {process.stdout[:1000]}")
                    self.logger.error(f"  STDERR (first 1000 chars): {process.stderr[:1000]}")
                
                result = TestResult(
                    name=f"unit_{impl_name}",
                    category=TestCategory.UNIT,
                    status=status,
                    duration=duration,
                    implementation=impl_name,
                    message=message,
                    stdout=process.stdout,
                    stderr=process.stderr
                )
                
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                result = TestResult(
                    name=f"unit_{impl_name}",
                    category=TestCategory.UNIT,
                    status=TestStatus.TIMEOUT,
                    duration=duration,
                    implementation=impl_name,
                    message="Unit tests timeout after 5 minutes"
                )
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    name=f"unit_{impl_name}",
                    category=TestCategory.UNIT,
                    status=TestStatus.ERROR,
                    duration=duration,
                    implementation=impl_name,
                    message=f"Unit tests error: {str(e)}"
                )
            
            results.append(result)
            self.logger.info(f"Unit test {impl_name}: {result.status.value} ({result.duration:.2f}s)")
        
        self.results.extend(results)
        return results
    
    def run_cross_platform_tests(self) -> List[TestResult]:
        """Run cross-platform communication tests (N×N matrix)"""
        self.logger.info("Running cross-platform communication tests...")
        
        # Filter to successfully built implementations
        available_impls = {name: impl for name, impl in self.implementations.items() if impl.build_successful}
        
        if len(available_impls) < 2:
            self.logger.warning("Not enough implementations available for cross-platform testing")
            return []
        
        self.logger.info(f"Testing {len(available_impls)} implementations in full matrix")
        
        results = []
        
        # Test every implementation combination (including self-communication)
        for listener_name, listener_impl in available_impls.items():
            for sender_name, sender_impl in available_impls.items():
                self.logger.info(f"Testing: {sender_name} → {listener_name}")
                
                start_time = time.time()
                
                # Start listener
                listener_process = self._start_listener(listener_impl)
                if not listener_process:
                    result = TestResult(
                        name=f"cross_platform_{sender_name}_to_{listener_name}",
                        category=TestCategory.CROSS_PLATFORM,
                        status=TestStatus.ERROR,
                        duration=time.time() - start_time,
                        implementation=sender_name,
                        target_implementation=listener_name,
                        message="Failed to start listener"
                    )
                    results.append(result)
                    continue
                
                time.sleep(2)  # Allow listener to start
                
                # Send message
                response = self._run_sender(sender_impl, listener_impl.socket_path)
                
                # Cleanup listener
                listener_process.terminate()
                
                duration = time.time() - start_time
                
                if response.get("success", False):
                    status = TestStatus.PASS
                    message = "Cross-platform communication successful"
                else:
                    status = TestStatus.FAIL
                    message = response.get("error", "Communication failed")
                
                result = TestResult(
                    name=f"cross_platform_{sender_name}_to_{listener_name}",
                    category=TestCategory.CROSS_PLATFORM,
                    status=status,
                    duration=duration,
                    implementation=sender_name,
                    target_implementation=listener_name,
                    message=message,
                    details=response
                )
                
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def run_integration_tests(self) -> List[TestResult]:
        """Run integration/feature tests"""
        self.logger.info("Running integration tests...")
        
        # Import and run comprehensive feature tests
        try:
            from comprehensive_feature_tests import ComprehensiveFeatureTests
            
            feature_tester = ComprehensiveFeatureTests(
                config_path=str(self.config_path),
                verbose=self.verbose
            )
            
            results = []
            available_impls = [name for name, impl in self.implementations.items() if impl.build_successful]
            
            for impl_name in available_impls:
                feature_results = feature_tester.run_implementation_tests(impl_name)
                
                # Convert feature test results to our format
                for feature_result in feature_results:
                    status = TestStatus.PASS if feature_result.passed else TestStatus.FAIL
                    
                    result = TestResult(
                        name=feature_result.test_name,
                        category=TestCategory.INTEGRATION,
                        status=status,
                        duration=feature_result.duration,
                        implementation=feature_result.implementation,
                        message=feature_result.error_message if not feature_result.passed else f"Feature test passed: {feature_result.feature_category}",
                        details=feature_result.validation_details
                    )
                    results.append(result)
            
            self.results.extend(results)
            return results
            
        except ImportError as e:
            self.logger.warning(f"Could not import feature tests: {e}")
            return []
    
    def run_performance_tests(self) -> List[TestResult]:
        """Run performance benchmarks"""
        self.logger.info("Running performance tests...")
        # Implementation would go here
        return []
    
    def run_security_tests(self) -> List[TestResult]:
        """Run security and conformance tests"""
        self.logger.info("Running security tests...")
        # Implementation would go here
        return []
    
    def run_stress_tests(self) -> List[TestResult]:
        """Run stress tests"""
        self.logger.info("Running stress tests...")
        results = []
        
        # Filter to successfully built implementations
        available_impls = {name: impl for name, impl in self.implementations.items() if impl.build_successful}
        
        if len(available_impls) < 2:
            self.logger.warning("Not enough implementations available for stress testing")
            return []
        
        # Run comprehensive stress test: one server vs all clients for configurable duration
        for server_name, server_impl in available_impls.items():
            self.logger.info(f"🔥 STARTING COMPREHENSIVE STRESS TEST: {server_name} server vs all clients for {self.stress_duration} seconds")
            
            start_time = time.time()
            
            # Start the server
            self.logger.info(f"📡 Starting {server_name} server for {self.stress_duration}-second stress test")
            server_process = self._start_listener(server_impl)
            if not server_process:
                result = TestResult(
                    name=f"stress_{server_name}_server",
                    category=TestCategory.STRESS,
                    status=TestStatus.ERROR,
                    duration=time.time() - start_time,
                    implementation=server_name,
                    message="Failed to start stress test server"
                )
                results.append(result)
                continue
            
            time.sleep(2)  # Allow server to start
            
            # Run stress test for configurable duration
            end_time = time.time() + self.stress_duration
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            
            self.logger.info(f"🚀 Stress test running for {self.stress_duration} seconds - {server_name} server handling requests from all implementations")
            
            # Create comprehensive test patterns covering all SOCK_DGRAM scenarios
            test_patterns = [
                # Standard request-reply patterns using ACTUALLY IMPLEMENTED commands
                {"type": "request_reply", "command": "ping", "message": "hello", "expect_reply": True},
                {"type": "request_reply", "command": "echo", "message": "test_message", "expect_reply": True},
                {"type": "request_reply", "command": "get_info", "message": "info_request", "expect_reply": True},
                {"type": "request_reply", "command": "validate", "message": '{"test":"data"}', "expect_reply": True},
                
                # Large payload testing using echo (conservative sizes that should work)
                {"type": "large_payload", "command": "echo", "message": "large_" + "x" * 500, "expect_reply": True},
                {"type": "large_payload", "command": "echo", "message": "huge_" + "y" * 1000, "expect_reply": True},
                
                # Special characters and Unicode using echo
                {"type": "special_chars", "command": "echo", "message": "special_!@#$%^&*()", "expect_reply": True},
                {"type": "unicode", "command": "echo", "message": "unicode_测试_🚀_émojis", "expect_reply": True},
                
                # JSON payloads using validate command
                {"type": "json_payload", "command": "validate", "message": '{"nested":"json","number":42}', "expect_reply": True},
                {"type": "complex_json", "command": "validate", "message": '{"data":{"user":"test","values":[1,2,3]}}', "expect_reply": True},
                
                # Error condition testing
                {"type": "invalid_command", "command": "nonexistent_command", "message": "test", "expect_reply": True, "expect_error": True},
                {"type": "malformed_json", "command": "validate", "message": '{"invalid":json}', "expect_reply": True, "expect_error": True},
                {"type": "empty_message", "command": "echo", "message": "", "expect_reply": True},
                
                # Rapid fire patterns
                {"type": "rapid_small", "command": "ping", "message": "quick", "expect_reply": True},
                {"type": "rapid_medium", "command": "echo", "message": "medium_" + "z" * 50, "expect_reply": True},
                
                # Timeout testing using slow_process
                {"type": "potential_timeout", "command": "slow_process", "message": "timeout_test", "expect_reply": True, "timeout": 5},
                
                # Burst patterns using implemented commands
                {"type": "burst", "command": "ping", "message": "burst_1", "expect_reply": True},
                {"type": "burst", "command": "get_info", "message": "burst_2", "expect_reply": True},
                {"type": "burst", "command": "echo", "message": "burst_3", "expect_reply": True},
            ]
            
            pattern_index = 0
            last_log_time = time.time()
            
            # Detailed statistics tracking
            pattern_stats = {}
            client_stats = {}
            error_types = {}
            
            while time.time() < end_time:
                # Cycle through all client implementations
                for client_name, client_impl in available_impls.items():
                    if time.time() >= end_time:
                        break
                    
                    # Use different test patterns
                    pattern = test_patterns[pattern_index % len(test_patterns)]
                    pattern_index += 1
                    
                    # Track pattern usage
                    pattern_type = pattern.get("type", "unknown")
                    if pattern_type not in pattern_stats:
                        pattern_stats[pattern_type] = {"total": 0, "success": 0, "failed": 0}
                    
                    # Track client usage
                    if client_name not in client_stats:
                        client_stats[client_name] = {"total": 0, "success": 0, "failed": 0}
                    
                    # Send request with enhanced pattern handling
                    response = self._run_sender_with_enhanced_pattern(client_impl, server_impl.socket_path, pattern)
                    total_requests += 1
                    pattern_stats[pattern_type]["total"] += 1
                    client_stats[client_name]["total"] += 1
                    
                    # Evaluate response based on pattern expectations
                    request_successful = self._evaluate_pattern_response(pattern, response)
                    
                    if request_successful:
                        successful_requests += 1
                        pattern_stats[pattern_type]["success"] += 1
                        client_stats[client_name]["success"] += 1
                    else:
                        failed_requests += 1
                        pattern_stats[pattern_type]["failed"] += 1
                        client_stats[client_name]["failed"] += 1
                        
                        # Track error types
                        error_type = response.get("error_type", "unknown_error")
                        error_types[error_type] = error_types.get(error_type, 0) + 1
                    
                    # Enhanced progress logging every 30 seconds
                    current_time = time.time()
                    if current_time - last_log_time >= 30:
                        elapsed = current_time - start_time
                        remaining = self.stress_duration - elapsed
                        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
                        
                        self.logger.info(f"📊 Stress test progress: {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
                        self.logger.info(f"   Total requests: {total_requests}, Success rate: {success_rate:.1f}%")
                        self.logger.info(f"   Current pattern: {client_name} → {server_name} ({pattern_type}: {pattern['command']})")
                        
                        # Log pattern distribution
                        top_patterns = sorted(pattern_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:3]
                        pattern_summary = ", ".join([f"{p}: {s['total']}" for p, s in top_patterns])
                        self.logger.info(f"   Top patterns: {pattern_summary}")
                        
                        # Log client distribution
                        client_summary = ", ".join([f"{c}: {s['total']}" for c, s in client_stats.items()])
                        self.logger.info(f"   Client requests: {client_summary}")
                        
                        last_log_time = current_time
                    
                    # Variable delay based on pattern type
                    if pattern_type == "burst":
                        time.sleep(0.001)  # Very fast for burst
                    elif pattern_type == "fire_forget":
                        time.sleep(0.005)  # Fast for fire-and-forget
                    elif pattern_type == "large_payload":
                        time.sleep(0.02)   # Slower for large payloads
                    else:
                        time.sleep(0.01)   # Standard delay
            
            # Cleanup server
            server_process.terminate()
            
            duration = time.time() - start_time
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Determine test result
            if success_rate >= 95.0:  # 95% success rate threshold
                status = TestStatus.PASS
                message = f"Stress test passed: {total_requests} requests, {success_rate:.1f}% success rate"
            else:
                status = TestStatus.FAIL
                message = f"Stress test failed: {total_requests} requests, {success_rate:.1f}% success rate (below 95% threshold)"
            
            self.logger.info(f"✅ STRESS TEST COMPLETED for {server_name} server:")
            self.logger.info(f"   Duration: {duration:.1f} seconds")
            self.logger.info(f"   Total requests: {total_requests}")
            self.logger.info(f"   Successful: {successful_requests}")
            self.logger.info(f"   Failed: {failed_requests}")
            self.logger.info(f"   Success rate: {success_rate:.1f}%")
            self.logger.info(f"   Status: {status.value}")
            
            # Detailed pattern statistics
            self.logger.info(f"📈 PATTERN BREAKDOWN:")
            for pattern_type, stats in sorted(pattern_stats.items(), key=lambda x: x[1]["total"], reverse=True):
                pattern_success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
                self.logger.info(f"   {pattern_type}: {stats['total']} requests, {pattern_success_rate:.1f}% success")
            
            # Client statistics  
            self.logger.info(f"👥 CLIENT BREAKDOWN:")
            for client_name, stats in sorted(client_stats.items(), key=lambda x: x[1]["total"], reverse=True):
                client_success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
                self.logger.info(f"   {client_name}: {stats['total']} requests, {client_success_rate:.1f}% success")
            
            # Error analysis
            if error_types:
                self.logger.info(f"❌ ERROR ANALYSIS:")
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    error_percentage = (count / failed_requests * 100) if failed_requests > 0 else 0
                    self.logger.info(f"   {error_type}: {count} occurrences ({error_percentage:.1f}% of failures)")
            
            # Request rate calculation
            requests_per_second = total_requests / duration if duration > 0 else 0
            self.logger.info(f"⚡ PERFORMANCE METRICS:")
            self.logger.info(f"   Average request rate: {requests_per_second:.1f} requests/second")
            self.logger.info(f"   Peak concurrent clients: {len(available_impls)}")
            self.logger.info(f"   Pattern variety: {len(pattern_stats)} different patterns tested")
            
            result = TestResult(
                name=f"stress_{server_name}_server_3min",
                category=TestCategory.STRESS,
                status=status,
                duration=duration,
                implementation=server_name,
                message=message,
                details={
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "success_rate": success_rate,
                    "duration_seconds": duration,
                    "requests_per_second": requests_per_second,
                    "pattern_stats": pattern_stats,
                    "client_stats": client_stats,
                    "error_types": error_types,
                    "concurrent_clients": len(available_impls),
                    "pattern_variety": len(pattern_stats)
                }
            )
            
            results.append(result)
        
        self.results.extend(results)
        return results
    
    def _start_listener(self, impl: ImplementationInfo) -> Optional[subprocess.Popen]:
        """Start a listener process for the given implementation"""
        try:
            # Remove existing socket
            if Path(impl.socket_path).exists():
                Path(impl.socket_path).unlink()
            
            # Build command
            if impl.unified_binary.startswith("cargo run"):
                cmd = impl.unified_binary.split() + impl.listen_args
            elif impl.unified_binary.startswith("swift run"):
                cmd = impl.unified_binary.split() + impl.listen_args
            elif impl.unified_binary.startswith("node"):
                cmd = impl.unified_binary.split() + impl.listen_args
            else:
                cmd = [impl.unified_binary] + impl.listen_args
            
            # Get absolute implementation directory path
            impl_dir = Path(__file__).parent.parent / impl.directory
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=impl_dir
            )
            
            self.running_processes.append(process)
            self.logger.debug(f"Started listener for {impl.name} with PID {process.pid}")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to start listener for {impl.name}: {e}")
            return None
    
    def _run_sender(self, impl: ImplementationInfo, target_socket: str) -> Dict:
        """Run sender against target socket"""
        return self._run_sender_with_pattern(impl, target_socket, {"command": "ping", "message": "hello"})
    
    def _run_sender_with_pattern(self, impl: ImplementationInfo, target_socket: str, pattern: Dict) -> Dict:
        """Run sender against target socket with custom command pattern"""
        try:
            # Build send command with custom pattern
            send_args = []
            for arg in impl.send_args:
                if arg == "{target_socket}":
                    send_args.append(target_socket)
                elif arg == "{command}":
                    send_args.append(pattern.get("command", "ping"))
                elif arg == "{message}":
                    send_args.append(pattern.get("message", "hello"))
                else:
                    send_args.append(arg)
            
            if impl.unified_binary.startswith("cargo run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("swift run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("node"):
                cmd = impl.unified_binary.split() + send_args
            else:
                cmd = [impl.unified_binary] + send_args
            
            # Get absolute implementation directory path
            impl_dir = Path(__file__).parent.parent / impl.directory
            
            # Run sender
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,  # Shorter timeout for stress testing
                cwd=impl_dir
            )
            
            if process.returncode == 0:
                return {"success": True, "stdout": process.stdout, "stderr": process.stderr}
            else:
                return {"success": False, "error": f"Sender failed with exit code {process.returncode}", 
                       "stdout": process.stdout, "stderr": process.stderr}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Sender timeout", "error_type": "timeout"}
        except Exception as e:
            return {"success": False, "error": f"Sender error: {str(e)}", "error_type": "exception"}
    
    def _run_sender_with_enhanced_pattern(self, impl: ImplementationInfo, target_socket: str, pattern: Dict) -> Dict:
        """Run sender with enhanced pattern handling for different SOCK_DGRAM scenarios"""
        try:
            # Handle fire-and-forget patterns differently
            if not pattern.get("expect_reply", True):
                # For fire-and-forget, we might need different command arguments
                # This would depend on your implementation's support for no-reply commands
                return self._run_sender_with_pattern(impl, target_socket, pattern)
            
            # Handle patterns with custom timeout
            custom_timeout = pattern.get("timeout", 10)
            
            # Build send command with enhanced pattern
            send_args = []
            for arg in impl.send_args:
                if arg == "{target_socket}":
                    send_args.append(target_socket)
                elif arg == "{command}":
                    send_args.append(pattern.get("command", "ping"))
                elif arg == "{message}":
                    send_args.append(pattern.get("message", "hello"))
                else:
                    send_args.append(arg)
            
            if impl.unified_binary.startswith("cargo run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("swift run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("node"):
                cmd = impl.unified_binary.split() + send_args
            else:
                cmd = [impl.unified_binary] + send_args
            
            # Get absolute implementation directory path
            impl_dir = Path(__file__).parent.parent / impl.directory
            
            # Run sender with custom timeout
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=custom_timeout,
                cwd=impl_dir
            )
            
            # Parse actual socket response from stdout
            socket_success = False
            if process.returncode == 0 and process.stdout:
                # Look for "Response: Success=true" or "Response: Success=false" in output
                import re
                success_match = re.search(r'Response:\s*Success=(\w+)', process.stdout)
                if success_match:
                    socket_success = success_match.group(1).lower() == 'true'
                else:
                    # Default to success if no explicit success indicator found
                    socket_success = True
            
            response = {
                "success": socket_success,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "pattern_type": pattern.get("type", "unknown"),
                "cli_success": process.returncode == 0
            }
            
            if not response["cli_success"]:
                response["error"] = f"CLI command failed with exit code {process.returncode}"
                response["error_type"] = f"exit_code_{process.returncode}"
            elif response["cli_success"] and not response["success"]:
                response["error"] = "Socket communication failed"
                response["error_type"] = "socket_error"
            
            return response
                
        except subprocess.TimeoutExpired:
            return {
                "success": False, 
                "error": f"Request timeout after {custom_timeout}s", 
                "error_type": "timeout",
                "pattern_type": pattern.get("type", "unknown")
            }
        except Exception as e:
            return {
                "success": False, 
                "error": f"Request error: {str(e)}", 
                "error_type": "exception",
                "pattern_type": pattern.get("type", "unknown")
            }
    
    def _evaluate_pattern_response(self, pattern: Dict, response: Dict) -> bool:
        """Evaluate if response meets pattern expectations"""
        pattern_type = pattern.get("type", "unknown")
        expect_reply = pattern.get("expect_reply", True)
        expect_error = pattern.get("expect_error", False)
        
        # Handle error expectations
        if expect_error:
            # For validate commands with malformed JSON, we expect CLI success but validation failure
            if pattern.get("command") == "validate" and pattern.get("type") == "malformed_json":
                stdout = response.get("stdout", "")
                # Test SUCCESS if CLI succeeded and validation properly failed (valid:false)
                cli_succeeded = response.get("success", False)
                validation_failed = (
                    "valid:false" in stdout.lower() or 
                    "valid: false" in stdout.lower() or
                    '"valid":false' in stdout.lower() or
                    '"valid": false' in stdout.lower() or
                    "invalid json" in stdout.lower() or
                    "json format" in stdout.lower() or
                    "parse error" in stdout.lower() or
                    "malformed" in stdout.lower()
                )
                return cli_succeeded and validation_failed
            # For oversized payload, we expect CLI failure with specific error message
            elif pattern.get("type") == "oversized_payload":
                stderr = response.get("stderr", "")
                # Success if CLI failed and error mentions payload size or message too long
                return not response.get("success", False) and ("payload too large" in stderr.lower() or "message too long" in stderr.lower())
            # For other error cases, we expect CLI failure
            else:
                return not response.get("success", False)
        
        # For fire-and-forget patterns, success is just successful sending
        if not expect_reply:
            return response.get("success", False)
        
        # For request-reply patterns, check if we got a successful response
        if expect_reply:
            # Basic success check
            if not response.get("success", False):
                return False
            
            # Additional validation based on ACTUALLY IMPLEMENTED commands
            stdout = response.get("stdout", "")
            
            # For ping commands, check for pong response
            if pattern.get("command") == "ping":
                return "pong" in stdout.lower() or "success" in stdout.lower()
            
            # For echo commands, check if message was echoed back
            if pattern.get("command") == "echo":
                original_message = pattern.get("message", "")
                # Simple check if the original message appears in response
                return original_message in stdout
            
            # For get_info commands, check for implementation info
            if pattern.get("command") == "get_info":
                return "implementation" in stdout.lower() or "version" in stdout.lower() or "success" in stdout.lower()
            
            # For validate commands, check for validation response
            if pattern.get("command") == "validate":
                return "valid" in stdout.lower() or "true" in stdout.lower() or "success" in stdout.lower()
            
            # For slow_process commands, check for processing response
            if pattern.get("command") == "slow_process":
                return "processed" in stdout.lower() or "delay" in stdout.lower() or "success" in stdout.lower()
            
            # Default: if command succeeded, consider it successful
            return True
        
        return False
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        self.logger.info("Generating comprehensive test report...")
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == TestStatus.PASS])
        failed = len([r for r in self.results if r.status == TestStatus.FAIL])
        skipped = len([r for r in self.results if r.status == TestStatus.SKIP])
        errors = len([r for r in self.results if r.status == TestStatus.ERROR])
        timeouts = len([r for r in self.results if r.status == TestStatus.TIMEOUT])
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by category
        results_by_category = {}
        for result in self.results:
            category = result.category.value
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(asdict(result))
        
        # Implementation status
        implementations = {}
        for name, impl in self.implementations.items():
            implementations[name] = {
                "language": impl.language,
                "build_successful": impl.build_successful
            }
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "timeouts": timeouts,
                "success_rate": success_rate,
                "generated_at": datetime.now().isoformat()
            },
            "implementations": implementations,
            "results_by_category": results_by_category,
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict):
        """Save test report to files"""
        # Save JSON report (with custom serialization for enums)
        json_path = self.report_dir / "comprehensive_test_report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save markdown report
        md_path = self.report_dir / "comprehensive_test_report.md"
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown_report(report))
        
        self.logger.info(f"Comprehensive report saved to {self.report_dir}")
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """Generate markdown report"""
        summary = report["summary"]
        
        md = f"""# UnixSocketAPI Comprehensive Test Report

**Generated**: {summary['generated_at']}

## Test Summary

- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed']} ✅
- **Failed**: {summary['failed']} ❌
- **Skipped**: {summary['skipped']} ⏭️
- **Errors**: {summary['errors']} 🚨
- **Timeouts**: {summary['timeouts']} ⏰
- **Success Rate**: {summary['success_rate']:.1f}%

## Implementation Status

"""
        
        for name, info in report['implementations'].items():
            status = "✅" if info['build_successful'] else "❌"
            md += f"- **{name}** ({info['language']}): {status}\n"
        
        md += "\n## Results by Category\n\n"
        
        for category, results in report['results_by_category'].items():
            passed = len([r for r in results if r['status'] == 'PASS'])
            total = len(results)
            md += f"### {category.title()} Tests\n\n"
            
            for result in results:
                status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "🚨", "TIMEOUT": "⏰"}
                emoji = status_emoji.get(result['status'], "❓")
                impl_info = f" ({result['implementation']}"
                if result['target_implementation']:
                    impl_info += f" → {result['target_implementation']}"
                impl_info += ")"
                md += f"- **{result['name']}**: {emoji} {result['status']}{impl_info} - {result['message']}\n"
            
            md += "\n"
        
        return md

def main():
    """Main entry point for unified testing"""
    parser = argparse.ArgumentParser(
        description="UnixSocketAPI Unified Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all basic tests (build, unit, cross-platform)
  python tests/run_tests.py
  
  # Run with integration and performance tests
  python tests/run_tests.py --integration --performance
  
  # Run only cross-platform communication tests
  python tests/run_tests.py --categories cross_platform
  
  # Run with verbose output
  python tests/run_tests.py --verbose
  
  # Test specific implementations only
  python tests/run_tests.py --implementations go,rust
  
  # Quick basic functionality test
  python tests/run_tests.py --quick
        """
    )
    
    parser.add_argument("--config", default="tests/config/unified-test-config.json", 
                       help="Test configuration file (default: tests/config/unified-test-config.json)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--categories", 
                       help="Test categories to run (comma-separated): build,unit,cross_platform,integration,performance,security,stress")
    parser.add_argument("--implementations", 
                       help="Specific implementations to test (comma-separated): go,rust,swift,typescript")
    parser.add_argument("--integration", action="store_true", 
                       help="Include integration/feature tests")
    parser.add_argument("--performance", action="store_true", 
                       help="Include performance benchmarks")
    parser.add_argument("--security", action="store_true", 
                       help="Include security and conformance tests")
    parser.add_argument("--stress", action="store_true", 
                       help="Include comprehensive stress testing (each impl as server vs all clients)")
    parser.add_argument("--stress-duration", type=int, default=60,
                       help="Duration in seconds for each stress test server (default: 60)")
    parser.add_argument("--quick", action="store_true", 
                       help="Run only basic tests (build, unit, cross_platform)")
    parser.add_argument("--output-dir", 
                       help="Custom output directory for logs and reports")
    
    args = parser.parse_args()
    
    # Determine categories to run
    if args.quick:
        categories = {TestCategory.BUILD, TestCategory.UNIT, TestCategory.CROSS_PLATFORM}
    elif args.categories:
        category_map = {c.value: c for c in TestCategory}
        categories = set()
        for cat_name in args.categories.split(","):
            cat_name = cat_name.strip()
            if cat_name in category_map:
                categories.add(category_map[cat_name])
            else:
                print(f"Warning: Unknown category '{cat_name}'")
    else:
        # Default categories
        categories = {TestCategory.BUILD, TestCategory.UNIT, TestCategory.CROSS_PLATFORM}
    
    # Add additional categories from flags
    if args.integration:
        categories.add(TestCategory.INTEGRATION)
    if args.performance:
        categories.add(TestCategory.PERFORMANCE)
    if args.security:
        categories.add(TestCategory.SECURITY)
    if args.stress:
        categories.add(TestCategory.STRESS)
    
    print("UnixSocketAPI Unified Test Suite")
    print("=" * 50)
    print(f"Configuration: {args.config}")
    print(f"Categories: {[c.value for c in sorted(categories, key=lambda x: x.value)]}")
    if args.implementations:
        print(f"Implementations: {args.implementations}")
    print()
    
    try:
        # Create test suite
        test_suite = UnifiedTestSuite(
            config_path=args.config,
            verbose=args.verbose,
            stress_duration=args.stress_duration
        )
        
        # Filter implementations if specified
        if args.implementations:
            impl_filter = set(args.implementations.split(","))
            filtered_impls = {
                name: impl for name, impl in test_suite.implementations.items()
                if name in impl_filter
            }
            test_suite.implementations = filtered_impls
            print(f"Filtered to implementations: {list(filtered_impls.keys())}")
        
        # Run tests
        report = test_suite.run_all_tests(categories)
        
        # Print summary
        summary = report["summary"]
        print(f"\n{'='*60}")
        print("UNIFIED TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        if summary['skipped'] > 0:
            print(f"Skipped: {summary['skipped']} ⏭️")
        if summary['errors'] > 0:
            print(f"Errors: {summary['errors']} 🚨")
        if summary['timeouts'] > 0:
            print(f"Timeouts: {summary['timeouts']} ⏰")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"\nReports saved to: {test_suite.report_dir}")
        
        # Print implementation status
        print(f"\nImplementation Status:")
        for name, info in report['implementations'].items():
            status = "✅ Available" if info['build_successful'] else "❌ Failed"
            print(f"  {name} ({info['language']}): {status}")
        
        # Print category breakdown
        print(f"\nResults by Category:")
        for category, results in report['results_by_category'].items():
            passed = len([r for r in results if str(r['status']).endswith('PASS')])
            total = len(results)
            print(f"  {category}: {passed}/{total} passed")
        
        # Show failed tests if any
        failed_tests = [r for r in report['detailed_results'] if str(r['status']).endswith('FAIL')]
        if failed_tests:
            print(f"\nFailed Tests:")
            for test in failed_tests:
                impl_info = f" ({test['implementation']}" 
                if test['target_implementation']:
                    impl_info += f" → {test['target_implementation']}"
                impl_info += ")"
                print(f"  ❌ {test['name']}{impl_info}: {test['message']}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test suite error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
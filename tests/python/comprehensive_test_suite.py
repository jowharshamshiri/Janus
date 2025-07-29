#!/usr/bin/env python3
"""
UnixSocketAPI Comprehensive Test Suite
Complete test coverage for SOCK_DGRAM implementations across Go, Rust, Swift, and TypeScript
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
    implementation: Optional[str] = None
    target_implementation: Optional[str] = None
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    details: Dict[str, Any] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class ImplementationInfo:
    """Information about a specific implementation"""
    name: str
    language: str
    directory: Path
    build_command: List[str]
    test_command: List[str]
    unified_binary: str
    listen_args: List[str]
    send_args: List[str]
    socket_path: str
    is_available: bool = False
    build_successful: bool = False

class ComprehensiveTestSuite:
    """Comprehensive test suite for SOCK_DGRAM Unix Socket implementations"""
    
    def __init__(self, config_path: str = "test-spec.json", verbose: bool = False):
        self.config_path = Path(config_path)
        self.verbose = verbose
        self.config = self._load_config()
        self.results: List[TestResult] = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="unixsock_comprehensive_test_"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path.cwd() / "tests" / "logs" / timestamp
        self.report_dir = Path.cwd() / "tests" / "reports" / timestamp
        self.running_processes: List[subprocess.Popen] = []
        
        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_logging()
        self.load_implementations()
        
        # Signal handling
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
                logging.FileHandler(self.log_dir / "comprehensive_test.log")
            ]
        )
        self.logger = logging.getLogger("ComprehensiveTestSuite")
    
    def _load_config(self) -> Dict:
        """Load test configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in configuration: {e}")
            sys.exit(1)
    
    def load_implementations(self):
        """Load and validate implementation configurations"""
        self.implementations: Dict[str, ImplementationInfo] = {}
        
        # Get project root (parent of tests directory)
        project_root = Path(__file__).parent.parent.parent
        
        for impl_name, impl_config in self.config["implementations"].items():
            # Map implementation configurations to unified SOCK_DGRAM model
            impl_info = ImplementationInfo(
                name=impl_name,
                language=impl_config.get("language", impl_name),
                directory=project_root / impl_config["directory"],
                build_command=impl_config["build_command"],
                test_command=impl_config["test_command"],
                unified_binary=self._get_unified_binary_path(impl_name, impl_config),
                listen_args=self._get_listen_args(impl_name, impl_config),
                send_args=self._get_send_args(impl_name, impl_config),
                socket_path=impl_config["socket_path"]
            )
            
            self.implementations[impl_name] = impl_info
            self.logger.debug(f"Loaded implementation: {impl_name}")
    
    def _get_unified_binary_path(self, impl_name: str, config: Dict) -> str:
        """Get unified binary path for SOCK_DGRAM process"""
        if impl_name == "go":
            return "./unixsock-dgram"
        elif impl_name == "rust":
            return "cargo run --bin unixsock-dgram --"
        elif impl_name == "swift":
            return "swift run SwiftUnixSockDgram"
        elif impl_name == "typescript":
            return "node dist/bin/unixsock-dgram.js"
        else:
            return config.get("unified_binary", "")
    
    def _get_listen_args(self, impl_name: str, config: Dict) -> List[str]:
        """Get listen arguments for unified binary"""
        socket_path = config["socket_path"]
        base_args = ["--listen", "--socket", socket_path]
        return base_args
    
    def _get_send_args(self, impl_name: str, config: Dict) -> List[str]:
        """Get send arguments for unified binary"""
        base_args = ["--send-to", "{target_socket}", "--command", "ping", "--message", "test"]
        return base_args
    
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
                self.logger.warning(f"Error cleaning up process: {e}")
        
        # Clean up temporary files
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp directory: {e}")
        
        # Remove socket files
        for impl in self.implementations.values():
            try:
                if Path(impl.socket_path).exists():
                    Path(impl.socket_path).unlink()
            except Exception as e:
                self.logger.warning(f"Error cleaning up socket {impl.socket_path}: {e}")
    
    def run_build_tests(self) -> List[TestResult]:
        """Run build tests for all implementations"""
        self.logger.info("Running build tests...")
        results = []
        
        for impl_name, impl in self.implementations.items():
            start_time = time.time()
            
            try:
                self.logger.info(f"Building {impl_name}...")
                
                # Change to implementation directory
                original_cwd = os.getcwd()
                os.chdir(impl.directory)
                
                # Run build command
                process = subprocess.run(
                    impl.build_command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                os.chdir(original_cwd)
                
                duration = time.time() - start_time
                
                if process.returncode == 0:
                    impl.build_successful = True
                    impl.is_available = True
                    status = TestStatus.PASS
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
                self.logger.info(f"Running unit tests for {impl_name}...")
                
                # Change to implementation directory
                original_cwd = os.getcwd()
                os.chdir(impl.directory)
                
                # Run test command
                process = subprocess.run(
                    impl.test_command,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                os.chdir(original_cwd)
                
                duration = time.time() - start_time
                
                if process.returncode == 0:
                    status = TestStatus.PASS
                    message = "Unit tests passed"
                else:
                    status = TestStatus.FAIL
                    message = f"Unit tests failed with exit code {process.returncode}"
                
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
                    message="Unit tests timeout after 10 minutes"
                )
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    name=f"unit_{impl_name}",
                    category=TestCategory.UNIT,
                    status=TestStatus.ERROR,
                    duration=duration,
                    implementation=impl_name,
                    message=f"Unit test error: {str(e)}"
                )
            
            results.append(result)
            self.logger.info(f"Unit test {impl_name}: {result.status.value} ({result.duration:.2f}s)")
        
        return results
    
    def run_cross_platform_tests(self) -> List[TestResult]:
        """Run comprehensive cross-platform communication tests"""
        self.logger.info("Running cross-platform communication tests...")
        results = []
        
        available_impls = {name: impl for name, impl in self.implementations.items() 
                          if impl.is_available and impl.build_successful}
        
        if len(available_impls) < 1:
            self.logger.warning("Need at least 1 working implementation for communication testing")
            return results
        
        self.logger.info(f"Testing {len(available_impls)} implementations in full matrix")
        
        # Complete test matrix: each implementation as listener, all implementations (including self) as senders
        for listener_name, listener_impl in available_impls.items():
            for sender_name, sender_impl in available_impls.items():
                # Test all combinations including self-communication
                self.logger.info(f"Testing: {sender_name} → {listener_name}")
                
                result = self._test_cross_platform_communication(
                    listener_name, listener_impl,
                    sender_name, sender_impl
                )
                results.append(result)
        
        # Additional feature tests for each implementation
        for impl_name, impl in available_impls.items():
            feature_results = self._test_implementation_features(impl_name, impl)
            results.extend(feature_results)
        
        return results
    
    def _test_cross_platform_communication(self, 
                                         listener_name: str, listener_impl: ImplementationInfo,
                                         sender_name: str, sender_impl: ImplementationInfo) -> TestResult:
        """Test communication between two implementations"""
        test_name = f"cross_platform_{sender_name}_to_{listener_name}"
        start_time = time.time()
        
        try:
            # Start listener process
            listener_process = self._start_listener(listener_impl)
            if not listener_process:
                return TestResult(
                    name=test_name,
                    category=TestCategory.CROSS_PLATFORM,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=sender_name,
                    target_implementation=listener_name,
                    message="Failed to start listener"
                )
            
            # Wait for listener to be ready
            if not self._wait_for_socket(listener_impl.socket_path, timeout=10):
                listener_process.terminate()
                return TestResult(
                    name=test_name,
                    category=TestCategory.CROSS_PLATFORM,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=sender_name,
                    target_implementation=listener_name,
                    message="Listener failed to create socket"
                )
            
            # Give listener time to stabilize
            time.sleep(1)
            
            # Run sender
            sender_result = self._run_sender(sender_impl, listener_impl.socket_path)
            
            # Cleanup listener
            listener_process.terminate()
            try:
                listener_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                listener_process.kill()
            
            duration = time.time() - start_time
            
            if sender_result["success"]:
                status = TestStatus.PASS
                message = "Cross-platform communication successful"
            else:
                status = TestStatus.FAIL
                message = f"Sender failed: {sender_result['error']}"
            
            return TestResult(
                name=test_name,
                category=TestCategory.CROSS_PLATFORM,
                status=status,
                duration=duration,
                implementation=sender_name,
                target_implementation=listener_name,
                message=message,
                stdout=sender_result.get("stdout", ""),
                stderr=sender_result.get("stderr", ""),
                details={
                    "listener_socket": listener_impl.socket_path,
                    "sender_args": sender_result.get("command", [])
                }
            )
            
        except Exception as e:
            return TestResult(
                name=test_name,
                category=TestCategory.CROSS_PLATFORM,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                implementation=sender_name,
                target_implementation=listener_name,
                message=f"Test error: {str(e)}"
            )
    
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
            
            # Change to implementation directory
            original_cwd = os.getcwd()
            os.chdir(impl.directory)
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=impl.directory
            )
            
            os.chdir(original_cwd)
            
            self.running_processes.append(process)
            self.logger.debug(f"Started listener for {impl.name} with PID {process.pid}")
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to start listener for {impl.name}: {e}")
            return None
    
    def _run_sender(self, impl: ImplementationInfo, target_socket: str) -> Dict:
        """Run sender against target socket"""
        try:
            # Build send command
            send_args = []
            for arg in impl.send_args:
                if arg == "{target_socket}":
                    send_args.append(target_socket)
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
            
            # Change to implementation directory
            original_cwd = os.getcwd()
            os.chdir(impl.directory)
            
            # Run sender
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=impl.directory
            )
            
            os.chdir(original_cwd)
            
            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "command": cmd,
                "error": None if process.returncode == 0 else f"Exit code {process.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "command": cmd,
                "error": "Sender timeout after 30 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "command": [],
                "error": str(e)
            }
    
    def _wait_for_socket(self, socket_path: str, timeout: int = 10) -> bool:
        """Wait for socket file to be created"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if Path(socket_path).exists():
                return True
            time.sleep(0.1)
        return False
    
    def _test_implementation_features(self, impl_name: str, impl: ImplementationInfo) -> List[TestResult]:
        """Test comprehensive features for a single implementation"""
        results = []
        
        # Test different commands and features
        test_commands = [
            ("ping", "hello", "Basic ping command"),
            ("echo", "test_message", "Echo command with message"),
            ("ping", "special_chars_!@#$%", "Special characters handling"),
            ("echo", "long_message_" + "x" * 100, "Long message handling"),
        ]
        
        for command, message, description in test_commands:
            result = self._test_specific_command(impl_name, impl, command, message, description)
            results.append(result)
        
        # Test timeout handling
        timeout_result = self._test_timeout_handling(impl_name, impl)
        results.append(timeout_result)
        
        # Test concurrent requests
        concurrent_result = self._test_concurrent_requests(impl_name, impl)
        results.append(concurrent_result)
        
        return results
    
    def _test_specific_command(self, impl_name: str, impl: ImplementationInfo, 
                              command: str, message: str, description: str) -> TestResult:
        """Test a specific command with the implementation"""
        test_name = f"feature_{impl_name}_{command}_{message[:20]}"
        start_time = time.time()
        
        try:
            # Start listener
            listener_process = self._start_listener(impl)
            if not listener_process:
                return TestResult(
                    name=test_name,
                    category=TestCategory.INTEGRATION,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=impl_name,
                    message=f"{description}: Failed to start listener"
                )
            
            # Wait for socket
            if not self._wait_for_socket(impl.socket_path, timeout=10):
                listener_process.terminate()
                return TestResult(
                    name=test_name,
                    category=TestCategory.INTEGRATION,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=impl_name,
                    message=f"{description}: Socket not created"
                )
            
            time.sleep(1)  # Stabilize
            
            # Run sender with specific command
            sender_result = self._run_sender_with_command(impl, impl.socket_path, command, message)
            
            # Cleanup
            listener_process.terminate()
            try:
                listener_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                listener_process.kill()
            
            duration = time.time() - start_time
            
            if sender_result["success"]:
                status = TestStatus.PASS
                result_message = f"{description}: Success"
            else:
                status = TestStatus.FAIL
                result_message = f"{description}: {sender_result['error']}"
            
            return TestResult(
                name=test_name,
                category=TestCategory.INTEGRATION,
                status=status,
                duration=duration,
                implementation=impl_name,
                message=result_message,
                stdout=sender_result.get("stdout", ""),
                stderr=sender_result.get("stderr", ""),
                details={
                    "command": command,
                    "message": message,
                    "description": description
                }
            )
            
        except Exception as e:
            return TestResult(
                name=test_name,
                category=TestCategory.INTEGRATION,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                implementation=impl_name,
                message=f"{description}: Error - {str(e)}"
            )
    
    def _run_sender_with_command(self, impl: ImplementationInfo, target_socket: str, 
                                command: str, message: str) -> Dict:
        """Run sender with specific command and message"""
        try:
            # Build send command with custom command and message
            send_args = ["--send-to", target_socket, "--command", command, "--message", message]
            
            if impl.unified_binary.startswith("cargo run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("swift run"):
                cmd = impl.unified_binary.split() + send_args
            elif impl.unified_binary.startswith("node"):
                cmd = impl.unified_binary.split() + send_args
            else:
                cmd = [impl.unified_binary] + send_args
            
            # Change to implementation directory
            original_cwd = os.getcwd()
            os.chdir(impl.directory)
            
            # Run sender
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=impl.directory
            )
            
            os.chdir(original_cwd)
            
            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "command": cmd,
                "error": None if process.returncode == 0 else f"Exit code {process.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "command": cmd,
                "error": "Command timeout after 30 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "command": [],
                "error": str(e)
            }
    
    def _test_timeout_handling(self, impl_name: str, impl: ImplementationInfo) -> TestResult:
        """Test timeout handling behavior"""
        test_name = f"feature_{impl_name}_timeout_handling"
        start_time = time.time()
        
        try:
            # Try to send to non-existent socket (should timeout gracefully)
            nonexistent_socket = f"/tmp/nonexistent_socket_{uuid.uuid4().hex[:8]}.sock"
            
            sender_result = self._run_sender_with_command(impl, nonexistent_socket, "ping", "test")
            
            duration = time.time() - start_time
            
            # Should fail gracefully, not crash
            if not sender_result["success"]:
                # Check if it's a proper timeout/connection error (not a crash)
                if "timeout" in sender_result["error"].lower() or \
                   "connection" in sender_result["error"].lower() or \
                   "no such file" in sender_result.get("stderr", "").lower():
                    status = TestStatus.PASS
                    message = "Timeout handling: Graceful failure"
                else:
                    status = TestStatus.FAIL
                    message = f"Timeout handling: Unexpected error - {sender_result['error']}"
            else:
                status = TestStatus.FAIL
                message = "Timeout handling: Should have failed but succeeded"
            
            return TestResult(
                name=test_name,
                category=TestCategory.INTEGRATION,
                status=status,
                duration=duration,
                implementation=impl_name,
                message=message,
                details={"test_type": "timeout_handling"}
            )
            
        except Exception as e:
            return TestResult(
                name=test_name,
                category=TestCategory.INTEGRATION,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                implementation=impl_name,
                message=f"Timeout test error: {str(e)}"
            )
    
    def _test_concurrent_requests(self, impl_name: str, impl: ImplementationInfo) -> TestResult:
        """Test concurrent request handling"""
        test_name = f"feature_{impl_name}_concurrent_requests"
        start_time = time.time()
        
        try:
            # Start listener
            listener_process = self._start_listener(impl)
            if not listener_process:
                return TestResult(
                    name=test_name,
                    category=TestCategory.STRESS,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=impl_name,
                    message="Concurrent test: Failed to start listener"
                )
            
            if not self._wait_for_socket(impl.socket_path, timeout=10):
                listener_process.terminate()
                return TestResult(
                    name=test_name,
                    category=TestCategory.STRESS,
                    status=TestStatus.FAIL,
                    duration=time.time() - start_time,
                    implementation=impl_name,
                    message="Concurrent test: Socket not created"
                )
            
            time.sleep(1)  # Stabilize
            
            # Run multiple concurrent requests
            num_concurrent = 5
            concurrent_results = []
            
            def run_concurrent_sender(index):
                return self._run_sender_with_command(
                    impl, impl.socket_path, 
                    "ping", f"concurrent_test_{index}"
                )
            
            with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [executor.submit(run_concurrent_sender, i) for i in range(num_concurrent)]
                concurrent_results = [f.result() for f in as_completed(futures)]
            
            # Cleanup
            listener_process.terminate()
            try:
                listener_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                listener_process.kill()
            
            duration = time.time() - start_time
            
            # Analyze results
            successful_requests = sum(1 for r in concurrent_results if r["success"])
            success_rate = successful_requests / num_concurrent * 100
            
            if success_rate >= 80:  # Allow some tolerance for concurrent stress
                status = TestStatus.PASS
                message = f"Concurrent test: {successful_requests}/{num_concurrent} succeeded ({success_rate:.1f}%)"
            else:
                status = TestStatus.FAIL
                message = f"Concurrent test: Only {successful_requests}/{num_concurrent} succeeded ({success_rate:.1f}%)"
            
            return TestResult(
                name=test_name,
                category=TestCategory.STRESS,
                status=status,
                duration=duration,
                implementation=impl_name,
                message=message,
                details={
                    "concurrent_requests": num_concurrent,
                    "successful_requests": successful_requests,
                    "success_rate": success_rate
                }
            )
            
        except Exception as e:
            return TestResult(
                name=test_name,
                category=TestCategory.STRESS,
                status=TestStatus.ERROR,
                duration=time.time() - start_time,
                implementation=impl_name,
                message=f"Concurrent test error: {str(e)}"
            )
    
    def run_performance_tests(self) -> List[TestResult]:
        """Run performance benchmark tests"""
        self.logger.info("Running performance tests...")
        results = []
        
        # Import performance benchmark module
        try:
            from . import performance_benchmark
            benchmark = performance_benchmark.PerformanceBenchmark(
                config_path=str(self.config_path),
                verbose=self.verbose
            )
            
            # Run benchmarks for each available implementation
            for impl_name, impl in self.implementations.items():
                if impl.is_available and impl.build_successful:
                    perf_results = benchmark.run_implementation_benchmarks(impl_name)
                    
                    for perf_result in perf_results:
                        test_result = TestResult(
                            name=f"performance_{impl_name}_{perf_result.name}",
                            category=TestCategory.PERFORMANCE,
                            status=TestStatus.PASS,
                            duration=0.0,  # Performance tests track their own timing
                            implementation=impl_name,
                            message=f"{perf_result.metric}: {perf_result.value} {perf_result.unit}",
                            details=asdict(perf_result)
                        )
                        results.append(test_result)
            
        except ImportError:
            self.logger.warning("Performance benchmark module not available")
        except Exception as e:
            self.logger.error(f"Performance test error: {e}")
        
        return results
    
    def run_security_tests(self) -> List[TestResult]:
        """Run security and conformance tests"""
        self.logger.info("Running security tests...")
        results = []
        
        # Import API spec validator
        try:
            from . import api_spec_validator
            validator = api_spec_validator.APISpecValidator(
                api_spec_path=str(self.config_path),
                verbose=self.verbose
            )
            
            # Run security validation for each implementation
            for impl_name, impl in self.implementations.items():
                if impl.is_available and impl.build_successful:
                    # SOCK_DGRAM usage validation
                    sock_dgram_valid, violations = validator.validate_sock_dgram_usage(str(impl.directory))
                    
                    result = TestResult(
                        name=f"security_sock_dgram_{impl_name}",
                        category=TestCategory.SECURITY,
                        status=TestStatus.PASS if sock_dgram_valid else TestStatus.FAIL,
                        duration=0.0,
                        implementation=impl_name,
                        message="SOCK_DGRAM only validation" + ("" if sock_dgram_valid else f": {violations}"),
                        details={"violations": violations}
                    )
                    results.append(result)
            
        except ImportError:
            self.logger.warning("API spec validator module not available")
        except Exception as e:
            self.logger.error(f"Security test error: {e}")
        
        return results
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        self.logger.info("Generating comprehensive test report...")
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASS])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAIL])
        skipped_tests = len([r for r in self.results if r.status == TestStatus.SKIP])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR])
        timeout_tests = len([r for r in self.results if r.status == TestStatus.TIMEOUT])
        
        # Group results by category  
        results_by_category = {}
        for result in self.results:
            category = result.category.value
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(asdict(result))
        
        # Generate report
        report = {
            "summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "errors": error_tests,
                "timeouts": timeout_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "implementations": {
                name: {
                    "available": impl.is_available,
                    "build_successful": impl.build_successful,
                    "language": impl.language,
                    "directory": str(impl.directory)
                }
                for name, impl in self.implementations.items()
            },
            "results_by_category": results_by_category,
            "detailed_results": [asdict(result) for result in self.results]
        }
        
        # Save JSON report
        json_report_path = self.report_dir / "comprehensive_test_report.json"
        with open(json_report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save markdown report
        md_report_path = self.report_dir / "comprehensive_test_report.md"
        self._generate_markdown_report(report, md_report_path)
        
        self.logger.info(f"Comprehensive report saved to {self.report_dir}")
        
        return report
    
    def _generate_markdown_report(self, report: Dict, output_path: Path):
        """Generate markdown test report"""
        with open(output_path, 'w') as f:
            f.write("# UnixSocketAPI Comprehensive Test Report\n\n")
            f.write(f"**Generated**: {report['summary']['timestamp']}\n\n")
            
            # Summary
            f.write("## Test Summary\n\n")
            f.write(f"- **Total Tests**: {report['summary']['total_tests']}\n")
            f.write(f"- **Passed**: {report['summary']['passed']} ✅\n")
            f.write(f"- **Failed**: {report['summary']['failed']} ❌\n")
            f.write(f"- **Skipped**: {report['summary']['skipped']} ⏭️\n")
            f.write(f"- **Errors**: {report['summary']['errors']} 🚨\n")
            f.write(f"- **Timeouts**: {report['summary']['timeouts']} ⏰\n")
            f.write(f"- **Success Rate**: {report['summary']['success_rate']:.1f}%\n\n")
            
            # Implementation status
            f.write("## Implementation Status\n\n")
            for name, info in report['implementations'].items():
                status = "✅" if info['build_successful'] else "❌"
                f.write(f"- **{name}** ({info['language']}): {status}\n")
            f.write("\n")
            
            # Results by category
            f.write("## Results by Category\n\n")
            for category, results in report['results_by_category'].items():
                f.write(f"### {category.title()} Tests\n\n")
                for result in results:
                    status_icon = {
                        "PASS": "✅",
                        "FAIL": "❌", 
                        "SKIP": "⏭️",
                        "ERROR": "🚨",
                        "TIMEOUT": "⏰"
                    }.get(result['status'], "❓")
                    
                    f.write(f"- **{result['name']}**: {status_icon} {result['status']}")
                    if result['implementation']:
                        f.write(f" ({result['implementation']}")
                        if result['target_implementation']:
                            f.write(f" → {result['target_implementation']}")
                        f.write(")")
                    f.write(f" - {result['message']}\n")
                f.write("\n")
    
    def run_all_tests(self, categories: Set[TestCategory] = None) -> Dict:
        """Run all specified test categories"""
        if categories is None:
            categories = {TestCategory.BUILD, TestCategory.UNIT, TestCategory.CROSS_PLATFORM}
        
        self.logger.info(f"Starting comprehensive test suite with categories: {[c.value for c in categories]}")
        
        try:
            # Build tests (always run first)
            if TestCategory.BUILD in categories:
                build_results = self.run_build_tests()
                self.results.extend(build_results)
            
            # Unit tests
            if TestCategory.UNIT in categories:
                unit_results = self.run_unit_tests()
                self.results.extend(unit_results)
            
            # Cross-platform tests
            if TestCategory.CROSS_PLATFORM in categories:
                cross_platform_results = self.run_cross_platform_tests()
                self.results.extend(cross_platform_results)
            
            # Performance tests
            if TestCategory.PERFORMANCE in categories:
                performance_results = self.run_performance_tests()
                self.results.extend(performance_results)
            
            # Security tests
            if TestCategory.SECURITY in categories:
                security_results = self.run_security_tests()
                self.results.extend(security_results)
            
            # Generate comprehensive report
            report = self.generate_comprehensive_report()
            
            return report
            
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="UnixSocketAPI Comprehensive Test Suite")
    parser.add_argument("--config", default="test-spec.json", help="Test configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--categories", default="build,unit,cross_platform", 
                       help="Test categories to run (comma-separated)")
    parser.add_argument("--implementations", help="Specific implementations to test (comma-separated)")
    parser.add_argument("--performance", action="store_true", help="Include performance tests")
    parser.add_argument("--security", action="store_true", help="Include security tests")
    
    args = parser.parse_args()
    
    # Parse categories
    category_map = {c.value: c for c in TestCategory}
    categories = set()
    for cat_name in args.categories.split(","):
        cat_name = cat_name.strip()
        if cat_name in category_map:
            categories.add(category_map[cat_name])
    
    if args.performance:
        categories.add(TestCategory.PERFORMANCE)
    if args.security:
        categories.add(TestCategory.SECURITY)
    
    # Run tests
    test_suite = ComprehensiveTestSuite(config_path=args.config, verbose=args.verbose)
    
    try:
        report = test_suite.run_all_tests(categories)
        
        # Print summary
        summary = report["summary"]
        print(f"\n{'='*60}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌") 
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Report saved to: {test_suite.report_dir}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test suite error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
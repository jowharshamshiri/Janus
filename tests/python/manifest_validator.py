#!/usr/bin/env python3
"""
Manifest Validator for Janus
Validates implementations against the central Manifest
"""

import json
import socket
import os
import time
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

class ManifestValidator:
    """Validates implementations against Manifest"""
    
    def __init__(self, manifest_path: str, verbose: bool = False):
        self.manifest_path = manifest_path
        self.verbose = verbose
        self.manifest = self._load_manifest()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("ManifestValidator")
    
    def _load_manifest(self) -> Dict:
        """Load Manifest"""
        with open(self.manifest_path, 'r') as f:
            return json.load(f)
    
    def validate_sock_dgram_usage(self, implementation_dir: str) -> Tuple[bool, List[str]]:
        """Validate that implementation uses only SOCK_DGRAM sockets"""
        violations = []
        
        # Search for SOCK_STREAM usage in source files
        source_patterns = {
            'go': ['*.go'],
            'rust': ['*.rs'],
            'swift': ['*.swift'],
            'typescript': ['*.ts', '*.js']
        }
        
        impl_name = Path(implementation_dir).name.lower()
        lang = None
        for key in source_patterns:
            if key in impl_name:
                lang = key
                break
        
        if not lang:
            violations.append(f"Unknown implementation language for {implementation_dir}")
            return False, violations
        
        # Check for forbidden patterns
        forbidden_patterns = [
            'SOCK_STREAM',
            'tcp',
            'listen(',
            'accept(',
            'connect(' if lang != 'go' else None,  # Go connect is different
            'ConnectionPool',
            'persistent',
            'keepalive'
        ]
        
        forbidden_patterns = [p for p in forbidden_patterns if p is not None]
        
        for pattern in source_patterns[lang]:
            try:
                result = subprocess.run(
                    ['find', implementation_dir, '-name', pattern, '-type', 'f'],
                    capture_output=True, text=True
                )
                
                for file_path in result.stdout.strip().split('\n'):
                    if not file_path:
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for forbidden in forbidden_patterns:
                            if forbidden.lower() in content.lower():
                                violations.append(f"Found forbidden pattern '{forbidden}' in {file_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not read {file_path}: {e}")
                        
            except Exception as e:
                self.logger.warning(f"Error searching for {pattern}: {e}")
        
        return len(violations) == 0, violations
    
    def validate_message_format(self, implementation_dir: str) -> Tuple[bool, List[str]]:
        """Validate that implementation uses correct JSON message format"""
        violations = []
        
        # Required message fields according to spec
        required_fields = ['channel', 'command', 'reply_to']
        
        # Search for message creation/parsing code
        try:
            result = subprocess.run(
                ['grep', '-r', '-i', 'channel.*command', implementation_dir],
                capture_output=True, text=True
            )
            
            if not result.stdout:
                violations.append("No message creation/parsing code found")
            else:
                # Basic validation that required fields are mentioned
                content = result.stdout.lower()
                for field in required_fields:
                    if field not in content:
                        violations.append(f"Required field '{field}' not found in message handling code")
                        
        except Exception as e:
            violations.append(f"Error searching message format code: {e}")
        
        return len(violations) == 0, violations
    
    def validate_api_commands(self, socket_path: str, server_process: subprocess.Popen) -> Tuple[bool, List[str]]:
        """Validate that server implements required API commands"""
        violations = []
        
        # Wait for server to be ready
        max_wait = 10
        for _ in range(max_wait * 10):
            if os.path.exists(socket_path):
                break
            if server_process.poll() is not None:
                violations.append("Server process exited before creating socket")
                return False, violations
            time.sleep(0.1)
        else:
            violations.append(f"Server did not create socket within {max_wait}s")
            return False, violations
        
        # Test each required command from Manifest
        if 'channels' in self.manifest:
            for channel_id, channel in self.manifest['channels'].items():
                for command_name, command_spec in channel.get('commands', {}).items():
                    success, error = self._test_command(socket_path, channel_id, command_name, command_spec)
                    if not success:
                        violations.append(f"Command {channel_id}.{command_name} failed: {error}")
        
        return len(violations) == 0, violations
    
    def _test_command(self, socket_path: str, channel: str, command: str, spec: Dict) -> Tuple[bool, str]:
        """Test a specific API command"""
        try:
            # Create client socket
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            reply_path = f"/tmp/test_reply_{int(time.time() * 1000000)}.sock"
            
            try:
                # Bind reply socket
                client_sock.bind(reply_path)
                
                # Prepare test message
                test_params = {}
                if 'parameters' in spec:
                    for param_name, param_spec in spec['parameters'].items():
                        if 'example' in param_spec:
                            test_params[param_name] = param_spec['example']
                        elif param_spec.get('type') == 'string':
                            test_params[param_name] = "test"
                        elif param_spec.get('type') == 'integer':
                            test_params[param_name] = 42
                        elif param_spec.get('type') == 'boolean':
                            test_params[param_name] = True
                
                message = {
                    'channel': channel,
                    'command': command,
                    'parameters': test_params,
                    'reply_to': reply_path
                }
                
                # Send message
                message_json = json.dumps(message).encode('utf-8')
                client_sock.sendto(message_json, socket_path)
                
                # Wait for response
                client_sock.settimeout(5.0)
                response_data, _ = client_sock.recvfrom(4096)
                
                # Parse response
                response = json.loads(response_data.decode('utf-8'))
                
                # Basic validation
                if 'status' not in response:
                    return False, "Response missing 'status' field"
                
                return True, ""
                
            finally:
                client_sock.close()
                try:
                    os.unlink(reply_path)
                except FileNotFoundError:
                    pass
                    
        except socket.timeout:
            return False, "Response timeout"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON response: {e}"
        except Exception as e:
            return False, f"Test error: {e}"
    
    def validate_timeout_handling(self, socket_path: str) -> Tuple[bool, List[str]]:
        """Validate proper timeout handling"""
        violations = []
        
        try:
            # Test with invalid reply_to path (should timeout gracefully)
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            invalid_reply_path = "/tmp/nonexistent_reply.sock"
            
            message = {
                'channel': 'system',
                'command': 'ping',
                'parameters': {'message': 'timeout_test'},
                'reply_to': invalid_reply_path
            }
            
            message_json = json.dumps(message).encode('utf-8')
            client_sock.sendto(message_json, socket_path)
            client_sock.close()
            
            # Server should handle this gracefully without crashing
            time.sleep(2)  # Give server time to process
            
        except Exception as e:
            violations.append(f"Error testing timeout handling: {e}")
        
        return len(violations) == 0, violations
    
    def validate_security_constraints(self, implementation_dir: str) -> Tuple[bool, List[str]]:
        """Validate security constraints are implemented"""
        violations = []
        
        # Check for security validation code
        security_patterns = [
            'validate',
            'sanitize',
            'security',
            'auth',
            'permission'
        ]
        
        found_security = False
        try:
            for pattern in security_patterns:
                result = subprocess.run(
                    ['grep', '-r', '-i', pattern, implementation_dir],
                    capture_output=True, text=True
                )
                if result.stdout:
                    found_security = True
                    break
            
            if not found_security:
                violations.append("No security validation code found")
                
        except Exception as e:
            violations.append(f"Error checking security constraints: {e}")
        
        return len(violations) == 0, violations
    
    def validate_implementation(self, implementation_dir: str, 
                              start_server_cmd: List[str],
                              socket_path: str) -> Dict[str, Any]:
        """Comprehensive validation of an implementation"""
        results = {
            'implementation': Path(implementation_dir).name,
            'socket_path': socket_path,
            'timestamp': time.time(),
            'tests': {},
            'overall_success': True
        }
        
        self.logger.info(f"Validating {results['implementation']}...")
        
        # 1. Validate SOCK_DGRAM usage
        success, violations = self.validate_sock_dgram_usage(implementation_dir)
        results['tests']['sock_dgram_only'] = {
            'success': success,
            'violations': violations
        }
        if not success:
            results['overall_success'] = False
            self.logger.error(f"SOCK_DGRAM validation failed: {violations}")
        
        # 2. Validate message format
        success, violations = self.validate_message_format(implementation_dir)
        results['tests']['message_format'] = {
            'success': success,
            'violations': violations
        }
        if not success:
            results['overall_success'] = False
            self.logger.error(f"Message format validation failed: {violations}")
        
        # 3. Validate security constraints
        success, violations = self.validate_security_constraints(implementation_dir)
        results['tests']['security_constraints'] = {
            'success': success,
            'violations': violations
        }
        if not success:
            results['overall_success'] = False
            self.logger.warning(f"Security validation issues: {violations}")
        
        # 4. Start server and validate API commands
        server_process = None
        try:
            # Clean up any existing socket
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
            
            # Start server
            self.logger.info(f"Starting server: {' '.join(start_server_cmd)}")
            server_process = subprocess.Popen(
                start_server_cmd + [socket_path],
                cwd=implementation_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Validate API commands
            success, violations = self.validate_api_commands(socket_path, server_process)
            results['tests']['api_commands'] = {
                'success': success,
                'violations': violations
            }
            if not success:
                results['overall_success'] = False
                self.logger.error(f"API commands validation failed: {violations}")
            
            # Validate timeout handling
            success, violations = self.validate_timeout_handling(socket_path)
            results['tests']['timeout_handling'] = {
                'success': success,
                'violations': violations
            }
            if not success:
                results['overall_success'] = False
                self.logger.error(f"Timeout handling validation failed: {violations}")
            
        except Exception as e:
            results['tests']['server_startup'] = {
                'success': False,
                'violations': [f"Server startup failed: {e}"]
            }
            results['overall_success'] = False
            self.logger.error(f"Server startup failed: {e}")
        
        finally:
            # Cleanup
            if server_process:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
                except Exception as e:
                    self.logger.warning(f"Error stopping server: {e}")
            
            try:
                os.unlink(socket_path)
            except FileNotFoundError:
                pass
        
        if results['overall_success']:
            self.logger.info(f"✅ {results['implementation']} validation passed")
        else:
            self.logger.error(f"❌ {results['implementation']} validation failed")
        
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Manifest compliance")
    parser.add_argument("--manifest", default="example-manifest.json", help="Manifest file")
    parser.add_argument("--implementation", required=True, help="Implementation directory")
    parser.add_argument("--server-cmd", nargs="+", required=True, help="Server startup command")
    parser.add_argument("--socket-path", required=True, help="Socket path for testing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", default="validation_results.json", help="Output file")
    
    args = parser.parse_args()
    
    validator = ManifestValidator(args.manifest, args.verbose)
    results = validator.validate_implementation(
        args.implementation,
        args.server_cmd,
        args.socket_path
    )
    
    # Write results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nValidation Results for {results['implementation']}")
    print("=" * 50)
    
    for test_name, test_result in results['tests'].items():
        status = "✅ PASS" if test_result['success'] else "❌ FAIL"
        print(f"{test_name:20} {status}")
        
        if test_result['violations']:
            for violation in test_result['violations']:
                print(f"  - {violation}")
    
    print(f"\nOverall: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
    print(f"Detailed results written to: {args.output}")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Test script for the spec command across all Janus implementations.
Validates that all implementations properly return their loaded API specifications.
"""

import json
import subprocess
import time
import os
import signal
import sys
import socket
import tempfile
from pathlib import Path

# Implementation configurations
IMPLEMENTATIONS = {
    'go': {
        'name': 'Go',
        'start_cmd': ['go', 'run', './cmd/janus', '--listen', '--socket', '{socket}', '--spec', '{spec}'],
        'test_cmd': ['go', 'run', './cmd/janus', '--send-to', '{socket}', '--command', 'spec', '--channel', 'test'],
        'dir': 'GoJanus'
    },
    'rust': {
        'name': 'Rust', 
        'start_cmd': ['cargo', 'run', '--bin', 'janus', '--', '--listen', '--socket', '{socket}', '--spec', '{spec}'],
        'test_cmd': ['cargo', 'run', '--bin', 'janus', '--', '--send-to', '{socket}', '--command', 'spec'],
        'dir': 'RustJanus'
    },
    'swift': {
        'name': 'Swift',
        'start_cmd': ['swift', 'run', 'SwiftJanusDgram', '--listen', '--socket', '{socket}', '--spec', '{spec}'],
        'test_cmd': ['swift', 'run', 'SwiftJanusDgram', '--send-to', '{socket}', '--command', 'spec'],
        'dir': 'SwiftJanus'
    },
    'typescript': {
        'name': 'TypeScript',
        'start_cmd': ['node', 'dist/bin/janus.js', '--listen', '--socket', '{socket}', '--spec', '{spec}'],
        'test_cmd': ['node', 'dist/bin/janus.js', '--send-to', '{socket}', '--command', 'spec'],
        'dir': 'TypeScriptJanus'
    }
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def cleanup_socket(socket_path):
    """Remove socket file if it exists"""
    try:
        os.unlink(socket_path)
    except FileNotFoundError:
        pass

def wait_for_socket(socket_path, timeout=10):
    """Wait for socket to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.connect(socket_path)
            sock.close()
            return True
        except (socket.error, FileNotFoundError):
            time.sleep(0.1)
    return False

def build_implementation(impl_name, config):
    """Build implementation if needed"""
    print(f"Building {config['name']} implementation...")
    
    original_dir = os.getcwd()
    try:
        os.chdir(config['dir'])
        
        if impl_name == 'go':
            result = subprocess.run(['go', 'build', './cmd/janus'], 
                                  capture_output=True, text=True, timeout=30)
        elif impl_name == 'rust':
            result = subprocess.run(['cargo', 'build', '--bin', 'janus'], 
                                  capture_output=True, text=True, timeout=60)
        elif impl_name == 'swift':
            result = subprocess.run(['swift', 'build'], 
                                  capture_output=True, text=True, timeout=60)
        elif impl_name == 'typescript':
            # Check if dist exists
            if not os.path.exists('dist'):
                result = subprocess.run(['npm', 'run', 'build'], 
                                      capture_output=True, text=True, timeout=60)
            else:
                result = subprocess.CompletedProcess(['echo', 'built'], 0, '', '')
        
        if result.returncode != 0:
            print_error(f"Build failed: {result.stderr}")
            return False
        else:
            print_success(f"Build successful")
            return True
            
    except subprocess.TimeoutExpired:
        print_error(f"Build timeout")
        return False
    except Exception as e:
        print_error(f"Build error: {e}")
        return False
    finally:
        os.chdir(original_dir)

def test_spec_command(impl_name, config):
    """Test the spec command for a specific implementation"""
    print(f"\nTesting {config['name']} spec command...")
    
    # Create unique socket path
    socket_path = f"/tmp/{impl_name}_spec_test_{os.getpid()}.sock"
    spec_path = os.path.abspath("tests/config/spec-command-test-api.json")
    
    # Clean up any existing socket
    cleanup_socket(socket_path)
    
    # Start server
    original_dir = os.getcwd()
    server_proc = None
    
    try:
        os.chdir(config['dir'])
        
        # Format commands
        start_cmd = [arg.format(socket=socket_path, spec=spec_path) for arg in config['start_cmd']]
        test_cmd = [arg.format(socket=socket_path, spec=spec_path) for arg in config['test_cmd']]
        
        print(f"Starting server: {' '.join(start_cmd)}")
        server_proc = subprocess.Popen(start_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        if not wait_for_socket(socket_path, timeout=15):
            print_error(f"Server failed to start within timeout")
            return False
        
        print_success(f"Server started successfully")
        
        # Test spec command
        print(f"Testing spec command: {' '.join(test_cmd)}")
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print_error(f"Spec command failed: {result.stderr}")
            return False
        
        # Parse and validate response
        output = result.stdout
        print(f"Raw output: {output[:200]}...")
        
        # Look for success indicators in output
        if 'Success=true' in output or 'success": true' in output or 'success: true' in output:
            # Try to extract and validate spec data
            if 'specification' in output.lower():
                print_success(f"Spec command returned specification data")
                
                # Additional validation: check if it contains expected fields
                if 'Cross-Platform Test API' in output:
                    print_success(f"Returned correct specification name")
                if 'version' in output.lower() and '1.0.0' in output:
                    print_success(f"Returned correct version")
                if 'channels' in output.lower():
                    print_success(f"Returned channels data")
                    
                return True
            else:
                print_error(f"Response missing specification data")
                return False
        else:
            print_error(f"Command reported failure")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"Spec command timeout")
        return False
    except Exception as e:
        print_error(f"Test error: {e}")
        return False
    finally:
        # Cleanup
        if server_proc:
            try:
                server_proc.terminate()
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
            except:
                pass
        
        cleanup_socket(socket_path)
        os.chdir(original_dir)

def run_cross_platform_spec_test():
    """Test spec command across all implementations"""
    print_header("JANUS SPEC COMMAND CROSS-PLATFORM TEST")
    
    # Check test spec file exists
    spec_file = "tests/config/spec-command-test-api.json"
    if not os.path.exists(spec_file):
        print_error(f"{spec_file} not found")
        return False
    
    print_success(f"Found {spec_file}")
    
    results = {}
    
    # Test each implementation
    for impl_name, config in IMPLEMENTATIONS.items():
        print_header(f"TESTING {config['name'].upper()} IMPLEMENTATION")
        
        # Check if implementation directory exists
        if not os.path.exists(config['dir']):
            print_warning(f"Directory {config['dir']} not found, skipping")
            results[impl_name] = 'SKIPPED'
            continue
        
        # Build implementation
        if not build_implementation(impl_name, config):
            results[impl_name] = 'BUILD_FAILED'
            continue
        
        # Test spec command
        if test_spec_command(impl_name, config):
            results[impl_name] = 'PASSED'
            print_success(f"{config['name']} spec command test PASSED")
        else:
            results[impl_name] = 'FAILED'
            print_error(f"{config['name']} spec command test FAILED")
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result == 'PASSED')
    total_tested = sum(1 for result in results.values() if result in ['PASSED', 'FAILED'])
    
    for impl_name, result in results.items():
        config = IMPLEMENTATIONS[impl_name]
        if result == 'PASSED':
            print_success(f"{config['name']}: {result}")
        elif result == 'FAILED':
            print_error(f"{config['name']}: {result}")
        else:
            print_warning(f"{config['name']}: {result}")
    
    success_rate = (passed / total_tested * 100) if total_tested > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {passed}/{total_tested} ({success_rate:.1f}%){Colors.END}")
    
    if passed == total_tested and total_tested > 0:
        print_success("ALL IMPLEMENTATIONS PASSED!")
        return True
    else:
        print_error("SOME IMPLEMENTATIONS FAILED")
        return False

if __name__ == "__main__":
    success = run_cross_platform_spec_test()
    sys.exit(0 if success else 1)
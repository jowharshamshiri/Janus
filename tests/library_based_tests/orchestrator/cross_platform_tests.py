#!/usr/bin/env python3
"""
Cross-Platform Communication Test Implementation
Provides real server startup and client communication tests
"""

import subprocess
import socket
import time
import json
import os
import threading
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import signal

class ServerManager:
    """Manages server lifecycle for cross-platform testing"""
    
    def __init__(self, implementation: str, socket_path: str):
        self.implementation = implementation
        self.socket_path = socket_path
        self.process: Optional[subprocess.Popen] = None
        self.ready = False
        self.error_message = ""
        
    def start_go_server(self, test_dir: Path) -> bool:
        """Start Go server using library API"""
        server_code = '''
package main

import (
    "fmt"
    "log"
    "os"
    "os/signal"
    "syscall"
    "GoJanus/pkg/server"
)

func main() {
    socketPath := os.Args[1]
    
    // Remove existing socket
    os.Remove(socketPath)
    
    srv, err := server.NewJanusServer(socketPath)
    if err != nil {
        log.Fatalf("Failed to create server: %v", err)
    }
    
    // Start server
    if err := srv.Start(); err != nil {
        log.Fatalf("Failed to start server: %v", err)
    }
    
    fmt.Println("SERVER_READY")
    
    // Wait for signal
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
    <-sigChan
    
    srv.Stop()
}
'''
        
        # Write temporary server file
        server_file = test_dir / "temp_server.go"
        server_file.write_text(server_code)
        
        try:
            # Build server
            build_result = subprocess.run(
                ["go", "build", "-o", "test_server", "temp_server.go"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if build_result.returncode != 0:
                self.error_message = f"Go build failed: {build_result.stderr}"
                return False
        
        except subprocess.TimeoutExpired:
            self.error_message = "Go build timed out after 30 seconds"
            return False
            
            # Start server process
            self.process = subprocess.Popen(
                ["./test_server", self.socket_path],
                cwd=test_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server ready signal
            return self._wait_for_ready()
            
        except Exception as e:
            self.error_message = f"Failed to start Go server: {e}"
            return False
        finally:
            # Cleanup temp file
            if server_file.exists():
                server_file.unlink()
    
    def start_rust_server(self, test_dir: Path) -> bool:
        """Start Rust server using library API"""
        server_code = '''
use std::env;
use tokio::runtime::Runtime;
use rust_janus::server::{JanusServer, ServerConfig};

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <socket_path>", args[0]);
        std::process::exit(1);
    }
    
    let socket_path = &args[1];
    
    // Remove existing socket
    let _ = std::fs::remove_file(socket_path);
    
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        let config = ServerConfig {
            socket_path: socket_path.to_string(),
            max_connections: 10,
            default_timeout: 30,
            max_message_size: 65536,
            cleanup_on_start: true,
            cleanup_on_shutdown: true,
        };
        
        let mut server = JanusServer::new(config);
        
        // Start the server
        if let Err(e) = server.start_listening().await {
            eprintln!("Failed to start server: {}", e);
            std::process::exit(1);
        }
        
        println!("SERVER_READY");
        
        // Run until terminated
        server.wait_for_completion().await;
    });
}
'''
        
        # Write temporary server file
        server_file = test_dir / "src" / "bin" / "test_server.rs"
        server_file.parent.mkdir(parents=True, exist_ok=True)
        server_file.write_text(server_code)
        
        try:
            # Build server
            build_result = subprocess.run(
                ["cargo", "build", "--bin", "test_server"],
                cwd=test_dir,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"Rust build stderr: {build_result.stderr}")
                self.error_message = f"Rust build failed: {build_result.stderr}"
                return False
            
            # Start server process
            self.process = subprocess.Popen(
                ["cargo", "run", "--bin", "test_server", "--", self.socket_path],
                cwd=test_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server ready signal
            return self._wait_for_ready()
            
        except Exception as e:
            self.error_message = f"Failed to start Rust server: {e}"
            return False
        finally:
            # Cleanup temp file
            if server_file.exists():
                server_file.unlink()
    
    def start_swift_server(self, test_dir: Path) -> bool:
        """Start Swift server using library API"""
        server_code = '''
import Foundation
import SwiftJanus

@main
struct ServerApp {
    static func main() async {
        let socketPath = CommandLine.arguments[1]
        
        // Remove existing socket
        try? FileManager.default.removeItem(atPath: socketPath)
        
        do {
            let server = JanusServer()
            try await server.startListening(socketPath)
            
            print("SERVER_READY")
            fflush(stdout)
            
            // Keep server running
            while true {
                try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
            }
        } catch {
            print("Failed to start server: \\(error)")
            exit(1)
        }
    }
}
'''
        
        # Write temporary server file
        sources_dir = test_dir / "Sources" / "TestServer"
        sources_dir.mkdir(parents=True, exist_ok=True)
        server_file = sources_dir / "main.swift"
        server_file.write_text(server_code)
        
        # Update Package.swift to include executable
        package_swift = test_dir / "Package.swift"
        package_content = package_swift.read_text()
        if "TestServer" not in package_content:
            # Add executable target
            package_content = package_content.replace(
                'targets: [',
                '''targets: [
        .executableTarget(
            name: "TestServer",
            dependencies: ["SwiftJanus"]
        ),'''
            )
            package_swift.write_text(package_content)
        
        try:
            # Build server
            build_result = subprocess.run(
                ["swift", "build", "--product", "TestServer"],
                cwd=test_dir,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                self.error_message = f"Swift build failed: {build_result.stderr}"
                return False
            
            # Start server process
            self.process = subprocess.Popen(
                [".build/debug/TestServer", self.socket_path],
                cwd=test_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server ready signal
            return self._wait_for_ready()
            
        except Exception as e:
            self.error_message = f"Failed to start Swift server: {e}"
            return False
    
    def start_typescript_server(self, test_dir: Path) -> bool:
        """Start TypeScript server using library API"""
        server_code = '''
import { JanusServer } from '../dist/server/janus-server.js';
import * as fs from 'fs';

const socketPath = process.argv[2];

// Remove existing socket
try {
    fs.unlinkSync(socketPath);
} catch (e) {
    // Ignore if doesn't exist
}

async function main() {
    try {
        const server = new JanusServer(socketPath);
        await server.start();
        
        console.log('SERVER_READY');
        
        // Keep running
        process.on('SIGINT', () => {
            server.stop();
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            server.stop();
            process.exit(0);
        });
        
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

main();
'''
        
        # Write temporary server file
        server_file = test_dir / "test_server.js"
        server_file.write_text(server_code)
        
        try:
            # Build TypeScript if needed
            if not (test_dir / "dist").exists():
                build_result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=test_dir,
                    capture_output=True,
                    text=True
                )
                
                if build_result.returncode != 0:
                    self.error_message = f"TypeScript build failed: {build_result.stderr}"
                    return False
            
            # Start server process
            self.process = subprocess.Popen(
                ["node", "test_server.js", self.socket_path],
                cwd=test_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server ready signal
            return self._wait_for_ready()
            
        except Exception as e:
            self.error_message = f"Failed to start TypeScript server: {e}"
            return False
        finally:
            # Cleanup temp file
            if server_file.exists():
                server_file.unlink()
    
    def _wait_for_ready(self, timeout: float = 10.0) -> bool:
        """Wait for server to signal it's ready"""
        if not self.process:
            return False
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                self.error_message = f"Server exited early. stdout: {stdout}, stderr: {stderr}"
                return False
            
            # Check for ready signal
            try:
                line = self.process.stdout.readline()
                if "SERVER_READY" in line:
                    self.ready = True
                    return True
            except:
                pass
            
            # Also check if socket exists
            if os.path.exists(self.socket_path):
                # Give it a moment to fully initialize
                time.sleep(0.5)
                self.ready = True
                return True
            
            time.sleep(0.1)
        
        self.error_message = "Timeout waiting for server to start"
        return False
    
    def start(self, test_dir: Path) -> bool:
        """Start the appropriate server"""
        # Clean up any existing socket
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        if self.implementation == "go":
            return self.start_go_server(test_dir)
        elif self.implementation == "rust":
            return self.start_rust_server(test_dir)
        elif self.implementation == "swift":
            return self.start_swift_server(test_dir)
        elif self.implementation == "typescript":
            return self.start_typescript_server(test_dir)
        else:
            self.error_message = f"Unknown implementation: {self.implementation}"
            return False
    
    def stop(self):
        """Stop the server process"""
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.ready = False
        
        # Clean up socket
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass


class ClientTester:
    """Runs client tests against servers"""
    
    @staticmethod
    def test_go_client(server_socket: str, test_dir: Path) -> Dict:
        """Test Go client against a server"""
        client_code = '''
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "os"
    "time"
    "GoJanus/pkg/protocol"
)

func main() {
    serverSocket := os.Args[1]
    
    client, err := protocol.New(serverSocket)
    if err != nil {
        log.Fatalf("Failed to create client: %v", err)
    }
    defer client.Close()
    
    // Test 1: Manifest request
    manifest, err := client.GetManifest()
    if err != nil {
        log.Printf("Manifest request failed: %v", err)
        os.Exit(1)
    }
    
    fmt.Printf("MANIFEST_VERSION:%s\\n", manifest.Version)
    
    // Test 2: Echo request
    args := map[string]interface{}{
        "message": "Hello from Go",
        "timestamp": time.Now().Format(time.RFC3339Nano),
    }
    
    result, err := client.Request("echo", args, 5.0)
    if err != nil {
        log.Printf("Echo request failed: %v", err)
        os.Exit(1)
    }
    
    resultJSON, _ := json.Marshal(result)
    fmt.Printf("ECHO_RESULT:%s\\n", string(resultJSON))
    
    fmt.Println("TEST_COMPLETE")
}
'''
        
        # Write and build test client
        client_file = test_dir / "temp_client.go"
        client_file.write_text(client_code)
        
        try:
            # Build client
            build_result = subprocess.run(
                ["go", "build", "-o", "test_client", "temp_client.go"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if build_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Go client build failed: {build_result.stderr}",
                    "tests": {}
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Go client build timed out after 30 seconds",
                "tests": {}
            }
            
            # Run client test
            result = subprocess.run(
                ["./test_client", server_socket],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            tests = {}
            if result.returncode == 0:
                output = result.stdout
                if "MANIFEST_VERSION:" in output:
                    tests["manifest_request"] = {
                        "passed": True,
                        "version": output.split("MANIFEST_VERSION:")[1].split("\n")[0]
                    }
                else:
                    tests["manifest_request"] = {
                        "passed": False,
                        "error": "No manifest version in output"
                    }
                
                if "ECHO_RESULT:" in output:
                    tests["echo_request"] = {
                        "passed": True,
                        "result": output.split("ECHO_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["echo_request"] = {
                        "passed": False,
                        "error": "No echo result in output"
                    }
                
                return {
                    "success": True,
                    "tests": tests
                }
            else:
                return {
                    "success": False,
                    "error": f"Client test failed: {result.stderr}",
                    "tests": {}
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception running Go client: {e}",
                "tests": {}
            }
        finally:
            if client_file.exists():
                client_file.unlink()
    
    @staticmethod
    def test_rust_client(server_socket: str, test_dir: Path) -> Dict:
        """Test Rust client against a server"""
        client_code = '''
use std::env;
use std::collections::HashMap;
use tokio::runtime::Runtime;
use rust_janus::protocol::JanusClient;
use serde_json::json;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <server_socket>", args[0]);
        std::process::exit(1);
    }
    
    let server_socket = &args[1];
    
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        match run_tests(server_socket).await {
            Ok(_) => {
                println!("TEST_COMPLETE");
                std::process::exit(0);
            }
            Err(e) => {
                eprintln!("Test failed: {}", e);
                std::process::exit(1);
            }
        }
    });
}

async fn run_tests(server_socket: &str) -> Result<(), Box<dyn std::error::Error>> {
    let client = JanusClient::new(server_socket).await?;
    
    // Test 1: Manifest request
    let manifest = client.get_manifest().await?;
    println!("MANIFEST_VERSION:{}", manifest.version);
    
    // Test 2: Echo request
    let mut args = HashMap::new();
    args.insert("message".to_string(), json!("Hello from Rust"));
    args.insert("timestamp".to_string(), json!(chrono::Utc::now().to_rfc3339()));
    
    let result = client.request("echo", args, Some(5.0)).await?;
    println!("ECHO_RESULT:{}", serde_json::to_string(&result)?);
    
    Ok(())
}
'''
        
        # Write test client
        client_file = test_dir / "src" / "bin" / "test_client.rs"
        client_file.parent.mkdir(parents=True, exist_ok=True)
        client_file.write_text(client_code)
        
        try:
            # Build client
            build_result = subprocess.run(
                ["cargo", "build", "--bin", "test_client"],
                cwd=test_dir,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Rust client build failed: {build_result.stderr}",
                    "tests": {}
                }
            
            # Run client test
            result = subprocess.run(
                ["cargo", "run", "--bin", "test_client", "--", server_socket],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            tests = {}
            if result.returncode == 0:
                output = result.stdout
                if "MANIFEST_VERSION:" in output:
                    tests["manifest_request"] = {
                        "passed": True,
                        "version": output.split("MANIFEST_VERSION:")[1].split("\n")[0]
                    }
                else:
                    tests["manifest_request"] = {
                        "passed": False,
                        "error": "No manifest version in output"
                    }
                
                if "ECHO_RESULT:" in output:
                    tests["echo_request"] = {
                        "passed": True,
                        "result": output.split("ECHO_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["echo_request"] = {
                        "passed": False,
                        "error": "No echo result in output"
                    }
                
                return {
                    "success": True,
                    "tests": tests
                }
            else:
                return {
                    "success": False,
                    "error": f"Client test failed: {result.stderr}",
                    "tests": {}
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception running Rust client: {e}",
                "tests": {}
            }
        finally:
            if client_file.exists():
                client_file.unlink()
    
    @staticmethod
    def test_swift_client(server_socket: str, test_dir: Path) -> Dict:
        """Test Swift client against a server"""
        # Swift client test would be similar
        # For now, return a placeholder
        return {
            "success": False,
            "error": "Swift client test not yet implemented",
            "tests": {}
        }
    
    @staticmethod
    def test_typescript_client(server_socket: str, test_dir: Path) -> Dict:
        """Test TypeScript client against a server"""
        client_code = '''
import { JanusClient } from './dist/protocol/janus-client.js';

const serverSocket = process.argv[2];

async function runTests() {
    try {
        const client = new JanusClient(serverSocket);
        
        // Test 1: Manifest request
        const manifest = await client.getManifest();
        console.log(`MANIFEST_VERSION:${manifest.version}`);
        
        // Test 2: Echo request
        const result = await client.request('echo', {
            message: 'Hello from TypeScript',
            timestamp: new Date().toISOString()
        }, 5.0);
        
        console.log(`ECHO_RESULT:${JSON.stringify(result)}`);
        console.log('TEST_COMPLETE');
        
        client.close();
        process.exit(0);
    } catch (error) {
        console.error('Test failed:', error);
        process.exit(1);
    }
}

runTests();
'''
        
        # Write test client
        client_file = test_dir / "test_client.js"
        client_file.write_text(client_code)
        
        try:
            # Run client test
            result = subprocess.run(
                ["node", "test_client.js", server_socket],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            tests = {}
            if result.returncode == 0:
                output = result.stdout
                if "MANIFEST_VERSION:" in output:
                    tests["manifest_request"] = {
                        "passed": True,
                        "version": output.split("MANIFEST_VERSION:")[1].split("\n")[0]
                    }
                else:
                    tests["manifest_request"] = {
                        "passed": False,
                        "error": "No manifest version in output"
                    }
                
                if "ECHO_RESULT:" in output:
                    tests["echo_request"] = {
                        "passed": True,
                        "result": output.split("ECHO_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["echo_request"] = {
                        "passed": False,
                        "error": "No echo result in output"
                    }
                
                return {
                    "success": True,
                    "tests": tests
                }
            else:
                return {
                    "success": False,
                    "error": f"Client test failed: {result.stderr}",
                    "tests": {}
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception running TypeScript client: {e}",
                "tests": {}
            }
        finally:
            if client_file.exists():
                client_file.unlink()


def run_cross_platform_test(client_impl: str, server_impl: str, base_dir: Path) -> Tuple[bool, Dict]:
    """Run a single cross-platform test combination"""
    
    # Generate unique socket path
    socket_path = f"/tmp/janus_test_{client_impl}_{server_impl}_{os.getpid()}.sock"
    
    # Get test directories
    client_dir = base_dir / client_impl
    server_dir = base_dir / server_impl
    
    # Start server
    server = ServerManager(server_impl, socket_path)
    if not server.start(server_dir):
        return False, {
            "error": f"Failed to start {server_impl} server: {server.error_message}",
            "phase": "server_startup"
        }
    
    try:
        # Run client tests
        tester = ClientTester()
        if client_impl == "go":
            result = tester.test_go_client(socket_path, client_dir)
        elif client_impl == "rust":
            result = tester.test_rust_client(socket_path, client_dir)
        elif client_impl == "swift":
            result = tester.test_swift_client(socket_path, client_dir)
        elif client_impl == "typescript":
            result = tester.test_typescript_client(socket_path, client_dir)
        else:
            result = {
                "success": False,
                "error": f"Unknown client implementation: {client_impl}",
                "tests": {}
            }
        
        return result["success"], result
        
    finally:
        # Always stop server
        server.stop()


def test_critical_combinations(base_dir: Path) -> List[Dict]:
    """Test the critical Go ↔ Rust combinations first"""
    results = []
    
    # Critical test 1: Go client → Rust server (failed in terraform)
    print("🔥 Testing critical combination: Go client → Rust server")
    success, details = run_cross_platform_test("go", "rust", base_dir)
    results.append({
        "combination": "go_client_rust_server",
        "success": success,
        "details": details,
        "priority": "CRITICAL"
    })
    
    # Critical test 2: Rust client → Go server (reverse validation)
    print("🔥 Testing critical combination: Rust client → Go server")
    success, details = run_cross_platform_test("rust", "go", base_dir)
    results.append({
        "combination": "rust_client_go_server",
        "success": success,
        "details": details,
        "priority": "CRITICAL"
    })
    
    return results
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
    "GoJanus/pkg/models"
)

func main() {
    socketPath := os.Args[1]
    
    // Remove existing socket
    os.Remove(socketPath)
    
    config := &server.ServerConfig{
        SocketPath: socketPath,
    }
    srv := server.NewJanusServer(config)
    
    // Register custom request handler
    srv.RegisterHandler("custom_test", server.NewObjectHandler(func(request *models.JanusRequest) (map[string]interface{}, error) {
        testParam := ""
        if request.Args != nil {
            if param, ok := request.Args["test_param"].(string); ok {
                testParam = param
            }
        }
        
        return map[string]interface{}{
            "result": "custom_test_success",
            "received_param": testParam,
        }, nil
    }))
    
    // Start server
    if err := srv.StartListening(); err != nil {
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
        
        # Create test manifest with custom request
        test_manifest = '''
{
    "version": "1.0.0",
    "models": {
        "CustomTestRequest": {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "Test parameter for custom request"
                }
            },
            "required": ["test_param"]
        },
        "CustomTestResponse": {
            "type": "object", 
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Result of custom test"
                },
                "received_param": {
                    "type": "string",
                    "description": "Parameter that was received"
                }
            }
        }
    }
}
'''
        manifest_file = test_dir / "test_manifest.json"
        manifest_file.write_text(test_manifest)
        
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
        
        try:
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
use rust_janus::JSONRPCError;
use serde_json;

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
        
        // Register custom request handler
        server.register_handler("custom_test", |request| {
            let test_param = request.args
                .as_ref()
                .and_then(|args| args.get("test_param"))
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            
            Ok(serde_json::json!({
                "result": "custom_test_success",
                "received_param": test_param
            }))
        }).await;
        
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
            
            // Keep server running by waiting for termination signal
            // The server now runs in background task, so we just wait
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
        
        # Check if Package.swift already has TestServer target (avoid unnecessary rebuilds)
        package_swift = test_dir / "Package.swift"
        package_content = package_swift.read_text()
        if "TestServer" not in package_content:
            # Add executable target only once
            package_content = package_content.replace(
                'targets: [',
                '''targets: [
        .executableTarget(
            name: "TestServer",
            dependencies: ["SwiftJanus"]
        ),'''
            )
            package_swift.write_text(package_content)
            # Clear build cache when Package.swift changes
            import shutil
            build_dir = test_dir / ".build"
            if build_dir.exists():
                shutil.rmtree(build_dir)
        
        try:
            # Check if TestServer is already built to avoid unnecessary rebuilds
            test_server_path = test_dir / ".build" / "debug" / "TestServer"
            if not test_server_path.exists():
                # Build server only if needed
                build_result = subprocess.run(
                    ["swift", "build", "--product", "TestServer"],
                    cwd=test_dir,
                    capture_output=True,
                    text=True,
                    timeout=30  # Add timeout for build
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
import { JanusServer } from '../../../TypeScriptJanus/dist/server/janus-server.js';
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
        const config = { 
            socketPath: socketPath,
            maxMessageSize: 64 * 1024,
            defaultTimeout: 30,
            maxConnections: 10,
            cleanupOnStart: true,
            cleanupOnShutdown: true
        };
        const server = new JanusServer(config);
        
        // Register custom handler for testing
        server.registerRequestHandler('custom_test', async (args) => {
            return { result: `Custom handler response: ${JSON.stringify(args)}` };
        });
        
        await server.listen();
        
        console.log('SERVER_READY');
        
        // Keep running
        process.on('SIGINT', () => {
            server.close();
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            server.close();
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
    "context"
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
    ctx := context.Background()
    manifestResp, err := client.SendRequest(ctx, "manifest", nil)
    if err != nil {
        log.Printf("Manifest request failed: %v", err)
        os.Exit(1)
    }
    
    if manifestResp.Success && manifestResp.Result != nil {
        if resultMap, ok := manifestResp.Result.(map[string]interface{}); ok {
            if version, ok := resultMap["version"].(string); ok {
                fmt.Printf("MANIFEST_VERSION:%s\\n", version)
            }
        }
    }
    
    // Test 2: Echo request
    args := map[string]interface{}{
        "message": "Hello from Go",
        "timestamp": time.Now().Format(time.RFC3339Nano),
    }
    
    result, err := client.SendRequest(ctx, "echo", args)
    if err != nil {
        log.Printf("Echo request failed: %v", err)
        os.Exit(1)
    }
    
    if result.Success && result.Result != nil {
        resultJSON, _ := json.Marshal(result.Result)
        fmt.Printf("ECHO_RESULT:%s\\n", string(resultJSON))
    }
    
    // Test 3: Custom request (if available)
    fmt.Println("\\nTest 3: Custom request...")
    customArgs := map[string]interface{}{
        "test_param": "go_value",
    }
    
    customResult, err := client.SendRequest(ctx, "custom_test", customArgs)
    if err != nil {
        log.Printf("Custom request failed: %v", err)
    } else if customResult.Success && customResult.Result != nil {
        customJSON, _ := json.Marshal(customResult.Result)
        fmt.Printf("CUSTOM_RESULT:%s\\n", string(customJSON))
    }
    
    fmt.Println("\\n✅ All tests completed")
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
        
        try:    
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
                
                # Check custom request test
                if "CUSTOM_RESULT:" in output:
                    tests["custom_request"] = {
                        "passed": True,
                        "result": output.split("CUSTOM_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["custom_request"] = {
                        "passed": False,
                        "error": "Custom request not supported or failed"
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
use rust_janus::protocol::janus_client::JanusClient;
use rust_janus::config::JanusClientConfig;
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
    use rust_janus::config::JanusClientConfig;
    
    let client_config = JanusClientConfig::default();
    let mut client = JanusClient::new(server_socket.to_string(), client_config).await?;
    
    // Test 1: Manifest request
    let manifest_result = client.send_request("manifest", None, None).await?;
    if manifest_result.success {
        if let Some(manifest_data) = manifest_result.result {
            if let Some(version) = manifest_data.get("version") {
                if let Some(version_str) = version.as_str() {
                    println!("MANIFEST_VERSION:{}", version_str);
                }
            }
        }
    }
    
    // Test 2: Echo request  
    let mut args = HashMap::new();
    args.insert("message".to_string(), json!("Hello from Rust"));
    args.insert("timestamp".to_string(), json!(chrono::Utc::now().to_rfc3339()));
    
    let result = client.send_request("echo", Some(args), None).await?;
    if result.success {
        if let Some(result_data) = result.result {
            println!("ECHO_RESULT:{}", serde_json::to_string(&result_data)?);
        }
    }
    
    // Test 3: Custom request
    println!("\\nTest 3: Custom request...");
    let mut custom_args = HashMap::new();
    custom_args.insert("test_param".to_string(), json!("rust_value"));
    
    let custom_result = client.send_request("custom_test", Some(custom_args), None).await?;
    if custom_result.success {
        if let Some(result_data) = custom_result.result {
            println!("CUSTOM_RESULT:{}", serde_json::to_string(&result_data)?);
        }
    }
    
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
                
                # Check custom request test
                if "CUSTOM_RESULT:" in output:
                    tests["custom_request"] = {
                        "passed": True,
                        "result": output.split("CUSTOM_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["custom_request"] = {
                        "passed": False,
                        "error": "Custom request not supported or failed"
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
        client_code = '''
import Foundation
import SwiftJanus

@main
struct ClientApp {
    static func main() async {
        let serverSocket = CommandLine.arguments[1]
        
        do {
            let client = try await JanusClient(socketPath: serverSocket)
            
            // Test 1: Manifest request
            let manifestResponse = try await client.sendRequest("manifest")
            
            if manifestResponse.success,
               let result = manifestResponse.result?.value as? [String: Any],
               let version = result["version"] as? String {
                print("MANIFEST_VERSION:\\(version)")
            }
            
            // Test 2: Echo request
            let echoResponse = try await client.sendRequest("echo", 
                args: ["message": AnyCodable("Hello from Swift"),
                       "timestamp": AnyCodable(ISO8601DateFormatter().string(from: Date()))])
            
            if echoResponse.success,
               let result = echoResponse.result?.value {
                if let jsonData = try? JSONSerialization.data(withJSONObject: result),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    print("ECHO_RESULT:\\(jsonString)")
                }
            }
            
            // Test 3: Custom request (if available)
            let customResponse = try await client.sendRequest("custom_test",
                args: ["test_param": AnyCodable("swift_value")])
            
            if customResponse.success,
               let result = customResponse.result?.value {
                if let jsonData = try? JSONSerialization.data(withJSONObject: result),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    print("CUSTOM_RESULT:\\(jsonString)")
                }
            }
            
            print("TEST_COMPLETE")
            
        } catch {
            print("Test failed: \\(error)")
            exit(1)
        }
    }
}
'''
        
        # Write test client
        sources_dir = test_dir / "Sources" / "TestClient"  
        sources_dir.mkdir(parents=True, exist_ok=True)
        client_file = sources_dir / "main.swift"
        client_file.write_text(client_code)
        
        # Update Package.swift to include client executable
        package_swift = test_dir / "Package.swift"
        package_content = package_swift.read_text()
        if "TestClient" not in package_content:
            package_content = package_content.replace(
                'targets: [',
                '''targets: [
        .executableTarget(
            name: "TestClient",
            dependencies: ["SwiftJanus"]
        ),'''
            )
            package_swift.write_text(package_content)
        
        try:
            # Build client
            build_result = subprocess.run(
                ["swift", "build", "--product", "TestClient"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if build_result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Swift client build failed: {build_result.stderr}",
                    "tests": {}
                }
            
            # Run client test
            result = subprocess.run(
                [".build/debug/TestClient", server_socket],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Parse results
            tests = {}
            if result.returncode == 0:
                output = result.stdout
                
                # Check manifest test
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
                
                # Check echo test
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
                
                # Check custom request test
                if "CUSTOM_RESULT:" in output:
                    tests["custom_request"] = {
                        "passed": True,
                        "result": output.split("CUSTOM_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["custom_request"] = {
                        "passed": False,
                        "error": "Custom request not supported or failed"
                    }
                
                # Check custom request test
                if "CUSTOM_RESULT:" in output:
                    tests["custom_request"] = {
                        "passed": True,
                        "result": output.split("CUSTOM_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["custom_request"] = {
                        "passed": False,
                        "error": "Custom request not supported or failed"
                    }
                
                return {
                    "success": True,
                    "tests": tests
                }
            else:
                return {
                    "success": False,
                    "error": f"Swift client test failed: {result.stderr}",
                    "tests": {}
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception running Swift client: {e}",
                "tests": {}
            }
        finally:
            if client_file.exists():
                client_file.unlink()
    
    @staticmethod
    def test_typescript_client(server_socket: str, test_dir: Path) -> Dict:
        """Test TypeScript client against a server"""
        client_code = '''
import { JanusClient } from '../../../TypeScriptJanus/dist/protocol/janus-client.js';

const serverSocket = process.argv[2];

async function runTests() {
    try {
        const config = { 
            socketPath: serverSocket,
            maxMessageSize: 64 * 1024,
            defaultTimeout: 10000,
            enableValidation: false
        };
        const client = new JanusClient(config);
        
        // Test 1: Manifest request  
        const manifestResponse = await client.sendRequest('manifest');
        if (manifestResponse.success && manifestResponse.result) {
            const manifest = manifestResponse.result;
            if (manifest.version) {
                console.log(`MANIFEST_VERSION:${manifest.version}`);
            }
        }
        
        // Test 2: Echo request
        const echoResponse = await client.sendRequest('echo', {
            message: 'Hello from TypeScript',
            timestamp: new Date().toISOString()
        });
        
        if (echoResponse.success && echoResponse.result) {
            console.log(`ECHO_RESULT:${JSON.stringify(echoResponse.result)}`);
        }
        
        // Test 3: Custom request (if available) 
        const customResponse = await client.sendRequest('custom_test', {
            test_param: 'typescript_value'
        });
        
        if (customResponse.success && customResponse.result) {
            console.log(`CUSTOM_RESULT:${JSON.stringify(customResponse.result)}`);
        }
        
        console.log('TEST_COMPLETE');
        
        await client.disconnect();
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
                
                # Check custom request test
                if "CUSTOM_RESULT:" in output:
                    tests["custom_request"] = {
                        "passed": True,
                        "result": output.split("CUSTOM_RESULT:")[1].split("\n")[0]
                    }
                else:
                    tests["custom_request"] = {
                        "passed": False,
                        "error": "Custom request not supported or failed"
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


def test_critical_combinations(base_dir: Path, timeout_seconds: int = 60) -> List[Dict]:
    """Test the critical Go ↔ Rust combinations first with timeout"""
    import signal
    import time
    
    results = []
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Test exceeded timeout limit")
    
    # Critical test 1: Go client → Rust server (failed in terraform)
    print("🔥 Testing critical combination: Go client → Rust server")
    start_time = time.time()
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        success, details = run_cross_platform_test("go", "rust", base_dir)
        results.append({
            "combination": "go_client_rust_server",
            "success": success,
            "details": details,
            "priority": "CRITICAL"
        })
        
        signal.alarm(0)  # Cancel timeout
    except TimeoutError:
        results.append({
            "combination": "go_client_rust_server",
            "success": False,
            "details": {"error": f"Test timed out after {timeout_seconds} seconds"},
            "priority": "CRITICAL"
        })
        signal.alarm(0)  # Cancel timeout
    
    # Critical test 2: Rust client → Go server (reverse validation)
    print("🔥 Testing critical combination: Rust client → Go server")
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        success, details = run_cross_platform_test("rust", "go", base_dir)
        results.append({
            "combination": "rust_client_go_server",
            "success": success,
            "details": details,
            "priority": "CRITICAL"
        })
        
        signal.alarm(0)  # Cancel timeout
    except TimeoutError:
        results.append({
            "combination": "rust_client_go_server", 
            "success": False,
            "details": {"error": f"Test timed out after {timeout_seconds} seconds"},
            "priority": "CRITICAL"
        })
        signal.alarm(0)  # Cancel timeout
    
    return results
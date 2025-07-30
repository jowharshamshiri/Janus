#!/usr/bin/env python3
"""
High-Level API Usage Examples for Testing
Shows how to use JanusServer and JanusClient instead of direct socket access
"""

import json
import subprocess
import sys
import os
import time
import threading
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class TestServer:
    """High-level server abstraction using JanusServer APIs"""
    implementation: str
    socket_path: str
    process: Optional[subprocess.Popen] = None
    ready: bool = False

class HighLevelTestFramework:
    """Framework for testing using high-level APIs instead of direct socket access"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.servers: Dict[str, TestServer] = {}
        self.temp_dir = tempfile.mkdtemp(prefix="highlevel_test_")
        
    def start_server_rust(self, socket_path: str, handlers: Dict[str, str]) -> TestServer:
        """Start Rust server using high-level JanusServer API"""
        
        # Create Rust test server code using high-level API
        rust_server_code = f'''
use rust_janus::{{JanusServer, SocketError}};
use serde_json::json;
use std::collections::HashMap;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let mut server = JanusServer::new();
    
    // Register ping handler
    server.register_handler("ping", |_cmd| {{
        Ok(json!({{"message": "pong", "timestamp": chrono::Utc::now().timestamp()}}))
    }}).await;
    
    // Register echo handler  
    server.register_handler("echo", |cmd| {{
        if let Some(args) = &cmd.args {{
            if let Some(message) = args.get("message") {{
                Ok(json!({{"echo": message, "received_at": chrono::Utc::now().timestamp()}}))
            }} else {{
                Err(SocketError::ValidationFailed("Missing message argument".to_string()))
            }}
        }} else {{
            Err(SocketError::ValidationFailed("No arguments provided".to_string()))
        }}
    }}).await;
    
    // Register math handler
    server.register_handler("math", |cmd| {{
        if let Some(args) = &cmd.args {{
            let op = args.get("operation").and_then(|v| v.as_str()).unwrap_or("");
            let a = args.get("a").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let b = args.get("b").and_then(|v| v.as_f64()).unwrap_or(0.0);
            
            let result = match op {{
                "add" => a + b,
                "multiply" => a * b,
                _ => return Err(SocketError::ValidationFailed("Unknown operation".to_string())),
            }};
            
            Ok(json!({{"result": result, "operation": op}}))
        }} else {{
            Err(SocketError::ValidationFailed("No arguments provided".to_string()))
        }}
    }}).await;
    
    // Register validate handler
    server.register_handler("validate", |cmd| {{
        if cmd.args.is_some() {{
            Ok(json!({{"valid": true}}))
        }} else {{
            Ok(json!({{"valid": false}}))
        }}
    }}).await;
    
    // Register slow_process handler
    server.register_handler("slow_process", |_cmd| {{
        std::thread::sleep(std::time::Duration::from_secs(2));
        Ok(json!({{"completed": true, "delay": 2}}))
    }}).await;
    
    // Handle Ctrl+C gracefully
    tokio::spawn(async {{
        signal::ctrl_c().await.expect("Failed to listen for ctrl-c");
        std::process::exit(0);
    }});
    
    // Start listening (this will block)
    server.start_listening("{socket_path}").await?;
    
    Ok(())
}}
'''
        
        # Write server code to temp file
        server_file = Path(self.temp_dir) / "rust_test_server.rs"
        server_file.write_text(rust_server_code)
        
        # Create Cargo.toml for the test server
        cargo_toml = f'''
[package]
name = "test_server"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "test_server"
path = "rust_test_server.rs"

[dependencies]
rust-unix-sock-api = {{ path = "{self.base_dir}/RustJanus" }}
serde_json = "1.0"
tokio = {{ version = "1.0", features = ["full"] }}
chrono = {{ version = "0.4", features = ["serde"] }}
'''
        
        cargo_file = Path(self.temp_dir) / "Cargo.toml"
        cargo_file.write_text(cargo_toml)
        
        # Compile and start server
        compile_cmd = ["cargo", "build", "--bin", "test_server"]
        subprocess.run(compile_cmd, cwd=self.temp_dir, check=True, capture_output=True)
        
        server_cmd = ["cargo", "run", "--bin", "test_server"]
        process = subprocess.Popen(
            server_cmd,
            cwd=self.temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        server = TestServer(
            implementation="rust",
            socket_path=socket_path,
            process=process
        )
        
        # Wait for server to be ready
        self._wait_for_server_ready(server)
        
        return server
    
    def start_server_go(self, socket_path: str, handlers: Dict[str, str]) -> TestServer:
        """Start Go server using high-level JanusServer API"""
        
        go_server_code = f'''
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
    "strconv"
    
    "github.com/user/GoJanus/pkg/server"
    "github.com/user/GoJanus/pkg/models"
)

func main() {{
    srv := &server.JanusServer{{}}
    
    // Register ping handler
    srv.RegisterHandler("ping", func(cmd *models.SocketCommand) (interface{{}}, *models.SocketError) {{
        return map[string]interface{{}}{{
            "message":   "pong",
            "timestamp": time.Now().Unix(),
        }}, nil
    }})
    
    // Register echo handler
    srv.RegisterHandler("echo", func(cmd *models.SocketCommand) (interface{{}}, *models.SocketError) {{
        if cmd.Args == nil {{
            return nil, &models.SocketError{{
                Code:    "NO_ARGUMENTS",
                Message: "No arguments provided",
                Details: "",
            }}
        }}
        
        message, exists := cmd.Args["message"]
        if !exists {{
            return nil, &models.SocketError{{
                Code:    "MISSING_ARGUMENT", 
                Message: "Missing message argument",
                Details: "",
            }}
        }}
        
        return map[string]interface{{}}{{
            "echo":        message,
            "received_at": time.Now().Unix(),
        }}, nil
    }})
    
    // Register math handler
    srv.RegisterHandler("math", func(cmd *models.SocketCommand) (interface{{}}, *models.SocketError) {{
        if cmd.Args == nil {{
            return nil, &models.SocketError{{
                Code:    "NO_ARGUMENTS",
                Message: "No arguments provided",
                Details: "",
            }}
        }}
        
        operation, opExists := cmd.Args["operation"].(string)
        a, aExists := cmd.Args["a"].(float64)
        b, bExists := cmd.Args["b"].(float64)
        
        if !opExists || !aExists || !bExists {{
            return nil, &models.SocketError{{
                Code:    "INVALID_ARGUMENTS",
                Message: "Missing or invalid arguments",
                Details: "",
            }}
        }}
        
        var result float64
        switch operation {{
        case "add":
            result = a + b
        case "multiply":
            result = a * b
        default:
            return nil, &models.SocketError{{
                Code:    "UNKNOWN_OPERATION",
                Message: "Unknown operation: " + operation,
                Details: "",
            }}
        }}
        
        return map[string]interface{{}}{{
            "result":    result,
            "operation": operation,
        }}, nil
    }})
    
    // Register validate handler
    srv.RegisterHandler("validate", func(cmd *models.SocketCommand) (interface{{}}, *models.SocketError) {{
        valid := cmd.Args != nil
        return map[string]interface{{}}{{
            "valid": valid,
        }}, nil
    }})
    
    // Register slow_process handler
    srv.RegisterHandler("slow_process", func(cmd *models.SocketCommand) (interface{{}}, *models.SocketError) {{
        time.Sleep(2 * time.Second)
        return map[string]interface{{}}{{
            "completed": true,
            "delay":     2,
        }}, nil
    }})
    
    // Handle graceful shutdown
    c := make(chan os.Signal, 1)
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)
    
    go func() {{
        <-c
        fmt.Println("Shutting down server...")
        srv.Stop()
        os.Exit(0)
    }}()
    
    // Start listening (blocks until stopped)
    if err := srv.StartListening("{socket_path}"); err != nil {{
        fmt.Printf("Server error: %v\\n", err)
        os.Exit(1)
    }}
}}
'''
        
        # Write server code to temp file
        server_file = Path(self.temp_dir) / "go_test_server.go"
        server_file.write_text(go_server_code)
        
        # Create go.mod for the test server
        go_mod = f'''
module test_server

go 1.21

replace github.com/user/GoJanus => {self.base_dir}/GoJanus

require github.com/user/GoJanus v0.0.0-00010101000000-000000000000
'''
        
        mod_file = Path(self.temp_dir) / "go.mod"
        mod_file.write_text(go_mod)
        
        # Build and start server
        build_cmd = ["go", "build", "-o", "test_server", "go_test_server.go"]
        subprocess.run(build_cmd, cwd=self.temp_dir, check=True, capture_output=True)
        
        server_cmd = ["./test_server"]
        process = subprocess.Popen(
            server_cmd,
            cwd=self.temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        server = TestServer(
            implementation="go",
            socket_path=socket_path,
            process=process
        )
        
        # Wait for server to be ready
        self._wait_for_server_ready(server)
        
        return server
    
    def send_command_rust(self, target_socket: str, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send command using Rust high-level JanusClient API"""
        
        # Create Rust client code using high-level API
        args_json = json.dumps(args) if args else "None"
        
        rust_client_code = f'''
use rust_janus::JanusClient;
use std::collections::HashMap;
use std::time::Duration;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let client = JanusClient::new(Some("test"), Some(Duration::from_secs(30)));
    
    let args: Option<HashMap<String, serde_json::Value>> = {args_json}.map(|_| {{
        let mut map = HashMap::new();
        {self._generate_rust_args_code(args)}
        map
    }});
    
    let response = client.send_command("{target_socket}", "{command}", args).await?;
    
    println!("{{}}", serde_json::to_string(&response)?);
    
    Ok(())
}}
'''
        
        # Write client code to temp file
        client_file = Path(self.temp_dir) / "rust_test_client.rs"
        client_file.write_text(rust_client_code)
        
        # Run client
        client_cmd = ["cargo", "run", "--bin", "rust_test_client"]
        result = subprocess.run(
            client_cmd,
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Rust client failed: {{result.stderr}}")
        
        return json.loads(result.stdout.strip())
    
    def send_command_go(self, target_socket: str, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send command using Go high-level JanusClient API"""
        
        go_client_code = f'''
package main

import (
    "encoding/json"
    "fmt"
    "time"
    
    "github.com/user/GoJanus/pkg/client"
)

func main() {{
    client := &client.JanusClient{{}}
    client.SetChannelID("test")
    client.SetTimeout(30 * time.Second)
    
    var args map[string]interface{{}}
    {self._generate_go_args_code(args)}
    
    response, err := client.SendCommand("{target_socket}", "{command}", args)
    if err != nil {{
        fmt.Printf(`{{"error": "%s", "success": false}}`, err.Error())
        return
    }}
    
    jsonData, err := json.Marshal(response)
    if err != nil {{
        fmt.Printf(`{{"error": "%s", "success": false}}`, err.Error())
        return
    }}
    
    fmt.Print(string(jsonData))
}}
'''
        
        # Write client code to temp file
        client_file = Path(self.temp_dir) / "go_test_client.go"
        client_file.write_text(go_client_code)
        
        # Build and run client
        build_cmd = ["go", "build", "-o", "test_client", "go_test_client.go"]
        subprocess.run(build_cmd, cwd=self.temp_dir, check=True, capture_output=True)
        
        client_cmd = ["./test_client"]
        result = subprocess.run(
            client_cmd,
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Go client failed: {{result.stderr}}")
        
        return json.loads(result.stdout.strip())
    
    def _generate_rust_args_code(self, args: Optional[Dict[str, Any]]) -> str:
        """Generate Rust code to populate args HashMap"""
        if not args:
            return ""
        
        lines = []
        for key, value in args.items():
            if isinstance(value, str):
                lines.append(f'map.insert("{key}".to_string(), json!("{value}"));')
            elif isinstance(value, (int, float)):
                lines.append(f'map.insert("{key}".to_string(), json!({value}));')
            elif isinstance(value, bool):
                lines.append(f'map.insert("{key}".to_string(), json!({str(value).lower()}));')
            else:
                lines.append(f'map.insert("{key}".to_string(), json!({json.dumps(value)}));')
        
        return "\\n        ".join(lines)
    
    def _generate_go_args_code(self, args: Optional[Dict[str, Any]]) -> str:
        """Generate Go code to populate args map"""
        if not args:
            return "args = nil"
        
        lines = ["args = make(map[string]interface{})"]
        for key, value in args.items():
            if isinstance(value, str):
                lines.append(f'args["{key}"] = "{value}"')
            elif isinstance(value, (int, float, bool)):
                lines.append(f'args["{key}"] = {json.dumps(value)}')
            else:
                lines.append(f'args["{key}"] = {json.dumps(value)}')
        
        return "\\n    ".join(lines)
    
    def _wait_for_server_ready(self, server: TestServer, timeout: int = 10):
        """Wait for server to be ready to accept connections"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect to socket to check if server is ready
                import socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect(server.socket_path)
                sock.close()
                server.ready = True
                return
            except (ConnectionRefusedError, FileNotFoundError, socket.timeout):
                time.sleep(0.1)
                continue
        
        raise Exception(f"Server {server.implementation} not ready within {timeout} seconds")
    
    def cleanup(self):
        """Clean up all servers and temp files"""
        for server in self.servers.values():
            if server.process:
                server.process.terminate()
                try:
                    server.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.process.kill()
        
        # Remove temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

# Example usage
if __name__ == "__main__":
    # This shows how tests should be written using high-level APIs
    base_dir = Path(__file__).parent.parent.parent
    framework = HighLevelTestFramework(base_dir)
    
    try:
        # Start servers using high-level API
        rust_server = framework.start_server_rust("/tmp/test-rust.sock", {})
        go_server = framework.start_server_go("/tmp/test-go.sock", {})
        
        # Test cross-platform communication using high-level clients
        print("Testing Rust client -> Go server")
        response = framework.send_command_rust("/tmp/test-go.sock", "ping")
        print(f"Response: {response}")
        
        print("Testing Go client -> Rust server")  
        response = framework.send_command_go("/tmp/test-rust.sock", "echo", {"message": "Hello from Go!"})
        print(f"Response: {response}")
        
    finally:
        framework.cleanup()
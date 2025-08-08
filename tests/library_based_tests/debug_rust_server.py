#!/usr/bin/env python3
"""Debug Rust server custom handler registration"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def test_rust_server_custom_handler():
    """Test if Rust server can register and respond to custom_test handler"""
    
    test_dir = Path(tempfile.mkdtemp())
    socket_path = str(test_dir / "rust_server.sock")
    
    print(f"Testing Rust server custom handler in {test_dir}")
    
    try:
        # Use the RustJanus test directory structure  
        rust_dir = Path("/Users/bahram/ws/prj/Janus/tests/library_based_tests/rust")
        
        # Create a simple server that definitely has the custom handler
        server_code = '''
use std::env;
use tokio::runtime::Runtime;
use rust_janus::{JanusServer, ServerConfig, JSONRPCError};
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
        
        println!("Registering custom_test handler...");
        
        // Register custom request handler
        server.register_handler("custom_test", |request| {
            println!("Custom test handler called!");
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
        
        println!("Handler registered, starting server...");
        
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
        
        # Copy to rust test directory and build there
        (rust_dir / "src" / "bin" / "debug_server.rs").write_text(server_code)
        
        # Update Cargo.toml to include debug_server binary
        cargo_toml_path = rust_dir / "Cargo.toml"
        cargo_content = cargo_toml_path.read_text()
        
        if "debug_server" not in cargo_content:
            # Add debug_server binary
            cargo_content += '''
[[bin]]
name = "debug_server"
path = "src/bin/debug_server.rs"
'''
            cargo_toml_path.write_text(cargo_content)
        
        print("Building Rust debug server...")
        build_result = subprocess.run([
            "cargo", "build", "--bin", "debug_server"
        ], cwd=rust_dir, capture_output=True, text=True, timeout=60)
        
        if build_result.returncode != 0:
            print(f"❌ Build failed: {build_result.stderr}")
            return False
        
        print("✅ Build successful")
        
        # Start server
        server_process = subprocess.Popen([
            "./target/debug/debug_server", socket_path
        ], cwd=rust_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server ready
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < 10:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Server exited: {stdout} | {stderr}")
                return False
            
            if os.path.exists(socket_path):
                server_ready = True
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Server failed to start")
            server_process.terminate()
            return False
        
        print("✅ Server started, testing custom_test request...")
        
        # Test with simple echo command to see if server responds at all
        test_result = subprocess.run([
            "echo", '{"id":"test-123","method":"custom_test","args":{"test_param":"debug_value"},"reply_to":"/tmp/test_reply.sock","timestamp":"2025-08-08T12:00:00.000Z"}'
        ], capture_output=True, text=True)
        
        # Send via nc or socat to the server
        send_result = subprocess.run([
            "socat", "-", f"UNIX-SENDTO:{socket_path}"
        ], input='{"id":"test-123","method":"custom_test","args":{"test_param":"debug_value"},"reply_to":"/tmp/test_reply.sock","timestamp":"2025-08-08T12:00:00.000Z"}', 
        capture_output=True, text=True, timeout=5)
        
        print(f"Send result: {send_result.returncode}")
        print(f"Send stdout: {send_result.stdout}")
        print(f"Send stderr: {send_result.stderr}")
        
        # Check server output
        time.sleep(2)
        if server_process.poll() is None:
            print("✅ Server still running")
        else:
            stdout, stderr = server_process.communicate()
            print(f"Server output: {stdout}")
            print(f"Server errors: {stderr}")
        
        # Clean up
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
        
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = test_rust_server_custom_handler()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""Test if Rust server builds correctly with custom handler"""

import subprocess
import tempfile
from pathlib import Path

def test_rust_server_build():
    test_dir = Path(tempfile.mkdtemp())
    
    print(f"Testing Rust server build in {test_dir}")
    
    try:
        # Copy the exact server code from cross_platform_tests.py
        server_code = '''
use tokio;
use RustJanus::server::JanusServer;
use RustJanus::config::ServerConfig;
use RustJanus::models::JSONRPCError;

#[tokio::main]
async fn main() {
    let socket_path = std::env::args().nth(1).expect("Socket path required");
    
    // Remove existing socket
    let _ = std::fs::remove_file(&socket_path);
    
    let config = ServerConfig {
        socket_path: socket_path.clone(),
        max_connections: 100,
        default_timeout: 30.0,
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
}
'''
        
        # Create Cargo.toml
        cargo_toml = '''
[package]
name = "test_rust_server"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "test_server"
path = "src/main.rs"

[dependencies]
RustJanus = { path = "/Users/bahram/ws/prj/Janus/RustJanus" }
tokio = { version = "1.0", features = ["full"] }
serde_json = "1.0"
'''
        
        # Write files
        (test_dir / "Cargo.toml").write_text(cargo_toml)
        (test_dir / "src").mkdir()
        (test_dir / "src" / "main.rs").write_text(server_code)
        
        print("Building Rust server...")
        build_result = subprocess.run([
            "cargo", "build"
        ], cwd=test_dir, capture_output=True, text=True, timeout=60)
        
        print(f"Build return code: {build_result.returncode}")
        if build_result.stdout:
            print(f"Build stdout: {build_result.stdout}")
        if build_result.stderr:
            print(f"Build stderr: {build_result.stderr}")
        
        return build_result.returncode == 0
        
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_rust_server_build()
    print(f"Build {'successful' if success else 'failed'}")
    exit(0 if success else 1)
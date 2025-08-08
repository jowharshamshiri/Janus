#!/usr/bin/env python3
"""Debug Rust server handler registration in detail"""

import subprocess
import time
import os
import tempfile
from pathlib import Path
import sys
import signal

sys.path.insert(0, str(Path.cwd() / "orchestrator"))
from cross_platform_tests import ServerManager

def debug_rust_server_registration():
    """Debug Rust server handler registration process step by step"""
    
    socket_path = f"/tmp/debug_rust_{os.getpid()}.sock"
    
    print(f"🔍 Debugging Rust server registration with socket {socket_path}")
    
    try:
        # Create enhanced debug Rust server with detailed logging
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
    println!("🔧 Starting Rust server with socket: {}", socket_path);
    
    // Remove existing socket
    let _ = std::fs::remove_file(socket_path);
    
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        println!("🔧 Creating server config...");
        let config = ServerConfig {
            socket_path: socket_path.to_string(),
            max_connections: 10,
            default_timeout: 30,
            max_message_size: 65536,
            cleanup_on_start: true,
            cleanup_on_shutdown: true,
        };
        
        println!("🔧 Creating JanusServer instance...");
        let mut server = JanusServer::new(config);
        
        println!("🔧 Registering custom_test handler...");
        server.register_handler("custom_test", |request| {
            println!("🎯 custom_test handler called with request: {:?}", request);
            let test_param = request.args
                .as_ref()
                .and_then(|args| args.get("test_param"))
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            
            let response = serde_json::json!({
                "result": "custom_test_success", 
                "received_param": test_param,
                "handler_called": true
            });
            
            println!("🎯 custom_test returning: {:?}", response);
            Ok(response)
        }).await;
        
        println!("🔧 Handler registered successfully");
        
        println!("🔧 Starting server listening...");
        if let Err(e) = server.start_listening().await {
            eprintln!("❌ Failed to start server: {}", e);
            std::process::exit(1);
        }
        
        println!("SERVER_READY");
        println!("🔧 Server ready and listening...");
        
        // Enhanced wait with periodic status
        tokio::select! {
            result = server.wait_for_completion() => {
                match result {
                    Ok(_) => println!("🔧 Server completed successfully"),
                    Err(e) => eprintln!("❌ Server error: {}", e)
                }
            }
            _ = tokio::signal::ctrl_c() => {
                println!("🔧 Received interrupt signal, shutting down...");
            }
        }
    });
}
'''
        
        # Create enhanced Rust project structure
        rust_test_dir = Path("/Users/bahram/ws/prj/Janus/tests/library_based_tests/rust")
        debug_server_path = rust_test_dir / "src" / "bin" / "debug_enhanced.rs"
        debug_server_path.write_text(server_code)
        
        # Update Cargo.toml to include debug binary
        cargo_toml = rust_test_dir / "Cargo.toml"
        cargo_content = cargo_toml.read_text()
        
        if "debug_enhanced" not in cargo_content:
            cargo_content += '''
[[bin]]
name = "debug_enhanced"
path = "src/bin/debug_enhanced.rs"
'''
            cargo_toml.write_text(cargo_content)
        
        print("🔧 Building enhanced debug server...")
        build_result = subprocess.run([
            "cargo", "build", "--bin", "debug_enhanced"
        ], cwd=rust_test_dir, capture_output=True, text=True, timeout=60)
        
        if build_result.returncode != 0:
            print(f"❌ Build failed: {build_result.stderr}")
            return False
        
        print("✅ Build successful")
        
        # Start enhanced server
        print("🔧 Starting enhanced debug server...")
        server_process = subprocess.Popen([
            "./target/debug/debug_enhanced", socket_path
        ], cwd=rust_test_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        bufsize=1, universal_newlines=True)
        
        # Wait for server ready with real-time output
        start_time = time.time()
        server_ready = False
        
        while time.time() - start_time < 15:
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"❌ Server exited early:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
            
            # Check for socket file
            if os.path.exists(socket_path):
                server_ready = True
                print("✅ Socket file created, server appears ready")
                break
            
            time.sleep(0.1)
        
        if not server_ready:
            print("❌ Server failed to create socket within timeout")
            server_process.terminate()
            return False
        
        # Give server a moment to fully initialize
        time.sleep(2)
        
        # Now test the custom_test request using the cross-platform test infrastructure
        print("🔧 Testing custom_test request with TypeScript client...")
        
        # Get the TypeScript client test code from cross-platform tests
        ts_client_code = '''
import { JanusClient } from '/Users/bahram/ws/prj/Janus/TypeScriptJanus/dist/protocol/janus-client.js';

const serverSocket = process.argv[2];

async function runTests() {
    try {
        console.log('🔧 Creating TypeScript client...');
        const config = { 
            socketPath: serverSocket,
            maxMessageSize: 64 * 1024,
            defaultTimeout: 10000,
            enableValidation: false
        };
        const client = new JanusClient(config);
        
        console.log('🔧 Testing custom_test request...');
        const customResponse = await client.sendRequest('custom_test', {
            test_param: 'typescript_debug_value'
        });
        
        console.log('✅ CUSTOM_TEST_SUCCESS:', JSON.stringify(customResponse));
        
        await client.disconnect();
        process.exit(0);
        
    } catch (error) {
        console.log('❌ CUSTOM_TEST_ERROR:', error.message);
        console.log('Error code:', error.code);
        console.log('Error details:', error.details);
        process.exit(1);
    }
}

runTests();
'''
        
        # Create TypeScript test client
        test_dir = Path(tempfile.mkdtemp())
        ts_test_dir = test_dir / "typescript_test"
        ts_test_dir.mkdir()
        (ts_test_dir / "test_client.mjs").write_text(ts_client_code)
        
        # Run TypeScript client test
        client_result = subprocess.run([
            "node", "test_client.mjs", socket_path
        ], cwd=ts_test_dir, capture_output=True, text=True, timeout=15)
        
        print(f"TypeScript client return code: {client_result.returncode}")
        print(f"TypeScript client stdout: {client_result.stdout}")
        print(f"TypeScript client stderr: {client_result.stderr}")
        
        # Check server output for handler calls
        time.sleep(1)
        
        # Try to get server output
        try:
            # Send SIGTERM to get server to output final logs
            server_process.terminate()
            stdout, stderr = server_process.communicate(timeout=5)
            print(f"🔧 Server final output:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        except subprocess.TimeoutExpired:
            server_process.kill()
            stdout, stderr = server_process.communicate()
            print(f"🔧 Server output (after kill):")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        
        success = client_result.returncode == 0 and "CUSTOM_TEST_SUCCESS" in client_result.stdout
        return success
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    finally:
        try:
            if 'server_process' in locals():
                server_process.kill()
        except:
            pass
        try:
            os.remove(socket_path)
        except:
            pass

if __name__ == "__main__":
    success = debug_rust_server_registration()
    print(f"\n🎯 Debug test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
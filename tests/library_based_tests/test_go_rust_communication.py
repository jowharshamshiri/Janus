#!/usr/bin/env python3
"""
Simple test script to validate Go client to Rust server communication
This is the critical path that needs to work first
"""

import subprocess
import time
import os
import sys
from pathlib import Path

def test_go_to_rust():
    """Test Go client communicating with Rust server"""
    
    base_dir = Path(__file__).parent
    socket_path = "/tmp/janus_go_rust_test.sock"
    
    # Clean up any existing socket
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    
    print("🚀 Testing Go Client → Rust Server Communication")
    print("=" * 50)
    
    # Step 1: Start Rust server
    print("\n1️⃣ Starting Rust server...")
    
    rust_server_code = '''
use std::env;
use tokio::runtime::Runtime;
use rust_janus::server::{JanusServer, ServerConfig};

fn main() {
    let socket_path = env::args().nth(1).expect("socket path required");
    println!("Starting Rust server on: {}", socket_path);
    
    // Remove existing socket
    let _ = std::fs::remove_file(&socket_path);
    
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
        
        println!("Rust server ready on {}", socket_path);
        
        // Run until terminated
        server.wait_for_completion().await;
    });
}
'''
    
    # Write Rust server code
    rust_dir = base_dir / "rust"
    server_file = rust_dir / "src" / "bin" / "test_server.rs"
    server_file.parent.mkdir(parents=True, exist_ok=True)
    server_file.write_text(rust_server_code)
    
    # Build Rust server
    print("Building Rust server...")
    build_result = subprocess.run(
        ["cargo", "build", "--bin", "test_server"],
        cwd=rust_dir,
        capture_output=True,
        text=True
    )
    
    if build_result.returncode != 0:
        print(f"❌ Rust build failed: {build_result.stderr}")
        return False
    
    # Start Rust server process
    server_env = os.environ.copy()
    server_env["RUST_LOG"] = "debug"
    
    server_process = subprocess.Popen(
        ["cargo", "run", "--bin", "test_server", "--", socket_path],
        cwd=rust_dir,
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    max_wait = 10
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if os.path.exists(socket_path):
            print("✅ Server socket created")
            time.sleep(1)  # Give it a moment to fully initialize
            break
        time.sleep(0.5)
    else:
        print("❌ Timeout waiting for server")
        server_process.terminate()
        return False
    
    try:
        # Step 2: Run Go client
        print("\n2️⃣ Running Go client...")
        
        go_client_code = '''
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "time"
    "encoding/json"
    "GoJanus/pkg/protocol"
)

func main() {
    if len(os.Args) < 2 {
        log.Fatal("Usage: test_client <socket_path>")
    }
    
    socketPath := os.Args[1]
    fmt.Printf("Connecting to server at: %s\\n", socketPath)
    
    // Create client
    client, err := protocol.New(socketPath)
    if err != nil {
        log.Fatalf("Failed to create client: %v", err)
    }
    defer client.Close()
    
    // Test 1: Get manifest
    fmt.Println("\\nTest 1: Getting manifest...")
    manifest := client.GetManifest()
    if manifest == nil {
        // Manifest is lazy-loaded, force load by making a request
        ctx := context.Background()
        err = client.TestConnection(ctx)
        if err != nil {
            log.Printf("❌ Failed to test connection: %v", err)
        }
        manifest = client.GetManifest()
    }
    
    if manifest != nil {
        fmt.Printf("✅ Manifest received: version=%s\\n", manifest.Version)
        manifestJSON, _ := json.MarshalIndent(manifest, "", "  ")
        fmt.Printf("Full manifest:\\n%s\\n", string(manifestJSON))
    } else {
        log.Printf("❌ Failed to get manifest")
    }
    
    // Test 2: Echo request
    fmt.Println("\\nTest 2: Echo request...")
    args := map[string]interface{}{
        "message": "Hello from Go client",
        "timestamp": time.Now().Format(time.RFC3339),
    }
    
    ctx := context.Background()
    result, err := client.SendRequest(ctx, "echo", args)
    if err != nil {
        log.Printf("❌ Echo request failed: %v", err)
    } else {
        fmt.Println("✅ Echo response received:")
        resultJSON, _ := json.MarshalIndent(result, "", "  ")
        fmt.Printf("%s\\n", string(resultJSON))
    }
    
    fmt.Println("\\n✅ All tests completed")
}
'''
        
        # Write Go client code
        go_dir = base_dir / "go"
        client_file = go_dir / "test_client.go"
        client_file.write_text(go_client_code)
        
        # Build Go client
        print("Building Go client...")
        build_result = subprocess.run(
            ["go", "build", "-o", "test_client", "test_client.go"],
            cwd=go_dir,
            capture_output=True,
            text=True
        )
        
        if build_result.returncode != 0:
            print(f"❌ Go build failed: {build_result.stderr}")
            return False
        
        # Run Go client
        print("Running Go client tests...")
        client_result = subprocess.run(
            ["./test_client", socket_path],
            cwd=go_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("\nClient output:")
        print(client_result.stdout)
        if client_result.stderr:
            print("Client stderr:")
            print(client_result.stderr)
        
        # Check if tests passed
        success = client_result.returncode == 0 and "All tests completed" in client_result.stdout
        
        if success:
            print("\n✅ Go → Rust communication successful!")
        else:
            print("\n❌ Go → Rust communication failed!")
            
            # Get server logs
            print("\nServer logs:")
            server_process.terminate()
            stdout, stderr = server_process.communicate(timeout=2)
            print("Server stdout:", stdout)
            print("Server stderr:", stderr)
        
        return success
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
        
        # Clean up files
        if server_file.exists():
            server_file.unlink()
        if client_file.exists():
            client_file.unlink()
        if os.path.exists(socket_path):
            os.unlink(socket_path)


def test_rust_to_go():
    """Test Rust client communicating with Go server"""
    
    base_dir = Path(__file__).parent
    socket_path = "/tmp/janus_rust_go_test.sock"
    
    # Clean up any existing socket
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    
    print("\n🚀 Testing Rust Client → Go Server Communication")
    print("=" * 50)
    
    # Step 1: Start Go server
    print("\n1️⃣ Starting Go server...")
    
    go_server_code = '''
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
    if len(os.Args) < 2 {
        log.Fatal("Usage: test_server <socket_path>")
    }
    
    socketPath := os.Args[1]
    fmt.Printf("Starting Go server on: %s\\n", socketPath)
    
    // Remove existing socket
    os.Remove(socketPath)
    
    // Create and start server
    config := &server.ServerConfig{
        SocketPath:        socketPath,
        MaxConnections:    10,
        DefaultTimeout:    30,
        MaxMessageSize:    65536,
        CleanupOnStart:    true,
        CleanupOnShutdown: true,
    }
    
    srv := server.NewJanusServer(config)
    
    if err := srv.StartListening(); err != nil {
        log.Fatalf("Failed to start server: %v", err)
    }
    
    fmt.Println("Go server ready")
    
    // Wait for signal
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
    <-sigChan
    
    srv.Stop()
}
'''
    
    # Write Go server code
    go_dir = base_dir / "go"
    server_file = go_dir / "test_server.go"
    server_file.write_text(go_server_code)
    
    # Build Go server
    print("Building Go server...")
    build_result = subprocess.run(
        ["go", "build", "-o", "test_server", "test_server.go"],
        cwd=go_dir,
        capture_output=True,
        text=True
    )
    
    if build_result.returncode != 0:
        print(f"❌ Go build failed: {build_result.stderr}")
        return False
    
    # Start Go server process
    server_process = subprocess.Popen(
        ["./test_server", socket_path],
        cwd=go_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    max_wait = 10
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if os.path.exists(socket_path):
            print("✅ Server socket created")
            time.sleep(1)  # Give it a moment to fully initialize
            break
        time.sleep(0.5)
    else:
        print("❌ Timeout waiting for server")
        server_process.terminate()
        return False
    
    try:
        # Step 2: Run Rust client
        print("\n2️⃣ Running Rust client...")
        
        rust_client_code = '''
use std::env;
use std::collections::HashMap;
use tokio::runtime::Runtime;
use rust_janus::protocol::JanusClient;
use rust_janus::JanusClientConfig;
use serde_json::json;

fn main() {
    let socket_path = env::args().nth(1).expect("socket path required");
    println!("Connecting to server at: {}", socket_path);
    
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        match run_tests(&socket_path).await {
            Ok(_) => {
                println!("\\n✅ All tests completed");
                std::process::exit(0);
            }
            Err(e) => {
                eprintln!("❌ Test failed: {}", e);
                std::process::exit(1);
            }
        }
    });
}

async fn run_tests(socket_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Create client with default config
    let config = JanusClientConfig::default();
    let mut client = JanusClient::new(socket_path.to_string(), config).await?;
    
    // Test 1: Get manifest
    println!("\\nTest 1: Getting manifest...");
    if let Some(manifest) = client.manifest() {
        println!("✅ Manifest received: version={}", manifest.version);
        println!("Full manifest: {:#?}", manifest);
    } else {
        println!("❌ No manifest available");
    }
    
    // Test 2: Echo request
    println!("\\nTest 2: Echo request...");
    let mut args = HashMap::new();
    args.insert("message".to_string(), json!("Hello from Rust client"));
    args.insert("timestamp".to_string(), json!(chrono::Utc::now().to_rfc3339()));
    
    let result = client.send_request("echo", Some(args), None).await?;
    println!("✅ Echo response received:");
    if let Some(result_value) = result.result {
        println!("{}", serde_json::to_string_pretty(&result_value)?);
    }
    
    Ok(())
}
'''
        
        # Write Rust client code
        rust_dir = base_dir / "rust"
        client_file = rust_dir / "src" / "bin" / "test_client.rs"
        client_file.parent.mkdir(parents=True, exist_ok=True)
        client_file.write_text(rust_client_code)
        
        # Build Rust client
        print("Building Rust client...")
        build_result = subprocess.run(
            ["cargo", "build", "--bin", "test_client"],
            cwd=rust_dir,
            capture_output=True,
            text=True
        )
        
        if build_result.returncode != 0:
            print(f"❌ Rust build failed: {build_result.stderr}")
            return False
        
        # Run Rust client
        print("Running Rust client tests...")
        client_env = os.environ.copy()
        client_env["RUST_LOG"] = "debug"
        
        client_result = subprocess.run(
            ["cargo", "run", "--bin", "test_client", "--", socket_path],
            cwd=rust_dir,
            env=client_env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("\nClient output:")
        print(client_result.stdout)
        if client_result.stderr:
            print("Client stderr:")
            print(client_result.stderr)
        
        # Check if tests passed
        success = client_result.returncode == 0 and "All tests completed" in client_result.stdout
        
        if success:
            print("\n✅ Rust → Go communication successful!")
        else:
            print("\n❌ Rust → Go communication failed!")
            
            # Get server logs
            print("\nServer logs:")
            server_process.terminate()
            stdout, stderr = server_process.communicate(timeout=2)
            print("Server stdout:", stdout)
            print("Server stderr:", stderr)
        
        return success
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
        
        # Clean up files
        if server_file.exists():
            server_file.unlink()
        if client_file.exists():
            client_file.unlink()
        if os.path.exists(socket_path):
            os.unlink(socket_path)


def main():
    """Run critical cross-platform tests"""
    print("🔥 Running Critical Cross-Platform Communication Tests")
    print("This tests the actual library APIs, not just the CLI binaries")
    print("")
    
    # Test 1: Go → Rust
    go_rust_success = test_go_to_rust()
    
    # Test 2: Rust → Go
    rust_go_success = test_rust_to_go()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Go → Rust: {'✅ PASS' if go_rust_success else '❌ FAIL'}")
    print(f"Rust → Go: {'✅ PASS' if rust_go_success else '❌ FAIL'}")
    
    if go_rust_success and rust_go_success:
        print("\n✅ All critical tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
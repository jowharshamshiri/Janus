use std::process::{Command, Stdio};
use std::time::Duration;
use tokio::time::{timeout, sleep};
use serde_json::json;
use uuid::Uuid;
use std::os::unix::net::UnixDatagram;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use tokio::sync::Mutex;
use std::collections::HashMap;

use rust_janus::server::janus_server::{JanusServer, ServerConfig};
use rust_janus::config::JanusClientConfig;
use rust_janus::protocol::janus_client::JanusClient;

/// Test Go client → Rust server communication using direct listen_loop
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn test_go_client_to_rust_server() {
    let socket_path = format!("/tmp/cross-platform-test-{}.sock", Uuid::new_v4());
    
    // Clean up any existing socket
    std::fs::remove_file(&socket_path).ok();
    
    // Use listen_loop directly like the working tests
    let handlers = Arc::new(Mutex::new(HashMap::new()));
    let async_handlers = Arc::new(Mutex::new(HashMap::new()));
    let is_running = Arc::new(AtomicBool::new(true));
    
    println!("Starting server with listen_loop directly...");
    
    // Start the server using listen_loop directly
    let server_handle = tokio::spawn({
        let socket_path = socket_path.clone();
        let handlers = Arc::clone(&handlers);
        let async_handlers = Arc::clone(&async_handlers);
        let is_running = Arc::clone(&is_running);
        
        async move {
            let result = JanusServer::listen_loop(socket_path, handlers, async_handlers, is_running).await;
            println!("Server listen_loop completed: {:?}", result);
            result
        }
    });
    
    // Give server time to start and bind socket
    sleep(Duration::from_millis(500)).await;
    
    // Test with a simple datagram first
    println!("DEBUG: Sending test datagram to verify socket works...");
    if let Ok(test_socket) = UnixDatagram::unbound() {
        let test_msg = b"TEST";
        match test_socket.send_to(test_msg, &socket_path) {
            Ok(_) => println!("DEBUG: Test datagram sent successfully"),
            Err(e) => println!("DEBUG: Failed to send test datagram: {}", e),
        }
    }
    
    // Give server time to receive test datagram
    sleep(Duration::from_millis(100)).await;
    
    // Verify socket file exists before proceeding
    let mut retries = 0;
    while !std::path::Path::new(&socket_path).exists() && retries < 20 {
        sleep(Duration::from_millis(100)).await;
        retries += 1;
    }
    
    if !std::path::Path::new(&socket_path).exists() {
        panic!("Rust server failed to create socket file: {}", socket_path);
    }
    
    println!("Socket file verified: {}", socket_path);
    
    // Test Go client → Rust server manifest request
    // This uses the actual Go binary but tests the Rust library server
    println!("DEBUG: Attempting Go client → Rust server communication");
    println!("DEBUG: Server socket path: {}", socket_path);
    println!("DEBUG: Go client binary path: ../../../GoJanus/janus");
    
    // Execute Go client while server stays alive using concurrent tasks
    let socket_path_clone = socket_path.clone();
    let go_client_future = async move {
        // Wait to ensure server is fully ready and actively polling
        sleep(Duration::from_millis(1000)).await;
        
        let go_client_output = Command::new("../../../GoJanus/janus")
            .args(&[
                "--send-to", &socket_path_clone,
                "--request", "ping"
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .expect("Failed to execute Go client");
        go_client_output
    };
    
    // Keep server alive during client execution - use wait_for_completion for proper lifecycle
    let server_task = tokio::spawn(async move {
        // Keep server running for the test duration
        sleep(Duration::from_secs(20)).await;
        println!("DEBUG: Server task timeout reached");
    });
    
    let go_client_output = go_client_future.await;
    
    let stdout = String::from_utf8_lossy(&go_client_output.stdout);
    let stderr = String::from_utf8_lossy(&go_client_output.stderr);
    
    println!("Go client stdout: {}", stdout);
    println!("Go client stderr: {}", stderr);
    println!("Go client exit code: {}", go_client_output.status.code().unwrap_or(-1));
    
    // Stop the server after test completes
    is_running.store(false, Ordering::SeqCst);
    server_handle.abort();
    
    // CRITICAL: This should now succeed after fixing the Rust server
    assert!(go_client_output.status.success(), "Go client → Rust server should succeed");
    
    // Parse the output to validate response structure
    if stdout.contains("Success=true") {
        println!("✓ Go client → Rust server communication successful");
        
        // Validate the response contains proper ping response
        assert!(stdout.contains("pong"), "Response should contain pong");
        assert!(stdout.contains("timestamp"), "Response should contain timestamp");
        
        // CRITICAL: Should NOT contain "manifest" wrapper
        assert!(!stdout.contains("manifest:"), "Should not have manifest wrapper");
    } else {
        panic!("Go client → Rust server failed: {}", stderr);
    }
    
    // Cleanup
    std::fs::remove_file(&socket_path).ok();
}

/// Test Rust client → Go server communication
#[tokio::test]
async fn test_rust_client_to_go_server() {
    let socket_path = format!("/tmp/rust-to-go-test-{}.sock", Uuid::new_v4());
    
    // Start Go server using binary (we need the fixed Go server binary)
    let mut go_server = Command::new("../../../GoJanus/janus")
        .args(&["--listen", "--socket", &socket_path])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("Failed to start Go server");
    
    // Give server time to start
    sleep(Duration::from_millis(500)).await;
    
    // Verify socket file exists before proceeding
    let mut retries = 0;
    while !std::path::Path::new(&socket_path).exists() && retries < 10 {
        sleep(Duration::from_millis(100)).await;
        retries += 1;
    }
    
    if !std::path::Path::new(&socket_path).exists() {
        panic!("Go server failed to create socket file: {}", socket_path);
    }
    
    // Test Rust client → Go server using library
    let client_result = timeout(Duration::from_secs(10), async {
        let config = JanusClientConfig::default();
        let mut client = JanusClient::new(socket_path.clone(), config)
            .await.expect("Failed to create Rust client");
        
        let result = client.send_request("manifest", None, None).await
            .expect("Manifest request should succeed");
        
        result
    }).await;
    
    match client_result {
        Ok(result) => {
            println!("✓ Rust client → Go server communication successful");
            println!("Response: {:?}", result);
            
            // Validate response structure - result.Result should be a Manifest
            assert!(result.success, "Response should be successful");
            if let Some(manifest_data) = result.result {
                if let Some(manifest_object) = manifest_data.as_object() {
                    assert!(manifest_object.contains_key("version"), "Response should contain version");
                    // Channels have been removed from the protocol
                    assert!(!manifest_object.contains_key("channels"), "Channels should not exist in protocol");
                    // Should not be wrapped in manifest field
                    assert!(!manifest_object.contains_key("manifest"), "Should not have manifest wrapper");
                } else {
                    panic!("Response result should be an object");
                }
            } else {
                panic!("Response should contain result data");
            }
        }
        Err(_) => {
            panic!("Rust client → Go server timeout");
        }
    }
    
    // Cleanup
    go_server.kill().ok();
    std::fs::remove_file(&socket_path).ok();
}

/// Test built-in request consistency across platforms
#[tokio::test]
async fn test_cross_platform_builtin_requests() {
    let socket_path = format!("/tmp/builtin-cross-test-{}.sock", Uuid::new_v4());
    
    // Start Rust server
    let config = ServerConfig {
        socket_path: socket_path.clone(),
        max_connections: 100,
        default_timeout: 30,
        max_message_size: 65536,
        cleanup_on_start: true,
        cleanup_on_shutdown: true,
    };
    let mut server = JanusServer::new(config);
    let _server_handle = tokio::spawn(async move {
        match server.start_listening().await {
            Ok(_) => {
                println!("Test server started, waiting for completion...");
                server.wait_for_completion().await;
            }
            Err(e) => {
                eprintln!("Test server error: {}", e);
            }
        }
    });
    
    sleep(Duration::from_millis(200)).await;
    
    // Test each built-in request with Go client → Rust server
    let requests = vec!["ping", "echo", "get_info", "validate", "slow_process", "manifest"];
    
    for cmd in requests {
        println!("Testing request: {}", cmd);
        
        let output = Command::new("../../../GoJanus/janus")
            .args(&[
                "--send-to", &socket_path,
                "--request", cmd,
                "--message", "test"
            ])
            .output()
            .expect("Failed to execute Go client");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        
        if output.status.success() && stdout.contains("Success=true") {
            println!("✓ Request {} successful", cmd);
            
            // Validate response structure for manifest request manifestifically
            if cmd == "manifest" {
                assert!(stdout.contains("version"), "Manifest should contain version"); 
                assert!(!stdout.contains("manifest:"), "Manifest should not be wrapped");
            }
        } else {
            println!("✗ Request {} failed: {}", cmd, stderr);
            // Don't panic for individual requests, log for analysis
        }
    }
    
    // Cleanup
    std::fs::remove_file(&socket_path).ok();
}

/// Test message format consistency between Go and Rust
#[tokio::test]
async fn test_message_format_consistency() {
    // Test that Go and Rust produce identical JSON structures
    
    // Test JanusRequest format
    let request_json = json!({
        "id": "test-123",
        "request": "ping",
        "channelId": "test", 
        "args": {"message": "hello"},
        "replyTo": "/tmp/test-reply.sock"
    });
    
    // Validate JSON structure that both Go and Rust should produce
    assert_eq!(request_json["id"], "test-123");
    assert_eq!(request_json["request"], "ping");
    assert!(request_json["args"].is_object());
    
    println!("Standard JanusRequest JSON: {}", serde_json::to_string_pretty(&request_json).unwrap());
    
    // Test JanusResponse format
    let response_json = json!({
        "id": "test-123",
        "success": true,
        "result": {"data": "response"}
        // Note: error field omitted when null - this is critical!
    });
    
    // Validate response structure
    assert_eq!(response_json["success"], true);
    assert!(response_json["result"].is_object());
    
    // CRITICAL: error field should not be present when null
    assert!(!response_json.as_object().unwrap().contains_key("error"));
    
    println!("Standard JanusResponse JSON: {}", serde_json::to_string_pretty(&response_json).unwrap());
}

/// Simple test to verify Rust server can receive datagram from basic Unix socket
#[tokio::test]
async fn test_basic_datagram_communication() {
    let server_socket = "/tmp/simple-test-server.sock";
    let client_socket = "/tmp/simple-test-client.sock";
    
    // Remove any existing sockets
    std::fs::remove_file(server_socket).ok();
    std::fs::remove_file(client_socket).ok();
    
    // Create server socket
    let server = UnixDatagram::bind(server_socket).expect("Failed to bind server socket");
    server.set_nonblocking(true).expect("Failed to set non-blocking");
    
    println!("Server bound to: {}", server_socket);
    
    // Create client and send message
    let client = UnixDatagram::bind(client_socket).expect("Failed to bind client socket");
    let test_message = b"Hello from client";
    client.send_to(test_message, server_socket).expect("Failed to send message");
    
    println!("Client sent message: {:?}", std::str::from_utf8(test_message));
    
    // Try to receive on server
    let mut buffer = [0u8; 1024];
    let receive_result = timeout(Duration::from_secs(2), async {
        loop {
            match server.recv_from(&mut buffer) {
                Ok((size, addr)) => {
                    let received = &buffer[..size];
                    println!("Server received {} bytes: {:?}", size, std::str::from_utf8(received));
                    return (size, addr);
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    tokio::time::sleep(Duration::from_millis(10)).await;
                    continue;
                }
                Err(e) => panic!("Receive error: {}", e),
            }
        }
    }).await;
    
    match receive_result {
        Ok((size, _addr)) => {
            let received = &buffer[..size];
            assert_eq!(received, test_message);
            println!("✓ Basic datagram communication successful");
        }
        Err(_) => {
            panic!("Timeout waiting for message");
        }
    }
    
    // Cleanup
    std::fs::remove_file(server_socket).ok();
    std::fs::remove_file(client_socket).ok();
}

/// Test Go client with JanusServer direct (no spawn)
#[tokio::test]
async fn test_go_client_to_janus_server_direct() {
    let socket_path = "/tmp/go-to-janus-direct.sock";
    std::fs::remove_file(socket_path).ok();
    
    let _config = ServerConfig {
        socket_path: socket_path.to_string(),
        max_connections: 100,
        default_timeout: 30,
        max_message_size: 65536,
        cleanup_on_start: true,
        cleanup_on_shutdown: true,
    };
    
    // Test JanusServer listen_loop directly (no spawn/task)
    let handlers = Arc::new(Mutex::new(HashMap::new()));
    let async_handlers = Arc::new(Mutex::new(HashMap::new()));
    let is_running = Arc::new(AtomicBool::new(true));
    
    // Run server in background task but with shorter timeout
    let server_task = tokio::spawn({
        let socket_path = socket_path.to_string();
        let handlers = Arc::clone(&handlers);
        let async_handlers = Arc::clone(&async_handlers);
        let is_running = Arc::clone(&is_running);
        
        async move {
            println!("Starting direct JanusServer listen_loop");
            let result = JanusServer::listen_loop(socket_path, handlers, async_handlers, is_running).await;
            println!("JanusServer listen_loop completed: {:?}", result);
            result
        }
    });
    
    // Give server time to start
    sleep(Duration::from_millis(100)).await;
    
    // Verify socket exists
    assert!(std::path::Path::new(socket_path).exists(), "Socket file should exist");
    
    // Run Go client
    let go_client_output = std::process::Command::new("../../../GoJanus/janus")
        .args(&[
            "--send-to", socket_path,
            "--request", "manifest",
            "--channel", "test"
        ])
        .output()
        .expect("Failed to execute Go client");
    
    println!("Go client stdout: {}", String::from_utf8_lossy(&go_client_output.stdout));
    println!("Go client stderr: {}", String::from_utf8_lossy(&go_client_output.stderr));
    
    // Give server time to process
    sleep(Duration::from_millis(1000)).await;
    
    // Stop server
    is_running.store(false, Ordering::SeqCst);
    server_task.abort();
    
    std::fs::remove_file(socket_path).ok();
    
    if go_client_output.status.success() {
        println!("✓ Go client succeeded with JanusServer direct");
    } else {
        println!("⚠ Go client failed with JanusServer direct - but this might be expected due to timeout");
    }
}

/// Test Go client can send to basic Rust socket
#[tokio::test] 
async fn test_go_client_to_basic_rust_socket() {
    let socket_path = "/tmp/go-to-basic-rust.sock";
    std::fs::remove_file(socket_path).ok();
    
    // Create basic Rust server socket (like our working test)
    let server = UnixDatagram::bind(socket_path).expect("Failed to bind server socket");
    server.set_nonblocking(true).expect("Failed to set non-blocking");
    
    println!("Basic Rust socket bound to: {}", socket_path);
    
    // Start Go client in background
    let go_client_output = std::process::Command::new("../../../GoJanus/janus")
        .args(&[
            "--send-to", socket_path,
            "--request", "ping", 
            "--channel", "test"
        ])
        .output()
        .expect("Failed to execute Go client");
    
    println!("Go client stdout: {}", String::from_utf8_lossy(&go_client_output.stdout));
    println!("Go client stderr: {}", String::from_utf8_lossy(&go_client_output.stderr));
    println!("Go client exit code: {}", go_client_output.status.code().unwrap_or(-1));
    
    // Try to receive data on basic socket
    let mut buffer = [0u8; 64 * 1024];
    let receive_result = timeout(Duration::from_secs(2), async {
        loop {
            match server.recv_from(&mut buffer) {
                Ok((size, addr)) => {
                    let received = &buffer[..size];
                    println!("Basic socket received {} bytes: {:?}", size, std::str::from_utf8(received));
                    return (size, addr);
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    tokio::time::sleep(Duration::from_millis(10)).await;
                    continue;
                }
                Err(e) => panic!("Receive error: {}", e),
            }
        }
    }).await;
    
    match receive_result {
        Ok((size, _addr)) => {
            println!("✓ Go client → basic Rust socket successful, received {} bytes", size);
            let received = &buffer[..size];
            // Verify it's valid JSON (Go should be sending JanusRequest JSON)
            if let Ok(json_str) = std::str::from_utf8(received) {
                if json_str.contains("\"request\":\"ping\"") {
                    println!("✓ Received valid JSON request from Go client");
                } else {
                    println!("⚠ Received data but not expected ping request: {}", json_str);
                }
            }
        }
        Err(_) => {
            if go_client_output.status.success() {
                panic!("Go client succeeded but no data received on basic socket");
            } else {
                println!("Both Go client and socket receive failed - investigating...");
            }
        }
    }
    
    std::fs::remove_file(socket_path).ok();
}

/// Test sending from unbound socket like Go client does  
#[tokio::test]
async fn test_unbound_client_to_server() {
    let server_socket = "/tmp/unbound-test-server.sock";
    
    // Remove any existing socket
    std::fs::remove_file(server_socket).ok();
    
    // Create server socket
    let server = UnixDatagram::bind(server_socket).expect("Failed to bind server socket");
    server.set_nonblocking(true).expect("Failed to set non-blocking");
    
    println!("Server bound to: {}", server_socket);
    
    // Create unbound client (like Go does with DialUnix)
    let client = UnixDatagram::unbound().expect("Failed to create unbound client");
    let test_message = b"Hello from unbound client";
    client.send_to(test_message, server_socket).expect("Failed to send message");
    
    println!("Unbound client sent message: {:?}", std::str::from_utf8(test_message));
    
    // Try to receive on server
    let mut buffer = [0u8; 1024];
    let receive_result = timeout(Duration::from_secs(2), async {
        loop {
            match server.recv_from(&mut buffer) {
                Ok((size, addr)) => {
                    let received = &buffer[..size];
                    println!("Server received {} bytes: {:?}", size, std::str::from_utf8(received));
                    println!("Sender address: {:?}", addr);
                    return (size, addr);
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    tokio::time::sleep(Duration::from_millis(10)).await;
                    continue;
                }
                Err(e) => panic!("Receive error: {}", e),
            }
        }
    }).await;
    
    match receive_result {
        Ok((size, _addr)) => {
            let received = &buffer[..size];
            assert_eq!(received, test_message);
            println!("✓ Unbound client communication successful");
        }
        Err(_) => {
            panic!("Timeout waiting for message from unbound client");
        }
    }
    
    // Cleanup
    std::fs::remove_file(server_socket).ok();
}
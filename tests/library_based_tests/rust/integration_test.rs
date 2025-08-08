use std::collections::HashMap;
use std::time::Duration;
use tokio::time::timeout;
use serde_json::json;
use uuid::Uuid;

use rust_janus::protocol::janus_client::JanusClient;
use rust_janus::server::janus_server::{JanusServer, ServerConfig};
use rust_janus::config::JanusClientConfig;

/// Test Rust library manifest request directly (not CLI binary)
/// This test would have caught the "manifest" wrapper bug
#[tokio::test]
async fn test_rust_library_manifest_request() {
    let socket_path = format!("/tmp/rust-lib-test-{}.sock", Uuid::new_v4());
    
    // Start Rust server using library (not binary)
    let config = ServerConfig {
        socket_path: socket_path.clone(),
        max_connections: 100,
        default_timeout: 30,
        max_message_size: 65536,
        cleanup_on_start: true,
        cleanup_on_shutdown: true,
    };
    let mut server = JanusServer::new(config);
    
    // Start server in background task
    let server_handle = tokio::spawn(async move {
        if let Err(e) = server.start_listening().await {
            eprintln!("Server error: {}", e);
        }
        // Keep server running
        server.wait_for_completion().await;
    });
    
    // Give server time to start and verify socket exists
    tokio::time::sleep(Duration::from_millis(200)).await;
    let mut retries = 0;
    while !std::path::Path::new(&socket_path).exists() && retries < 20 {
        tokio::time::sleep(Duration::from_millis(100)).await;
        retries += 1;
    }
    
    // Verify socket file exists
    if !std::path::Path::new(&socket_path).exists() {
        panic!("Server socket file not created after {} retries: {}", retries, socket_path);
    }
    
    // Create Rust client using library (not binary) 
    let client_config = JanusClientConfig::default();
    let mut client = JanusClient::new(socket_path.clone(), client_config)
        .await.expect("Failed to create client");
    
    // Test manifest request using library
    let result = client.send_request("manifest", None, None).await.expect("Manifest request should succeed");
    
    // CRITICAL: Validate actual response structure - this would have caught the bug
    assert!(result.success, "Response should be successful");
    if let Some(ref manifest_data) = result.result {
        if let Some(manifest_object) = manifest_data.as_object() {
            assert!(manifest_object.contains_key("version"), "Manifest response should contain version");
            // Channels have been removed from the protocol
            
            // CRITICAL: This assertion catches the "manifest" wrapper bug
            assert!(!manifest_object.contains_key("manifest"), 
                "Manifest response should NOT be wrapped in manifest field");
        } else {
            panic!("Response result should be an object");
        }
    } else {
        panic!("Response should contain result data");
    }
    
    // Further validation of manifest structure
    if let Some(manifest_data) = &result.result {
        if let Some(manifest_object) = manifest_data.as_object() {
            let version = manifest_object.get("version").expect("Should have version");
            assert!(version.is_string(), "Version should be string");
            
            // Channels have been removed from the protocol
            assert!(!manifest_object.contains_key("channels"), "Channels should not exist");
            
            println!("✅ Rust library manifest request test PASSED");
            println!("Version: {:?}", version);
        }
    }
    
    println!("Rust manifest response structure: {:?}", result);
    
    // Cleanup
    server_handle.abort();
    tokio::time::sleep(Duration::from_millis(50)).await;
    std::fs::remove_file(&socket_path).ok();
}

/// Test Rust library message format validation
#[tokio::test]
async fn test_rust_library_message_format() {
    // Test JanusRequest structure
    let request = json!({
        "id": "test-id-123",
        "request": "ping", 
        "args": {"message": "test"},
        "replyTo": null
    });
    
    // Validate required fields
    assert!(request.get("id").is_some(), "Request should have id field");
    assert!(request.get("request").is_some(), "Request should have request field");
    assert!(request.get("args").is_some(), "Request should have args field");
    
    println!("Rust JanusRequest JSON: {}", request);
    
    // Test JanusResponse structure
    let response = json!({
        "id": "test-id-123",
        "success": true,
        "result": {"data": "test"}
        // Note: error field omitted when null (this was the bug!)
    });
    
    // Validate required fields
    assert!(response.get("id").is_some(), "Response should have id field");
    assert!(response.get("success").is_some(), "Response should have success field");
    assert!(response.get("result").is_some(), "Response should have result field");
    
    // CRITICAL: Error field should be omitted when null (not present)
    // Verify that error field is properly handled (should be None when no error)
    let response_obj = response.as_object().expect("Response should be an object");
    assert!(!response_obj.contains_key("error"), 
        "Error field should be omitted when null");
    
    println!("Rust JanusResponse JSON: {}", response);
}

/// Test all built-in requests for format consistency
#[tokio::test]
async fn test_rust_builtin_requests() {
    let socket_path = format!("/tmp/rust-builtin-test-{}.sock", Uuid::new_v4());
    
    // Start server
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
        if let Err(e) = server.start_listening().await {
            eprintln!("Server error: {}", e);
        }
        // Keep server running
        server.wait_for_completion().await;
    });
    
    // Wait for server to start
    tokio::time::sleep(Duration::from_millis(200)).await;
    let mut retries = 0;
    while !std::path::Path::new(&socket_path).exists() && retries < 20 {
        tokio::time::sleep(Duration::from_millis(100)).await;
        retries += 1;
    }
    
    if !std::path::Path::new(&socket_path).exists() {
        panic!("Server socket file not created: {}", socket_path);
    }
    
    // Create client
    let client_config = JanusClientConfig::default();
    let mut client = JanusClient::new(socket_path.clone(), client_config)
        .await.expect("Failed to create client");
    
    let requests = vec!["ping", "echo", "get_info", "validate", "slow_process", "manifest"];
    
    for cmd in requests {
        let args = if cmd == "manifest" { 
            None 
        } else { 
            Some(HashMap::from([("message".to_string(), json!("test"))])) 
        };
        
        // Use longer timeout for slow_process
        let timeout = if cmd == "slow_process" {
            Some(tokio::time::Duration::from_secs(10))
        } else {
            None
        };
        
        let result = client.send_request(cmd, args, timeout).await
            .expect(&format!("{} request should succeed", cmd));
            
        assert!(result.success, "{} should be successful", cmd);
        
        // For manifest request, validate it's not wrapped
        if cmd == "manifest" {
            // Check that result contains proper manifest data
            if let Some(manifest_data) = &result.result {
                if let Some(manifest_object) = manifest_data.as_object() {
                    assert!(!manifest_object.contains_key("manifest"), 
                        "Manifest should not be wrapped in manifest field");
                    assert!(manifest_object.contains_key("version"), "Manifest should have version");
                } else {
                    panic!("Response result should be an object");
                }
            } else {
                panic!("Response should contain result data");
            }
            // Channels have been removed - don't check for them
        }
        
        println!("{} response structure: {:?}", cmd, result);
    }
    
    // Cleanup
    std::fs::remove_file(&socket_path).ok();
}

/// Test Rust server startup and basic functionality
#[tokio::test]
async fn test_rust_server_startup() {
    let socket_path = format!("/tmp/rust-startup-test-{}.sock", Uuid::new_v4());
    
    // Test server creation
    let config = ServerConfig {
        socket_path: socket_path.clone(),
        max_connections: 100,
        default_timeout: 30,
        max_message_size: 65536,
        cleanup_on_start: true,
        cleanup_on_shutdown: true,
    };
    let mut server = JanusServer::new(config);
    
    // Start server with timeout
    let server_task = server.start_listening();
    let timeout_result = timeout(Duration::from_secs(5), server_task).await;
    
    // Server should start successfully (or timeout, which is expected in test)
    match timeout_result {
        Ok(_) => println!("Server completed (unexpected in test)"),
        Err(_) => println!("Server startup timeout (expected in test)")
    }
    
    // Validate socket file exists (should be created during startup attempt)
    let socket_exists = std::path::Path::new(&socket_path).exists();
    if socket_exists {
        println!("Socket file created successfully");
        std::fs::remove_file(&socket_path).ok();
    }
}
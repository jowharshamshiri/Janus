#!/bin/bash

# Simple test to verify socket creation functionality

echo "=== Testing Socket Creation Functionality ==="
echo ""

# Test Go implementation
echo "1. Testing Go implementation..."
cd GoUnixSockAPI

# Create a simple test program in examples directory
mkdir -p examples
cat > examples/test_server.go << 'EOF'
package main

import (
    "context"
    "fmt"
    "log"
    "time"
    api "github.com/user/GoUnixSockAPI"
)

func main() {
    socketPath := "/tmp/go_socket_test.sock"
    
    // Create simple API spec
    spec := &api.APISpecification{
        Version: "1.0.0",
        Name: "Test API",
        Channels: map[string]*api.ChannelSpec{
            "test": {
                Name: "test",
                Description: "Test channel",
                Commands: map[string]*api.CommandSpec{
                    "ping": {
                        Description: "Ping command",
                        Response: &api.ResponseSpec{Type: "object"},
                    },
                },
            },
        },
    }
    
    // Create client
    client, err := api.NewUnixSockAPIClient(socketPath, "test", spec)
    if err != nil {
        log.Fatalf("Failed to create client: %v", err)
    }
    defer client.Close()
    
    // Register handler - this should trigger server mode
    err = client.RegisterCommandHandler("ping", func(cmd *api.SocketCommand) (*api.SocketResponse, error) {
        return api.NewSuccessResponse(cmd.ID, cmd.ChannelID, map[string]interface{}{"pong": true}), nil
    })
    if err != nil {
        log.Fatalf("Failed to register handler: %v", err)
    }
    
    fmt.Println("Registered handler. Starting listening (should create socket)...")
    
    // Start listening - should create socket since we have handlers
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    err = client.StartListening(ctx)
    if err != nil {
        log.Fatalf("Failed to start listening: %v", err)
    }
    
    // Check if socket was created
    if _, err := os.Stat(socketPath); err == nil {
        fmt.Println("✓ Socket created successfully at:", socketPath)
    } else {
        fmt.Println("✗ Socket was not created")
    }
    
    time.Sleep(2 * time.Second)
    fmt.Println("Test complete")
}
EOF

# Add missing import
sed -i '' 's/"time"/"time"\n    "os"/' examples/test_server.go

go run examples/test_server.go
rm -f examples/test_server.go /tmp/go_socket_test.sock

cd ..
echo ""

# Test Rust implementation
echo "2. Testing Rust implementation..."
cd RustUnixSockAPI

# Create a simple test program
cat > examples/test_socket_creation.rs << 'EOF'
use rust_unix_sock_api::prelude::*;
use std::sync::Arc;
use std::path::Path;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let socket_path = "/tmp/rust_socket_test.sock";
    
    // Remove existing socket
    let _ = std::fs::remove_file(socket_path);
    
    // Create simple API spec
    let mut spec = ApiSpecification::new("1.0.0".to_string());
    let mut channel = ChannelSpec::new("Test channel".to_string());
    channel.commands.insert("ping".to_string(), 
        CommandSpec::new("Ping".to_string(), ResponseSpec::new("object".to_string())));
    spec.add_channel("test".to_string(), channel);
    
    // Create client
    let client = UnixSockApiClient::new(
        socket_path.to_string(),
        "test".to_string(),
        spec,
        UnixSockApiClientConfig::default(),
    ).await?;
    
    // Register handler - this should trigger server mode
    let handler: CommandHandler = Arc::new(|_cmd, _args| {
        Box::pin(async move {
            let mut response = std::collections::HashMap::new();
            response.insert("pong".to_string(), serde_json::Value::Bool(true));
            Ok(Some(response))
        })
    });
    client.register_command_handler("ping", handler).await?;
    
    println!("Registered handler. Starting listening (should create socket)...");
    
    // Start listening - should create socket since we have handlers
    client.start_listening().await?;
    
    // Give it a moment to create the socket
    sleep(Duration::from_millis(500)).await;
    
    // Check if socket was created
    if Path::new(socket_path).exists() {
        println!("✓ Socket created successfully at: {}", socket_path);
    } else {
        println!("✗ Socket was not created");
    }
    
    sleep(Duration::from_secs(2)).await;
    println!("Test complete");
    
    Ok(())
}
EOF

cargo run --example test_socket_creation
rm -f examples/test_socket_creation.rs /tmp/rust_socket_test.sock

cd ..
echo ""

echo "=== Socket Creation Test Complete ==="
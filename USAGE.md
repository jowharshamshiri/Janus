# Janus - Usage Guide

This guide shows how to use the high-level APIs in each implementation to create servers and clients with API specifications (Manifests).

## Overview

Each implementation provides two simple classes:
- **Server**: `JanusServer` - API specification-driven server with command handlers
- **Client**: `JanusClient` - Automatic specification fetching with validation

All implementations use the **Dynamic Specification Architecture** where:
1. Server loads a Manifest (API specification) file defining available commands
2. Client automatically fetches the specification from the server for validation
3. All custom commands are validated against the specification

## API Specification (Manifest)

Before creating servers or clients, you need a Manifest file defining your API. Here's an example:

**my-api-spec.json:**
```json
{
  "name": "My Application API",
  "version": "1.0.0",
  "description": "Example API for demonstration",
  "channels": {
    "default": {
      "commands": {
        "get_user": {
          "description": "Retrieve user information",
          "arguments": {
            "user_id": {
              "type": "string",
              "required": true,
              "description": "User identifier"
            }
          },
          "response": {
            "type": "object",
            "properties": {
              "id": {"type": "string"},
              "name": {"type": "string"},
              "email": {"type": "string"}
            }
          }
        },
        "update_profile": {
          "description": "Update user profile",
          "arguments": {
            "user_id": {"type": "string", "required": true},
            "name": {"type": "string", "required": false},
            "email": {"type": "string", "required": false}
          },
          "response": {
            "type": "object",
            "properties": {
              "success": {"type": "boolean"},
              "updated_fields": {"type": "array"}
            }
          }
        },
        "log_event": {
          "description": "Log application event (fire-and-forget)",
          "arguments": {
            "level": {"type": "string", "required": true},
            "message": {"type": "string", "required": true}
          }
        }
      }
    }
  }
}
```

**Note**: Built-in commands (`ping`, `echo`, `get_info`, `validate`, `slow_process`, `spec`) are always available and cannot be overridden in Manifests.

---

## Rust Implementation

### Server Usage

```rust
use RustJanus::{JanusServer, JSONRPCError, JSONRPCErrorCode};
use serde_json::json;
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load API specification from Manifest file
    let mut server = JanusServer::from_manifest_file("my-api-spec.json").await?;
    
    // Register handlers for commands defined in the Manifest
    server.register_handler("get_user", |cmd| {
        // Extract user_id argument (validated by Manifest)
        let user_id = cmd.args.as_ref()
            .and_then(|args| args.get("user_id"))
            .and_then(|v| v.as_str())
            .ok_or_else(|| JSONRPCError::new(
                JSONRPCErrorCode::InvalidParams, 
                "Missing user_id"
            ))?;
        
        // Simulate user lookup
        Ok(json!({
            "id": user_id,
            "name": "John Doe",
            "email": "john@example.com"
        }))
    }).await;
    
    server.register_handler("update_profile", |cmd| {
        let args = cmd.args.as_ref().ok_or_else(|| 
            JSONRPCError::new(JSONRPCErrorCode::InvalidParams, "No arguments")
        )?;
        
        let user_id = args.get("user_id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| JSONRPCError::new(
                JSONRPCErrorCode::InvalidParams, 
                "Missing user_id"
            ))?;
        
        let mut updated_fields = Vec::new();
        if args.contains_key("name") { updated_fields.push("name"); }
        if args.contains_key("email") { updated_fields.push("email"); }
        
        Ok(json!({
            "success": true,
            "updated_fields": updated_fields
        }))
    }).await;
    
    server.register_handler("log_event", |cmd| {
        // Fire-and-forget logging - no response needed
        let args = cmd.args.as_ref().unwrap();
        let level = args["level"].as_str().unwrap();
        let message = args["message"].as_str().unwrap();
        
        println!("[{}] {}", level, message);
        Ok(json!(null)) // No response for fire-and-forget
    }).await;
    
    // Start listening (blocks until stopped)
    server.start_listening("/tmp/my-server.sock").await?;
    
    Ok(())
}
```

### Client Usage

```rust
use RustJanus::JanusClient;
use std::collections::HashMap;
use std::time::Duration;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create client - specification is fetched automatically from server
    let client = JanusClient::new("/tmp/my-server.sock", "default").await?;
    
    // Built-in commands (always available)
    let response = client.send_command("ping", None).await?;
    if response.success {
        println!("Server ping: {:?}", response.result);
    }
    
    // Custom command defined in Manifest (arguments validated automatically)
    let mut user_args = HashMap::new();
    user_args.insert("user_id".to_string(), json!("user123"));
    
    let response = client.send_command("get_user", Some(user_args)).await?;
    if response.success {
        println!("User data: {:?}", response.result);
    } else {
        println!("Error: {:?}", response.error);
    }
    
    // Update profile command with multiple arguments
    let mut update_args = HashMap::new();
    update_args.insert("user_id".to_string(), json!("user123"));
    update_args.insert("name".to_string(), json!("Jane Doe"));
    update_args.insert("email".to_string(), json!("jane@example.com"));
    
    let response = client.send_command("update_profile", Some(update_args)).await?;
    if response.success {
        println!("Profile updated: {:?}", response.result);
    } else {
        println!("Update failed: {:?}", response.error);
    }
    
    // Fire-and-forget command (no response expected)
    let mut log_args = HashMap::new();
    log_args.insert("level".to_string(), json!("info"));
    log_args.insert("message".to_string(), json!("User profile updated"));
    
    client.send_command_no_response("log_event", Some(log_args)).await?;
    
    // Get server API specification
    let spec_response = client.send_command("spec", None).await?;
    println!("Server API spec: {:?}", spec_response.result);
    
    Ok(())
}
```

---

## Go Implementation

### Server Usage

```go
package main

import (
    "fmt"
    "os"
    "os/signal"
    "syscall"
    
    "github.com/jowharshamshiri/GoJanus/pkg/server"
    "github.com/jowharshamshiri/GoJanus/pkg/models"
    "github.com/jowharshamshiri/GoJanus/pkg/specification"
)

func main() {
    // Load API specification from Manifest file
    manifest, err := specification.ParseManifestFromFile("my-api-spec.json")
    if err != nil {
        fmt.Printf("Failed to load manifest: %v\n", err)
        return
    }
    
    // Create server with configuration
    config := &server.ServerConfig{
        SocketPath:        "/tmp/my-server.sock",
        CleanupOnStart:    true,
        CleanupOnShutdown: true,
    }
    srv := server.NewJanusServer(config)
    
    // Set the server's manifest for validation and spec command
    srv.SetManifest(manifest)
    
    // Register handlers for commands defined in the Manifest
    srv.RegisterHandler("get_user", server.NewObjectHandler(func(cmd *models.JanusCommand) (map[string]interface{}, error) {
        // Extract user_id argument (validated by Manifest)
        userID, exists := cmd.Args["user_id"]
        if !exists {
            return nil, &models.JSONRPCError{
                Code:    models.InvalidParams,
                Message: "Missing user_id argument",
            }
        }
        
        userIDStr, ok := userID.(string)
        if !ok {
            return nil, &models.JSONRPCError{
                Code:    models.InvalidParams,
                Message: "user_id must be a string",
            }
        }
        
        // Simulate user lookup
        return map[string]interface{}{
            "id":    userIDStr,
            "name":  "John Doe",
            "email": "john@example.com",
        }, nil
    }))
    
    srv.RegisterHandler("update_profile", server.NewObjectHandler(func(cmd *models.JanusCommand) (map[string]interface{}, error) {
        if cmd.Args == nil {
            return nil, &models.JSONRPCError{
                Code:    models.InvalidParams,
                Message: "No arguments provided",
            }
        }
        
        userID, exists := cmd.Args["user_id"]
        if !exists {
            return nil, &models.JSONRPCError{
                Code:    models.InvalidParams,
                Message: "Missing user_id argument",
            }
        }
        
        updatedFields := []string{}
        if _, exists := cmd.Args["name"]; exists {
            updatedFields = append(updatedFields, "name")
        }
        if _, exists := cmd.Args["email"]; exists {
            updatedFields = append(updatedFields, "email")
        }
        
        return map[string]interface{}{
            "success":        true,
            "updated_fields": updatedFields,
        }, nil
    }))
    
    srv.RegisterHandler("log_event", server.NewBoolHandler(func(cmd *models.JanusCommand) (bool, error) {
        // Fire-and-forget logging
        level := cmd.Args["level"].(string)
        message := cmd.Args["message"].(string)
        
        fmt.Printf("[%s] %s\n", level, message)
        return true, nil
    }))
    
    // Handle graceful shutdown
    c := make(chan os.Signal, 1)
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)
    
    go func() {
        <-c
        fmt.Println("Shutting down server...")
        srv.Stop()
    }()
    
    // Start listening (blocks until stopped)
    if err := srv.StartListening("/tmp/my-server.sock"); err != nil {
        fmt.Printf("Server error: %v\n", err)
    }
}
```

### Client Usage

```go
package main

import (
    "fmt"
    "time"
    
    "github.com/jowharshamshiri/GoJanus/pkg/protocol"
)

func main() {
    // Create client - specification is fetched automatically from server
    client, err := protocol.NewJanusClient("/tmp/my-server.sock", "default")
    if err != nil {
        fmt.Printf("Failed to create client: %v\n", err)
        return
    }
    
    // Set timeout for commands
    client.SetTimeout(30 * time.Second)
    
    // Built-in commands (always available)
    response, err := client.SendCommand("ping", nil)
    if err != nil {
        fmt.Printf("Ping failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("Server ping: %v\n", response.Result)
    }
    
    // Custom command defined in Manifest (arguments validated automatically)
    userArgs := map[string]interface{}{
        "user_id": "user123",
    }
    
    response, err = client.SendCommand("get_user", userArgs)
    if err != nil {
        fmt.Printf("Get user failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("User data: %v\n", response.Result)
    } else {
        fmt.Printf("Error: %v\n", response.Error)
    }
    
    // Update profile command with multiple arguments
    updateArgs := map[string]interface{}{
        "user_id": "user123",
        "name":    "Jane Doe",
        "email":   "jane@example.com",
    }
    
    response, err = client.SendCommand("update_profile", updateArgs)
    if err != nil {
        fmt.Printf("Update profile failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("Profile updated: %v\n", response.Result)
    } else {
        fmt.Printf("Update failed: %v\n", response.Error)
    }
    
    // Fire-and-forget command (no response expected)
    logArgs := map[string]interface{}{
        "level":   "info",
        "message": "User profile updated",
    }
    
    if err := client.SendCommandNoResponse("log_event", logArgs); err != nil {
        fmt.Printf("Fire-and-forget failed: %v\n", err)
    }
    
    // Get server API specification
    specResponse, err := client.SendCommand("spec", nil)
    if err == nil && specResponse.Success {
        fmt.Printf("Server API spec: %v\n", specResponse.Result)
    }
    
    // Test connectivity
    if client.Ping() {
        fmt.Println("Server is responsive")
    }
}
```

---

## Swift Implementation

### Server Usage

```swift
import Foundation
import SwiftJanus

@available(macOS 10.14, iOS 12.0, *)
@main
struct ServerApp {
    static func main() async throws {
        // Create server
        let server = JanusServer()
        
        // Register command handlers
        server.registerHandler("ping") { cmd in
            return .success([
                "message": "pong",
                "timestamp": Date().timeIntervalSince1970
            ])
        }
        
        server.registerHandler("echo") { cmd in
            guard let args = cmd.args,
                  let message = args["message"] else {
                return .failure(SocketError(
                    code: "MISSING_ARGUMENT",
                    message: "Missing 'message' argument",
                    details: nil
                ))
            }
            
            return .success([
                "echo": message,
                "received_at": Date().timeIntervalSince1970
            ])
        }
        
        // Handle graceful shutdown
        let signalSource = DispatchSource.makeSignalSource(signal: SIGINT, queue: .main)
        signalSource.setEventHandler {
            print("Shutting down server...")
            server.stop()
            exit(0)
        }
        signalSource.resume()
        signal(SIGINT, SIG_IGN)
        
        // Start listening (blocks until stopped)
        try await server.startListening("/tmp/my-server.sock")
    }
}
```

### Client Usage

```swift
import Foundation
import SwiftJanus

@available(macOS 10.14, iOS 12.0, *)
@main
struct ClientApp {
    static func main() async throws {
        // Create client
        let client = JanusClient(channelId: "my-app", timeout: 30.0)
        
        // Simple ping
        let response = try await client.sendCommand("/tmp/my-server.sock", "ping")
        if response.success {
            print("Ping successful: \(response.result?.value ?? "nil")")
        }
        
        // Command with arguments
        let args = ["message": "Hello, Server!"]
        
        let echoResponse = try await client.sendCommand("/tmp/my-server.sock", "echo", args: args)
        if echoResponse.success {
            print("Echo response: \(echoResponse.result?.value ?? "nil")")
        } else {
            print("Error: \(echoResponse.error?.message ?? "Unknown error")")
        }
        
        // Fire-and-forget command
        let logArgs = [
            "level": "info",
            "message": "Background task completed"
        ]
        
        try await client.sendCommandNoResponse("/tmp/my-server.sock", "log", args: logArgs)
        
        // Test connectivity
        if await client.ping("/tmp/my-server.sock") {
            print("Server is responsive")
        }
    }
}
```

---

## Cross-Language Communication

All implementations are fully compatible. You can mix and match:

### Example: Go Server + Rust Client

**Go Server:**
```go
server := &server.JanusServer{}
server.RegisterHandler("process", func(cmd *models.JanusCommand) (interface{}, *models.SocketError) {
    // Process data from any language
    return map[string]interface{}{"processed": true, "language": "go"}, nil
})
server.StartListening("/tmp/mixed-server.sock")
```

**Rust Client:**
```rust
let client = JanusClient::new(Some("rust-client"), Some(Duration::from_secs(10)));
let mut args = HashMap::new();
args.insert("data".to_string(), json!("from rust"));

let response = client.send_command("/tmp/mixed-server.sock", "process", Some(args)).await?;
println!("Go server responded: {:?}", response.result);
```

### Example: Swift Server + Go Client

**Swift Server:**
```swift
let server = JanusServer()
server.registerHandler("analyze") { cmd in
    return .success(["analysis": "complete", "language": "swift"])
}
try await server.startListening("/tmp/swift-server.sock")
```

**Go Client:**
```go
client := &client.JanusClient{}
response, err := client.SendCommand("/tmp/swift-server.sock", "analyze", nil)
fmt.Printf("Swift server responded: %v\n", response.Result)
```

---

## Common Patterns

### 1. Request-Response Pattern
All implementations support request-response by default:

```rust
// Rust
let response = client.send_command(socket, "get_data", args).await?;

// Go  
response, err := client.SendCommand(socket, "get_data", args)

// Swift
let response = try await client.sendCommand(socket, "get_data", args: args)
```

### 2. Fire-and-Forget Pattern
For commands that don't need responses:

```rust
// Rust
client.send_command_no_response(socket, "log_event", args).await?;

// Go
client.SendCommandNoResponse(socket, "log_event", args)

// Swift
try await client.sendCommandNoResponse(socket, "log_event", args: args)
```

### 3. Health Checks
Quick connectivity testing:

```rust
// Rust
if client.ping(socket).await { /* server is up */ }

// Go
if client.Ping(socket) { /* server is up */ }

// Swift  
if await client.ping(socket) { /* server is up */ }
```

### 4. Error Handling
Consistent error handling across languages:

```rust
// Rust
server.register_handler("validate", |cmd| {
    if validate_input(&cmd.args) {
        Ok(json!({"valid": true}))
    } else {
        Err(SocketError {
            code: "VALIDATION_FAILED".to_string(),
            message: "Input validation failed".to_string(),
            details: Some("Check required fields".to_string()),
        })
    }
}).await;
```

```go
// Go
server.RegisterHandler("validate", func(cmd *models.JanusCommand) (interface{}, *models.SocketError) {
    if validateInput(cmd.Args) {
        return map[string]interface{}{"valid": true}, nil
    } else {
        return nil, &models.SocketError{
            Code:    "VALIDATION_FAILED",
            Message: "Input validation failed",
            Details: "Check required fields",
        }
    }
})
```

```swift
// Swift
server.registerHandler("validate") { cmd in
    if validateInput(cmd.args) {
        return .success(["valid": true])
    } else {
        return .failure(SocketError(
            code: "VALIDATION_FAILED",
            message: "Input validation failed",
            details: "Check required fields"
        ))
    }
}
```

---

## Best Practices

1. **Define your API in a Manifest**: Always create a comprehensive API specification file before implementing servers
2. **Use meaningful command names**: `get_user_profile` instead of `cmd1` - and define them in your Manifest
3. **Leverage automatic validation**: Let the Dynamic Specification Architecture validate arguments for you
4. **Handle errors with JSON-RPC codes**: Use standardized JSONRPCError codes for consistent error handling
5. **Test with the `spec` command**: Clients can fetch server API specifications for debugging
6. **Validate Manifest syntax**: Use `janus-docs-cli validate` to check your API specifications
7. **Generate documentation**: Use `janus-docs-cli generate` to create professional API docs
8. **Test cross-language compatibility**: Verify your server works with clients from other languages
9. **Use built-in commands sparingly**: Built-ins (`ping`, `echo`, `get_info`, `validate`, `slow_process`, `spec`) are for testing, not production APIs
10. **Version your APIs**: Include version numbers in your Manifest for API evolution

---

## Quick Start Checklist

### 1. Create API Specification (Manifest):
1. ✅ Create JSON file defining your API commands, arguments, and responses
2. ✅ Validate with `janus-docs-cli validate my-api-spec.json`
3. ✅ Generate documentation with `janus-docs-cli generate my-api-spec.json`

### 2. Server Setup:
1. ✅ Load Manifest file with `ParseManifestFromFile`/`from_manifest_file`/`loadManifest`
2. ✅ Create `JanusServer` instance and set the Manifest
3. ✅ Register command handlers for commands defined in your Manifest
4. ✅ Call `start_listening`/`StartListening`/`startListening` with socket path
5. ✅ Handle graceful shutdown (optional but recommended)

### 3. Client Setup:
1. ✅ Create `JanusClient` instance with socket path and channel ID
2. ✅ Client automatically fetches API specification from server
3. ✅ Call `send_command`/`SendCommand`/`sendCommand` with command name and args
4. ✅ Arguments are automatically validated against the Manifest
5. ✅ Handle response success/error cases
6. ✅ Use built-in `ping` and `spec` commands for testing

### 4. Testing:
1. ✅ Test built-in commands: `ping`, `spec`, `get_info`
2. ✅ Test your custom commands defined in the Manifest
3. ✅ Verify cross-language compatibility (Go ↔ Rust ↔ Swift ↔ TypeScript)
4. ✅ Use `spec` command to debug API specification issues

That's it! Your specification-driven, cross-language Unix socket API is ready.
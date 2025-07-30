# Janus - Usage Guide

This guide shows how to use the high-level APIs in each implementation to create servers and clients with minimal code.

## Overview

Each implementation provides two simple classes:
- **Server**: `JanusServer` - One-line listening with command handlers
- **Client**: `JanusClient` - One-line command sending with automatic response handling

All implementations have identical APIs (adapted for language conventions) and are fully cross-compatible.

---

## Rust Implementation

### Server Usage

```rust
use RustJanus::{JanusServer, SocketError};
use serde_json::json;
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create server
    let mut server = JanusServer::new();
    
    // Register command handlers
    server.register_handler("ping", |_cmd| {
        Ok(json!({"message": "pong", "timestamp": chrono::Utc::now().timestamp()}))
    }).await;
    
    server.register_handler("echo", |cmd| {
        if let Some(args) = &cmd.args {
            if let Some(message) = args.get("message") {
                Ok(json!({"echo": message, "received_at": chrono::Utc::now().timestamp()}))
            } else {
                Err(SocketError {
                    code: "MISSING_ARGUMENT".to_string(),
                    message: "Missing 'message' argument".to_string(),
                    details: None,
                })
            }
        } else {
            Err(SocketError {
                code: "NO_ARGUMENTS".to_string(),
                message: "No arguments provided".to_string(),
                details: None,
            })
        }
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
    // Create client
    let client = JanusClient::new(Some("my-app"), Some(Duration::from_secs(30)));
    
    // Simple ping
    let response = client.send_command("/tmp/my-server.sock", "ping", None).await?;
    if response.success {
        println!("Ping successful: {:?}", response.result);
    }
    
    // Command with arguments
    let mut args = HashMap::new();
    args.insert("message".to_string(), json!("Hello, Server!"));
    
    let response = client.send_command("/tmp/my-server.sock", "echo", Some(args)).await?;
    if response.success {
        println!("Echo response: {:?}", response.result);
    } else {
        println!("Error: {:?}", response.error);
    }
    
    // Fire-and-forget command
    let mut log_args = HashMap::new();
    log_args.insert("level".to_string(), json!("info"));
    log_args.insert("message".to_string(), json!("Background task completed"));
    
    client.send_command_no_response("/tmp/my-server.sock", "log", Some(log_args)).await?;
    
    // Test connectivity
    if client.ping("/tmp/my-server.sock").await {
        println!("Server is responsive");
    }
    
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
    "time"
    "os"
    "os/signal"
    "syscall"
    
    "your-project/pkg/server"
    "your-project/pkg/models"
)

func main() {
    // Create server
    srv := &server.JanusServer{}
    
    // Register command handlers
    srv.RegisterHandler("ping", func(cmd *models.SocketCommand) (interface{}, *models.SocketError) {
        return map[string]interface{}{
            "message":   "pong",
            "timestamp": time.Now().Unix(),
        }, nil
    })
    
    srv.RegisterHandler("echo", func(cmd *models.SocketCommand) (interface{}, *models.SocketError) {
        if cmd.Args == nil {
            return nil, &models.SocketError{
                Code:    "NO_ARGUMENTS",
                Message: "No arguments provided",
                Details: "",
            }
        }
        
        message, exists := cmd.Args["message"]
        if !exists {
            return nil, &models.SocketError{
                Code:    "MISSING_ARGUMENT",
                Message: "Missing 'message' argument",
                Details: "",
            }
        }
        
        return map[string]interface{}{
            "echo":        message,
            "received_at": time.Now().Unix(),
        }, nil
    })
    
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
    
    "your-project/pkg/client"
)

func main() {
    // Create client
    client := &client.JanusClient{}
    client.SetChannelID("my-app")
    client.SetTimeout(30 * time.Second)
    
    // Simple ping
    response, err := client.SendCommand("/tmp/my-server.sock", "ping", nil)
    if err != nil {
        fmt.Printf("Command failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("Ping successful: %v\n", response.Result)
    }
    
    // Command with arguments
    args := map[string]interface{}{
        "message": "Hello, Server!",
    }
    
    response, err = client.SendCommand("/tmp/my-server.sock", "echo", args)
    if err != nil {
        fmt.Printf("Echo failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("Echo response: %v\n", response.Result)
    } else {
        fmt.Printf("Error: %v\n", response.Error)
    }
    
    // Fire-and-forget command
    logArgs := map[string]interface{}{
        "level":   "info",
        "message": "Background task completed",
    }
    
    if err := client.SendCommandNoResponse("/tmp/my-server.sock", "log", logArgs); err != nil {
        fmt.Printf("Fire-and-forget failed: %v\n", err)
    }
    
    // Test connectivity
    if client.Ping("/tmp/my-server.sock") {
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
server.RegisterHandler("process", func(cmd *models.SocketCommand) (interface{}, *models.SocketError) {
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
server.RegisterHandler("validate", func(cmd *models.SocketCommand) (interface{}, *models.SocketError) {
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

1. **Use meaningful command names**: `get_user_profile` instead of `cmd1`
2. **Validate inputs**: Always check arguments in handlers
3. **Handle errors gracefully**: Provide descriptive error messages
4. **Use appropriate timeouts**: Set realistic timeouts for your use case
5. **Clean up resources**: Stop servers gracefully and handle signals
6. **Test cross-language compatibility**: Verify your server works with clients from other languages
7. **Use structured logging**: Log important events for debugging
8. **Implement health checks**: Use ping to monitor server availability

---

## Quick Start Checklist

### Server Setup:
1. ✅ Create `JanusServer` instance
2. ✅ Register command handlers with `registerHandler`/`RegisterHandler`
3. ✅ Call `start_listening`/`StartListening`/`startListening` with socket path
4. ✅ Handle graceful shutdown (optional but recommended)

### Client Setup:
1. ✅ Create `JanusClient` instance with optional channel ID and timeout
2. ✅ Call `send_command`/`SendCommand`/`sendCommand` with socket path, command, and args
3. ✅ Handle response success/error cases
4. ✅ Use `ping` for connectivity testing

That's it! Your cross-language Unix socket communication is ready.
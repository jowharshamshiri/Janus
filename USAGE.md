# Janus - Usage Guide

This guide shows how to use the high-level APIs in each implementation to create servers and clients with API manifests.

## Overview

Each implementation provides two simple classes:
- **Server**: `JanusServer` - API manifest-driven server with request handlers
- **Client**: `JanusClient` - Automatic manifest fetching with validation

All implementations use the **Dynamic Manifest Architecture** where:
1. Server loads a manifest file defining available requests
2. Client automatically fetches the manifest from the server for validation
3. All custom requests are validated against the manifest

## API Manifest

Before creating servers or clients, you need a manifest file defining your API. Here's an example:

**my-api-manifest.json:**
```json
{
  "name": "My Application API",
  "version": "1.0.0",
  "description": "Example API for demonstration",
  "models": {
    "GetUserRequest": {
      "type": "object",
      "properties": {
        "user_id": {
          "type": "string",
          "description": "User identifier"
        }
      },
      "required": ["user_id"]
    },
    "GetUserResponse": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "email": {"type": "string"}
      }
    },
    "UpdateProfileRequest": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "name": {"type": "string"},
        "email": {"type": "string"}
      },
      "required": ["user_id"]
    }
  }
}
```

**Note**: Built-in requests (`ping`, `echo`, `get_info`, `validate`, `slow_process`, `manifest`) are always available and cannot be overridden in manifests.

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
    
    "GoJanus/pkg/server"
    "GoJanus/pkg/models"
    "GoJanus/pkg/manifest"
)

func main() {
    // Load API manifest from file (optional)
    manifestData, err := manifest.ParseManifestFromFile("my-api-manifest.json")
    if err != nil {
        fmt.Printf("Failed to load manifest: %v\n", err)
        return
    }
    
    // Create server with configuration
    config := &server.ServerConfig{
        SocketPath: "/tmp/my-server.sock",
    }
    srv := server.NewJanusServer(config)
    
    // Set the server's manifest for validation and manifest request
    srv.SetManifest(manifestData)
    
    // Register handlers for custom requests defined in the manifest
    srv.RegisterHandler("get_user", server.NewObjectHandler(func(cmd *models.JanusRequest) (map[string]interface{}, error) {
        // Extract user_id argument (validated by manifest)
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
    
    // Handle graceful shutdown
    c := make(chan os.Signal, 1)
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)
    
    go func() {
        <-c
        fmt.Println("Shutting down server...")
        srv.Stop()
    }()
    
    // Start listening (blocks until stopped)
    if err := srv.StartListening(); err != nil {
        fmt.Printf("Server error: %v\n", err)
    }
}
```

### Client Usage

```go
package main

import (
    "context"
    "fmt"
    
    "GoJanus/pkg/protocol"
)

func main() {
    // Create client - manifest is fetched automatically from server
    client, err := protocol.New("/tmp/my-server.sock")
    if err != nil {
        fmt.Printf("Failed to create client: %v\n", err)
        return
    }
    
    ctx := context.Background()
    
    // Built-in requests (always available)
    response, err := client.SendRequest(ctx, "ping", nil)
    if err != nil {
        fmt.Printf("Ping failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("Server ping: %v\n", response.Result)
    }
    
    // Custom request defined in manifest (arguments validated automatically)
    userArgs := map[string]interface{}{
        "user_id": "user123",
    }
    
    response, err = client.SendRequest(ctx, "get_user", userArgs)
    if err != nil {
        fmt.Printf("Get user failed: %v\n", err)
        return
    }
    
    if response.Success {
        fmt.Printf("User data: %v\n", response.Result)
    } else {
        fmt.Printf("Error: %v\n", response.Error)
    }
    
    // Get server API manifest
    manifestResponse, err := client.SendRequest(ctx, "manifest", nil)
    if err == nil && manifestResponse.Success {
        fmt.Printf("Server API manifest: %v\n", manifestResponse.Result)
    }
}
```

---

## Rust Implementation

### Server Usage

```rust
use std::collections::HashMap;
use serde_json::{json, Value};
use rust_janus::server::janus_server::{JanusServer, ServerConfig};
use rust_janus::protocol::message_types::{JanusRequest, JSONRPCError};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create server with configuration
    let config = ServerConfig {
        socket_path: "/tmp/my-server.sock".to_string(),
        max_connections: 100,
        default_timeout: 30,
        max_message_size: 65536,
        cleanup_on_start: true,
        cleanup_on_shutdown: true,
    };
    
    let mut server = JanusServer::new(config);
    
    // Register handlers for custom requests defined in the manifest
    server.register_handler("get_user", |request: &JanusRequest| -> Result<Value, JSONRPCError> {
        // Extract user_id argument (validated by manifest)
        let user_id = request.args.as_ref()
            .and_then(|args| args.get("user_id"))
            .and_then(|v| v.as_str())
            .ok_or_else(|| JSONRPCError {
                code: -32602,
                message: "Missing user_id argument".to_string(),
                data: None,
            })?;
        
        // Simulate user lookup
        Ok(json!({
            "id": user_id,
            "name": "John Doe",
            "email": "john@example.com"
        }))
    });
    
    // Start listening (blocks until stopped)
    server.start_listening().await?;
    
    Ok(())
}
```

### Client Usage

```rust
use std::collections::HashMap;
use serde_json::json;
use rust_janus::protocol::janus_client::JanusClient;
use rust_janus::config::JanusClientConfig;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create client - manifest is fetched automatically from server
    let config = JanusClientConfig::default();
    let mut client = JanusClient::new("/tmp/my-server.sock".to_string(), config).await?;
    
    // Built-in requests (always available) 
    let response = client.send_request("ping", None, None).await?;
    if response.success {
        println!("Server ping: {:?}", response.result);
    }
    
    // Custom request defined in manifest (arguments validated automatically)
    let mut user_args = HashMap::new();
    user_args.insert("user_id".to_string(), json!("user123"));
    
    let response = client.send_request("get_user", Some(user_args), None).await?;
    if response.success {
        println!("User data: {:?}", response.result);
    } else {
        println!("Error: {:?}", response.error);
    }
    
    // Get server API manifest
    let manifest_response = client.send_request("manifest", None, None).await?;
    println!("Server API manifest: {:?}", manifest_response.result);
    
    Ok(())
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
        
        // Register handlers for custom requests defined in the manifest
        server.registerHandler("get_user") { request in
            guard let args = request.args,
                  let userId = args["user_id"] as? String else {
                return .failure(JSONRPCError(
                    code: JSONRPCErrorCode.invalidParams,
                    message: "Missing user_id argument"
                ))
            }
            
            // Simulate user lookup
            return .success([
                "id": userId,
                "name": "John Doe",
                "email": "john@example.com"
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
        // Create client - manifest is fetched automatically from server
        let client = try await JanusClient(socketPath: "/tmp/my-server.sock")
        
        // Built-in requests (always available)
        let response = try await client.sendRequest("ping")
        if response.success {
            print("Server ping: \(response.result?.value ?? "nil")")
        }
        
        // Custom request defined in manifest (arguments validated automatically)
        let userArgs: [String: AnyCodable] = [
            "user_id": AnyCodable("user123")
        ]
        
        let userResponse = try await client.sendRequest("get_user", args: userArgs)
        if userResponse.success {
            print("User data: \(userResponse.result?.value ?? "nil")")
        } else {
            print("Error: \(userResponse.error?.message ?? "Unknown error")")
        }
        
        // Get server API manifest
        let manifestResponse = try await client.sendRequest("manifest")
        print("Server API manifest: \(manifestResponse.result?.value ?? "nil")")
    }
}
```

---

## TypeScript Implementation

### Server Usage

```typescript
import { JanusServer, JSONRPCError } from 'typescript-janus';

async function main() {
  // Create server
  const server = new JanusServer({ socketPath: '/tmp/my-server.sock' });
  
  // Register handlers for custom requests defined in the manifest
  server.registerRequestHandler('get_user', async (request) => {
    if (!request.args?.user_id) {
      throw new JSONRPCError(-32602, 'Missing user_id argument');
    }
    
    // Simulate user lookup
    return {
      id: request.args.user_id,
      name: 'John Doe',
      email: 'john@example.com'
    };
  });
  
  // Start listening (blocks until stopped)
  await server.listen();
  console.log('Server listening on /tmp/my-server.sock...');
}

main().catch(console.error);
```

### Client Usage

```typescript
import { JanusClient, JanusClientConfig } from 'typescript-janus';

async function main() {
  // Create client - manifest is fetched automatically from server
  const config: JanusClientConfig = {
    socketPath: '/tmp/my-server.sock'
  };
  const client = await JanusClient.create(config);

  // Built-in requests (always available)
  const response = await client.sendRequest('ping');
  if (response.success) {
    console.log('Server ping:', response.result);
  }

  // Custom request defined in manifest (arguments validated automatically)
  const userArgs = {
    user_id: 'user123'
  };

  const userResponse = await client.sendRequest('get_user', userArgs);
  if (userResponse.success) {
    console.log('User data:', userResponse.result);
  } else {
    console.log('Error:', userResponse.error);
  }
  
  // Get server API manifest
  const manifestResponse = await client.sendRequest('manifest');
  console.log('Server API manifest:', manifestResponse.result);
}

main().catch(console.error);
```

---

## Cross-Language Communication

All implementations are fully compatible. You can mix and match:

- **Go server** ↔ **Rust client**
- **Swift server** ↔ **TypeScript client**  
- **TypeScript server** ↔ **Go client**
- Any combination works seamlessly

---

## Best Practices

1. **Define your API in a manifest**: Create a comprehensive API manifest file before implementing servers
2. **Use meaningful request names**: `get_user_profile` instead of `cmd1`
3. **Leverage automatic validation**: Let the Dynamic Manifest Architecture validate arguments
4. **Handle errors with JSON-RPC codes**: Use standardized JSONRPCError codes
5. **Test with the `manifest` request**: Clients can fetch server API manifests for debugging
6. **Test cross-language compatibility**: Verify your server works with clients from other languages
7. **Version your APIs**: Include version numbers in your manifest for API evolution

---

## Quick Start Checklist

### 1. Create API Manifest:
- ✅ Create JSON file defining your API models and data structures
- ✅ Validate JSON syntax

### 2. Server Setup:
- ✅ Create `JanusServer` instance 
- ✅ Register request handlers for custom requests
- ✅ Call `start_listening`/`StartListening`/`startListening` with socket path
- ✅ Handle graceful shutdown (recommended)

### 3. Client Setup:
- ✅ Create `JanusClient` instance with socket path
- ✅ Client automatically fetches API manifest from server
- ✅ Call `send_request`/`SendRequest`/`sendRequest` with request name and args
- ✅ Handle response success/error cases

### 4. Testing:
- ✅ Test built-in requests: `ping`, `manifest`, `get_info`  
- ✅ Test your custom requests
- ✅ Verify cross-language compatibility
- ✅ Use `manifest` request to debug API issues

That's it! Your manifest-driven, cross-language Unix socket API is ready.
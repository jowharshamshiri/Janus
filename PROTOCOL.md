# Janus Protocol Specification

**Version**: 2.0.0  
**Status**: Production Ready  
**Socket Type**: SOCK_DGRAM (Connectionless Datagram)
**Compatibility**: Go, Rust, Swift, TypeScript implementations  
**Date**: 2025-07-29  

## Overview

The Janus Protocol provides a standardized approach to inter-process communication using **connectionless Unix domain datagram sockets (SOCK_DGRAM)** with JSON-based messaging, comprehensive security validation, and stateless communication patterns. This specification ensures compatibility across multiple programming language implementations while maintaining the simplicity and efficiency of connectionless communication.

## Table of Contents

1. [Message Format](#message-format)
2. [Communication Patterns](#communication-patterns)
3. [Security Framework](#security-framework)
4. [Connection Management](#connection-management)
5. [Manifest Format](#manifest-format)
6. [Error Handling](#error-handling)
7. [Timeout Management](#timeout-management)
8. [Cross-Language Compatibility](#cross-language-compatibility)
9. [Implementation Guidelines](#implementation-guidelines)

## Message Format

### Wire Protocol

All messages use **direct JSON payload** without length prefixes (connectionless datagram communication):

```
[JSON message payload]
```

#### Datagram Format
- **Transport**: UDP-style connectionless datagrams over Unix domain sockets
- **Framing**: Each datagram contains exactly one complete JSON message
- **Size Limit**: Maximum datagram size enforced by OS (typically 64KB for Unix domain sockets)
- **Boundary Detection**: Automatic per-datagram boundaries (no manual framing required)

### Core Message Types

#### SocketCommand (Client → Server)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "channelId": "user-service", 
  "command": "create-user",
  "reply_to": "/tmp/client_response_123456.sock",
  "args": {
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user"
  },
  "timeout": 30.0,
  "timestamp": 1722249000.123
}
```

**Field Specifications**:
- `id` (required): UUID v4 string for response correlation
- `channelId` (required): Channel routing identifier (1-256 chars, alphanumeric + `-_`)
- `command` (required): Command name (1-256 chars, alphanumeric + `-_`)
- `args` (optional): Command arguments object (max 5MB)
- `timeout` (optional): Timeout in seconds (0.1-300.0, default: 30.0)
- `timestamp` (required): Unix timestamp (seconds since epoch) as f64 with microsecond precision

#### SocketResponse (Server → Client)

```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "channelId": "user-service",
  "success": true,
  "result": {
    "userId": "12345",
    "status": "created",
    "message": "User created successfully"
  },
  "timestamp": 1722249001.234
}
```

**Success Response Fields**:
- `commandId` (required): UUID from original command
- `channelId` (required): Channel verification
- `success` (required): `true` for successful operations
- `result` (optional): Response data object
- `timestamp` (required): Response generation Unix timestamp (f64 seconds since epoch)

**Error Response Example**:
```json
{
  "commandId": "550e8400-e29b-41d4-a716-446655440000",
  "channelId": "user-service",
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Username contains invalid characters",
    "details": "Username must contain only alphanumeric characters and underscores"
  },
  "timestamp": 1722249001.234
}
```

#### Message Envelope (Wire Format)

For implementations requiring type discrimination:

```json
{
  "type": "command",
  "payload": "eyJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsImNoYW5uZWxJZCI6InVzZXItc2VydmljZSIsImNvbW1hbmQiOiJjcmVhdGUtdXNlciIsImFyZ3MiOnsidXNlcm5hbWUiOiJqb2huX2RvZSIsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIn0sInRpbWVvdXQiOjMwLjAsInRpbWVzdGFtcCI6IjIwMjUtMDctMjlUMTA6NTA6MDAuMDAwWiJ9"
}
```

- `type`: `"command"` or `"response"`
- `payload`: Base64-encoded JSON of actual message

## Communication Patterns

### Connectionless Request-Response Model

The protocol uses **connectionless request-response** with **UUID correlation** for stateless communication:

#### Client Flow
1. **Generate Command**: Create UUID and timestamp
2. **Send Datagram**: Transmit single datagram with complete command
3. **Listen for Response**: Bind to response socket and wait for reply datagram
4. **Response Correlation**: Match responses via UUID
5. **Socket Cleanup**: Close socket after receiving response or timeout

#### Server Flow  
1. **Bind Server Socket**: Listen on server socket path for incoming datagrams
2. **Receive Datagrams**: Process each complete command datagram independently
3. **Validate Security**: Apply comprehensive security framework per message
4. **Execute Handler**: Process command with timeout enforcement
5. **Send Response Datagram**: Send reply to client's response socket path

### Connectionless Lifecycle

#### Stateless Datagram Model
- **No Persistent Connections**: Each request-response is independent
- **Client Response Socket**: Client creates temporary socket for responses
- **Server Socket Binding**: Server maintains single bound socket for all clients
- **Automatic Cleanup**: OS handles socket cleanup automatically

```
Client                          Server
  |                               |
  |-- Create Response Socket -----|
  |    (Bind to temp path)        |
  |                               |
  |-- Send Command Datagram ----->|
  |    (UUID: abc123, reply_to)   |-- Receive & Validate
  |                               |-- Execute Handler
  |<-- Response Datagram ---------|
  |    (commandId: abc123)        |
  |                               |
  |-- Close Response Socket ------|
  |                               |
  |-- Create New Response Socket--|
  |-- Send Command Datagram ----->|
  |    (UUID: def456, reply_to)   |-- Execute Handler
  |<-- Response Datagram ---------|
  |    (commandId: def456)        |
  |-- Close Response Socket ------|
```

### Message Correlation System

#### UUID-Based Tracking
- **Command Generation**: UUID v4 for each command
- **Response Socket**: Temporary socket path for receiving replies
- **Reply-To Mechanism**: Server sends response to client's reply_to socket
- **Timeout Cleanup**: Client socket timeout for unresponsive servers

#### Implementation Pattern
```typescript
// Pseudo-code for connectionless correlation system
class JanusClient {
  async sendCommand(command: SocketCommand): Promise<SocketResponse> {
    // Create temporary response socket
    const responseSocket = `/tmp/client_response_${Date.now()}_${Math.random()}.sock`;
    const socket = dgram.createSocket('unix_dgram');
    socket.bind(responseSocket);
    
    // Add reply_to field
    command.reply_to = responseSocket;
    
    // Send command datagram
    await this.sendDatagram(JSON.stringify(command), serverSocketPath);
    
    // Wait for response with timeout
    const response = await this.waitForResponse(socket, command.timeout);
    
    // Cleanup
    socket.close();
    fs.unlinkSync(responseSocket);
    
    return response;
  }
  
  handleResponse(socket: Socket): Promise<SocketResponse> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Response timeout'));
      }, this.timeout);
      
      socket.once('message', (data) => {
        clearTimeout(timeout);
        resolve(JSON.parse(data.toString()));
      });
    });
  }
}
```

## Security Framework

### Comprehensive Validation (25+ Security Mechanisms)

#### Socket Path Security
```typescript
interface SocketPathValidation {
  maxLength: 108;              // Unix socket limit
  allowedDirectories: ["/tmp/", "/var/run/", "/var/tmp/"];
  preventPathTraversal: true;  // Block "../" sequences
  preventNullBytes: true;      // Block "\x00" characters
  characterWhitelist: /^[a-zA-Z0-9\/_.-]+$/;
}
```

#### Channel/Command Name Security
```typescript
interface NameValidation {
  maxLength: 256;              // Configurable
  pattern: /^[a-zA-Z0-9_-]+$/; // Alphanumeric + underscore + hyphen
  utf8Validation: true;        // Ensure valid encoding
  nonEmpty: true;              // Reject empty strings
}
```

#### Message Content Security
```typescript
interface MessageSecurity {
  maxArgsSize: 5 * 1024 * 1024;      // 5MB args data limit
  maxTotalSize: 10 * 1024 * 1024;    // 10MB total message limit
  nullByteDetection: true;           // Scan entire payload
  utf8Validation: true;              // Complete encoding verification
  jsonStructureValidation: true;     // Balanced braces, proper format
}
```

#### Resource Limits
```typescript
interface ResourceLimits {
  maxConnections: 100;         // Concurrent connections
  maxHandlers: 500;           // Command handlers
  maxPendingCommands: 1000;   // Awaiting responses
  minTimeout: 0.1;            // Seconds
  maxTimeout: 300.0;          // 5 minutes
}
```

### Security Error Codes

| Code | Description | Prevention |
|------|-------------|------------|
| `SECURITY_VIOLATION` | General security validation failure | Input sanitization |
| `PATH_TRAVERSAL_ATTEMPT` | Detected "../" in socket path | Path validation |
| `INVALID_SOCKET_PATH` | Socket path fails validation | Character whitelist |
| `RESOURCE_LIMIT_EXCEEDED` | Resource usage over limits | Connection/memory limits |
| `CHANNEL_ISOLATION_VIOLATION` | Cross-channel access attempt | Channel verification |
| `MESSAGE_TOO_LARGE` | Message exceeds size limits | Size validation |
| `INVALID_CHARACTER_ENCODING` | Non-UTF8 or null bytes | Encoding validation |

## Connection Management

### Connection Pool Architecture

```typescript
interface ConnectionPool {
  maxSize: number;              // Maximum pool size
  availableConnections: Connection[];
  activeConnections: Map<string, Connection>;
  
  getConnection(channelId: string): Promise<Connection>;
  releaseConnection(connection: Connection): void;
  healthCheck(): Promise<boolean>;
  cleanup(): void;
}
```

### Socket States

1. **UNBOUND**: No socket created
2. **BINDING**: Creating and binding response socket
3. **BOUND**: Socket ready to receive datagrams
4. **SENDING**: Transmitting command datagram
5. **WAITING**: Listening for response datagram
6. **CLEANUP**: Closing socket and removing file
7. **CLOSED**: Socket resources deallocated

### Error Recovery Strategy

```typescript
interface DatagramConfig {
  maxRetries: 3;
  initialTimeout: 5000;        // ms per attempt
  backoffMultiplier: 1.5;
  maxTimeout: 15000;           // ms
  socketCleanupDelay: 100;     // ms before cleanup
}
```

## Manifest Format

### JSON Schema Structure

```json
{
  "version": "1.0.0",
  "name": "User Management API",
  "description": "Comprehensive user management operations",
  "channels": {
    "user-service": {
      "name": "User Service",
      "description": "Core user management operations",
      "commands": {
        "create-user": {
          "name": "Create User",
          "description": "Create a new user account",
          "args": {
            "username": {
              "name": "Username", 
              "type": "string",
              "description": "Unique username for the account",
              "required": true,
              "pattern": "^[a-zA-Z0-9_]{3,50}$",
              "minLength": 3,
              "maxLength": 50
            },
            "email": {
              "name": "Email Address",
              "type": "string", 
              "description": "User's email address",
              "required": true,
              "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
            },
            "role": {
              "name": "User Role",
              "type": "string",
              "description": "User's system role",
              "required": false,
              "default": "user",
              "enum": ["admin", "moderator", "user", "guest"]
            },
            "profile": {
              "name": "User Profile",
              "type": "object",
              "description": "Extended user profile information",
              "required": false,
              "modelRef": "UserProfile"
            }
          },
          "response": {
            "type": "object",
            "description": "User creation result",
            "properties": {
              "userId": {
                "type": "string",
                "description": "Generated user ID"
              },
              "status": {
                "type": "string", 
                "description": "Creation status"
              },
              "message": {
                "type": "string",
                "description": "Status message"
              }
            },
            "required": ["userId", "status"],
            "modelRef": "CreateUserResponse"
          },
          "errorCodes": [
            "VALIDATION_FAILED",
            "USERNAME_EXISTS", 
            "EMAIL_EXISTS",
            "SECURITY_VIOLATION"
          ]
        }
      }
    }
  },
  "models": {
    "UserProfile": {
      "name": "User Profile",
      "type": "object",
      "description": "Extended user profile information",
      "properties": {
        "firstName": {
          "type": "string",
          "description": "User's first name",
          "maxLength": 100
        },
        "lastName": {
          "type": "string", 
          "description": "User's last name",
          "maxLength": 100
        },
        "age": {
          "type": "integer",
          "description": "User's age",
          "minimum": 13,
          "maximum": 120
        },
        "preferences": {
          "type": "object",
          "description": "User preferences",
          "properties": {}
        }
      },
      "required": []
    },
    "CreateUserResponse": {
      "name": "Create User Response",
      "type": "object", 
      "description": "Response from user creation operation",
      "properties": {
        "userId": {
          "type": "string",
          "description": "Unique identifier for the created user"
        },
        "status": {
          "type": "string",
          "description": "Operation status",
          "enum": ["created", "pending", "failed"]
        },
        "message": {
          "type": "string",
          "description": "Human-readable status message"
        },
        "createdAt": {
          "type": "string",
          "description": "ISO 8601 timestamp of creation"
        }
      },
      "required": ["userId", "status", "message"]
    }
  }
}
```

### Specification Validation Rules

- **Version**: Semantic versioning (major.minor.patch)
- **Channels**: Must have at least one channel
- **Commands**: Must have unique names within channel
- **Arguments**: Type validation with comprehensive constraints
- **Models**: Reusable type definitions with inheritance support
- **Error Codes**: Predefined set of error conditions

## Error Handling

### Error Categories and Codes

#### Validation Errors
- `VALIDATION_FAILED`: General validation failure
- `MISSING_REQUIRED_ARGUMENT`: Required parameter missing
- `INVALID_ARGUMENT`: Type or format validation failure
- `ARGUMENT_OUT_OF_RANGE`: Numeric value outside bounds
- `INVALID_ENUM_VALUE`: Value not in allowed enumeration

#### Security Errors  
- `SECURITY_VIOLATION`: Security validation failure
- `PATH_TRAVERSAL_ATTEMPT`: Directory traversal detected
- `RESOURCE_LIMIT_EXCEEDED`: Resource usage over limits
- `CHANNEL_ISOLATION_VIOLATION`: Cross-channel access attempt
- `AUTHENTICATION_FAILED`: Channel authentication failure

#### Communication Errors
- `CONNECTION_ERROR`: Socket communication failure
- `ENCODING_FAILED`: JSON serialization error
- `DECODING_FAILED`: JSON deserialization error
- `MESSAGE_TOO_LARGE`: Size limit exceeded
- `PROTOCOL_VIOLATION`: Protocol format violation

#### Runtime Errors
- `COMMAND_TIMEOUT`: Command execution timeout
- `HANDLER_TIMEOUT`: Handler processing timeout
- `HANDLER_NOT_FOUND`: No handler for command
- `INTERNAL_ERROR`: Unexpected system error
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable

### Error Response Format

```json
{
  "commandId": "uuid-from-request",
  "channelId": "channel-name", 
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Username contains invalid characters",
    "details": "Username must contain only alphanumeric characters and underscores",
    "field": "username",
    "value": "invalid-value",
    "constraints": {
      "pattern": "^[a-zA-Z0-9_]+$",
      "minLength": 3,
      "maxLength": 50
    }
  },
  "timestamp": 1722249001.234
}
```

## Timeout Management

### Bilateral Timeout System

#### Command Timeout (Client-Side)
- **Purpose**: Prevent client from waiting indefinitely
- **Default**: 30.0 seconds
- **Range**: 0.1 - 300.0 seconds
- **Behavior**: Client cancels operation after timeout

#### Handler Timeout (Server-Side)  
- **Purpose**: Prevent server resource exhaustion
- **Default**: 30.0 seconds
- **Range**: 0.1 - 300.0 seconds  
- **Behavior**: Server terminates handler after timeout

#### Connection Timeout
- **Purpose**: Limit connection establishment time
- **Default**: 10.0 seconds
- **Behavior**: Fail connection if not established in time

### Timeout Profiles

```typescript
interface TimeoutProfiles {
  standard: {
    command: 30.0,
    handler: 30.0,
    connection: 10.0
  },
  aggressive: {
    command: 5.0,
    handler: 5.0, 
    connection: 3.0
  },
  relaxed: {
    command: 120.0,
    handler: 120.0,
    connection: 30.0
  }
}
```

### Timeout Error Handling

```json
{
  "commandId": "uuid-from-request",
  "channelId": "channel-name",
  "success": false,
  "error": {
    "code": "COMMAND_TIMEOUT",
    "message": "Command execution exceeded timeout limit",
    "details": "Operation timed out after 30.0 seconds",
    "timeout": 30.0,
    "elapsed": 30.1
  },
  "timestamp": "2025-07-29T10:50:31.234Z"
}
```

## Cross-Language Compatibility

### Wire Format Compatibility

All implementations must produce **byte-for-byte identical** wire format:

1. **4-byte big-endian length prefix** 
2. **UTF-8 encoded JSON payload**
3. **Consistent field ordering** (for deterministic serialization)
4. **Unix timestamps (f64)** with millisecond precision
5. **UUID v4 format** for command correlation

### Language-Specific Considerations

#### Go Implementation
- Use `encoding/json` with consistent field tags
- `binary.BigEndian` for length prefix
- `time.RFC3339Nano` for timestamps
- `google/uuid` for UUID generation

#### Rust Implementation  
- Use `serde_json` with `preserve_order` feature
- `byteorder::BigEndian` for length prefix
- `chrono::DateTime<Utc>` for timestamps
- `uuid::Uuid::new_v4()` for UUID generation

#### Swift Implementation
- Use `JSONEncoder` with sorted keys
- `CFByteOrder` functions for length prefix
- `Unix timestamp (f64)` for timestamps
- `UUID()` for UUID generation

#### TypeScript Implementation (Future)
- Use `JSON.stringify` with replacer for ordering
- `Buffer` with `writeUInt32BE` for length prefix
- `Date.now() / 1000` for timestamps
- `crypto.randomUUID()` for UUID generation

### Validation Consistency

All implementations must enforce **identical validation rules**:

- Same maximum lengths and size limits
- Identical regular expression patterns
- Consistent error codes and messages
- Uniform timeout handling
- Compatible security mechanisms

### Test Compatibility Matrix

```
        Go    Rust  Swift TypeScript
Go      ✓     ✓     ✓     ✓
Rust    ✓     ✓     ✓     ✓  
Swift   ✓     ✓     ✓     ✓
TypeScript ✓  ✓     ✓     ✓
```

Each implementation must successfully communicate with every other implementation as both client and server.

## Implementation Guidelines

### Required Components

#### Core Components
1. **Message Framing**: 4-byte length prefix handling
2. **JSON Serialization**: Consistent field ordering
3. **Security Validator**: All 25+ validation mechanisms
4. **Connection Manager**: Pool and lifecycle management
5. **Response Tracker**: UUID correlation system
6. **Timeout Manager**: Bilateral timeout enforcement
7. **Error Handler**: Comprehensive error categorization

#### Manifest Engine
1. **Specification Parser**: JSON schema validation
2. **Type Validator**: Runtime type checking
3. **Model Registry**: Reusable type definitions
4. **Command Registry**: Dynamic command discovery
5. **Documentation Generator**: API documentation export

### Performance Requirements

#### Latency Targets
- **Local Unix Socket**: < 1ms response time
- **Message Serialization**: < 0.1ms for typical messages
- **Security Validation**: < 0.01ms per validation rule
- **Connection Establishment**: < 10ms

#### Throughput Targets
- **Concurrent Connections**: 100+ simultaneous
- **Messages Per Second**: 1000+ per connection
- **Memory Usage**: < 10MB base + 1KB per connection
- **CPU Usage**: < 5% per 1000 messages/second

#### Resource Limits
- **Memory**: Configurable limits with leak prevention
- **File Descriptors**: Proper cleanup and pooling
- **Network Buffers**: Size limits and overflow protection
- **Thread/Task Pools**: Bounded concurrency

### Testing Requirements

#### Unit Tests
- Message serialization/deserialization
- Security validation (all 25+ mechanisms)
- Timeout handling and cleanup
- Error code generation
- Connection lifecycle management

#### Integration Tests
- Cross-language client-server communication
- Manifest parsing and validation  
- Performance benchmarking
- Resource limit enforcement
- Security vulnerability testing

#### Cross-Platform Tests
- All implementation pairs (N×N matrix)
- Consistent message format validation
- Compatible error handling
- Uniform timeout behavior
- Identical security enforcement

### Documentation Requirements

#### API Documentation
- Complete command reference
- Type definitions and constraints
- Error codes and handling
- Examples and usage patterns
- Performance characteristics

#### Implementation Guide
- Language-specific setup instructions
- Configuration options
- Best practices and patterns
- Troubleshooting guide
- Security considerations

---

## Appendix

### Reference Implementations

- **Go**: `/Users/bahram/ws/prj/Janus/GoJanus/`
- **Rust**: `/Users/bahram/ws/prj/Janus/RustJanus/`  
- **Swift**: `/Users/bahram/ws/prj/Janus/SwiftJanus/`

### Protocol Version History

- **v1.0.0** (2025-07-29): Initial specification with async communication patterns

### Contributing

This specification is maintained as part of the Janus project. Changes must maintain backward compatibility and cross-language consistency.
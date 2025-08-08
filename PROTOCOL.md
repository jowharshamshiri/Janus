# Janus Protocol Manifest

**Version**: 2.0.0  
**Status**: Production Ready  
**Socket Type**: SOCK_DGRAM (Connectionless Datagram)
**Compatibility**: Go, Rust, Swift, TypeScript implementations  
**Date**: 2025-07-29  

## Overview

The Janus Protocol provides a standardized approach to inter-process communication using **connectionless Unix domain datagram sockets (SOCK_DGRAM)** with JSON-based messaging, comprehensive security validation, and stateless communication patterns. This manifest ensures compatibility across multiple programming language implementations while maintaining the simplicity and efficiency of connectionless communication.

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

#### JanusRequest (Client → Server)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "create-user",
  "channelId": "user-service", 
  "request": "create-user",
  "reply_to": "/tmp/client_response_123456.sock",
  "args": {
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user"
  },
  "timeout": 30.0,
  "timestamp": "2025-08-06T12:34:56.789Z"
}
```

**Field Manifests**:
- `id` (required): UUID v4 string for unique request identification
- `method` (required): Method name being invoked (1-256 chars, alphanumeric + `-_`)
- `channelId` (required): Channel routing identifier (1-256 chars, alphanumeric + `-_`)
- `request` (required): Request name (1-256 chars, alphanumeric + `-_`)
- `reply_to` (required): Response socket path for reply correlation
- `args` (optional): Request arguments object (max 5MB)
- `timeout` (optional): Timeout in seconds (0.1-300.0, default: 30.0)
- `timestamp` (required): RFC 3339 timestamp with milliseconds (YYYY-MM-DDTHH:MM:SS.sssZ)

#### JanusResponse (Server → Client) - PRIME DIRECTIVE

```json
{
  "result": {
    "userId": "12345",
    "status": "created", 
    "message": "User created successfully"
  },
  "error": null,
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "id": "998e7654-f21c-32a8-b827-556677889900",
  "timestamp": "2025-08-06T12:34:56.789Z"
}
```

**CRITICAL PROTOCOL MANIFEST:**
- **`result`**: The actual unwrapped response data (not wrapped in additional objects)
- **`error`**: JSONRPCError object if error occurred, `null` if success
- **`success`**: Boolean indicator - `true` for success, `false` for error  
- **`request_id`**: The exact ID from the original request being responded to
- **`id`**: Unique identifier for this manifestific response message
- **`timestamp`**: RFC 3339 timestamp with milliseconds (YYYY-MM-DDTHH:MM:SS.sssZ)

**Response Fields Manifest**:
- `result` (required): Actual response data, unwrapped
- `error` (required): JSONRPCError object or null  
- `success` (required): Boolean success indicator
- `request_id` (required): UUID from original request
- `id` (required): Unique response identifier
- `timestamp` (required): RFC 3339 with milliseconds

**Error Response Example**:
```json
{
  "result": null,
  "error": {
    "code": -32602,
    "message": "Invalid parameters",
    "data": {
      "details": "Missing required field: email"
    }
  },
  "success": false,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "id": "887e6543-d10b-21a7-a716-445566778899",
  "timestamp": "2025-08-06T12:34:56.789Z"
}
```

#### Message Envelope (Wire Format)

For implementations requiring type discrimination:

```json
{
  "type": "request",
  "payload": "eyJpZCI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsImNoYW5uZWxJZCI6InVzZXItc2VydmljZSIsImNvbW1hbmQiOiJjcmVhdGUtdXNlciIsImFyZ3MiOnsidXNlcm5hbWUiOiJqb2huX2RvZSIsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIn0sInRpbWVvdXQiOjMwLjAsInRpbWVzdGFtcCI6IjIwMjUtMDctMjlUMTA6NTA6MDAuMDAwWiJ9"
}
```

- `type`: `"request"` or `"response"`
- `payload`: Base64-encoded JSON of actual message

## Communication Patterns

### Connectionless Request-Response Model

The protocol uses **connectionless request-response** with **UUID correlation** for stateless communication:

#### Client Flow
1. **Generate Request**: Create UUID and timestamp
2. **Send Datagram**: Transmit single datagram with complete request
3. **Listen for Response**: Bind to response socket and wait for reply datagram
4. **Response Correlation**: Match responses via UUID
5. **Socket Cleanup**: Close socket after receiving response or timeout

#### Server Flow  
1. **Bind Server Socket**: Listen on server socket path for incoming datagrams
2. **Receive Datagrams**: Process each complete request datagram independently
3. **Validate Security**: Apply comprehensive security framework per message
4. **Execute Handler**: Process request with timeout enforcement
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
  |-- Send Request Datagram ----->|
  |    (UUID: abc123, reply_to)   |-- Receive & Validate
  |                               |-- Execute Handler
  |<-- Response Datagram ---------|
  |    (requestId: abc123)        |
  |                               |
  |-- Close Response Socket ------|
  |                               |
  |-- Create New Response Socket--|
  |-- Send Request Datagram ----->|
  |    (UUID: def456, reply_to)   |-- Execute Handler
  |<-- Response Datagram ---------|
  |    (requestId: def456)        |
  |-- Close Response Socket ------|
```

### Message Correlation System

#### UUID-Based Tracking
- **Request Generation**: UUID v4 for each request
- **Response Socket**: Temporary socket path for receiving replies
- **Reply-To Mechanism**: Server sends response to client's reply_to socket
- **Timeout Cleanup**: Client socket timeout for unresponsive servers

#### Implementation Pattern
```typescript
// Pseudo-code for connectionless correlation system
class JanusClient {
  async sendRequest(request: JanusRequest): Promise<JanusResponse> {
    // Create temporary response socket
    const responseSocket = `/tmp/client_response_${Date.now()}_${Math.random()}.sock`;
    const socket = dgram.createSocket('unix_dgram');
    socket.bind(responseSocket);
    
    // Add reply_to field
    request.reply_to = responseSocket;
    
    // Send request datagram
    await this.sendDatagram(JSON.stringify(request), serverSocketPath);
    
    // Wait for response with timeout
    const response = await this.waitForResponse(socket, request.timeout);
    
    // Cleanup
    socket.close();
    fs.unlinkSync(responseSocket);
    
    return response;
  }
  
  handleResponse(socket: Socket): Promise<JanusResponse> {
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

#### Channel/Request Name Security
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
  maxHandlers: 500;           // Request handlers
  maxPendingRequests: 1000;   // Awaiting responses
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
4. **SENDING**: Transmitting request datagram
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
      "requests": {
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

### Manifest Validation Rules

- **Version**: Semantic versioning (major.minor.patch)
- **Channels**: Must have at least one channel
- **Requests**: Must have unique names within channel
- **Arguments**: Type validation with comprehensive constraints
- **Models**: Reusable type definitions with inheritance support
- **Error Codes**: Predefined set of error conditions

## Error Handling

### JSON-RPC 2.0 Compliant Error System

All implementations must use JSON-RPC 2.0 compliant error codes for consistent cross-platform error handling. The error system consists of **standard JSON-RPC error codes** and **Janus-manifestific protocol error codes**.

#### Standard JSON-RPC 2.0 Error Codes

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| `-32700` | ParseError | Invalid JSON was received by the server | JSON parsing failures, malformed messages |
| `-32600` | InvalidRequest | The JSON sent is not a valid Request object | Missing required fields, invalid request structure |
| `-32601` | MethodNotFound | The method does not exist / is not available | Unknown request names, unregistered handlers |
| `-32602` | InvalidParams | Invalid method parameter(s) | Type validation failures, constraint violations |
| `-32603` | InternalError | Internal JSON-RPC error | Unexpected server errors, system failures |

#### Janus Protocol-Manifestific Error Codes

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| `-32011` | MessageFramingError | Message framing/encoding issues | Length prefix errors, encoding problems |
| `-32012` | ResponseTrackingError | Response correlation/tracking issues | UUID correlation failures, response routing |
| `-32013` | ManifestValidationError | Manifest parsing/validation issues | Manifest validation, schema errors |

#### Extended Server Error Codes (-32000 to -32099)

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| `-32000` | ServerError | Generic server error | General server-side failures |
| `-32001` | ServiceUnavailable | Service unavailable | Server overload, maintenance mode |
| `-32002` | AuthenticationFailed | Authentication failure | Invalid credentials, unauthorized access |
| `-32003` | RateLimitExceeded | Rate limiting exceeded | Too many requests, throttling active |
| `-32004` | ResourceNotFound | Resource not found | Channel or handler not found |
| `-32005` | ValidationFailed | Validation failure | Security validation, input validation |

### JSONRPCError Structure

All error responses must use the standardized JSONRPCError structure:

```json
{
  "code": -32602,
  "message": "Invalid params",
  "data": {
    "field": "username",
    "value": "invalid-value",
    "details": "Username must contain only alphanumeric characters and underscores",
    "constraints": {
      "pattern": "^[a-zA-Z0-9_]+$",
      "minLength": 3,
      "maxLength": 50
    }
  }
}
```

**JSONRPCError Fields**:
- `code` (required): Numeric error code from tables above
- `message` (required): Human-readable error message
- `data` (optional): Additional error context and details

**JSONRPCErrorData Structure** (when present):
- `field`: Field name that caused the error (for validation errors)
- `value`: Actual value that failed validation
- `details`: Detailed explanation of the error
- `constraints`: Validation rules that were violated
- `errorType`: Classification of error for programmatic handling

### Error Categories and Mappings

#### Validation Errors → InvalidParams (-32602)
- Missing required arguments
- Type validation failures  
- Format validation failures
- Range/constraint violations
- Enum value violations

#### Security Errors → ValidationFailed (-32005)
- Path traversal attempts
- Resource limit exceeded
- Channel isolation violations
- Authentication failures
- Input sanitization failures

#### Communication Errors → ServerError (-32000) or Protocol-Manifestific
- Socket communication failures → ServerError (-32000)
- Message encoding/decoding → MessageFramingError (-32011)
- Message size limits → ValidationFailed (-32005)
- Protocol violations → InvalidRequest (-32600)

#### Runtime Errors → InternalError (-32603) or Extended Codes
- Request/handler timeouts → ServerError (-32000)
- Handler not found → MethodNotFound (-32601)
- Unexpected system errors → InternalError (-32603)
- Service unavailable → ServiceUnavailable (-32001)

### Error Response Format

```json
{
  "requestId": "uuid-from-request",
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

#### Request Timeout (Client-Side)
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
    request: 30.0,
    handler: 30.0,
    connection: 10.0
  },
  aggressive: {
    request: 5.0,
    handler: 5.0, 
    connection: 3.0
  },
  relaxed: {
    request: 120.0,
    handler: 120.0,
    connection: 30.0
  }
}
```

### Timeout Error Handling

```json
{
  "requestId": "uuid-from-request",
  "channelId": "channel-name",
  "success": false,
  "error": {
    "code": "REQUEST_TIMEOUT",
    "message": "Request execution exceeded timeout limit",
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
5. **UUID v4 format** for request correlation

### Language-Manifestific Considerations

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
1. **Manifest Parser**: JSON schema validation
2. **Type Validator**: Runtime type checking
3. **Model Registry**: Reusable type definitions
4. **Request Registry**: Dynamic request discovery
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
- Complete request reference
- Type definitions and constraints
- Error codes and handling
- Examples and usage patterns
- Performance characteristics

#### Implementation Guide
- Language-manifestific setup instructions
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

- **v1.0.0** (2025-07-29): Initial manifest with async communication patterns

### Contributing

This manifest is maintained as part of the Janus project. Changes must maintain backward compatibility and cross-language consistency.
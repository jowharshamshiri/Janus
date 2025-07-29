# UnixSockAPI - Cross-Platform Unix Socket Communication

A comprehensive Unix Socket API library providing consistent, secure, and high-performance inter-process communication across **Go**, **Rust**, **Swift**, and **TypeScript**.

## 🚀 Features

- **🌍 Cross-Platform**: Full implementations in Go, Rust, Swift, and TypeScript
- **⚡ Async Communication**: True async patterns with UUID-based response correlation
- **🔒 Security First**: 25+ security validation mechanisms built-in
- **📖 Auto Documentation**: Professional API docs with live reload CLI tool
- **🧪 Comprehensive Testing**: All 16 cross-platform combinations validated
- **📋 Type Safety**: Full type definitions and validation across all languages
- **🎯 Sub-millisecond**: High-performance local socket communication

## 📦 Quick Start

### Using the Documentation CLI

```bash
# Install the documentation CLI globally
npm install -g unixsocket-docs-cli

# Create a new API specification
unixsocket-docs init "My API"

# Generate professional documentation
unixsocket-docs generate api-spec.json

# Serve with live reload during development
unixsocket-docs serve api-spec.json --watch --open
```

### Language-Specific Usage

#### TypeScript/Node.js
```bash
cd TypeScriptUnixSockAPI
npm install && npm run build

# Start server
npm run server

# Run client (in another terminal)
npm run client
```

#### Swift (macOS/iOS)
```bash
cd SwiftUnixSockAPI
swift build

# Start server
swift run SwiftUnixSockAPI-Server

# Run client (in another terminal)  
swift run SwiftUnixSockAPI-Client
```

#### Rust
```bash
cd RustUnixSockAPI
cargo build --release

# Start server
cargo run --bin server

# Run client (in another terminal)
cargo run --bin client
```

#### Go
```bash
cd GoUnixSockAPI
go build -o bin/server ./cmd/server
go build -o bin/client ./cmd/client

# Start server
./bin/server

# Run client (in another terminal)
./bin/client
```

## 🧪 Cross-Platform Testing

Test all implementations communicating with each other:

```bash
# Runs 16 test combinations (4×4 matrix)
./test_cross_platform.sh
```

**Test Matrix**:
- TypeScript ↔ Go, Rust, Swift
- Go ↔ TypeScript, Rust, Swift  
- Rust ↔ TypeScript, Go, Swift
- Swift ↔ TypeScript, Go, Rust

## 📋 Protocol Specification

The library implements a comprehensive Unix socket protocol with:

- **4-byte big-endian length prefixes** for message framing
- **JSON-based messaging** with UUID correlation
- **Async request/response** patterns
- **Comprehensive security validation**
- **Standardized error handling**

See [PROTOCOL.md](PROTOCOL.md) for the complete specification.

## 🔒 Security Features

- **Path Validation**: Directory whitelist, traversal prevention
- **Input Sanitization**: Null byte detection, UTF-8 validation
- **Resource Limits**: Configurable size and connection limits
- **Timeout Management**: Bilateral timeout system
- **Audit Logging**: Comprehensive security event logging

## 📖 Documentation

### Generated Documentation

Professional API documentation is automatically generated:

```bash
# Install CLI tool
npm install -g unixsocket-docs-cli

# Generate docs for your API
unixsocket-docs generate your-api-spec.json

# Serve with live reload
unixsocket-docs serve your-api-spec.json --watch
```

### Reference Documentation

- **[PROTOCOL.md](PROTOCOL.md)** - Complete protocol specification
- **[Example API Spec](example-api-spec.json)** - Sample API specification
- **Language READMEs** - Implementation-specific documentation in each directory

## 🏗️ Implementation Details

### TypeScript Implementation
- **Location**: `TypeScriptUnixSockAPI/`
- **Features**: Full type safety, async/await, Jest testing
- **Package**: Ready for NPM publication
- **Documentation**: Automatic API doc generation

### Swift Implementation  
- **Location**: `SwiftUnixSockAPI/`
- **Features**: Native async/await, Combine integration, SwiftPM package
- **Platform**: macOS and iOS ready
- **Testing**: 129 comprehensive tests

### Rust Implementation
- **Location**: `RustUnixSockAPI/`
- **Features**: Memory safety, zero-cost abstractions, Tokio async
- **Performance**: Optimized for high throughput
- **Testing**: 122 tests (library + integration)

### Go Implementation
- **Location**: `GoUnixSockAPI/`
- **Features**: Goroutines, channels, comprehensive error handling  
- **Performance**: High-performance server implementation
- **Testing**: 63 tests with full coverage

## 🚀 Performance

All implementations target:
- **< 1ms response times** for local Unix socket communication
- **1000+ messages/second** per connection
- **100+ concurrent connections**
- **< 10MB memory usage** baseline

Performance benchmarks available in each implementation directory.

## 🛠️ Development

### Project Structure

```
UnixSockAPI/
├── TypeScriptUnixSockAPI/    # Node.js implementation  
├── SwiftUnixSockAPI/         # Swift implementation
├── RustUnixSockAPI/          # Rust implementation
├── GoUnixSockAPI/          # Go implementation
├── unixsocket-docs-cli/      # Documentation CLI tool
├── PROTOCOL.md               # Protocol specification
├── example-api-spec.json     # Example API specification
└── test_cross_platform.sh    # Cross-platform testing
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the existing code patterns in each language
4. **Add tests** for new functionality
5. **Run** the cross-platform test suite
6. **Submit** a pull request

### Running Tests

Each implementation has its own test suite:

```bash
# TypeScript
cd TypeScriptUnixSockAPI && npm test

# Swift  
cd SwiftUnixSockAPI && swift test

# Rust
cd RustUnixSockAPI && cargo test

# Go
cd GoUnixSockAPI && go test ./...

# Cross-platform integration
./test_cross_platform.sh
```

## 📊 API Specification Format

APIs are defined using JSON specifications:

```json
{
  "version": "1.0.0",
  "name": "My API",
  "description": "Unix Socket API",
  "channels": {
    "user-service": {
      "name": "User Service", 
      "commands": {
        "create-user": {
          "name": "Create User",
          "description": "Create a new user account",
          "args": {
            "username": {
              "type": "string",
              "required": true,
              "minLength": 3,
              "maxLength": 50
            }
          },
          "response": {
            "type": "object", 
            "description": "User creation result"
          }
        }
      }
    }
  }
}
```

## 🔧 Tools

### Documentation CLI (`unixsocket-docs-cli`)

Professional documentation generation tool:

- **Generate**: Static documentation from API specs
- **Serve**: Live reload development server
- **Validate**: API specification validation
- **Init**: Bootstrap new API specifications

```bash
npm install -g unixsocket-docs-cli
unixsocket-docs --help
```

## 📄 License

MIT License - see individual implementation directories for details.

## 🤝 Support

- **Documentation**: See implementation READMEs and PROTOCOL.md
- **Issues**: Report bugs and feature requests via GitHub issues
- **Examples**: Complete examples in each implementation directory

## 🎯 Use Cases

Perfect for:
- **Microservices Communication**: High-performance IPC
- **Plugin Architectures**: Secure subprocess communication  
- **Development Tools**: CLI tools with daemon processes
- **System Services**: OS-level service communication
- **Mobile Apps**: iOS app-to-service communication
- **Cross-Language Integration**: Polyglot system architectures
# Janus - Cross-Platform Unix Socket Communication

A Janus library providing inter-process communication across **Go**, **Rust**, **Swift**, and **TypeScript**.

## Features

- **Cross-Platform**: Implementations in Go, Rust, Swift, and TypeScript
- **Connectionless**: SOCK_DGRAM datagram sockets for stateless communication
- **Simple**: No connection overhead, direct datagram exchange
- **Security**: 25+ security validation mechanisms built-in
- **Documentation**: API docs with live reload CLI tool
- **Testing**: Test infrastructure with N×N matrix validation
- **Type Safety**: Type definitions and validation across languages
- **Performance**: Sub-millisecond connectionless socket communication

## Quick Start

### Using the Documentation CLI

```bash
# Install the documentation CLI globally
npm install -g janus-docs-cli

# Create a new Manifest
janus-docs init "My API"

# Generate professional documentation
janus-docs generate manifest.json

# Serve with live reload during development
janus-docs serve manifest.json --watch --open
```

### Language-Specific Usage

#### TypeScript/Node.js
```bash
cd TypeScriptJanus
npm install && npm run build

# Start server
npm run server

# Run client (in another terminal)
npm run client
```

#### Swift (macOS/iOS)
```bash
cd SwiftJanus
swift build

# Start server
swift run SwiftJanus-Server

# Run client (in another terminal)  
swift run SwiftJanus-Client
```

#### Rust
```bash
cd RustJanus
cargo build --release

# Start server
cargo run --bin server

# Run client (in another terminal)
cargo run --bin client
```

#### Go
```bash
cd GoJanus
go build -o bin/server ./cmd/server
go build -o bin/client ./cmd/client

# Start server
./bin/server

# Run client (in another terminal)
./bin/client
```

## Cross-Platform Testing

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

## Protocol Specification

The library implements a Unix socket protocol with:

- **4-byte big-endian length prefixes** for message framing
- **JSON-based messaging** with UUID correlation
- **Async request/response** patterns
- **Security validation**
- **Standardized error handling**

See [PROTOCOL.md](PROTOCOL.md) for the complete specification.

## Security Features

- **Path Validation**: Directory whitelist, traversal prevention
- **Input Sanitization**: Null byte detection, UTF-8 validation
- **Resource Limits**: Configurable size and connection limits
- **Timeout Management**: Bilateral timeout system
- **Audit Logging**: Security event logging

## Documentation

### Generated Documentation

API documentation is automatically generated:

```bash
# Install CLI tool
npm install -g janus-docs-cli

# Generate docs for your API
janus-docs generate your-manifest.json

# Serve with live reload
janus-docs serve your-manifest.json --watch
```

### Reference Documentation

- **[PROTOCOL.md](PROTOCOL.md)** - Complete protocol specification
- **[tests/README.md](tests/README.md)** - Testing guide  
- **Language READMEs** - Implementation-specific documentation in each directory

## Implementation Details

### TypeScript Implementation
- **Location**: `TypeScriptJanus/`
- **Features**: Type safety, async/await, Jest testing
- **Package**: Ready for NPM publication
- **Documentation**: Automatic API doc generation

### Swift Implementation  
- **Location**: `SwiftJanus/`
- **Features**: Native async/await, Combine integration, SwiftPM package
- **Platform**: macOS and iOS ready
- **Testing**: 129 tests

### Rust Implementation
- **Location**: `RustJanus/`
- **Features**: Memory safety, zero-cost abstractions, Tokio async
- **Performance**: Optimized for throughput
- **Testing**: 122 tests (library + integration)

### Go Implementation
- **Location**: `GoJanus/`
- **Features**: Goroutines, channels, error handling  
- **Performance**: Server implementation
- **Testing**: 63 tests with coverage

## Performance

All implementations target:
- **< 1ms response times** for local Unix socket communication
- **1000+ messages/second** per connection
- **100+ concurrent connections**
- **< 10MB memory usage** baseline

Performance benchmarks available in each implementation directory.

## Development

### Project Structure

```
Janus/
├── TypeScriptJanus/    # Node.js implementation  
├── SwiftJanus/         # Swift implementation
├── RustJanus/          # Rust implementation
├── GoJanus/            # Go implementation
├── janus-docs-cli/      # Documentation CLI tool
├── tests/                    # Test infrastructure
│   ├── run_all_tests.sh      # Test runner
│   ├── config/               # Test configurations
│   ├── python/               # Python test suite
│   └── README.md            # Testing guide
├── PROTOCOL.md               # Protocol specification
└── CLAUDE.md                 # Project instructions
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the existing code patterns in each language
4. **Add tests** for new functionality
5. **Run** the cross-platform test suite
6. **Submit** a pull request

### Running Tests

**Master Test Runner (Recommended)**:
```bash
# Run all basic tests (builds, unit, cross-platform, security)
./tests/run_all_tests.sh

# Quick validation
./tests/run_all_tests.sh --quick

# Full comprehensive testing
./tests/run_all_tests.sh --all

# Test specific implementations
./tests/run_all_tests.sh --implementations go,rust

# CI/CD mode
./tests/run_all_tests.sh --ci --performance
```

**Individual Implementation Tests**:
```bash
# TypeScript
cd TypeScriptJanus && npm test

# Swift  
cd SwiftJanus && swift test

# Rust
cd RustJanus && cargo test

# Go
cd GoJanus && go test ./...
```

**See [tests/README.md](tests/README.md) for complete testing documentation.**

## 📊 Manifest Format

APIs are defined using JSON specifications:

```json
{
  "version": "1.0.0",
  "name": "My API",
  "description": "Janus",
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

## Tools

### Documentation CLI (`janus-docs-cli`)

Documentation generation tool:

- **Generate**: Static documentation from Manifests
- **Serve**: Live reload development server
- **Validate**: Manifest validation
- **Init**: Bootstrap new Manifests

```bash
npm install -g janus-docs-cli
janus-docs --help
```

## License

MIT License - see individual implementation directories for details.

## Support

- **Documentation**: See implementation READMEs and PROTOCOL.md
- **Issues**: Report bugs and feature requests via GitHub issues
- **Examples**: Examples in each implementation directory

## Use Cases

Suitable for:
- **Microservices Communication**: IPC
- **Plugin Architectures**: Subprocess communication  
- **Development Tools**: CLI tools with daemon processes
- **System Services**: OS-level service communication
- **Mobile Apps**: iOS app-to-service communication
- **Cross-Language Integration**: Polyglot system architectures
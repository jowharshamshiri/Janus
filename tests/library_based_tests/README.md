# Library-Based Cross-Platform Test Infrastructure

## Problem Statement

Current test infrastructure calls CLI binaries instead of libraries, missing critical bugs:
- Rust binary wrapped manifest response in "manifest" field for months undetected
- Go client → Rust server communication failed in production terraform
- Message format inconsistencies not caught by unit tests
- Built-in requests never tested across 16 client-server combinations

## Solution: Direct Library Testing

Instead of calling binaries, test the actual libraries directly:

### Current (Binary-Based) Approach
```bash
# Tests call binaries - bypasses library tests
./go-janus --send-to /tmp/server.sock --request manifest
cargo run -- --send-to /tmp/server.sock --request manifest  
```

### New (Library-Based) Approach
```go
// Test libraries directly
client := gojanus.NewClient("/tmp/server.sock", "test")
result, err := client.SendRequest("manifest", nil)
// Validate actual JSON structure, response format, etc.
```

## Test Categories to Implement

### 1. Message Format Validation Tests (F0276, F0280)
- Test JanusRequest structure consistency across all implementations
- Test JanusResponse structure consistency across all implementations  
- Test error response format consistency
- Test built-in request response formats match exactly

### 2. Cross-Platform Library Communication Tests (F0278, F0279)
- Test all 16 client-server combinations using libraries not binaries
- Test manifest request returns identical JSON structure
- Test dynamic manifest fetching end-to-end
- Test built-in requests (ping, echo, get_info, validate, slow_process, manifest)

### 3. Binary vs Library Consistency Tests (F0277)
- Compare library responses with binary responses
- Ensure CLI binaries have same built-in requests as libraries
- Validate message formats are identical between library and binary

### 4. Real Communication Tests (F0281, F0282)
- Replace mock manifest tests with real server communication
- Test actual socket communication not mocked responses
- Ensure tests fail when they should (no false positives)

## Implementation Plan

### Phase 1: Go Library Integration Tests
1. Create proper Go integration test that starts real Go server using library
2. Test Go client → Go server manifest request returns proper JSON structure
3. Validate response format matches expected schema
4. Test all built-in requests return consistent structures

### Phase 2: Rust Library Integration Tests  
1. Create Rust integration test using library APIs
2. Test Rust client → Rust server communication
3. Validate identical response format to Go

### Phase 3: Cross-Platform Library Matrix
1. Go client → Rust server using libraries
2. Rust client → Go server using libraries
3. Add Swift and TypeScript to complete 16-combination matrix
4. Test message format consistency across all combinations

### Phase 4: Message Structure Validation
1. JSON schema validation for JanusRequest
2. JSON schema validation for JanusResponse
3. Built-in request response structure tests
4. Error response format consistency tests

## File Structure

```
tests/library_based_tests/
├── go/
│   ├── integration_test.go           # Go library integration tests
│   ├── cross_platform_test.go        # Go client → other servers
│   └── message_format_test.go        # Message structure validation
├── rust/
│   ├── integration_test.rs           # Rust library integration tests  
│   ├── cross_platform_test.rs        # Rust client → other servers
│   └── message_format_test.rs        # Message structure validation
├── swift/
│   ├── IntegrationTests.swift        # Swift library integration tests
│   ├── CrossPlatformTests.swift      # Swift client → other servers  
│   └── MessageFormatTests.swift      # Message structure validation
├── typescript/
│   ├── integration.test.ts           # TypeScript library tests
│   ├── cross-platform.test.ts       # TypeScript client → other servers
│   └── message-format.test.ts       # Message structure validation
├── schemas/
│   ├── janus-request.schema.json     # JanusRequest JSON schema
│   ├── janus-response.schema.json    # JanusResponse JSON schema
│   └── builtin-responses.schema.json # Built-in request response schemas
└── orchestrator/
    ├── test_orchestrator.py          # Cross-platform test coordinator
    └── server_manager.py             # Start/stop servers for testing
```

## Success Criteria

1. **Catch Format Bugs**: Tests must catch message format inconsistencies like the Rust "manifest" wrapper bug
2. **Real Communication**: All tests use actual socket communication between library implementations
3. **Structure Validation**: JSON message structures validated against schemas
4. **16-Combination Matrix**: All client-server combinations tested with libraries
5. **No False Positives**: Tests fail when implementations have actual bugs

This infrastructure will prevent cross-platform communication bugs from reaching production.
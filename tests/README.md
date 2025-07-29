# UnixSocketAPI Unified Test Infrastructure

This directory contains the complete, organized test infrastructure for validating SOCK_DGRAM Unix Socket implementations across Go, Rust, Swift, and TypeScript.

## 🏗️ Organized Structure

```
tests/
├── README.md                     # This comprehensive guide
├── run_all_tests.sh             # 🎯 MASTER TEST RUNNER - Start here!
├── run_comprehensive_tests.py   # Python test orchestrator
├── bash/                        # Bash test scripts
│   ├── test_cross_platform.sh   # Cross-platform communication tests
│   └── test_socket_creation.sh  # Socket creation validation
├── config/                      # Test configurations
│   ├── unified-test-config.json # 🔧 MAIN TEST CONFIG
│   ├── test-spec.json           # Legacy test spec (deprecated)
│   ├── test-api-spec.json       # API specification for tests
│   └── api-specification-schema.json # API schema validation
├── python/                      # Python test modules
│   ├── comprehensive_test_suite.py # Complete test suite implementation
│   ├── test_orchestrator.py     # Test orchestration (legacy)
│   ├── api_spec_validator.py    # API compliance validation
│   └── performance_benchmark.py # Performance testing
├── legacy/                      # Deprecated/reference files
│   └── test_validation.txt      # Old test report
├── test_logs/                   # Test execution logs (organized by timestamp)
└── test_reports/                # Test reports (organized by timestamp)
```

## Overview

The test infrastructure provides comprehensive validation including:

- **Build Tests**: Verify all implementations compile successfully
- **Unit Tests**: Run language-specific test suites
- **Cross-Platform Tests**: Complete N×N communication matrix testing
- **Self-Communication Tests**: Each implementation talks to itself
- **Feature Tests**: Command variations, timeout handling, concurrent requests
- **Performance Tests**: Latency, throughput, and stress testing
- **Security Tests**: SOCK_DGRAM compliance and protocol validation

## 🚀 Quick Start

### Master Test Runner (Recommended)
```bash
# Run all basic tests (builds, unit, integration, security)
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

### Direct Python Runner
```bash
# Run all basic tests
python tests/run_comprehensive_tests.py

# Full test suite with performance and security
python tests/run_comprehensive_tests.py --performance --security --stress

# Test specific implementations
python tests/run_comprehensive_tests.py --implementations go,rust

# Verbose output
python tests/run_comprehensive_tests.py --verbose
```

### Bash Scripts (Legacy)
```bash
# Cross-platform communication testing
./tests/bash/test_cross_platform.sh

# Socket creation validation  
./tests/bash/test_socket_creation.sh
```

## Test Categories

### Build Tests
- Validates all implementations compile successfully
- Required before any other tests can run
- Creates unified SOCK_DGRAM binaries

### Unit Tests
- Runs language-specific test suites
- `go test ./...`, `cargo test`, `swift test`, `npm test`
- Validates individual implementation functionality

### Cross-Platform Tests
- **Complete N×N Matrix**: Every implementation talks to every other implementation
- **Self-Communication**: Each implementation talks to itself
- **Feature Validation**: Tests different commands (ping, echo) and message types
- **Total Combinations**: 16 tests (4×4 matrix) for basic communication

### Integration Tests
- **Command Variations**: Tests ping, echo, special characters, long messages
- **Timeout Handling**: Validates graceful failure when connecting to non-existent sockets
- **Concurrent Requests**: Tests multiple simultaneous requests to same listener

### Performance Tests
- **Latency Measurements**: Request-response timing
- **Throughput Testing**: Messages per second
- **Concurrent Load**: Multiple clients simultaneously
- **Memory Usage**: Resource consumption monitoring

### Security Tests
- **SOCK_DGRAM Compliance**: Ensures only SOCK_DGRAM sockets are used
- **Protocol Validation**: Verifies proper message format and reply_to mechanism
- **Input Validation**: Tests security constraints and sanitization

## Test Structure

```
tests/
├── README.md                          # This file
├── run_comprehensive_tests.py         # Main test runner
├── python/                            # Python test modules
│   ├── comprehensive_test_suite.py    # Main test suite
│   ├── test_orchestrator.py           # Original orchestrator (legacy)
│   ├── api_spec_validator.py          # API specification validation
│   └── performance_benchmark.py       # Performance testing
├── logs/                              # Test execution logs
│   └── YYYYMMDD_HHMMSS/              # Timestamped log directories
└── reports/                           # Test reports
    └── YYYYMMDD_HHMMSS/              # Timestamped report directories
        ├── comprehensive_test_report.json
        └── comprehensive_test_report.md
```

## Implementation Matrix

The test suite validates communication between all implementations:

| Sender → Listener | Go | Rust | Swift | TypeScript |
|-------------------|----|----- |-------|------------|
| **Go**           | ✅  | ✅   | ✅    | ✅         |
| **Rust**         | ✅  | ✅   | ✅    | ✅         |
| **Swift**        | ✅  | ✅   | ✅    | ✅         |
| **TypeScript**   | ✅  | ✅   | ✅    | ✅         |

**Total Tests**: 16 cross-platform communication tests + feature tests for each implementation

## Test Configuration

Tests are configured via `test-spec.json` in the project root:

```json
{
  "implementations": {
    "go": {
      "directory": "GoUnixSockAPI",
      "build_command": ["go", "build", "-o", "unixsock-dgram", "./cmd/unixsock-dgram"],
      "test_command": ["go", "test", "./..."],
      "unified_binary": "./unixsock-dgram",
      "socket_path": "/tmp/go-unixsock-api.sock"
    }
  }
}
```

## SOCK_DGRAM Architecture

All tests validate the unified SOCK_DGRAM process model:

- **No Client/Server Distinction**: Each process can both listen and send
- **Unified Binary**: Single executable with `--listen` and `--send-to` modes
- **Connectionless**: No persistent connections, each message is independent
- **Reply-To Mechanism**: Temporary response sockets for request-response patterns

### Command Examples

```bash
# Start listener
./unixsock-dgram --listen --socket /tmp/test.sock

# Send message
./unixsock-dgram --send-to /tmp/test.sock --command ping --message hello
```

## Advanced Usage

### Custom Test Categories
```bash
python tests/run_comprehensive_tests.py --categories build,cross_platform
```

### Filter Implementations
```bash
python tests/run_comprehensive_tests.py --implementations rust,swift
```

### Full Test Suite
```bash
python tests/run_comprehensive_tests.py --performance --security --stress --verbose
```

### Custom Configuration
```bash
python tests/run_comprehensive_tests.py --config custom-test-spec.json
```

## Test Reports

Test results are saved in timestamped directories:

- **JSON Report**: Machine-readable complete test results
- **Markdown Report**: Human-readable summary with test matrix
- **Logs**: Detailed execution logs for debugging

### Report Contents

- **Summary Statistics**: Pass/fail counts, success rates
- **Implementation Status**: Build success, availability
- **Category Breakdown**: Results by test category
- **Detailed Results**: Complete test outcomes with timing
- **Cross-Platform Matrix**: Visual representation of communication tests

## Troubleshooting

### Build Failures
```bash
# Check specific implementation
python tests/run_comprehensive_tests.py --implementations go --verbose
```

### Communication Failures
```bash
# Run only cross-platform tests with verbose output
python tests/run_comprehensive_tests.py --categories cross_platform --verbose
```

### Socket Issues
```bash
# Clean up any stuck socket files
rm -f /tmp/*unixsock*.sock
```

## Development Guidelines

### Adding New Tests
1. Add test methods to `comprehensive_test_suite.py`
2. Update test categories as needed
3. Add configuration to `test-spec.json`
4. Update this README

### Modifying Implementations
1. Ensure SOCK_DGRAM compliance
2. Maintain unified binary interface
3. Run full test suite before committing
4. Update configuration if binary paths change

### Performance Baseline Updates
1. Run performance tests on known-good state
2. Update target values in configuration
3. Document performance requirements

## CI/CD Integration

The test suite is designed for automated execution:

```bash
# Exit code 0 = all tests passed
# Exit code 1 = some tests failed
# Exit code 130 = interrupted by user
python tests/run_comprehensive_tests.py
echo "Exit code: $?"
```

For continuous integration, use:
```bash
python tests/run_comprehensive_tests.py --performance --security
```

## Contributing

When contributing to the test infrastructure:

1. **Test Changes**: Run full test suite before submitting
2. **Documentation**: Update this README for new features
3. **Backward Compatibility**: Ensure existing tests continue to work
4. **Configuration**: Update test-spec.json for new implementations
5. **Cross-Platform**: Test on multiple platforms where possible

For questions about the test infrastructure, refer to the project documentation or create an issue.
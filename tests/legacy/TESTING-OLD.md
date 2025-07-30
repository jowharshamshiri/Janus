# Janus Comprehensive Testing Guide

This document describes the comprehensive cross-platform testing infrastructure for the Janus project, which validates SOCK_DGRAM Unix domain socket implementations across Go, Rust, Swift, and TypeScript.

## Overview

The testing infrastructure provides:

- **Cross-platform validation** - Tests all 16 combinations of client/server pairs
- **API specification compliance** - Validates implementations against central API spec
- **Performance benchmarking** - Measures latency, throughput, and memory usage
- **Security validation** - Ensures SOCK_DGRAM-only usage and proper security
- **Automated CI/CD** - GitHub Actions workflows for continuous testing
- **Comprehensive reporting** - Detailed test reports with metrics and analysis

## Test Architecture

### Central API Specification
All tests are driven by a central API specification (`test-spec.json`) that defines:
- Protocol requirements (SOCK_DGRAM only)
- Test commands and expected responses
- Performance targets and benchmarks
- Implementation-specific build/test commands
- Cross-platform test matrix (4×4 = 16 combinations)

### Test Components

```
Janus/
├── test-spec.json                    # Central test specification
├── test_orchestrator.py             # Main test orchestrator
├── api_spec_validator.py            # API compliance validator
├── performance_benchmark.py         # Performance benchmarking suite
├── run_comprehensive_tests.sh       # Comprehensive test runner
├── .github/workflows/                # CI/CD workflows
│   └── cross-platform-tests.yml
└── test_logs/                        # Test execution logs
    └── test_reports/                 # Generated test reports
```

## Quick Start

### Prerequisites

Ensure you have all required tools installed:

```bash
# Required for all platforms
python3
go (1.21+)
cargo (Rust stable)
node (18+)
npm

# Required for macOS only
swift (5.9+)
```

### Running Tests

#### Full Test Suite
```bash
# Run complete test suite (builds, unit tests, integration tests)
./run_comprehensive_tests.sh

# Run with performance benchmarks
./run_comprehensive_tests.sh --performance --verbose

# Run specific implementations only
./run_comprehensive_tests.sh -i go,rust --performance
```

#### Individual Test Components

**Build Validation:**
```bash
./run_comprehensive_tests.sh --no-unit --no-integration --no-security
```

**Unit Tests Only:**
```bash
./run_comprehensive_tests.sh --no-builds --no-integration --no-security
```

**Cross-Platform Integration Tests:**
```bash
python3 test_orchestrator.py --categories integration --verbose
```

**API Specification Compliance:**
```bash
python3 api_spec_validator.py \
  --implementation GoJanus \
  --server-cmd go run cmd/server/main.go \
  --socket-path /tmp/test.sock
```

**Performance Benchmarks:**
```bash
python3 performance_benchmark.py --verbose --implementations go,rust
```

## Test Categories

### 1. Build Tests
Validates that all implementations compile successfully:

- **Go**: `go build ./...`
- **Rust**: `cargo build --release`
- **Swift**: `swift build -c release` (macOS only)
- **TypeScript**: `npm ci && npm run build`

### 2. Unit Tests
Runs language-specific unit test suites:

- **Go**: `go test ./...`
- **Rust**: `cargo test`
- **Swift**: `swift test`
- **TypeScript**: `npm test`

### 3. Integration Tests
Cross-platform communication validation:

- **Self-communication**: Each implementation talks to itself (4 tests)
- **Cross-communication**: Each implementation talks to others (12 tests)
- **Total combinations**: 16 client/server pairs
- **Test commands**: ping, echo, get_info, stress_test

### 4. API Specification Compliance
Validates adherence to SOCK_DGRAM protocol:

- **SOCK_DGRAM only**: No SOCK_STREAM or TCP usage
- **Message format**: Proper JSON with required fields
- **Reply-to mechanism**: Correct temporary socket usage
- **Timeout handling**: Graceful error handling
- **Security constraints**: Input validation and sanitization

### 5. Performance Benchmarks
Measures performance characteristics:

- **Latency test**: Request-response latency (1000 iterations)
- **Throughput test**: Messages per second (30s duration, 10 concurrent clients)
- **Concurrency test**: Success rate under load (50 clients, 100 req/client)
- **Memory usage**: Memory consumption during operation

### 6. Security Tests
Security validation and vulnerability scanning:

- **Code analysis**: Pattern matching for forbidden constructs
- **Protocol validation**: SOCK_DGRAM enforcement
- **Input validation**: Security constraint verification
- **Static analysis**: Language-specific security scanning

## Test Specification Format

The central `test-spec.json` defines the complete test configuration:

```json
{
  "implementations": {
    "go": {
      "directory": "GoJanus",
      "build_command": ["go", "build", "./..."],
      "test_command": ["go", "test", "./..."],
      "server_command": ["go", "run", "cmd/server/main.go"],
      "socket_path": "/tmp/go-janus-api.sock"
    }
  },
  "test_commands": {
    "ping": {
      "channel": "system",
      "command": "ping",
      "parameters": {"message": "hello"},
      "expected_response": {"status": "success", "echo": "hello"}
    }
  },
  "performance_benchmarks": {
    "latency_test": {
      "iterations": 1000,
      "target_p99_ms": 10
    }
  }
}
```

## CI/CD Integration

### GitHub Actions Workflow

The project includes comprehensive GitHub Actions workflows (`.github/workflows/cross-platform-tests.yml`):

#### Build Matrix
- **Platforms**: Ubuntu, macOS
- **Languages**: Go, Rust, Swift (macOS only), TypeScript
- **Parallel execution**: All builds run simultaneously

#### Test Phases
1. **Build validation** - Compile all implementations
2. **Unit tests** - Language-specific test suites
3. **Integration tests** - Cross-platform communication
4. **Security tests** - Compliance and vulnerability scanning
5. **Performance tests** - Benchmarks (on schedule or `[benchmark]` commit message)

#### Reporting
- **Artifacts**: Test results, coverage reports, logs
- **PR comments**: Automatic test result summaries
- **Reports**: Comprehensive test reports with 90-day retention

### Triggering CI
```bash
# Regular push/PR - runs build, unit, integration, security tests
git push origin feature-branch

# Include performance benchmarks
git commit -m "Add new feature [benchmark]"
git push origin main

# Scheduled runs - daily at 02:00 UTC with full test suite
```

## Test Reports

### Comprehensive Report Structure
```
test_reports/YYYYMMDD_HHMMSS/
├── comprehensive_test_report.md      # Main report
├── build_summary.txt                 # Build results
├── unit_tests_summary.txt           # Unit test results
├── integration_report.txt           # Cross-platform tests
├── security_summary.txt             # Security validation
├── performance_report.txt           # Benchmark results
└── security_*.json                  # Detailed security analysis
```

### Report Contents
- **Executive Summary**: Pass/fail status, timing, coverage
- **Build Status**: Compilation results for each implementation
- **Unit Test Results**: Language-specific test outcomes
- **Integration Matrix**: 4×4 communication test results
- **Performance Metrics**: Latency, throughput, memory usage
- **Security Analysis**: Compliance and vulnerability assessment
- **Detailed Logs**: Complete execution traces

## Performance Targets

### Latency Targets
- **P95 latency**: < 10ms
- **P99 latency**: < 50ms
- **Average latency**: < 5ms

### Throughput Targets
- **Single client**: > 1000 req/s
- **10 concurrent clients**: > 5000 req/s
- **Success rate**: > 99%

### Memory Targets
- **Average memory usage**: < 50MB
- **Peak memory usage**: < 100MB
- **Memory growth**: < 1MB/hour

### Concurrency Targets
- **50 concurrent clients**: > 99% success rate
- **100 requests per client**: < 1% failure rate
- **Total throughput**: > 1000 req/s

## Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Check build logs
cat test_logs/latest/build_*.log

# Test individual implementation
cd GoJanus && go build ./...
```

**Integration Test Failures:**
```bash
# Run with verbose logging
python3 test_orchestrator.py --categories integration --verbose

# Check server startup
./run_comprehensive_tests.sh -i go --no-unit --verbose
```

**Performance Issues:**
```bash
# Run isolated performance test
python3 performance_benchmark.py --implementations go --verbose

# Check system resources
htop
df -h /tmp
```

### Debugging Commands

**Check socket files:**
```bash
ls -la /tmp/*sock* /tmp/*unix*
```

**Monitor test processes:**
```bash
ps aux | grep -E "(test|server|client)"
```

**Check test logs:**
```bash
tail -f test_logs/latest/comprehensive_test.log
```

## Development Guidelines

### Adding New Tests

1. **Update test specification** (`test-spec.json`)
2. **Add test logic** to appropriate component
3. **Update CI workflow** if needed
4. **Test locally** before committing
5. **Update documentation**

### Modifying Implementations

1. **Ensure SOCK_DGRAM compliance**
2. **Run full test suite** before committing
3. **Update performance baselines** if needed
4. **Maintain API compatibility**
5. **Update test commands** if API changes

### Best Practices

- **Always run tests locally** before pushing
- **Use verbose mode** for debugging
- **Check all 16 communication combinations**
- **Validate performance impact** of changes
- **Maintain backward compatibility**
- **Document test changes** in commit messages

## Advanced Usage

### Custom Test Configurations

**Create custom test spec:**
```json
{
  "name": "Custom Test Suite",
  "implementations": {"go": {...}},
  "test_commands": {"custom_test": {...}},
  "performance_benchmarks": {...}
}
```

**Run with custom config:**
```bash
python3 test_orchestrator.py --config custom-test-spec.json
```

### Parallel Testing

**Run tests in parallel:**
```bash
./run_comprehensive_tests.sh --parallel --performance
```

**Limit concurrent tests:**
```bash
# Modify test-spec.json
"environment": {
  "max_parallel_tests": 2
}
```

### Extended Performance Testing

**Long-running benchmarks:**
```bash
python3 performance_benchmark.py \
  --config extended-perf-spec.json \
  --implementations all \
  --verbose
```

**Memory leak detection:**
```bash
# Run extended memory benchmark
python3 performance_benchmark.py --memory-duration 3600  # 1 hour
```

## Contributing

When contributing to the test infrastructure:

1. **Test your changes** with the full test suite
2. **Maintain backward compatibility** with existing tests
3. **Update documentation** for new features
4. **Follow the existing code style** and patterns
5. **Add appropriate error handling** and logging

### Test Infrastructure Changes

**Adding new test categories:**
1. Update `test-spec.json` with new category
2. Add implementation in `test_orchestrator.py`
3. Update CI workflow
4. Add documentation

**Modifying performance targets:**
1. Update targets in `test-spec.json`
2. Validate with current implementations
3. Update CI thresholds
4. Document rationale

For questions or issues with the testing infrastructure, please refer to the project's issue tracker or documentation.
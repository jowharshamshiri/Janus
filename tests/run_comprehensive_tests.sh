#!/bin/bash

# UnixSocketAPI Comprehensive Test Suite Runner
# Executes complete test suite with build validation, unit tests, integration tests, and performance benchmarks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="${SCRIPT_DIR}/test_logs/${TIMESTAMP}"
REPORT_DIR="${SCRIPT_DIR}/test_reports/${TIMESTAMP}"

# Default settings
VERBOSE=false
RUN_BUILDS=true
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=true
RUN_PERFORMANCE_TESTS=false
RUN_SECURITY_TESTS=true
IMPLEMENTATIONS=("go" "rust" "swift" "typescript")
PARALLEL_TESTS=false

# Help function
show_help() {
    cat << EOF
UnixSocketAPI Comprehensive Test Suite

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -i, --implementations   Specify implementations to test (go,rust,swift,typescript)
    --no-builds            Skip build phase
    --no-unit              Skip unit tests
    --no-integration       Skip integration tests
    --performance          Include performance benchmarks
    --no-security          Skip security tests
    --parallel             Run tests in parallel where possible
    --log-dir DIR          Custom log directory
    --report-dir DIR       Custom report directory

EXAMPLES:
    $0                                    # Run standard test suite
    $0 --verbose --performance            # Run all tests with benchmarks
    $0 -i go,rust --no-integration        # Test only Go and Rust, skip integration
    $0 --parallel --performance           # Run tests in parallel with benchmarks

TEST PHASES:
    1. Prerequisites Check - Verify all required tools are installed
    2. Build Phase - Build all implementations
    3. Unit Tests - Run language-specific unit tests
    4. Integration Tests - Cross-platform communication tests
    5. Security Tests - API specification compliance and security validation
    6. Performance Tests - Benchmarking (optional)
    7. Report Generation - Comprehensive test report

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "${LOG_DIR}/comprehensive_test.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "${LOG_DIR}/comprehensive_test.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "${LOG_DIR}/comprehensive_test.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "${LOG_DIR}/comprehensive_test.log"
}

# Setup logging directories
setup_logging() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${REPORT_DIR}"
    
    log_info "Test run started at $(date)"
    log_info "Logs directory: ${LOG_DIR}"
    log_info "Reports directory: ${REPORT_DIR}"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -i|--implementations)
                IFS=',' read -ra IMPLEMENTATIONS <<< "$2"
                shift 2
                ;;
            --no-builds)
                RUN_BUILDS=false
                shift
                ;;
            --no-unit)
                RUN_UNIT_TESTS=false
                shift
                ;;
            --no-integration)
                RUN_INTEGRATION_TESTS=false
                shift
                ;;
            --performance)
                RUN_PERFORMANCE_TESTS=true
                shift
                ;;
            --no-security)
                RUN_SECURITY_TESTS=false
                shift
                ;;
            --parallel)
                PARALLEL_TESTS=true
                shift
                ;;
            --log-dir)
                LOG_DIR="$2"
                shift 2
                ;;
            --report-dir)
                REPORT_DIR="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    local tools=("python3" "go" "cargo" "node" "npm")
    
    # Add Swift only on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        tools+=("swift")
    fi
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools before running tests"
        return 1
    fi
    
    # Check Python dependencies
    if ! python3 -c "import json, socket, threading, subprocess, statistics" &> /dev/null; then
        log_warning "Some Python modules may be missing, but continuing..."
    fi
    
    log_success "Prerequisites check completed"
    return 0
}

# Filter implementations based on platform
filter_implementations() {
    local filtered=()
    
    for impl in "${IMPLEMENTATIONS[@]}"; do
        case "$impl" in
            "swift")
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    filtered+=("$impl")
                else
                    log_warning "Skipping Swift implementation (not available on non-macOS)"
                fi
                ;;
            *)
                filtered+=("$impl")
                ;;
        esac
    done
    
    IMPLEMENTATIONS=("${filtered[@]}")
    log_info "Testing implementations: ${IMPLEMENTATIONS[*]}"
}

# Build phase
run_build_phase() {
    if [[ "$RUN_BUILDS" == false ]]; then
        log_info "Skipping build phase"
        return 0
    fi
    
    log_info "Starting build phase..."
    
    local build_results=()
    local failed_builds=()
    
    for impl in "${IMPLEMENTATIONS[@]}"; do
        log_info "Building $impl implementation..."
        
        local build_log="${LOG_DIR}/build_${impl}.log"
        local build_success=true
        
        case "$impl" in
            "go")
                (cd GoUnixSockAPI && go build -v ./...) > "$build_log" 2>&1 || build_success=false
                ;;
            "rust")
                (cd RustUnixSockAPI && cargo build --release) > "$build_log" 2>&1 || build_success=false
                ;;
            "swift")
                (cd SwiftUnixSockAPI && swift build -c release) > "$build_log" 2>&1 || build_success=false
                ;;
            "typescript")
                (cd TypeScriptUnixSockAPI && npm ci && npm run build) > "$build_log" 2>&1 || build_success=false
                ;;
        esac
        
        if [[ "$build_success" == true ]]; then
            log_success "$impl build completed"
            build_results+=("$impl:SUCCESS")
        else
            log_error "$impl build failed (see $build_log)"
            build_results+=("$impl:FAILED")
            failed_builds+=("$impl")
        fi
    done
    
    # Update implementations list to exclude failed builds
    if [[ ${#failed_builds[@]} -gt 0 ]]; then
        local working_impls=()
        for impl in "${IMPLEMENTATIONS[@]}"; do
            if [[ ! " ${failed_builds[@]} " =~ " ${impl} " ]]; then
                working_impls+=("$impl")
            fi
        done
        
        if [[ ${#working_impls[@]} -eq 0 ]]; then
            log_error "All builds failed, cannot continue"
            return 1
        fi
        
        IMPLEMENTATIONS=("${working_impls[@]}")
        log_warning "Continuing with working implementations: ${IMPLEMENTATIONS[*]}"
    fi
    
    # Write build summary
    {
        echo "BUILD PHASE SUMMARY"
        echo "=================="
        echo "Timestamp: $(date)"
        echo ""
        for result in "${build_results[@]}"; do
            echo "$result"
        done
    } > "${REPORT_DIR}/build_summary.txt"
    
    log_success "Build phase completed"
    return 0
}

# Unit tests phase
run_unit_tests() {
    if [[ "$RUN_UNIT_TESTS" == false ]]; then
        log_info "Skipping unit tests"
        return 0
    fi
    
    log_info "Starting unit tests phase..."
    
    local test_results=()
    
    for impl in "${IMPLEMENTATIONS[@]}"; do
        log_info "Running unit tests for $impl..."
        
        local test_log="${LOG_DIR}/unit_test_${impl}.log"
        local test_success=true
        
        case "$impl" in
            "go")
                (cd GoUnixSockAPI && go test -v ./...) > "$test_log" 2>&1 || test_success=false
                ;;
            "rust")
                (cd RustUnixSockAPI && cargo test) > "$test_log" 2>&1 || test_success=false
                ;;
            "swift")
                (cd SwiftUnixSockAPI && swift test) > "$test_log" 2>&1 || test_success=false
                ;;
            "typescript")
                (cd TypeScriptUnixSockAPI && npm test) > "$test_log" 2>&1 || test_success=false
                ;;
        esac
        
        if [[ "$test_success" == true ]]; then
            log_success "$impl unit tests passed"
            test_results+=("$impl:PASSED")
        else
            log_warning "$impl unit tests failed (see $test_log)"
            test_results+=("$impl:FAILED")
        fi
    done
    
    # Write unit test summary
    {
        echo "UNIT TESTS SUMMARY"
        echo "=================="
        echo "Timestamp: $(date)"
        echo ""
        for result in "${test_results[@]}"; do
            echo "$result"
        done
    } > "${REPORT_DIR}/unit_tests_summary.txt"
    
    log_success "Unit tests phase completed"
    return 0
}

# Integration tests phase
run_integration_tests() {
    if [[ "$RUN_INTEGRATION_TESTS" == false ]]; then
        log_info "Skipping integration tests"
        return 0
    fi
    
    log_info "Starting integration tests phase..."
    
    local orchestrator_args="--categories integration --verbose"
    if [[ "$VERBOSE" == true ]]; then
        orchestrator_args="$orchestrator_args --verbose"
    fi
    
    local integration_log="${LOG_DIR}/integration_tests.log"
    local integration_report="${REPORT_DIR}/integration_report.txt"
    
    if python3 test_orchestrator.py $orchestrator_args --report "$integration_report" > "$integration_log" 2>&1; then
        log_success "Integration tests completed successfully"
    else
        log_warning "Integration tests completed with issues (see $integration_log)"
    fi
    
    return 0
}

# Security tests phase
run_security_tests() {
    if [[ "$RUN_SECURITY_TESTS" == false ]]; then
        log_info "Skipping security tests"
        return 0
    fi
    
    log_info "Starting security tests phase..."
    
    local security_results=()
    
    for impl in "${IMPLEMENTATIONS[@]}"; do
        log_info "Running security validation for $impl..."
        
        local security_log="${LOG_DIR}/security_${impl}.log"
        local security_report="${REPORT_DIR}/security_${impl}.json"
        
        # Determine implementation directory and server command
        local impl_dir=""
        local server_cmd=()
        local socket_path="/tmp/security_test_${impl}.sock"
        
        case "$impl" in
            "go")
                impl_dir="GoUnixSockAPI"
                server_cmd=("go" "run" "cmd/server/main.go")
                ;;
            "rust")
                impl_dir="RustUnixSockAPI"
                server_cmd=("cargo" "run" "--bin" "server")
                ;;
            "swift")
                impl_dir="SwiftUnixSockAPI"
                server_cmd=("swift" "run" "SwiftUnixSockAPI-Server")
                ;;
            "typescript")
                impl_dir="TypeScriptUnixSockAPI"
                server_cmd=("node" "dist/examples/simple-server.js")
                ;;
        esac
        
        if python3 api_spec_validator.py \
            --api-spec example-api-spec.json \
            --implementation "$impl_dir" \
            --server-cmd "${server_cmd[@]}" \
            --socket-path "$socket_path" \
            --output "$security_report" \
            --verbose > "$security_log" 2>&1; then
            log_success "$impl security validation passed"
            security_results+=("$impl:PASSED")
        else
            log_warning "$impl security validation failed (see $security_log)"
            security_results+=("$impl:FAILED")
        fi
    done
    
    # Write security summary
    {
        echo "SECURITY TESTS SUMMARY"
        echo "======================"
        echo "Timestamp: $(date)"
        echo ""
        for result in "${security_results[@]}"; do
            echo "$result"
        done
    } > "${REPORT_DIR}/security_summary.txt"
    
    log_success "Security tests phase completed"
    return 0
}

# Performance tests phase
run_performance_tests() {
    if [[ "$RUN_PERFORMANCE_TESTS" == false ]]; then
        log_info "Skipping performance tests"
        return 0
    fi
    
    log_info "Starting performance tests phase..."
    
    local performance_log="${LOG_DIR}/performance_tests.log"
    local performance_results="${REPORT_DIR}/performance_results.json"
    local performance_report="${REPORT_DIR}/performance_report.txt"
    
    local impl_args=""
    if [[ ${#IMPLEMENTATIONS[@]} -gt 0 ]]; then
        impl_args="--implementations ${IMPLEMENTATIONS[*]}"
    fi
    
    if python3 performance_benchmark.py \
        --config test-spec.json \
        $impl_args \
        --output "$performance_results" \
        --report "$performance_report" \
        --verbose > "$performance_log" 2>&1; then
        log_success "Performance tests completed successfully"
    else
        log_warning "Performance tests completed with issues (see $performance_log)"
    fi
    
    return 0
}

# Generate final comprehensive report
generate_final_report() {
    log_info "Generating comprehensive test report..."
    
    local final_report="${REPORT_DIR}/comprehensive_test_report.md"
    
    {
        echo "# UnixSocketAPI Comprehensive Test Report"
        echo ""
        echo "**Generated:** $(date)"
        echo "**Test Run ID:** $TIMESTAMP"
        echo "**Implementations Tested:** ${IMPLEMENTATIONS[*]}"
        echo ""
        echo "## Test Configuration"
        echo ""
        echo "- Build Phase: $RUN_BUILDS"
        echo "- Unit Tests: $RUN_UNIT_TESTS"
        echo "- Integration Tests: $RUN_INTEGRATION_TESTS"
        echo "- Security Tests: $RUN_SECURITY_TESTS"
        echo "- Performance Tests: $RUN_PERFORMANCE_TESTS"
        echo "- Verbose Mode: $VERBOSE"
        echo "- Parallel Tests: $PARALLEL_TESTS"
        echo ""
        
        # Include individual phase reports
        for report_file in "${REPORT_DIR}"/*.txt; do
            if [[ -f "$report_file" && "$(basename "$report_file")" != "comprehensive_test_report.md" ]]; then
                echo "## $(basename "$report_file" .txt | tr '_' ' ' | tr '[:lower:]' '[:upper:]')"
                echo ""
                echo '```'
                cat "$report_file"
                echo '```'
                echo ""
            fi
        done
        
        # Include performance results if available
        if [[ -f "${REPORT_DIR}/performance_report.txt" ]]; then
            echo "## Performance Benchmark Results"
            echo ""
            echo '```'
            cat "${REPORT_DIR}/performance_report.txt"
            echo '```'
            echo ""
        fi
        
        echo "## Test Logs"
        echo ""
        echo "Detailed logs are available in: \`${LOG_DIR}\`"
        echo ""
        echo "- Build logs: \`build_*.log\`"
        echo "- Unit test logs: \`unit_test_*.log\`"
        echo "- Integration test log: \`integration_tests.log\`"
        echo "- Security test logs: \`security_*.log\`"
        if [[ "$RUN_PERFORMANCE_TESTS" == true ]]; then
            echo "- Performance test log: \`performance_tests.log\`"
        fi
        echo ""
        echo "## Summary"
        echo ""
        echo "Test run completed at $(date)"
        
    } > "$final_report"
    
    log_success "Comprehensive test report generated: $final_report"
    
    # Display summary
    echo ""
    echo "=========================================="
    echo "UNIXSOCKETAPI TEST RUN SUMMARY"
    echo "=========================================="
    echo "Timestamp: $TIMESTAMP"
    echo "Implementations: ${IMPLEMENTATIONS[*]}"
    echo ""
    echo "Reports available in: $REPORT_DIR"
    echo "Logs available in: $LOG_DIR"
    echo ""
    echo "Main report: $final_report"
    echo "=========================================="
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    
    # Kill any remaining test processes
    pkill -f "test_orchestrator.py" 2>/dev/null || true
    pkill -f "api_spec_validator.py" 2>/dev/null || true
    pkill -f "performance_benchmark.py" 2>/dev/null || true
    
    # Clean up temporary socket files
    rm -f /tmp/*unixsock* /tmp/*test*.sock /tmp/*benchmark*.sock 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Signal handlers
trap cleanup EXIT
trap 'log_error "Test run interrupted"; exit 130' INT TERM

# Main execution
main() {
    parse_args "$@"
    setup_logging
    
    log_info "Starting UnixSocketAPI comprehensive test suite"
    log_info "Configuration: builds=$RUN_BUILDS, unit=$RUN_UNIT_TESTS, integration=$RUN_INTEGRATION_TESTS, security=$RUN_SECURITY_TESTS, performance=$RUN_PERFORMANCE_TESTS"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        exit 1
    fi
    
    # Filter implementations based on platform
    filter_implementations
    
    # Run test phases
    local phase_failures=0
    
    if ! run_build_phase; then
        ((phase_failures++))
        log_error "Build phase failed"
    fi
    
    if ! run_unit_tests; then
        ((phase_failures++))
        log_warning "Unit tests phase had issues"
    fi
    
    if ! run_integration_tests; then
        ((phase_failures++))
        log_warning "Integration tests phase had issues"
    fi
    
    if ! run_security_tests; then
        ((phase_failures++))
        log_warning "Security tests phase had issues"
    fi
    
    if ! run_performance_tests; then
        ((phase_failures++))
        log_warning "Performance tests phase had issues"
    fi
    
    # Generate final report
    generate_final_report
    
    if [[ $phase_failures -eq 0 ]]; then
        log_success "All test phases completed successfully"
        exit 0
    else
        log_warning "Test run completed with $phase_failures phase(s) having issues"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
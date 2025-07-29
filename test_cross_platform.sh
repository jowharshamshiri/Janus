#!/bin/bash

# Cross-Platform Unix Socket API Testing Infrastructure
# Tests communication between Swift, Rust, and Go implementations

set -e

# Configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOCKET_PATH="/tmp/cross_platform_test.sock"
LOG_DIR="${TEST_DIR}/test_logs"
TIMEOUT=30
VERBOSE=${VERBOSE:-0}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "${LOG_DIR}"

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠${NC} $1"
}

# Cleanup function
cleanup() {
    log "Cleaning up test processes and socket..."
    
    # Kill any remaining test processes
    pkill -f "swift.*test" 2>/dev/null || true
    pkill -f "cargo.*test" 2>/dev/null || true
    pkill -f "go.*test" 2>/dev/null || true
    
    # Remove test socket
    rm -f "${SOCKET_PATH}"
    
    # Wait a moment for cleanup
    sleep 1
}

# Set up cleanup trap
trap cleanup EXIT

# Check if implementations exist and are buildable
check_implementation() {
    local impl_name="$1"
    local impl_dir="$2"
    local build_cmd="$3"
    
    log "Checking ${impl_name} implementation..."
    
    if [[ ! -d "${impl_dir}" ]]; then
        log_error "${impl_name} directory not found: ${impl_dir}"
        return 1
    fi
    
    cd "${impl_dir}"
    
    if [[ ${VERBOSE} -eq 1 ]]; then
        log "Building ${impl_name}..."
        eval "${build_cmd}"
    else
        eval "${build_cmd}" > "${LOG_DIR}/$(echo ${impl_name} | tr '[:upper:]' '[:lower:]')_build.log" 2>&1
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "${impl_name} builds successfully"
        return 0
    else
        log_error "${impl_name} failed to build"
        if [[ ${VERBOSE} -eq 0 ]]; then
            log "Build log saved to: ${LOG_DIR}/$(echo ${impl_name} | tr '[:upper:]' '[:lower:]')_build.log"
        fi
        return 1
    fi
}

# Start a server implementation
start_server() {
    local impl_name="$1"
    local impl_dir="$2"
    local server_cmd="$3"
    local pid_file="${LOG_DIR}/$(echo ${impl_name} | tr '[:upper:]' '[:lower:]')_server.pid"
    
    log "Starting ${impl_name} server..."
    
    cd "${impl_dir}"
    
    # Remove old socket
    rm -f "${SOCKET_PATH}"
    
    if [[ ${VERBOSE} -eq 1 ]]; then
        eval "${server_cmd}" &
    else
        eval "${server_cmd}" > "${LOG_DIR}/$(echo ${impl_name} | tr '[:upper:]' '[:lower:]')_server.log" 2>&1 &
    fi
    
    local server_pid=$!
    echo "${server_pid}" > "${pid_file}"
    
    # Wait for server to be ready
    local attempts=0
    while [[ ${attempts} -lt 10 ]] && [[ ! -S "${SOCKET_PATH}" ]]; do
        sleep 0.5
        ((attempts++))
    done
    
    if [[ -S "${SOCKET_PATH}" ]]; then
        log_success "${impl_name} server started (PID: ${server_pid})"
        return 0
    else
        log_error "${impl_name} server failed to start"
        kill -9 "${server_pid}" 2>/dev/null || true
        return 1
    fi
}

# Stop a server implementation
stop_server() {
    local impl_name="$1"
    local pid_file="${LOG_DIR}/$(echo ${impl_name} | tr '[:upper:]' '[:lower:]')_server.pid"
    
    if [[ -f "${pid_file}" ]]; then
        local server_pid=$(cat "${pid_file}")
        log "Stopping ${impl_name} server (PID: ${server_pid})..."
        kill -TERM "${server_pid}" 2>/dev/null || true
        sleep 1
        kill -9 "${server_pid}" 2>/dev/null || true
        rm -f "${pid_file}"
        rm -f "${SOCKET_PATH}"
    fi
}

# Run a client test
run_client_test() {
    local client_impl="$1"
    local client_dir="$2"
    local client_cmd="$3"
    local server_impl="$4"
    
    log "Testing ${client_impl} client → ${server_impl} server..."
    
    cd "${client_dir}"
    
    local test_log="${LOG_DIR}/$(echo ${client_impl} | tr '[:upper:]' '[:lower:]')_to_$(echo ${server_impl} | tr '[:upper:]' '[:lower:]')_test.log"
    
    if [[ ${VERBOSE} -eq 1 ]]; then
        gtimeout "${TIMEOUT}" bash -c "${client_cmd}"
    else
        gtimeout "${TIMEOUT}" bash -c "${client_cmd}" > "${test_log}" 2>&1
    fi
    
    local exit_code=$?
    
    if [[ ${exit_code} -eq 0 ]]; then
        log_success "${client_impl} → ${server_impl} communication successful"
        return 0
    elif [[ ${exit_code} -eq 124 ]]; then
        log_error "${client_impl} → ${server_impl} communication timed out"
        return 1
    else
        log_error "${client_impl} → ${server_impl} communication failed (exit code: ${exit_code})"
        if [[ ${VERBOSE} -eq 0 ]]; then
            log "Test log saved to: ${test_log}"
        fi
        return 1
    fi
}

# Main test function
run_cross_platform_tests() {
    local implementations=("Swift" "Rust" "Go" "TypeScript")
    local impl_dirs=("${TEST_DIR}/SwiftUnixSockAPI" "${TEST_DIR}/RustUnixSockAPI" "${TEST_DIR}/GoUnixSocketAPI" "${TEST_DIR}/TypeScriptUnixSockAPI")
    local build_cmds=("swift build" "cargo build" "go build -o bin/server ./cmd/server && go build -o bin/client ./cmd/client" "npm run build")
    local server_cmds=(".build/arm64-apple-macosx/debug/SwiftUnixSockAPI-Server --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "cargo run --bin server -- --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "./bin/server --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "node dist/examples/simple-server.js --socket-path=${SOCKET_PATH} --spec=test-api-spec.json")
    local client_cmds=("swift run SwiftUnixSockAPI-Client --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "cargo run --bin client -- --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "./bin/client --socket-path=${SOCKET_PATH} --spec=test-api-spec.json" "node dist/examples/simple-client.js --socket-path=${SOCKET_PATH} --spec=test-api-spec.json")
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    log "Starting cross-platform Unix socket communication tests..."
    log "Socket path: ${SOCKET_PATH}"
    log "Timeout: ${TIMEOUT}s"
    echo
    
    # Check all implementations
    local available_implementations=()
    local available_dirs=()
    local available_server_cmds=()
    local available_client_cmds=()
    
    for i in "${!implementations[@]}"; do
        if check_implementation "${implementations[i]}" "${impl_dirs[i]}" "${build_cmds[i]}"; then
            available_implementations+=("${implementations[i]}")
            available_dirs+=("${impl_dirs[i]}")
            available_server_cmds+=("${server_cmds[i]}")
            available_client_cmds+=("${client_cmds[i]}")
        fi
    done
    
    if [[ ${#available_implementations[@]} -lt 2 ]]; then
        log_error "Need at least 2 working implementations for cross-platform testing"
        exit 1
    fi
    
    echo
    log "Available implementations: ${available_implementations[*]}"
    echo
    
    # Run cross-platform tests (each implementation as server, others as clients)
    for server_idx in "${!available_implementations[@]}"; do
        local server_impl="${available_implementations[server_idx]}"
        local server_dir="${available_dirs[server_idx]}"
        local server_cmd="${available_server_cmds[server_idx]}"
        
        echo "=== Testing with ${server_impl} as server ==="
        
        if start_server "${server_impl}" "${server_dir}" "${server_cmd}"; then
            sleep 2 # Give server time to stabilize
            
            for client_idx in "${!available_implementations[@]}"; do
                if [[ ${client_idx} -ne ${server_idx} ]]; then
                    local client_impl="${available_implementations[client_idx]}"
                    local client_dir="${available_dirs[client_idx]}"
                    local client_cmd="${available_client_cmds[client_idx]}"
                    
                    ((total_tests++))
                    if run_client_test "${client_impl}" "${client_dir}" "${client_cmd}" "${server_impl}"; then
                        ((passed_tests++))
                    else
                        ((failed_tests++))
                    fi
                fi
            done
            
            stop_server "${server_impl}"
        else
            log_error "Failed to start ${server_impl} server, skipping client tests"
            # Count failed tests for this server
            local num_clients=$((${#available_implementations[@]} - 1))
            total_tests=$((total_tests + num_clients))
            failed_tests=$((failed_tests + num_clients))
        fi
        
        echo
    done
    
    # Print summary
    echo "=========================================="
    echo "CROSS-PLATFORM TEST SUMMARY"
    echo "=========================================="
    echo "Total tests: ${total_tests}"
    echo -e "Passed: ${GREEN}${passed_tests}${NC}"
    echo -e "Failed: ${RED}${failed_tests}${NC}"
    echo
    
    if [[ ${failed_tests} -eq 0 ]]; then
        log_success "All cross-platform tests passed! 🎉"
        echo
        log "All Unix socket implementations can communicate successfully:"
        for impl in "${available_implementations[@]}"; do
            echo "  ✓ ${impl}"
        done
        return 0
    else
        log_error "Some tests failed. Check logs in: ${LOG_DIR}"
        return 1
    fi
}

# Additional utility functions
create_test_examples() {
    log "Creating test example files..."
    
    # Create example API specification
    cat > "${TEST_DIR}/test-api-spec.json" << 'EOF'
{
    "version": "1.0.0",
    "name": "Cross-Platform Test API",
    "channels": {
        "test": {
            "name": "test",
            "description": "Test channel for cross-platform communication",
            "commands": {
                "ping": {
                    "name": "ping",
                    "description": "Simple ping command",
                    "args": {},
                    "response": {
                        "type": "object",
                        "properties": {
                            "pong": {
                                "type": "boolean",
                                "required": true
                            },
                            "timestamp": {
                                "type": "string",
                                "required": true
                            }
                        }
                    }
                },
                "echo": {
                    "name": "echo",
                    "description": "Echo back the input",
                    "args": {
                        "message": {
                            "type": "string",
                            "required": true
                        }
                    },
                    "response": {
                        "type": "object",
                        "properties": {
                            "echo": {
                                "type": "string",
                                "required": true
                            }
                        }
                    }
                }
            }
        }
    }
}
EOF
    
    # Copy spec to each implementation directory for consistent paths
    cp "${TEST_DIR}/test-api-spec.json" "${TEST_DIR}/RustUnixSockAPI/test-api-spec.json" 2>/dev/null || true
    cp "${TEST_DIR}/test-api-spec.json" "${TEST_DIR}/GoUnixSocketAPI/test-api-spec.json" 2>/dev/null || true
    cp "${TEST_DIR}/test-api-spec.json" "${TEST_DIR}/SwiftUnixSockAPI/test-api-spec.json" 2>/dev/null || true
    
    log_success "Test API specification created: test-api-spec.json"
}

# Command line argument handling
case "${1:-test}" in
    "test"|"")
        create_test_examples
        run_cross_platform_tests
        ;;
    "check")
        log "Checking implementations only..."
        check_implementation "Swift" "${TEST_DIR}/SwiftUnixSockAPI" "swift build"
        check_implementation "Rust" "${TEST_DIR}/RustUnixSockAPI" "cargo build"
        check_implementation "Go" "${TEST_DIR}/GoUnixSocketAPI" "go build"
        ;;
    "clean")
        log "Cleaning up test artifacts..."
        cleanup
        rm -rf "${LOG_DIR}"
        rm -f "${TEST_DIR}/test-api-spec.json"
        log_success "Cleanup complete"
        ;;
    "help"|"-h"|"--help")
        echo "Cross-Platform Unix Socket API Test Infrastructure"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  test (default)  Run full cross-platform communication tests"
        echo "  check          Check if all implementations build successfully"
        echo "  clean          Clean up test artifacts and logs"
        echo "  help           Show this help message"
        echo
        echo "Environment variables:"
        echo "  VERBOSE=1      Enable verbose output"
        echo
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  VERBOSE=1 $0 test     # Run tests with verbose output"
        echo "  $0 check              # Just check builds"
        echo "  $0 clean              # Clean up"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
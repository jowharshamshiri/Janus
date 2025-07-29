#!/bin/bash

# UnixSocketAPI Master Test Runner
# Comprehensive test suite orchestrating all test types

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Default settings
VERBOSE=false
RUN_BUILDS=true
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=true
RUN_PERFORMANCE_TESTS=false
RUN_SECURITY_TESTS=true
RUN_STRESS_TESTS=false
IMPLEMENTATIONS="go,rust,swift,typescript"
CONFIG_FILE="${SCRIPT_DIR}/config/unified-test-config.json"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${NC}"
}

show_help() {
    cat << EOF
UnixSocketAPI Master Test Runner

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -c, --config FILE       Test configuration file 
    -i, --implementations   Comma-separated list of implementations to test
    --builds-only          Run only build tests
    --unit-only            Run only unit tests
    --integration-only     Run only integration tests
    --no-builds            Skip build tests
    --no-unit              Skip unit tests  
    --no-integration       Skip integration tests
    --no-security          Skip security tests
    --performance          Include performance tests
    --stress               Include stress tests
    --all                  Run all test categories
    --quick                Run quick test suite (builds + basic integration)
    --ci                   CI mode - appropriate for automated testing

EXAMPLES:
    # Run all basic tests (builds, unit, integration, security)
    $0

    # Quick validation
    $0 --quick

    # Full comprehensive testing
    $0 --all --performance --stress

    # Test specific implementations only
    $0 --implementations go,rust

    # CI/CD pipeline mode
    $0 --ci --performance

    # Integration tests only with verbose output
    $0 --integration-only --verbose

EOF
}

# Parse command line arguments
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
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -i|--implementations)
            IMPLEMENTATIONS="$2"
            shift 2
            ;;
        --builds-only)
            RUN_UNIT_TESTS=false
            RUN_INTEGRATION_TESTS=false
            RUN_SECURITY_TESTS=false
            shift
            ;;
        --unit-only)
            RUN_BUILDS=false
            RUN_INTEGRATION_TESTS=false
            RUN_SECURITY_TESTS=false
            shift
            ;;
        --integration-only)
            RUN_BUILDS=false
            RUN_UNIT_TESTS=false
            RUN_SECURITY_TESTS=false
            shift
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
        --no-security)
            RUN_SECURITY_TESTS=false
            shift
            ;;
        --performance)
            RUN_PERFORMANCE_TESTS=true
            shift
            ;;
        --stress)
            RUN_STRESS_TESTS=true
            shift
            ;;
        --all)
            RUN_BUILDS=true
            RUN_UNIT_TESTS=true
            RUN_INTEGRATION_TESTS=true
            RUN_SECURITY_TESTS=true
            RUN_PERFORMANCE_TESTS=true
            RUN_STRESS_TESTS=true
            shift
            ;;
        --quick)
            RUN_BUILDS=true
            RUN_UNIT_TESTS=false
            RUN_INTEGRATION_TESTS=true
            RUN_SECURITY_TESTS=false
            RUN_PERFORMANCE_TESTS=false
            shift
            ;;
        --ci)
            RUN_BUILDS=true
            RUN_UNIT_TESTS=true
            RUN_INTEGRATION_TESTS=true
            RUN_SECURITY_TESTS=true
            # Performance tests optional for CI
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate configuration
if [[ ! -f "$CONFIG_FILE" ]]; then
    log_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Build test categories
CATEGORIES=""
if [[ "$RUN_BUILDS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}build,"
fi
if [[ "$RUN_UNIT_TESTS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}unit,"
fi
if [[ "$RUN_INTEGRATION_TESTS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}cross_platform,"
fi
if [[ "$RUN_SECURITY_TESTS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}security,"
fi
if [[ "$RUN_PERFORMANCE_TESTS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}performance,"
fi
if [[ "$RUN_STRESS_TESTS" == "true" ]]; then
    CATEGORIES="${CATEGORIES}stress,"
fi

# Remove trailing comma
CATEGORIES="${CATEGORIES%,}"

if [[ -z "$CATEGORIES" ]]; then
    log_error "No test categories selected"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Print configuration
log_section "UnixSocketAPI Comprehensive Test Suite"
echo "Configuration: $CONFIG_FILE"
echo "Implementations: $IMPLEMENTATIONS"
echo "Categories: $CATEGORIES"
echo "Timestamp: $TIMESTAMP"
echo ""

# Build Python command
PYTHON_CMD="python tests/run_comprehensive_tests.py"
PYTHON_CMD="$PYTHON_CMD --config \"$CONFIG_FILE\""
PYTHON_CMD="$PYTHON_CMD --categories \"$CATEGORIES\""
PYTHON_CMD="$PYTHON_CMD --implementations \"$IMPLEMENTATIONS\""

if [[ "$VERBOSE" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --verbose"
fi

# Add performance and security flags
if [[ "$RUN_PERFORMANCE_TESTS" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --performance"
fi
if [[ "$RUN_SECURITY_TESTS" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --security"
fi
if [[ "$RUN_STRESS_TESTS" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --stress"
fi

# Execute comprehensive test suite
log_section "Executing Comprehensive Test Suite"
log_info "Running: $PYTHON_CMD"
echo ""

# Run the tests
set +e  # Don't exit on test failures
eval "$PYTHON_CMD"
EXIT_CODE=$?
set -e

# Check results
if [[ $EXIT_CODE -eq 0 ]]; then
    log_success "All tests passed! ✅"
    echo ""
    log_info "Test logs and reports available in:"
    log_info "  - tests/test_logs/latest/"
    log_info "  - tests/test_reports/latest/"
elif [[ $EXIT_CODE -eq 130 ]]; then
    log_warning "Tests interrupted by user"
else
    log_error "Some tests failed ❌"
    echo ""
    log_info "Check detailed reports in tests/test_reports/ for failure analysis"
fi

echo ""
log_section "Test Suite Complete"
echo "Exit code: $EXIT_CODE"

exit $EXIT_CODE
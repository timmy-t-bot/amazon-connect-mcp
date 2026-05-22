#!/bin/bash
# Test runner script for Amazon Connect MCP
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh unit         # Run unit tests only
#   ./run_tests.sh integration  # Run integration tests only
#   ./run_tests.sh coverage     # Run with coverage report
#   ./run_tests.sh watch        # Run tests in watch mode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TESTS_DIR="${PROJECT_ROOT}/tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

run_unit_tests() {
    print_header "Running Unit Tests"
    
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Install with: pip install pytest"
        exit 1
    fi
    
    cd "${PROJECT_ROOT}"
    
    # Run unit tests
    pytest "${TESTS_DIR}" -v -m "unit" --tb=short "$@"
    
    print_success "Unit tests completed"
}

run_integration_tests() {
    print_header "Running Integration Tests"
    
    cd "${PROJECT_ROOT}"
    
    # Run integration tests (requires AWS credentials)
    pytest "${TESTS_DIR}" -v -m "integration" --tb=short "$@"
    
    print_success "Integration tests completed"
}

run_all_tests() {
    print_header "Running All Tests"
    
    cd "${PROJECT_ROOT}"
    
    pytest "${TESTS_DIR}" -v --tb=short "$@"
    
    print_success "All tests completed"
}

run_coverage() {
    print_header "Running Tests with Coverage"
    
    cd "${PROJECT_ROOT}"
    
    if ! command -v pytest-cov &> /dev/null && ! python -c "import pytest_cov" 2>/dev/null; then
        print_info "pytest-cov not found. Install with: pip install pytest-cov"
        exit 1
    fi
    
    # Run with coverage
    pytest "${TESTS_DIR}" -v --cov=src/amazon_connect_mcp --cov=src/contact_flows --cov-report=term-missing --cov-report=html:htmlcov "$@"
    
    print_success "Coverage report generated in htmlcov/"
}

run_watch_mode() {
    print_header "Running Tests in Watch Mode"
    
    cd "${PROJECT_ROOT}"
    
    if ! command -v ptw &> /dev/null; then
        print_info "pytest-watch not found. Install with: pip install pytest-watch"
        # Fallback to pytest with -f option
        pytest "${TESTS_DIR}" -f -v "$@"
    else
        ptw "${TESTS_DIR}" -v "$@"
    fi
}

run_specific_test() {
    print_header "Running Specific Test: $1"
    
    cd "${PROJECT_ROOT}"
    
    pytest "${TESTS_DIR}/test_$1.py" -v --tb=short "$@"
}

# Main command handler
case "${1:-all}" in
    unit|u)
        shift
        run_unit_tests "$@"
        ;;
    integration|int|i)
        shift
        run_integration_tests "$@"
        ;;
    all|a)
        shift
        run_all_tests "$@"
        ;;
    coverage|cov|c)
        shift
        run_coverage "$@"
        ;;
    watch|w)
        shift
        run_watch_mode "$@"
        ;;
    contact_flows|cf)
        shift
        run_specific_test "contact_flows" "$@"
        ;;
    components|comp)
        shift
        run_specific_test "components" "$@"
        ;;
    server|srv)
        shift
        run_specific_test "server" "$@"
        ;;
    api|bridge)
        shift
        run_specific_test "connect_api_bridge" "$@"
        ;;
    --help|-h)
        echo "Amazon Connect MCP Test Runner"
        echo ""
        echo "Usage: ./run_tests.sh [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  unit, u               Run unit tests only"
        echo "  integration, int, i  Run integration tests"
        echo "  all, a                Run all tests (default)"
        echo "  coverage, cov, c       Run tests with coverage report"
        echo "  watch, w              Run tests in watch mode"
        echo "  contact_flows, cf     Run contact flow tests"
        echo "  components, comp     Run component tests"
        echo "  server, srv          Run server tests"
        echo "  api, bridge          Run API bridge tests"
        echo ""
        echo "Options:"
        echo "  -k PATTERN           Only run tests matching pattern"
        echo "  -x                   Stop on first failure"
        echo "  --lf                 Run last failed tests first"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh                    # Run all tests"
        echo "  ./run_tests.sh unit               # Run unit tests"
        echo "  ./run_tests.sh coverage -k queue   # Coverage for queue tests"
        echo "  ./run_tests.sh unit -x            # Stop on first failure"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run './run_tests.sh --help' for usage information"
        exit 1
        ;;
esac

exit 0

#!/bin/bash

# Exit on any error
set -e

echo "🧪 Entertainment Planner - Test Suite"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "success" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "error" ]; then
        echo -e "${RED}❌ $message${NC}"
    fi
}

# Test 1: Ingest Layer - TimeOut Parser
echo "🔹 Test 1: Ingest Layer - TimeOut Parser"
echo "----------------------------------------"
if cd apps/ingest/tests && python3 test_timeout_parser.py; then
    print_status "success" "Ingest test passed - Parser inserts exactly 3 rows"
else
    print_status "error" "Ingest test failed"
    exit 1
fi
cd ../../..

# Test 2: Search Layer - Search Provider
echo ""
echo "🔹 Test 2: Search Layer - Search Provider"
echo "----------------------------------------"
if cd packages/search/tests && python3 test_search_provider.py; then
    print_status "success" "Search test passed - kNN returns deterministic ordering"
else
    print_status "error" "Search test failed"
    exit 1
fi
cd ../../..

# Test 3: API Layer - Recommendation Endpoint
echo ""
echo "🔹 Test 3: API Layer - Recommendation Endpoint"
echo "----------------------------------------------"
if cd apps/api/tests && python3 test_recommend.py; then
    print_status "success" "API test passed - 3-step route validation"
else
    print_status "error" "API test failed"
    exit 1
fi
cd ../../..

echo ""
echo "🎉 All Tests Passed!"
echo "==================="
print_status "success" "Ingest Layer: Snapshot 3 rows ✓"
print_status "success" "Search Layer: Deterministic order ✓"
print_status "success" "API Layer: 3-step route present ✓"
echo ""
echo "✅ Test suite completed successfully!"

#!/bin/bash

# Exit on any error
set -e

echo "🚀 Entertainment Planner MVP - End-to-End Smoke Test"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "success" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "warning" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    elif [ "$status" = "error" ]; then
        echo -e "${RED}❌ $message${NC}"
    fi
}

print_step() {
    local step=$1
    local message=$2
    echo ""
    echo "🔹 Step $step: $message"
    echo "----------------------------------------"
}

# Step 1: Initialize database
print_step "1" "Initialize database with schema and mock data"
echo "Running: python apps/ingest/db_init.py"
if python3 apps/ingest/db_init.py; then
    print_status "success" "Database initialized successfully"
else
    print_status "error" "Database initialization failed"
    exit 1
fi

# Step 2: Parse TimeOut Bangkok data
print_step "2" "Parse TimeOut Bangkok data (limit: 5)"
echo "Running: python apps/ingest/parsers/timeout_bkk.py --limit 5"
if python3 apps/ingest/parsers/timeout_bkk.py --limit 5; then
    print_status "success" "TimeOut Bangkok data parsed successfully"
else
    print_status "error" "TimeOut Bangkok parsing failed"
    exit 1
fi

# Step 3: Enrich places data
print_step "3" "Enrich places data with external APIs (limit: 5)"
echo "Running: python apps/ingest/enrich/run_enrich.py --limit 5 --city bangkok"
if python3 apps/ingest/enrich/run_enrich.py --limit 5 --city bangkok; then
    print_status "success" "Places data enriched successfully"
else
    print_status "error" "Places enrichment failed"
    exit 1
fi

# Step 4: Normalize data
print_step "4" "Normalize and clean data (limit: 10)"
echo "Running: python apps/ingest/normalize/normalizer.py --limit 10"
if python3 apps/ingest/normalize/normalizer.py --limit 10; then
    print_status "success" "Data normalization completed successfully"
else
    print_status "error" "Data normalization failed"
    exit 1
fi

# Step 5: Build search indices
print_step "5" "Build search indices (FTS5 + embeddings)"
echo "Running: python apps/ingest/index/build_index.py"
if python3 apps/ingest/index/build_index.py; then
    print_status "success" "Search indices built successfully"
else
    print_status "error" "Search index building failed"
    exit 1
fi

# Step 6: Verify data pipeline
print_step "6" "Verify data pipeline results"
echo "Checking database row counts..."

RAW_COUNT=$(sqlite3 raw.db "SELECT COUNT(*) FROM raw_places;" 2>/dev/null || echo "0")
PLACES_COUNT=$(sqlite3 clean.db "SELECT COUNT(*) FROM places;" 2>/dev/null || echo "0")
FTS_COUNT=$(sqlite3 clean.db "SELECT COUNT(*) FROM fts_places;" 2>/dev/null || echo "0")
EMBEDDINGS_COUNT=$(sqlite3 clean.db "SELECT COUNT(*) FROM embeddings;" 2>/dev/null || echo "0")

echo "📊 Data Pipeline Results:"
echo "   Raw places: $RAW_COUNT"
echo "   Clean places: $PLACES_COUNT"
echo "   FTS entries: $FTS_COUNT"
echo "   Embeddings: $EMBEDDINGS_COUNT"

if [ "$PLACES_COUNT" -gt 0 ] && [ "$FTS_COUNT" -gt 0 ]; then
    print_status "success" "Data pipeline verification passed"
else
    print_status "error" "Data pipeline verification failed - insufficient data"
    exit 1
fi

# Step 7: Start API server
print_step "7" "Start API server"
echo "To start the API server, run this command in a separate terminal:"
echo ""
echo "   cd apps/api && python3 main.py"
echo ""
echo "Waiting for API to be available..."

# Wait for API to start (with timeout)
TIMEOUT=30
COUNTER=0
while [ $COUNTER -lt $TIMEOUT ]; do
    if curl -s "http://localhost:8000/api/health" > /dev/null 2>&1; then
        print_status "success" "API server is running"
        break
    fi
    echo -n "."
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $TIMEOUT ]; then
    print_status "warning" "API server not detected. Please start it manually and continue."
    echo ""
    echo "Manual API start command:"
    echo "   cd apps/api && python3 main.py"
    echo ""
    read -p "Press Enter when API is running, or Ctrl+C to exit..."
fi

# Step 8: Test API endpoints
print_step "8" "Test API endpoints"

echo "🔍 Testing /api/health..."
if curl -s "http://localhost:8000/api/health" | grep -q '"ok":true'; then
    print_status "success" "Health endpoint working"
else
    print_status "error" "Health endpoint failed"
    exit 1
fi

echo "🔍 Testing /api/places/recommend..."
RECOMMEND_RESPONSE=$(curl -s "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.7563&lng=100.5018")
if echo "$RECOMMEND_RESPONSE" | grep -q '"routes"'; then
    print_status "success" "Recommendation endpoint working"
    
    # Extract and display route information
    echo ""
    echo "📋 Generated Route:"
    echo "$RECOMMEND_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'routes' in data and data['routes']:
        route = data['routes'][0]
        print(f'   Steps: {route.get(\"steps\", [])}')
        print(f'   Distance: {route.get(\"total_distance_m\", 0)}m')
        print(f'   Fit Score: {route.get(\"fit_score\", 0):.3f}')
        if 'alternatives' in data and data['alternatives']:
            print(f'   Alternatives: {len(data[\"alternatives\"])} available')
    else:
        print('   No routes generated')
except:
    print('   Could not parse route data')
"
else
    print_status "error" "Recommendation endpoint failed"
    exit 1
fi

# Step 9: Test feedback system
print_step "9" "Test feedback system"

echo "📝 Submitting test feedback..."
FEEDBACK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [1,2,3], "useful": true, "note": "Smoke test feedback"}')

if echo "$FEEDBACK_RESPONSE" | grep -q '"message":"Feedback submitted successfully"'; then
    print_status "success" "Feedback system working"
else
    print_status "error" "Feedback system failed"
    exit 1
fi

# Step 10: Final verification
print_step "10" "Final verification"

echo "🔍 Checking feedback storage..."
FEEDBACK_COUNT=$(sqlite3 clean.db "SELECT COUNT(*) FROM feedback;" 2>/dev/null || echo "0")
if [ "$FEEDBACK_COUNT" -gt 0 ]; then
    print_status "success" "Feedback stored successfully ($FEEDBACK_COUNT entries)"
else
    print_status "error" "Feedback not stored"
    exit 1
fi

echo ""
echo "🎉 MVP Smoke Test Complete!"
echo "=========================="
print_status "success" "All systems operational"
echo ""

echo "📊 Final Status:"
echo "   ✅ Database: Initialized and populated"
echo "   ✅ Data Pipeline: Raw → Enriched → Normalized → Indexed"
echo "   ✅ API Server: Running and responding"
echo "   ✅ Core Endpoints: Health, Recommendations, Feedback"
echo "   ✅ Data Storage: Places, FTS, Embeddings, Feedback"
echo ""

echo "🚀 Next Steps:"
echo "   1. API is running at: http://localhost:8000"
echo "   2. API docs available at: http://localhost:8000/docs"
echo "   3. Test UI at: http://localhost:3000 (if running)"
echo ""

echo "💡 Useful Commands:"
echo "   • View places: sqlite3 clean.db 'SELECT id, name FROM places LIMIT 5;'"
echo "   • View feedback: sqlite3 clean.db 'SELECT * FROM feedback;'"
echo "   • Check cache: sqlite3 clean.db 'SELECT COUNT(*) FROM cache_entries;'"
echo ""

print_status "success" "MVP is ready for use!"

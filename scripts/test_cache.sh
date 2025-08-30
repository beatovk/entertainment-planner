#!/bin/bash

echo "🧪 Testing Entertainment Planner API Caching..."
echo ""

# Ensure the database exists
echo "1️⃣ Checking database..."
if [ ! -f "clean.db" ]; then
    echo "   Database not found, initializing..."
    python3 apps/ingest/db_init.py
else
    echo "   Database exists ✓"
fi

echo ""

# Test 1: First call (should be MISS)
echo "2️⃣ First call to /api/places/recommend (expect MISS)..."
echo "📍 Using Bangkok coordinates: lat=13.73, lng=100.52"
echo "🎯 Vibe: lazy, Intents: tom-yum,walk,rooftop"
echo ""

curl -i -s "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.73&lng=100.52" | head -20
echo ""

# Wait a moment
sleep 2

# Test 2: Second call (should be HIT from memory)
echo "3️⃣ Second call to /api/places/recommend (expect HIT from memory)..."
echo ""

curl -i -s "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.73&lng=100.52" | head -20
echo ""

# Test 3: Warmup endpoint
echo "4️⃣ Testing cache warmup endpoint..."
echo ""

curl -i -s "http://localhost:8000/api/cache/warm?city=bangkok&day=2025-09-01&combos=lazy:tom-yum,walk,rooftop|budget:thai-spicy,park,rooftop" | head -20
echo ""

# Test 4: Test with different coordinates (should be MISS)
echo "5️⃣ Testing with different coordinates (expect MISS)..."
echo "📍 Using different coordinates: lat=13.75, lng=100.50"
echo ""

curl -i -s "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.75&lng=100.50" | head -20
echo ""

echo "✅ Cache testing complete!"
echo ""
echo "💡 To restart the API and test persistence:"
echo "   1. Stop the current API process"
echo "   2. Start it again: ./scripts/run_api.sh"
echo "   3. Repeat the same request - should get HIT from SQLite"

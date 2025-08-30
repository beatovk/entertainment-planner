#!/bin/bash

echo "📝 Testing Entertainment Planner Feedback System"
echo ""

# Ensure API is running
echo "🔍 Checking if API is running..."
if ! curl -s "http://localhost:8000/api/health" > /dev/null; then
    echo "❌ API is not running. Please start it first:"
    echo "   ./scripts/run_api.sh"
    exit 1
fi
echo "✅ API is running"
echo ""

# Submit positive feedback
echo "1️⃣ Submitting positive feedback..."
curl -i -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [1,2,3], "useful": true, "note": "Great route for lazy day!"}'
echo ""

# Submit negative feedback
echo "2️⃣ Submitting negative feedback..."
curl -i -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [4,5,6], "useful": false, "note": "Too expensive for budget travelers"}'
echo ""

# Submit feedback without note
echo "3️⃣ Submitting feedback without note..."
curl -i -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [7,8,9], "useful": true}'
echo ""

echo "✅ Feedback tests complete!"
echo ""
echo "💾 To view feedback in database:"
echo "   sqlite3 clean.db 'SELECT * FROM feedback;'"
echo ""
echo "📊 To see feedback summary:"
echo "   sqlite3 clean.db 'SELECT useful, COUNT(*) as count FROM feedback GROUP BY useful;'"
echo ""
echo "🕒 To see recent feedback:"
echo "   sqlite3 clean.db 'SELECT id, created_at, route_json, useful, note FROM feedback ORDER BY created_at DESC LIMIT 5;'"

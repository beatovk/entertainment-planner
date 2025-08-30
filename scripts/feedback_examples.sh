#!/bin/bash

echo "📝 Entertainment Planner Feedback Examples"
echo "=========================================="
echo ""

# Check if API is running
if ! curl -s "http://localhost:8000/api/health" > /dev/null; then
    echo "❌ API is not running. Please start it first:"
    echo "   ./scripts/run_api.sh"
    exit 1
fi

echo "✅ API is running"
echo ""

# Example 1: Positive feedback with note
echo "1️⃣ Example: Positive feedback with detailed note"
curl -s -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [2,5,8], "useful": true, "note": "Perfect lazy day route! Loved the tom yum and rooftop views."}' | jq '.'
echo ""

# Example 2: Negative feedback with note
echo "2️⃣ Example: Negative feedback with improvement suggestion"
curl -s -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [1,4,11], "useful": false, "note": "Route too expensive for budget travelers. Need more affordable options."}' | jq '.'
echo ""

# Example 3: Feedback without note
echo "3️⃣ Example: Simple feedback without note"
curl -s -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [3,6,9], "useful": true}' | jq '.'
echo ""

# Example 4: Feedback for different route
echo "4️⃣ Example: Feedback for scenic route"
curl -s -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [7,10,12], "useful": true, "note": "Beautiful scenic route with great photo opportunities!"}' | jq '.'
echo ""

echo "✅ All feedback examples submitted!"
echo ""
echo "📊 Database Queries Examples:"
echo "=============================="
echo ""

echo "💾 View all feedback:"
echo "   sqlite3 clean.db 'SELECT * FROM feedback;'"
echo ""

echo "📈 Feedback summary by usefulness:"
echo "   sqlite3 clean.db 'SELECT useful, COUNT(*) as count FROM feedback GROUP BY useful;'"
echo ""

echo "🕒 Recent feedback (last 5):"
echo "   sqlite3 clean.db 'SELECT id, created_at, route_json, useful, note FROM feedback ORDER BY created_at DESC LIMIT 5;'"
echo ""

echo "🔍 Search feedback by note content:"
echo "   sqlite3 clean.db \"SELECT * FROM feedback WHERE note LIKE '%lazy%';\""
echo ""

echo "📅 Feedback by date:"
echo "   sqlite3 clean.db \"SELECT DATE(created_at) as date, COUNT(*) as count FROM feedback GROUP BY DATE(created_at);\""
echo ""

echo "🎯 Routes with most feedback:"
echo "   sqlite3 clean.db 'SELECT route_json, COUNT(*) as feedback_count FROM feedback GROUP BY route_json ORDER BY feedback_count DESC;'"
echo ""

echo "💡 To run these queries, copy and paste them into your terminal"
echo "   Make sure you're in the project root directory"

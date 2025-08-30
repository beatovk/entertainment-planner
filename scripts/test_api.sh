#!/bin/bash

echo "🧪 Testing Entertainment Planner API..."
echo ""

# Test health endpoint
echo "1️⃣ Testing /api/health..."
curl -s "http://localhost:8000/api/health" | jq '.'
echo ""

# Test getting a place by ID (assuming ID 1 exists)
echo "2️⃣ Testing /api/places/1..."
curl -s "http://localhost:8000/api/places/1" | jq '.'
echo ""

# Test recommendation endpoint with Bangkok coordinates
echo "3️⃣ Testing /api/places/recommend..."
echo "📍 Using Bangkok coordinates: lat=13.7563, lng=100.5018"
echo "🎯 Vibe: lazy, Intents: tom-yum,walk,rooftop"
echo ""

curl -s "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.7563&lng=100.5018" | jq '.'
echo ""

echo "✅ API testing complete!"
echo ""
echo "💡 To see the full API documentation, visit: http://localhost:8000/docs"

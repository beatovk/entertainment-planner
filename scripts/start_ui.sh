#!/bin/bash

echo "🎨 Starting Entertainment Planner UI..."
echo "📍 UI will be available at: http://localhost:3000"
echo "🔗 API proxy configured to: http://localhost:8000"
echo ""
echo "Make sure the API server is running first:"
echo "  ./scripts/run_api.sh"
echo ""
echo "Press Ctrl+C to stop the UI server"
echo ""

cd apps/ui

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
npm start

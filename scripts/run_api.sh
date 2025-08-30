#!/bin/bash

echo "🚀 Starting Entertainment Planner API..."
echo "📍 API will be available at: http://localhost:8000"
echo "📖 API docs will be at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd apps/api
python main.py

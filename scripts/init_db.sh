#!/bin/bash
set -e

echo "🚀 Initializing Entertainment Planner Databases..."

# Run database initialization
python3 apps/ingest/db_init.py

echo "✅ Database initialization script completed!"

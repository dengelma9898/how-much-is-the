#!/bin/bash

# Preisvergleich Backend Start Script
echo "🚀 Starting Preisvergleich Backend..."

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Usage: cd backend && ./start.sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Start the server
echo "🌐 Starting server on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 
#!/bin/bash

# Legacy start.sh - Verwendung des neuen Python Start-Scripts
echo "🔄 start.sh ist deprecated. Verwende das neue Python Start-Script:"
echo "   python start.py --env local --reload"
echo "   python start.py --env dev"
echo "   python start.py --env prod"
echo ""
echo "🚀 Starte mit Standard-Einstellungen (local environment)..."
echo ""

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "   Usage: cd backend && ./start.sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Verwende das neue Python Start-Script (ARM64-optimiert)
echo "🌐 Starting with new multi-environment system..."

# Für M1 Mac: Nutze explizit ARM64-Architektur
if [[ $(uname -m) == "arm64" ]]; then
    echo "🍎 M1 Mac erkannt - nutze ARM64-Architektur"
    arch -arm64 python3 start.py --env local --reload
else
    python3 start.py --env local --reload
fi 
#!/bin/bash

# Client API Start Script mit Environment-Parameter
# Usage: ./start-client-api.sh [env]
# Example: ./start-client-api.sh prod
#          ./start-client-api.sh dev
#          ./start-client-api.sh (uses 'local' as default)

ENV=${1:-local}
PORT=8001
HOST=0.0.0.0

# Determine environment file (client-specific first)
if [ -f ".env.client" ]; then
    ENV_FILE=".env.client"
    echo "📋 Using client environment: $ENV_FILE"
    # Load client-specific environment
    set -a && source .env.client && set +a
elif [ -f ".env.${ENV}" ]; then
    ENV_FILE=".env.${ENV}"
    echo "📋 Using general environment: $ENV_FILE" 
    set -a && source .env.${ENV} && set +a
else
    echo "⚠️  No environment file found!"
    echo "💡 Create client environment:"
    echo "   cp env.client.example .env.client"
    echo "📝 Then edit .env.client with your settings"
    exit 1
fi

echo "🚀 Starting Preisvergleich Client API..."
echo "📂 Environment: $ENV ($ENV_FILE)"
echo "🌐 Port: $PORT"
echo "🔒 Access Level: READ-ONLY"
echo ""

cd client-api

# Set environment variable for the app to pick up
export APP_ENV=$ENV

# Start the API with ARM64 Python
arch -arm64 python3 -m uvicorn main:app --host $HOST --port $PORT --reload

echo ""
echo "✅ Client API stopped" 
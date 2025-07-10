#!/bin/bash

# Admin API Start Script mit Environment-Parameter
# Usage: ./start-admin-api.sh [env]
# Example: ./start-admin-api.sh prod
#          ./start-admin-api.sh dev
#          ./start-admin-api.sh (uses 'local' as default)

ENV=${1:-local}
PORT=8002
HOST=0.0.0.0

# Determine environment file (admin-specific first)
if [ -f ".env.admin" ]; then
    ENV_FILE=".env.admin"
    echo "📋 Using admin environment: $ENV_FILE"
    # Load admin-specific environment
    set -a && source .env.admin && set +a
elif [ -f ".env.${ENV}" ]; then
    ENV_FILE=".env.${ENV}"
    echo "📋 Using general environment: $ENV_FILE"
    set -a && source .env.${ENV} && set +a
else
    echo "⚠️  No environment file found!"
    echo "💡 Create admin environment:"
    echo "   cp env.admin.example .env.admin"
    echo "📝 Then edit .env.admin with your settings"
    exit 1
fi

echo "🚀 Starting Preisvergleich Admin API..."
echo "📂 Environment: $ENV ($ENV_FILE)"
echo "🌐 Port: $PORT"
echo "🔓 Access Level: READ-WRITE"
echo "⚙️  Features: Scheduler, Crawler, Administration"
echo ""

cd admin-api

# Set environment variable for the app to pick up
export APP_ENV=$ENV

# Start the API with ARM64 Python
arch -arm64 python3 -m uvicorn main:app --host $HOST --port $PORT --reload

echo ""
echo "✅ Admin API stopped" 
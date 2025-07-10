#!/bin/bash

# Universal Start Script für Preisvergleich Split Architecture
# Usage: ./start.sh [api] [env]
# 
# Examples:
#   ./start.sh client           # Start Client API with 'local' env
#   ./start.sh admin            # Start Admin API with 'local' env
#   ./start.sh client prod      # Start Client API with 'prod' env
#   ./start.sh admin dev        # Start Admin API with 'dev' env
#   ./start.sh both             # Start both APIs in background

API=${1:-help}
ENV=${2:-local}

show_help() {
    echo "🚀 Preisvergleich Split Architecture - Start Script"
    echo ""
    echo "Usage: ./start.sh [api] [env]"
    echo ""
    echo "APIs:"
    echo "  client    Start Client API (Port 8001, Read-only)"
    echo "  admin     Start Admin API (Port 8002, Read-write)"
    echo "  both      Start both APIs in background"
    echo ""
    echo "Environments:"
    echo "  local     Use .env.local (default)"
    echo "  dev       Use .env.dev"
    echo "  prod      Use .env.prod"
    echo ""
    echo "Examples:"
    echo "  ./start.sh client           # Client API with local env"
    echo "  ./start.sh admin prod       # Admin API with prod env"
    echo "  ./start.sh both             # Both APIs in background"
    echo ""
}

start_client() {
    echo "🔵 Starting Client API..."
    ./start-client-api.sh $ENV
}

start_admin() {
    echo "🔴 Starting Admin API..."
    ./start-admin-api.sh $ENV
}

start_both() {
    echo "🚀 Starting both APIs in background..."
    echo "🔵 Client API starting on port 8001..."
    ./start-client-api.sh $ENV &
    CLIENT_PID=$!
    
    sleep 2
    
    echo "🔴 Admin API starting on port 8002..."
    ./start-admin-api.sh $ENV &
    ADMIN_PID=$!
    
    echo ""
    echo "✅ Both APIs started!"
    echo "🔵 Client API PID: $CLIENT_PID"
    echo "🔴 Admin API PID: $ADMIN_PID"
    echo ""
    echo "Press Ctrl+C to stop both APIs..."
    
    # Wait for Ctrl+C
    trap "echo ''; echo '🛑 Stopping APIs...'; kill $CLIENT_PID $ADMIN_PID 2>/dev/null; echo '✅ Both APIs stopped'; exit 0" INT
    wait
}

case $API in
    client)
        start_client
        ;;
    admin)
        start_admin
        ;;
    both)
        start_both
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac 
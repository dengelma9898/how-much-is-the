#!/bin/bash

# Start script for Client API (Read-only)
echo "Starting Preisvergleich Client API..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the Client API on port 8001
cd client-api
uvicorn main:app --host 0.0.0.0 --port 8001 --reload 
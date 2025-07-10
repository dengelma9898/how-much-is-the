#!/bin/bash

# Start script for Admin API (Read-write)
echo "Starting Preisvergleich Admin API..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the Admin API on port 8002
cd admin-api
uvicorn main:app --host 0.0.0.0 --port 8002 --reload 
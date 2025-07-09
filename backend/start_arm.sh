#!/bin/bash

# Startet den FastAPI-Server mit ARM-Architektur
echo "🚀 Starte Preisvergleich API Server mit ARM-Architektur..."
echo "Server läuft auf: http://localhost:8000"
echo "Swagger UI: http://localhost:8000/docs"
echo ""

arch -arm64 python3 start.py 
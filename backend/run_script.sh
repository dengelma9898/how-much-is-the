#!/bin/bash

# Hilfsskript zum Starten von Python-Skripten mit ARM-Architektur
# Verwendung: ./run_script.sh script_name.py

if [ $# -eq 0 ]; then
    echo "❌ Kein Skript-Name angegeben!"
    echo "Verwendung: ./run_script.sh <script_name.py>"
    echo "Beispiel: ./run_script.sh test_aldi_crawler.py"
    exit 1
fi

SCRIPT_NAME=$1

if [ ! -f "$SCRIPT_NAME" ]; then
    echo "❌ Skript '$SCRIPT_NAME' nicht gefunden!"
    exit 1
fi

echo "🚀 Starte '$SCRIPT_NAME' mit ARM-Architektur..."
echo "Kommando: arch -arm64 python3 $SCRIPT_NAME"
echo ""

arch -arm64 python3 "$SCRIPT_NAME" 
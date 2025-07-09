# Preisvergleich API Backend

Eine FastAPI-basierte Backend-API für die Preisvergleich-App.

## Features

- 🔍 Produktsuche in deutschen Supermärkten
- 🏪 Unterstützung für REWE, EDEKA, Lidl, ALDI, Kaufland, dm, Rossmann
- 📍 Regionale Preisunterschiede basierend auf Postleitzahl
- 🕷️ Firecrawl-Integration für Web-Scraping (vorbereitet)
- 📚 Automatische OpenAPI/Swagger-Dokumentation
- 🧪 Mock-Daten für Entwicklung und Tests

## Installation

1. Python 3.8+ installieren
2. Dependencies installieren:
```bash
pip install -r requirements.txt
```

3. Environment-Variablen konfigurieren:
```bash
cp .env.example .env
# .env bearbeiten und API-Keys eintragen
```

## Entwicklung

Server starten:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Die API ist dann verfügbar unter:
- http://localhost:8000 - Root endpoint
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

## API-Endpunkte

### Health Check
- `GET /api/v1/health` - API-Status prüfen

### Produktsuche
- `POST /api/v1/search` - Produkte suchen
- `GET /api/v1/stores` - Verfügbare Supermärkte

### Beispiel-Request
```json
{
  "query": "Oatly",
  "postal_code": "10115"
}
```

## Tests

Tests ausführen:
```bash
pytest
```

## Python-Skripte starten (Apple Silicon M1/M2 Macs)

⚠️ **WICHTIG**: Auf Apple Silicon Macs müssen Python-Skripte mit ARM-Architektur gestartet werden:

### Direkt mit arch-Kommando:
```bash
arch -arm64 python3 script_name.py
```

### Mit dem Hilfsskript:
```bash
./run_script.sh script_name.py
```

### Beispiele:
```bash
# Test-Skripte ausführen
arch -arm64 python3 test_aldi_crawler.py
arch -arm64 python3 test_lidl_crawler.py

# Oder mit Hilfsskript
./run_script.sh test_aldi_crawler.py
./run_script.sh test_lidl_crawler.py

# Server starten
arch -arm64 python3 start.py
```

**Warum?** Die installierten Python-Pakete (pydantic, etc.) sind für ARM64 kompiliert, aber das Standard-Python verwendet x86_64, was zu Import-Fehlern führt.

## Projektstruktur

```
backend/
├── app/
│   ├── core/          # Konfiguration
│   ├── models/        # Pydantic-Modelle
│   ├── routers/       # API-Router
│   ├── services/      # Business Logic
│   └── main.py        # FastAPI App
├── requirements.txt
└── README.md
```

## Nächste Schritte

1. Firecrawl-Integration implementieren
2. Echte Supermarkt-Websites crawlen
3. Datenbank für Caching hinzufügen
4. Rate Limiting implementieren
5. Authentifizierung hinzufügen 
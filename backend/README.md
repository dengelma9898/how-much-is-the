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
# API Testing Guide 🧪

Dieser Guide erklärt, wie du das Preisvergleich-Backend mit verschiedenen Tools testen kannst.

## 📋 Verfügbare Test-Tools

### 1. HTTP-Client-Datei (VS Code)
- **Datei:** `api_test.http`
- **Tool:** VS Code REST Client Extension
- **Ideal für:** Interaktive Tests, Entwicklung

### 2. Bash-Test-Skript (Terminal)
- **Datei:** `test_api.sh`
- **Tool:** curl + jq
- **Ideal für:** Automatisierte Tests, CI/CD

### 3. Swagger UI (Browser)
- **URL:** http://127.0.0.1:8000/docs
- **Ideal für:** API-Exploration, Dokumentation

## 🚀 Quick Start

### 1. Backend starten
```bash
# Terminal 1: Backend starten
arch -arm64 python3 start.py --env local --reload
```

### 2. Tests ausführen
```bash
# Terminal 2: API-Tests
./test_api.sh health     # Schneller Health-Check
./test_api.sh all        # Alle Tests
```

## 🔧 VS Code HTTP Client Setup

### Installation
1. Öffne VS Code
2. Installiere die Extension: **"REST Client"** von Huachao Mao
3. Öffne die Datei `api_test.http`

### Verwendung
1. **Einzelne Requests:** Klicke "Send Request" über jeder Anfrage
2. **Variable anpassen:** Ändere `@baseUrl` falls nötig
3. **Parameter ändern:** Passe Query-Parameter oder JSON-Body an

### Beispiel-Workflow
```http
### 1. Health Check
GET {{baseUrl}}/api/v1/health

### 2. Stores auflisten
GET {{baseUrl}}/api/v1/stores

### 3. Manueller Crawl
POST {{baseUrl}}/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115

### 4. Crawl-Status prüfen (verwende crawl_id aus Response)
GET {{baseUrl}}/api/v1/admin/crawl/status/your-crawl-id-here
```

## 🖥️ Terminal-basierte Tests

### Voraussetzungen
```bash
# curl (meist vorinstalliert)
curl --version

# jq für JSON-Formatierung
brew install jq
```

### Skript-Verwendung
```bash
# Alle Tests
./test_api.sh

# Spezifische Test-Kategorien
./test_api.sh health        # Health & Info
./test_api.sh search        # Suchfunktionen
./test_api.sh admin         # Admin-Endpoints
./test_api.sh crawl         # Crawling-System
./test_api.sh errors        # Error-Handling
./test_api.sh performance   # Performance-Tests
```

### Beispiel-Output
```bash
🚀 Preisvergleich Backend API Tests
Base URL: http://127.0.0.1:8000
Test PLZ: 10115

=== HEALTH & INFO TESTS ===
▶ API Root
GET /
{
  "app": "Preisvergleich API",
  "version": "1.0.0",
  "status": "running"
}
✅ Status: 200
```

## 📊 API-Endpoints Übersicht

### Health & Info
| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | API-Informationen |
| `/api/v1/health` | GET | Health Check |
| `/api/v1/stores` | GET | Verfügbare Stores |

### Suche
| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/v1/search/database` | GET | Datenbanksuche |
| `/api/v1/search` | POST | Vollständige Suche |

### Admin & Crawling
| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/v1/admin/system/overview` | GET | System-Dashboard |
| `/api/v1/admin/crawl/status/overview` | GET | Crawl-Dashboard |
| `/api/v1/admin/crawl/trigger` | POST | Manueller Crawl |
| `/api/v1/admin/crawl/status/{id}` | GET | Crawl-Status |
| `/api/v1/admin/crawl/{id}` | DELETE | Crawl abbrechen |
| `/api/v1/admin/crawl/store/{store}/status` | GET | Store-Status |

## 🧪 Test-Szenarien

### 1. Grundfunktionen testen
```bash
# Health Check
curl http://127.0.0.1:8000/api/v1/health

# Stores laden
curl http://127.0.0.1:8000/api/v1/stores

# Datenbank-Suche
curl "http://127.0.0.1:8000/api/v1/search/database?query=Milch&postal_code=10115"
```

### 2. Manuellen Crawl testen
```bash
# Crawl starten
curl -X POST "http://127.0.0.1:8000/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115"

# Status prüfen (verwende crawl_id aus Response)
curl "http://127.0.0.1:8000/api/v1/admin/crawl/status/YOUR_CRAWL_ID"

# Store-Status
curl "http://127.0.0.1:8000/api/v1/admin/crawl/store/Lidl/status"
```

### 3. Rate Limiting testen
```bash
# Zwei schnelle Crawls → Zweiter sollte 429 zurückgeben
curl -X POST "http://127.0.0.1:8000/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115"
curl -X POST "http://127.0.0.1:8000/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115"
```

### 4. Error Handling testen
```bash
# Ungültiger Store
curl -X POST "http://127.0.0.1:8000/api/v1/admin/crawl/trigger?store_name=InvalidStore&postal_code=10115"

# Fehlende Parameter
curl -X POST "http://127.0.0.1:8000/api/v1/admin/crawl/trigger"

# 404 Test
curl "http://127.0.0.1:8000/api/v1/nonexistent"
```

## 🔍 Erwartete Responses

### Erfolgreiche Responses

#### Health Check
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

#### Crawl Start
```json
{
  "crawl_id": "12345678-1234-5678-9abc-123456789abc",
  "message": "Crawl für Lidl gestartet",
  "store_name": "Lidl",
  "postal_code": "10115",
  "status": "PENDING"
}
```

#### Suchergebnisse
```json
{
  "results": [
    {
      "id": 1,
      "name": "Bio Vollmilch",
      "price": 1.29,
      "store_name": "Lidl",
      "availability": true
    }
  ],
  "total": 1,
  "query": "Milch",
  "postal_code": "10115"
}
```

### Error Responses

#### Rate Limited (429)
```json
{
  "detail": "Rate limit exceeded. Please wait 5 minutes between crawls for the same store."
}
```

#### Crawl Conflict (409)
```json
{
  "detail": "Crawl already running for store Lidl"
}
```

#### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["query", "postal_code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 🐛 Troubleshooting

### Backend nicht erreichbar
```bash
# Prüfe ob Backend läuft
curl -s http://127.0.0.1:8000/api/v1/health || echo "Backend offline"

# Backend starten
arch -arm64 python3 start.py --env local --reload
```

### jq nicht gefunden
```bash
# macOS
brew install jq

# Alternative: Tests ohne jq
curl -s http://127.0.0.1:8000/api/v1/health
```

### Permission Denied (test_api.sh)
```bash
# Ausführungsrechte setzen
chmod +x test_api.sh
```

### HTTP 500 Errors
```bash
# Backend-Logs prüfen
# Logs erscheinen im Terminal wo Backend läuft

# Datenbank-Status prüfen
curl http://127.0.0.1:8000/api/v1/admin/system/overview
```

## 🎯 Tipps & Best Practices

### Entwicklung
1. **Starte mit Health Check** um sicherzustellen, dass Backend läuft
2. **Nutze System Overview** für vollständige Systeminfo
3. **Verwende Crawl-IDs** aus Responses für Status-Tracking
4. **Teste Rate Limiting** um Limits zu verstehen

### Testing
1. **Automatisierte Tests:** Nutze `test_api.sh all` für komplette Testsuite
2. **Interaktive Tests:** Nutze VS Code HTTP Client für experimentieren
3. **Performance:** Verwende mehrere gleichzeitige Requests für Load-Testing
4. **Monitoring:** Verwende Admin-Endpoints für Real-Time-Monitoring

### Produktion
1. **Base URL anpassen** für verschiedene Umgebungen
2. **API-Keys verwenden** falls Authentication implementiert
3. **Error Handling** in Client-Code implementieren
4. **Rate Limits respektieren** (5 Min zwischen Crawls pro Store)

## 📚 Weiterführende Links

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json
- **Backend Dokumentation:** `README_DATABASE.md`
- **Manual Crawling Guide:** `README_MANUAL_CRAWLING_OPTIMIZATION.md`

---

**💡 Tipp:** Installiere die VS Code REST Client Extension für die beste Entwicklererfahrung beim API-Testing! 
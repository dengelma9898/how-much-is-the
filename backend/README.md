# 🚀 Preisvergleich Split Backend Architecture

Eine sichere, skalierbare FastAPI-basierte Backend-Architektur mit getrennten Client- und Admin-APIs.

## 🏗️ Architektur-Übersicht

Das Backend ist in eine **Split-Architektur** aufgeteilt:

- **🔵 Client API** (Port 8001): Read-only Zugriff für mobile Apps/Web-Clients
- **🔴 Admin API** (Port 8002): Read-write Zugriff für Administration und Crawler
- **📦 Shared Module**: Gemeinsame Models, Core und Services

### Sicherheitsvorteile
- ✅ **Principle of Least Privilege**: Client API hat minimale Berechtigungen
- ✅ **Attack Surface Reduction**: Admin-Funktionen isoliert
- ✅ **Database Security**: Separate Read-only vs. Read-write User

## 🚀 Quick Start

### 1. Environment Setup

#### Option A: Automatisches Setup (Empfohlen)
```bash
# Erstelle separate Client & Admin Environment-Dateien
./setup-env.sh
```

#### Option B: Manuelles Setup
```bash
# Client API Environment (Read-only)
cp env.client.example .env.client
# Bearbeite .env.client mit Client-spezifischen Einstellungen

# Admin API Environment (Full access)
cp env.admin.example .env.admin  
# Bearbeite .env.admin mit Admin-spezifischen Einstellungen
```

### 2. Database User Setup (einmalig)
```bash
# PostgreSQL Database-User für Split-Architektur erstellen
psql -U your_user -d preisvergleich_dev -f setup_database_users.sql
```

### 3. APIs starten

#### Option A: Einzelne APIs
```bash
# Client API (Read-only, Port 8001)
./start-client-api.sh [env]

# Admin API (Read-write, Port 8002)  
./start-admin-api.sh [env]
```

#### Option B: Universal Script
```bash
# Hilfe anzeigen
./start.sh

# Client API starten
./start.sh client local

# Admin API starten
./start.sh admin prod

# Beide APIs gleichzeitig
./start.sh both
```

### 4. Environment-Konfiguration

#### Separate Environment-Dateien (Empfohlen)
| API | Datei | Beschreibung | Berechtigungen |
|-----|-------|--------------|----------------|
| Client | `.env.client` | Client API Konfiguration | READ-ONLY |
| Admin | `.env.admin` | Admin API Konfiguration | READ-WRITE |

#### Legacy Environment-Parameter
| Environment | Datei | Beschreibung |
|-------------|-------|--------------|
| `local` | `.env.local` | Lokale Entwicklung |
| `dev` | `.env.dev` | Development Server |
| `prod` | `.env.prod` | Production |

**Beispiele:**
```bash
# Mit separaten Environment-Dateien (empfohlen)
./start-client-api.sh                 # Nutzt .env.client
./start-admin-api.sh                  # Nutzt .env.admin

# Mit Legacy Environment-Parameter
./start-client-api.sh dev              # Nutzt .env.dev
./start.sh admin prod                  # Admin API mit .env.prod
```

## 📱 API-Endpunkte

### Client API (Port 8001) - Read-only
```
GET  /api/v1/health      # Health Check
POST /api/v1/search      # Produktsuche
GET  /api/v1/stores      # Verfügbare Stores
```

### Admin API (Port 8002) - Read-write
```
GET  /api/v1/health              # Admin Health Check
GET  /api/v1/admin/status        # System Status
POST /api/v1/admin/crawl/start   # Crawler starten
GET  /api/v1/admin/crawl/status  # Crawler Status
POST /api/v1/admin/cleanup       # Cleanup ausführen
```

## 🗄️ Database-Konfiguration

### Separate Database-User
- **`preisvergleich_readonly`**: Nur SELECT-Rechte (Client API)
- **`preisvergleich_admin`**: Vollzugriff (Admin API)

### Environment-Variablen
```bash
# Client API (.env.client)
DATABASE_URL_READONLY=postgresql+asyncpg://preisvergleich_readonly:password@localhost:5432/preisvergleich_dev

# Admin API (.env.admin)  
DATABASE_URL=postgresql+asyncpg://preisvergleich_admin:password@localhost:5432/preisvergleich_dev
```

## 📱 Mobile App Integration

### Android
```kotlin
// NetworkModule.kt
.baseUrl("http://10.0.2.2:8001/") // Client API
```

### iOS
```swift
// APIService.swift
private let baseURL = "http://localhost:8001/api/v1" // Client API
```

## 🧪 Testing

### Test-Struktur
```
tests/
├── integration/          # API & Database Tests
│   ├── test_api_integration.py
│   ├── test_db_connection.py
│   └── test_api.sh      # HTTP API Tests
├── crawlers/            # Crawler-spezifische Tests
│   ├── test_aldi_crawler.py
│   ├── test_lidl_crawler.py
│   └── test_*.py
├── conftest.py         # Pytest-Konfiguration
└── __init__.py
```

### Test-Dependencies installieren
```bash
# Test-Abhängigkeiten installieren
arch -arm64 pip install -r requirements-test.txt
```

### Tests ausführen
```bash
# Test-Runner verwenden (empfohlen)
./run-tests.sh help                    # Hilfe anzeigen
./run-tests.sh                         # Alle Tests
./run-tests.sh integration             # Nur Integration Tests
./run-tests.sh crawlers                # Nur Crawler Tests
./run-tests.sh fast                    # Schnelle Tests

# Direkter pytest-Aufruf
arch -arm64 python3 -m pytest tests/                    # Alle Tests
arch -arm64 python3 -m pytest tests/integration/       # Integration Tests
arch -arm64 python3 -m pytest tests/crawlers/ -k lidl  # Nur Lidl Tests
```

### HTTP API Tests
```bash
# Vollständige API-Tests (erst APIs starten!)
cd tests/integration && ./test_api.sh
```

### Interactive HTTP Testing
```bash
# VS Code REST Client Extension verwenden (empfohlen)
# Öffne eine der folgenden Dateien:
backend/client_api_test.http    # 31 Tests für Client API (Port 8000)
backend/admin_api_test.http     # 48 Tests für Admin API (Port 8001)
```

**Test-Dateien:**
- `client_api_test.http` - Such- und Read-Only-Endpunkte
- `admin_api_test.http` - Crawling, Cleanup und System-Management
- Verwendung: VS Code → "REST Client" Extension → "Send Request" klicken

### Manual API Testing
```bash
# Health Checks
curl http://localhost:8000/api/v1/health  # Client API
curl http://localhost:8001/api/v1/health  # Admin API

# Produktsuche (Client API)
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Milch", "postal_code": "10115"}'

# System Status (Admin API)
curl http://localhost:8001/api/v1/admin/status
```

## 🍎 Apple Silicon Support

Alle Scripts nutzen automatisch ARM64-Architektur:
```bash
arch -arm64 python3 -m uvicorn main:app --port 8001
```

## 📁 Projektstruktur

```
backend/
├── client-api/           # Client API (Read-only)
│   ├── main.py
│   ├── routers/
│   └── requirements.txt
├── admin-api/            # Admin API (Read-write) 
│   ├── main.py
│   ├── routers/
│   ├── services/
│   └── requirements.txt
├── shared/               # Gemeinsame Module
│   ├── core/
│   ├── models/
│   └── services/
├── start.sh              # Universal Start Script
├── start-client-api.sh   # Client API Script
├── start-admin-api.sh    # Admin API Script
└── setup_database_users.sql
```

## 🚀 Production Deployment

### Docker Compose
```yaml
services:
  client-api:
    build: ./client-api
    ports: ["8001:8001"]
    environment:
      - DATABASE_URL_READONLY=postgresql://readonly@db/preisvergleich
    networks: [public]

  admin-api:
    build: ./admin-api
    ports: ["8002:8002"] 
    environment:
      - DATABASE_URL=postgresql://admin@db/preisvergleich
    networks: [internal]  # Nur intern
```

### Nginx Load Balancer
```nginx
upstream client_api { server localhost:8001; }
upstream admin_api { server localhost:8002; }

server {
    location /api/v1/search { proxy_pass http://client_api; }
    location /api/v1/stores { proxy_pass http://client_api; }
    
    location /api/v1/admin {
        proxy_pass http://admin_api;
        allow 10.0.0.0/8;  # Nur internes Netzwerk
        deny all;
    }
}
```

## 📚 Dokumentation

- **API-Dokumentation**: 
  - Client API: http://localhost:8001/docs
  - Admin API: http://localhost:8002/docs
- **Architektur-Details**: `README_SPLIT_ARCHITECTURE.md`
- **Migration-Status**: `MIGRATION_STATUS.md`

## 🔧 Features

- 🔍 **Produktsuche** in deutschen Supermärkten
- 🏪 **Multi-Store Support**: Lidl, ALDI (geplant)
- 📍 **Regionale Preise** basierend auf Postleitzahl
- 🕷️ **Intelligent Crawling** mit Scheduler
- 🛡️ **Sichere Architektur** mit Berechtigungs-Trennung
- 📊 **Admin Dashboard** für Monitoring und Kontrolle

---

**🎉 Die Split Backend Architecture ist produktionsbereit und bietet eine sichere, skalierbare Basis!** 
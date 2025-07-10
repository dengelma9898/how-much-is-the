# Split Backend Architecture

## 🏗️ Architektur-Übersicht

Das Backend wurde aus Sicherheitsgründen in **zwei separate Anwendungen** aufgeteilt:

### 🔒 **Client API** (Read-only)
- **Port**: 8001
- **Zweck**: Endpunkte für mobile Apps und Web-Clients
- **Berechtigungen**: Nur Lesezugriff auf die Datenbank
- **Endpoints**:
  - `GET /api/v1/health` - Health Check
  - `POST /api/v1/search` - Produktsuche
  - `GET /api/v1/stores` - Store-Liste

### ⚙️ **Admin API** (Read-write)
- **Port**: 8002
- **Zweck**: Administration, Crawler-Management, Scheduler
- **Berechtigungen**: Voll-Zugriff auf die Datenbank
- **Endpoints**:
  - `GET /api/v1/health` - Admin Health Check
  - `POST /api/v1/admin/crawl/trigger` - Crawler starten
  - `GET /api/v1/admin/system/overview` - System-Status
  - `POST /api/v1/admin/scheduler/start` - Scheduler starten
  - Alle anderen Admin-Funktionen

## 🔐 Sicherheitsvorteile

### **Principle of Least Privilege**
- Client API hat nur minimale Berechtigungen
- Admin API läuft isoliert und kann intern beschränkt werden

### **Attack Surface Reduction**
- Kompromittierung der Client API gefährdet nicht Admin-Funktionen
- Admin API kann über VPN/Firewall zusätzlich geschützt werden

### **Separate Authentication**
- Verschiedene Auth-Mechanismen möglich
- Client API kann öffentlich, Admin API kann geschützt sein

## 📁 Verzeichnisstruktur

```
backend/
├── shared/                     # Geteilte Komponenten
│   ├── models/                # Database + Pydantic Models
│   ├── core/                  # Database, Config
│   └── services/              # Gemeinsame Services
│
├── client-api/                # Read-only API
│   ├── main.py               # FastAPI App
│   ├── routers/
│   │   ├── search.py        # Produktsuche
│   │   └── health.py        # Health Check
│   └── requirements.txt      # Minimal Dependencies
│
└── admin-api/                 # Read-write API
    ├── main.py               # FastAPI App
    ├── routers/
    │   ├── admin.py         # Admin Endpoints
    │   └── health.py        # Admin Health
    ├── services/            # Crawler, Scheduler, etc.
    └── requirements.txt      # Full Dependencies
```

## 🚀 Starten der APIs

### **Beide APIs parallel starten:**
```bash
# Terminal 1 - Client API
cd backend
./start-client-api.sh

# Terminal 2 - Admin API  
cd backend
./start-admin-api.sh
```

### **Einzeln starten:**
```bash
# Client API (Port 8001)
cd backend/client-api
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Admin API (Port 8002)
cd backend/admin-api
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## 🔧 Datenbank-Konfiguration

### **Separate Database-Verbindungen**

Die neue Architektur unterstützt separate Database-Verbindungen:

```python
# Read-write (Admin API)
engine_rw = create_async_engine(settings.database_url)

# Read-only (Client API)
engine_ro = create_async_engine(
    getattr(settings, 'database_url_readonly', settings.database_url)
)
```

### **Umgebungsvariablen**

```bash
# Standard Database URL (Read-write)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/preisvergleich_dev

# Optional: Separate Read-only URL
DATABASE_URL_READONLY=postgresql+asyncpg://readonly_user:password@localhost:5432/preisvergleich_dev

# Optional: Separate CORS für Admin API
ADMIN_CORS_ORIGINS=["http://localhost:3000"]
```

## 📊 API Dokumentation

- **Client API**: http://localhost:8001/docs
- **Admin API**: http://localhost:8002/docs

## 🔄 Migration von der alten Architektur

### **Für Client-Anwendungen:**
- **Endpoint-URLs aktualisieren**: `localhost:8000` → `localhost:8001`
- **Funktionalität bleibt gleich**: Alle Search-Endpoints unverändert

### **Für Admin-Tools:**
- **Endpoint-URLs aktualisieren**: `localhost:8000` → `localhost:8002`
- **Erweiterte Admin-Features**: Zusätzliche Sicherheits-Headers möglich

## 🛡️ Produktions-Deployment

### **Empfohlene Konfiguration:**
```yaml
# docker-compose.yml
services:
  client-api:
    build: ./client-api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL_READONLY=postgresql://readonly_user@db/preisvergleich
    networks:
      - public

  admin-api:
    build: ./admin-api
    ports:
      - "8002:8002"    # Nur intern zugänglich
    environment:
      - DATABASE_URL=postgresql://admin_user@db/preisvergleich
    networks:
      - internal
```

### **Firewall-Regeln:**
- **Port 8001** (Client API): Öffentlich zugänglich
- **Port 8002** (Admin API): Nur VPN/intern zugänglich

## 🧪 Tests

Die bestehenden Tests müssen auf die neue Architektur angepasst werden:

```bash
# Client API Tests
cd backend/client-api
python -m pytest tests/

# Admin API Tests  
cd backend/admin-api
python -m pytest tests/
```

## ⚡ Performance

### **Vorteile:**
- **Separate Skalierung**: Client API kann häufiger deployed werden
- **Resource Optimization**: Verschiedene Ressourcen-Anforderungen
- **Caching**: Client API kann aggressiver gecacht werden

### **Load Balancing:**
```nginx
# nginx.conf
upstream client_api {
    server localhost:8001;
}

upstream admin_api {
    server localhost:8002;
}

server {
    location /api/v1/search {
        proxy_pass http://client_api;
    }
    
    location /api/v1/admin {
        proxy_pass http://admin_api;
        # Zusätzliche Sicherheits-Header
        allow 10.0.0.0/8;
        deny all;
    }
}
```

## 🔍 Monitoring

### **Health Checks:**
- **Client API**: `GET http://localhost:8001/api/v1/health`
- **Admin API**: `GET http://localhost:8002/api/v1/health`

### **Logging:**
Beide APIs loggen mit unterschiedlichen Prefixen:
- `[CLIENT-API]` für Client-Operationen
- `[ADMIN-API]` für Admin-Operationen

## 📈 Nächste Schritte

1. **Authentication hinzufügen**: JWT für Admin API
2. **Rate Limiting**: Separate Limits für beide APIs
3. **Monitoring**: Separate Metrics und Alerting
4. **Database Users**: Echte Read-only PostgreSQL User
5. **Container Images**: Separate Docker Images für Production 
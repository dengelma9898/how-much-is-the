# 🚀 Quick Start Guide - Split Backend Architecture

## ⚡ **Sofort loslegen - Beide APIs starten**

### **1. Client API starten (Port 8001)**
```bash
cd backend/client-api
arch -arm64 python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
**Verfügbare Endpoints:**
- `GET http://localhost:8001/api/v1/health` - Health Check
- `POST http://localhost:8001/api/v1/search` - Produktsuche
- `GET http://localhost:8001/api/v1/stores` - Store-Liste
- `GET http://localhost:8001/docs` - API Dokumentation

### **2. Admin API starten (Port 8002)**
```bash
cd backend/admin-api  
arch -arm64 python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```
**Verfügbare Endpoints:**
- `GET http://localhost:8002/api/v1/health` - Admin Health Check
- `GET http://localhost:8002/api/v1/admin/system/overview` - System Status
- `POST http://localhost:8002/api/v1/admin/crawl/trigger` - Crawler starten
- `GET http://localhost:8002/docs` - Admin API Dokumentation

## 🧪 **Schnelltests**

### **Health Checks:**
```bash
# Client API (sollte "read-only" zeigen)
curl http://localhost:8001/api/v1/health

# Admin API (sollte "read-write" + Scheduler Info zeigen)  
curl http://localhost:8002/api/v1/health
```

### **Funktionalitätstests:**
```bash
# Stores abrufen (Client API)
curl http://localhost:8001/api/v1/stores

# System Overview (Admin API)
curl http://localhost:8002/api/v1/admin/system/overview

# Produktsuche testen (Client API)
curl -X POST http://localhost:8001/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Milch", "postal_code": "10115"}'
```

## 📱 **Mobile App Updates**

### **Android (ApiService.kt):**
```kotlin
// Ändere BASE_URL von Port 8000 zu 8001
const val BASE_URL = "http://localhost:8001/api/v1/"
// oder für Emulator:
const val BASE_URL = "http://10.0.2.2:8001/api/v1/"
```

### **iOS (APIService.swift):**
```swift
// Ändere baseURL von Port 8000 zu 8001
let baseURL = "http://localhost:8001/api/v1/"
// oder für Simulator:
let baseURL = "http://127.0.0.1:8001/api/v1/"
```

## 🔧 **Development Workflow**

### **Parallele Entwicklung:**
```bash
# Terminal 1: Client API (für Mobile App Development)
cd backend/client-api && arch -arm64 python3 -m uvicorn main:app --port 8001 --reload

# Terminal 2: Admin API (für Crawler/Admin Development)  
cd backend/admin-api && arch -arm64 python3 -m uvicorn main:app --port 8002 --reload
```

### **Nur Client API für App-Development:**
```bash
# Wenn nur Mobile App entwickelt wird
cd backend/client-api
arch -arm64 python3 -m uvicorn main:app --port 8001 --reload
```

## 🛡️ **Sicherheitsfeatures**

### **Erreichte Sicherheitsverbesserungen:**
- ✅ **Principle of Least Privilege**: Client API hat nur Lesezugriff
- ✅ **Attack Surface Reduction**: Admin-Funktionen isoliert  
- ✅ **Separate Ports**: Client (8001) vs Admin (8002)
- ✅ **Database Isolation**: Read-only vs Read-write Verbindungen
- ✅ **Clear Boundaries**: Keine Admin-Funktionen in Client API

### **Produktions-Setup (Empfehlung):**
```yaml
# docker-compose.yml
services:
  client-api:
    ports: ["8001:8001"]
    networks: [public]           # Öffentlich zugänglich
    
  admin-api:
    ports: ["8002:8002"] 
    networks: [internal]         # Nur intern/VPN
```

## 📊 **Monitoring Commands**

### **Prozess-Monitoring:**
```bash
# API-Prozesse finden
ps aux | grep uvicorn

# Ports überprüfen
lsof -i :8001  # Client API
lsof -i :8002  # Admin API

# Logs verfolgen
tail -f ../client-api.log
tail -f ../admin-api.log
```

### **Performance Testing:**
```bash
# Load Test Client API
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8001/api/v1/health

# Stress Test Search Endpoint
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "postal_code": "10115"}' &
done
```

## 🔄 **Migration Checklist für bestehende Setups**

### **Für Client-Apps:**
- [ ] Android: BASE_URL von `:8000` zu `:8001` ändern
- [ ] iOS: baseURL von `:8000` zu `:8001` ändern
- [ ] Funktionalität testen: Search, Stores, Health
- [ ] **Keine anderen Änderungen nötig** - API bleibt gleich!

### **Für Admin-Tools:**
- [ ] Admin-URLs von `:8000` zu `:8002` ändern  
- [ ] Admin-Endpoints testen: `/admin/*`
- [ ] Crawler-Funktionalität prüfen
- [ ] Scheduler-Status überprüfen

### **Für CI/CD Pipelines:**
- [ ] Zwei separate Services deployen
- [ ] Port-Mappings aktualisieren: 8001 + 8002
- [ ] Health Checks für beide Ports
- [ ] Environment Variables für beide APIs

## 🎯 **Next Steps**

1. **Sofort**: Mobile Apps auf Port 8001 umstellen
2. **Diese Woche**: Admin-Tools auf Port 8002 testen
3. **Nächste Woche**: Produktions-Deployment vorbereiten
4. **Later**: JWT Auth für Admin API, Rate Limiting, Monitoring

---

## 📚 **Weitere Dokumentation**

- `README_SPLIT_ARCHITECTURE.md` - Vollständige Architektur-Dokumentation
- `MIGRATION_STATUS.md` - Aktueller Status und abgeschlossene Aufgaben
- `/docs` Endpoints - Interactive API Dokumentation 
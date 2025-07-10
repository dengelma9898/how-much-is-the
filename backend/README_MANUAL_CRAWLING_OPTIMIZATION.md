# Enhanced Manual Crawling System - Optimization Guide 🚀

This document explains the enhanced manual crawling functionality implemented for the Preisvergleich backend, including new features, optimizations, and usage guidelines.

## 🎯 Overview

Das erweiterte manuelle Crawling-System bietet:

- **Real-time Progress Tracking**: Live-Verfolgung des Crawl-Fortschritts
- **Rate Limiting**: Schutz vor zu häufigen Crawl-Anfragen  
- **Enhanced Monitoring**: Detaillierte Überwachung und Statistiken
- **Store-specific Configuration**: Individuelle Einstellungen pro Shop
- **Error Recovery**: Verbesserte Fehlerbehandlung und Recovery
- **Admin Dashboard**: Erweiterte Admin-Oberfläche mit Echtzeit-Updates

## 🔧 Neue Features

### 1. Real-time Crawl Status Tracking

```bash
# Starte einen manuellen Crawl
curl -X POST "http://localhost:8000/api/v1/admin/crawl/trigger?store_name=Lidl&triggered_by=admin"

# Response:
{
  "message": "Crawl triggered for Lidl",
  "crawl_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "status_endpoint": "/api/v1/admin/crawl/status/550e8400-e29b-41d4-a716-446655440000"
}

# Überprüfe den Status
curl "http://localhost:8000/api/v1/admin/crawl/status/550e8400-e29b-41d4-a716-446655440000"

# Response:
{
  "crawl_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_name": "Lidl",
  "status": "crawling",
  "progress_percentage": 45.2,
  "current_step": "Crawling query 'Bio-Produkte' (3/6)",
  "products_found": 67,
  "products_processed": 23,
  "errors_count": 1,
  "started_at": "2025-01-09T20:15:30Z"
}
```

### 2. Enhanced Admin Endpoints

#### System Overview
```bash
GET /api/v1/admin/system/overview
```
Umfassende Systemübersicht mit Crawler-Status, Scheduler-Info und Performance-Metriken.

#### Crawl Overview Dashboard
```bash
GET /api/v1/admin/crawl/status/overview
```
Real-time Dashboard mit aktiven Crawls, Verlauf und System-Zusammenfassung.

#### Store-specific Status
```bash
GET /api/v1/admin/crawl/store/Lidl/status
```
Detaillierter Status für einen spezifischen Store mit Rate-Limiting-Info.

#### Crawl Cancellation
```bash
DELETE /api/v1/admin/crawl/{crawl_id}?reason=Manual%20stop
```
Bricht einen laufenden Crawl ab.

### 3. Rate Limiting & Protection

```python
# Konfiguration in .env
MANUAL_CRAWL_RATE_LIMIT_MINUTES=5  # Mindestabstand zwischen Crawls
MAX_CONCURRENT_CRAWLS=2            # Maximale parallele Crawls
CRAWL_TIMEOUT_MINUTES=30           # Timeout für einzelne Crawls
```

**Schutzfunktionen:**
- Verhindert doppelte Crawls für denselben Store
- Rate Limiting mit konfigurierbaren Intervallen
- Automatic cleanup alter Tracking-Daten
- Timeout-Protection für hängende Crawls

### 4. Enhanced Progress Tracking

**Status-Stufen:**
1. `PENDING` - Crawl in Warteschlange
2. `INITIALIZING` - Crawler wird initialisiert
3. `CRAWLING` - Aktives Crawling läuft
4. `PROCESSING` - Datenverarbeitung und Deduplizierung
5. `COMPLETED` - Erfolgreich abgeschlossen
6. `FAILED` - Fehler aufgetreten
7. `CANCELLED` - Manuell abgebrochen

**Progress-Updates:**
- Detaillierte Fortschrittsanzeige (0-100%)
- Aktuelle Crawl-Phase mit Beschreibung
- Anzahl gefundener/verarbeiteter Produkte
- Fehleranzahl und -details
- Geschätzte Fertigstellungszeit

## 📊 Store-specific Optimizations

### Lidl Crawler
```python
# Optimierte Konfiguration
LIDL_CRAWLER_ENABLED=true
LIDL_BASE_URL=https://www.lidl.de
LIDL_MAX_PRODUCTS_PER_CRAWL=120    # Erhöht für bessere Abdeckung
LIDL_TIMEOUT_SECONDS=60            # Timeout pro Seite
```

### Aldi Crawler (mit Firecrawl)
```python
# Aldi mit Firecrawl-Integration
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
ALDI_MAX_PRODUCTS_PER_CRAWL=100
FIRECRAWL_ENABLED=true
FIRECRAWL_API_KEY=fc-your-key-here
FIRECRAWL_MAX_AGE=3600000          # 1h Cache
```

## 🛠️ Configuration Options

### Enhanced Environment Variables

```bash
# Rate Limiting Settings
MANUAL_CRAWL_RATE_LIMIT_MINUTES=5
MAX_CONCURRENT_CRAWLS=2
CRAWL_TIMEOUT_MINUTES=30

# Enhanced Monitoring Settings
CRAWL_STATUS_HISTORY_LIMIT=50
CRAWL_STATUS_CLEANUP_HOURS=24
ENABLE_DETAILED_CRAWL_LOGGING=true
ENABLE_PROGRESS_TRACKING=true

# Store-specific Settings
LIDL_CRAWLER_ENABLED=true
LIDL_MAX_PRODUCTS_PER_CRAWL=120
ALDI_CRAWLER_ENABLED=true
ALDI_MAX_PRODUCTS_PER_CRAWL=100

# Admin Interface Settings
ADMIN_DASHBOARD_ENABLED=true
ADMIN_AUTO_REFRESH_INTERVAL=5
ADMIN_MAX_LOG_ENTRIES=100
```

## 📈 Performance Optimizations

### 1. Intelligent Query Management
```python
# Dynamische Query-Auswahl basierend auf Store
def _get_default_queries(self, store_name: str) -> List[str]:
    """Store-specific default queries for comprehensive crawling"""
    if store_name == "Lidl":
        return [
            "Bio-Produkte", "Obst", "Gemüse", "Milchprodukte", 
            "Fleisch", "Backwaren", "Getränke", "Tiefkühl"
        ]
    elif store_name == "Aldi":
        return [
            "Milch", "Brot", "Käse", "Wurst", "Obst", "Gemüse"
        ]
    return ["Lebensmittel"]
```

### 2. Progressive Error Recovery
- Einzelne Query-Fehler brechen nicht den gesamten Crawl ab
- Intelligente Retry-Mechanismen
- Graceful Degradation bei Teilfehlern
- Detaillierte Fehlerprotokollierung

### 3. Efficient Data Processing
- Bulk-Insert für Datenbankoperationen
- Intelligent Deduplication Algorithmus
- Soft-Delete Strategie für alte Produkte
- Optimierte Datenbank-Indizes

## 🎮 Usage Examples

### 1. Einfacher manueller Crawl
```bash
# Alle Stores crawlen
curl -X POST "http://localhost:8000/api/v1/admin/crawl/trigger"

# Spezifischen Store crawlen
curl -X POST "http://localhost:8000/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115"
```

### 2. Mit Tracking und Monitoring
```bash
# Crawl starten und ID erhalten
CRAWL_ID=$(curl -s -X POST "http://localhost:8000/api/v1/admin/crawl/trigger?store_name=Lidl" | jq -r '.crawl_id')

# Status überwachen
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/admin/crawl/status/$CRAWL_ID" | jq -r '.status')
  PROGRESS=$(curl -s "http://localhost:8000/api/v1/admin/crawl/status/$CRAWL_ID" | jq -r '.progress_percentage')
  echo "Status: $STATUS, Progress: $PROGRESS%"
  
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    break
  fi
  
  sleep 5
done
```

### 3. System-Monitoring
```bash
# System-Übersicht
curl "http://localhost:8000/api/v1/admin/system/overview" | jq

# Aktive Crawls überwachen
curl "http://localhost:8000/api/v1/admin/crawl/status/overview" | jq

# Store-spezifischen Status prüfen
curl "http://localhost:8000/api/v1/admin/crawl/store/Lidl/status" | jq
```

## 🔧 Troubleshooting

### Rate Limiting Errors
```bash
# HTTP 429 - Too Many Requests
{
  "detail": "Rate limit exceeded for Lidl. Next crawl allowed at 20:25:30"
}
```
**Lösung:** Warten Sie bis zur angegebenen Zeit oder erhöhen Sie `MANUAL_CRAWL_RATE_LIMIT_MINUTES`.

### Concurrent Crawl Conflicts
```bash
# HTTP 409 - Conflict
{
  "detail": "Store Lidl is already being crawled"
}
```
**Lösung:** Warten Sie bis der aktuelle Crawl abgeschlossen ist oder brechen Sie ihn ab.

### Crawl Timeouts
```bash
# Crawl Status zeigt "failed" nach langer Zeit
{
  "status": "failed",
  "error_details": "Crawler timeout after 30 minutes"
}
```
**Lösung:** Erhöhen Sie `CRAWL_TIMEOUT_MINUTES` oder überprüfen Sie die Store-Website.

## 📊 Monitoring & Analytics

### Key Performance Indicators (KPIs)
- **Success Rate**: Prozentsatz erfolgreicher Crawls
- **Average Duration**: Durchschnittliche Crawl-Dauer
- **Products per Crawl**: Anzahl gecrawlter Produkte
- **Error Rate**: Fehlerrate nach Store
- **System Load**: Aktuelle Systemauslastung

### Log Analysis
```bash
# Crawl-spezifische Logs anzeigen
tail -f logs/app.log | grep "crawl_id=550e8400"

# Fehler-Analyse
grep "ERROR.*crawl" logs/app.log | tail -20

# Performance-Metriken
grep "Enhanced crawl completed" logs/app.log | tail -10
```

## 🚀 Future Enhancements

### Geplante Features
1. **WebSocket-Integration**: Real-time Updates für Admin-Dashboard
2. **Notification System**: E-Mail/Slack-Benachrichtigungen bei Crawl-Ereignissen  
3. **Advanced Scheduling**: Cron-ähnliche Konfiguration für Store-spezifische Crawls
4. **ML-based Optimization**: Intelligente Query-Auswahl basierend auf Erfolgsraten
5. **Distributed Crawling**: Lastverteilung auf mehrere Server
6. **API Rate Limiting**: Schutz der Admin-Endpoints vor Missbrauch

### Performance Roadmap
1. **Q1 2025**: WebSocket Integration + Advanced Dashboard
2. **Q2 2025**: Machine Learning Optimizations
3. **Q3 2025**: Distributed Architecture
4. **Q4 2025**: Full Automation mit AI-gestützter Optimierung

---

## 🔗 Related Documentation

- [Backend Database Setup](README_DATABASE.md)
- [Firecrawl Integration](README_FIRECRAWL.md)  
- [Environment Configuration](README_ENVIRONMENTS.md)
- [API Documentation](http://localhost:8000/docs)

## 🎯 Best Practices

1. **Monitoring**: Überwachen Sie System-Overview regelmäßig
2. **Rate Limiting**: Respektieren Sie die konfigurierten Limits
3. **Error Handling**: Nutzen Sie die detaillierten Fehlerinformationen
4. **Performance**: Optimieren Sie Store-spezifische Konfigurationen
5. **Maintenance**: Führen Sie regelmäßige Cleanup-Operationen durch

Das erweiterte manuelle Crawling-System bietet eine solide Grundlage für skalierbare und zuverlässige Produktdaten-Erfassung mit umfassendem Monitoring und optimaler Benutzerfreundlichkeit. 
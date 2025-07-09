# Multi-Environment Backend Setup 🌍

Diese Dokumentation erklärt, wie das Backend mit verschiedenen Umgebungskonfigurationen gestartet wird.

## 🎯 Überblick

Das Backend unterstützt drei verschiedene Umgebungen:

- **Local** (`.env.local`) - Lokale Entwicklung
- **Dev** (`.env.dev`) - Development-Server
- **Prod** (`.env.prod`) - Production-Server

Jede Umgebung hat ihre eigene `.env`-Datei mit spezifischen Konfigurationen.

## 🚀 Quick Start

### 1. Backend mit verschiedenen Umgebungen starten

```bash
cd backend

# Lokale Entwicklung (default)
python start.py --env local

# Development-Server
python start.py --env dev

# Production-Server
python start.py --env prod
```

### 2. Mit zusätzlichen Optionen

```bash
# Mit Auto-Reload für Entwicklung
python start.py --env local --reload

# Production mit spezifischem Host/Port
python start.py --env prod --host 0.0.0.0 --port 8080

# Mit mehreren Workers für Production
python start.py --env prod --workers 8
```

### 3. Mit Environment-Variable

```bash
# Setze Umgebung über Environment-Variable
export APP_ENV=dev
python start.py

# Oder inline
APP_ENV=prod python start.py
```

## 📁 Environment-Dateien

### `.env.local` - Lokale Entwicklung

```bash
# Lokale Entwicklungsumgebung
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-local-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=3600000
FIRECRAWL_MAX_RESULTS_PER_STORE=15

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
```

### `.env.dev` - Development-Server

```bash
# Development-Server-Umgebung
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-dev-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=1800000
FIRECRAWL_MAX_RESULTS_PER_STORE=20

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
```

### `.env.prod` - Production-Server

```bash
# Production-Server-Umgebung
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=WARNING

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-production-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=7200000
FIRECRAWL_MAX_RESULTS_PER_STORE=30

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
```

## 🔧 Start-Script Optionen

### Kommandozeilenargumente

```bash
python start.py --help
```

| Argument | Beschreibung | Beispiel |
|----------|-------------|----------|
| `--env` | Environment auswählen | `--env prod` |
| `--host` | Host IP überschreiben | `--host 0.0.0.0` |
| `--port` | Port überschreiben | `--port 8080` |
| `--reload` | Auto-Reload aktivieren | `--reload` |
| `--workers` | Anzahl Worker-Prozesse | `--workers 4` |
| `--log-level` | Log-Level überschreiben | `--log-level debug` |

### Beispiele

```bash
# Lokale Entwicklung mit Auto-Reload
python start.py --env local --reload

# Dev-Server auf allen Interfaces
python start.py --env dev --host 0.0.0.0

# Production mit 8 Workern
python start.py --env prod --workers 8

# Custom Port für Tests
python start.py --env local --port 9000

# Debug-Modus für Production-Tests
python start.py --env prod --log-level debug --reload
```

## 🔄 Automatische Environment-Erkennung

Das System erkennt die Umgebung in folgender Priorität:

1. **Kommandozeilen-Argument**: `--env prod`
2. **Environment-Variable**: `APP_ENV=dev`
3. **Default**: `local`

```bash
# Priorität 1: Kommandozeile (überschreibt APP_ENV)
APP_ENV=dev python start.py --env prod  # → verwendet prod

# Priorität 2: Environment-Variable
export APP_ENV=dev
python start.py  # → verwendet dev

# Priorität 3: Default
python start.py  # → verwendet local
```

## 📋 Automatische Datei-Erstellung

Beim ersten Start erstellt das System automatisch Beispiel-`.env`-Dateien:

```bash
python start.py --env local
```

Output:
```
⚠️  Environment-Datei .env.local nicht gefunden!
✅ Beispiel-Environment-Dateien erstellt:
   - .env.local
   - .env.dev
   - .env.prod

💡 Bitte bearbeite die .env-Dateien mit deinen echten API-Keys!
   Besonders wichtig: FIRECRAWL_API_KEY
```

## 🔍 Konfiguration validieren

Das Start-Script zeigt die aktuelle Konfiguration an:

```
🚀 Starte Preisvergleich-Backend
📁 Environment: local
📋 Config-Datei: .env.local

⚙️  Konfiguration:
   - Host: 127.0.0.1
   - Port: 8000
   - Debug: true
   - Log-Level: debug
   - Firecrawl: true
   - API-Key: fc-abcd****wxyz

🔧 Ausgeführter Befehl:
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
```

## 🧪 Testing mit verschiedenen Umgebungen

```bash
# Test-Script mit spezifischer Umgebung
APP_ENV=dev python test_aldi_crawler.py

# Oder Environment-Variable setzen
export APP_ENV=local
python test_aldi_crawler.py
```

## 🚀 Production Deployment

### Empfohlene Production-Einstellungen

```bash
# Production-Start mit optimalen Einstellungen
python start.py --env prod --workers 4 --host 0.0.0.0

# Oder mit Environment-Variable
export APP_ENV=prod
python start.py --workers 4 --host 0.0.0.0
```

### Production `.env.prod` Checklist

- [ ] `DEBUG=false` gesetzt
- [ ] `LOG_LEVEL=WARNING` oder `ERROR`
- [ ] Echter `FIRECRAWL_API_KEY` eingetragen
- [ ] `HOST=0.0.0.0` für externe Zugriffe
- [ ] Angemessene Cache-Zeiten (`FIRECRAWL_MAX_AGE`)

## 🔧 Legacy-Unterstützung

Das System ist abwärtskompatibel mit der alten `.env`-Datei:

```bash
# Falls .env.local nicht existiert, wird .env verwendet
python start.py --env local  # → lädt .env falls .env.local nicht da
```

## 🐳 Docker-Integration

Für Docker-Deployments:

```dockerfile
# Dockerfile
ENV APP_ENV=prod
CMD ["python", "start.py"]
```

Oder mit docker-compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    environment:
      - APP_ENV=prod
    command: python start.py --workers 4
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### 1. "Environment-Datei nicht gefunden"

**Problem**: `.env.{env}` existiert nicht

**Lösung**:
```bash
# Lasse das Script die Beispiel-Dateien erstellen
python start.py --env local

# Oder erstelle manuell
cp .env.local.example .env.local
```

#### 2. "Kann ohne .env.{env} nicht starten"

**Problem**: Erforderliche `.env`-Datei fehlt

**Lösung**:
```bash
# Erstelle fehlende Datei basierend auf Beispiel
cp .env.local .env.dev
# Dann bearbeite die spezifischen Einstellungen
```

#### 3. Falsche Konfiguration geladen

**Problem**: Unerwartete Environment-Konfiguration

**Lösung**:
```bash
# Überprüfe welche Datei geladen wird
python start.py --env local
# Schaue nach der Ausgabe "Loaded configuration from: ..."

# Oder prüfe APP_ENV Variable
echo $APP_ENV
unset APP_ENV  # Falls nötig zurücksetzen
```

#### 4. API-Key nicht gesetzt

**Problem**: Firecrawl API-Key fehlt

**Lösung**:
```bash
# Bearbeite die entsprechende .env-Datei
nano .env.local  # oder .env.dev, .env.prod

# Setze:
FIRECRAWL_API_KEY=fc-your-real-api-key-here
```

## 📚 Weitere Informationen

- [Firecrawl Integration](README_FIRECRAWL.md)
- [API Dokumentation](../docs/api.md)
- [Deployment Guide](../docs/deployment.md) 
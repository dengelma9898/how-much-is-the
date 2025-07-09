# Firecrawl Integration für Aldi-Preiscrawling 🔥🛒

Diese Dokumentation beschreibt die Integration von Firecrawl für das automatisierte Crawling von Aldi-Produktpreisen in unserem Backend.

## 🚀 Überblick

Die Firecrawl-Integration ermöglicht es, Produktdaten direkt von der Aldi-Suchfunktion zu extrahieren mit:

- **Direkte Produktsuche**: Nutzt die offizielle Aldi-Suchfunktion (https://www.aldi-sued.de/de/suchergebnis.html?search={query})
- **Strukturierte Datenextraktion**: LLM-basierte Extraktion für präzise Produktdaten (Name, Preis, Einheit, Grundpreis)
- **Performance-Optimierung**: 1-Stunden-Caching für bis zu 500% schnellere Responses
- **Intelligente Relevanz-Sortierung**: Automatisches Scoring nach Suchrelevanz
- **Robuste Fehlerbehandlung**: Graceful Fallback zu Mock-Daten

## 📋 Voraussetzungen

1. **Firecrawl API Key**: Registrierung bei [firecrawl.dev](https://firecrawl.dev)
2. **Python Dependencies**: Bereits in `requirements.txt` enthalten:
   ```
   firecrawl-py==0.0.20
   ```

## 🔧 Setup

### 1. Firecrawl API Key beschaffen

1. Gehe zu [firecrawl.dev](https://firecrawl.dev)
2. Erstelle einen Account
3. Generiere einen API Key im Dashboard
4. Der Key hat normalerweise das Format: `fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Environment-Variablen konfigurieren

Erstelle oder erweitere die `.env`-Datei im Backend-Verzeichnis:

```bash
# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-api-key-here
FIRECRAWL_ENABLED=true

# Optionale erweiterte Einstellungen
FIRECRAWL_MAX_AGE=3600000  # 1 Stunde Cache in Millisekunden
FIRECRAWL_MAX_RESULTS_PER_STORE=15
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
```

### 3. Backend starten

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## 🎯 Funktionsweise

### Crawling-Bereiche

Der Aldi-Crawler durchsucht parallel drei Hauptbereiche:

1. **Frischekracher** (`/de/angebote/frischekracher.html`)
   - Frische Produkte wie Obst, Gemüse, Fleisch
   - Wöchentlich wechselnde Angebote

2. **Aktuelle Angebote** (`/de/angebote.html`)
   - Haupt-Angebotssection mit verschiedenen Kategorien
   - Kleidung, Technik, Haushalt, etc.

3. **Markenaktionen** (`/de/angebote/markenaktion-der-woche.html`)
   - Spezielle Markenprodukte und Aktionen
   - Reduzierte Markenartikel

### Datenextraktion

```python
# Beispiel für extrahierte Produktdaten
{
    "name": "EXPERTIZ Kopierpapier",
    "price": "4.49",
    "unit": "500 Blatt",
    "brand": "EXPERTIZ", 
    "category": "Büro und Schule",
    "discount": "€ 4,49*",
    "availability": "ab 10.07.2025"
}
```

### Preisverarbeitung

Der Crawler verarbeitet verschiedene deutsche Preisformate:
- `€ 1,79*` → `1.79`
- `4,99 €` → `4.99`
- `€2,50` → `2.50`
- `1.234,56` → `1234.56`

## 🔍 API-Nutzung

### Produktsuche mit Firecrawl

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Milch",
    "postal_code": "12345"
  }'
```

### Response-Beispiel

```json
{
  "results": [
    {
      "name": "Frische Vollmilch 3,5%",
      "price": 1.19,
      "store": "Aldi Süd",
      "store_logo_url": "https://upload.wikimedia.org/...",
      "availability": "verfügbar",
      "unit": "1L",
      "category": "Frische Produkte",
      "brand": "Milfina",
      "origin": "Deutschland",
      "quality_info": "Klasse I"
    }
  ],
  "query": "Milch",
  "postal_code": "12345",
  "total_results": 1,
  "search_time_ms": 2340
}
```

## ⚙️ Konfiguration

### Einstellungen in `config.py`

```python
class Settings(BaseSettings):
    # Firecrawl-Grundkonfiguration
    firecrawl_api_key: Optional[str] = None
    firecrawl_enabled: bool = False
    
    # Performance-Einstellungen
    firecrawl_max_age: int = 3600000  # 1 Stunde Cache
    firecrawl_max_results_per_store: int = 15
    
    # Aldi-spezifische Einstellungen
    aldi_crawler_enabled: bool = True
    aldi_base_url: str = "https://www.aldi-sued.de"
```

### Cache-Verhalten

- **Firecrawl Cache**: 1 Stunde (3.600.000ms)
- **Vorteile**: Bis zu 500% schnellere Responses für wiederkehrende Queries
- **Automatisch**: Cache wird von Firecrawl verwaltet

## 🧪 Testing

### Testscript ausführen

```bash
cd backend
python test_aldi_crawler.py
```

### Beispiel-Output

```
🔥 Teste Aldi-Crawler mit Firecrawl-Integration

✅ Konfiguration:
   - Firecrawl aktiviert: True
   - API Key verfügbar: fc-****...****
   - Aldi-Crawler: True

🛒 Teste Produktsuche: 'Milch'
   ⏱️  Suchzeit: 2.3s
   📊 Gefunden: 3 Produkte
   💰 Preise: €0.89 - €1.79

🛒 Teste Produktsuche: 'Brot'
   ⏱️  Suchzeit: 1.8s (Cache!)
   📊 Gefunden: 5 Produkte
   💰 Preise: €0.79 - €2.49
```

## 🚨 Troubleshooting

### Häufige Probleme

#### 1. "Firecrawl ist deaktiviert oder API-Key fehlt"

**Lösung:**
```bash
# Überprüfe .env-Datei
FIRECRAWL_API_KEY=fc-your-actual-key
FIRECRAWL_ENABLED=true
```

#### 2. "firecrawl-py nicht installiert"

**Lösung:**
```bash
pip install firecrawl-py==0.0.20
```

#### 3. "Fehler beim Crawlen von [section]"

**Mögliche Ursachen:**
- Aldi-Website temporär nicht erreichbar
- API-Rate-Limits erreicht
- Netzwerkprobleme

**Lösung:**
- Prüfe Logs für Details: `tail -f logs/backend.log`
- Warte 5-10 Minuten und versuche erneut
- System fällt automatisch auf Mock-Daten zurück

#### 4. "Ungültiger Preisbereich" Warnungen

**Normal:** Crawler filtert automatisch unrealistische Preise (< €0.01 oder > €1000)

#### 5. Langsame Responses

**Lösungsansätze:**
- Cache sollte nach erstem Request greifen
- Überprüfe `firecrawl_max_age` Einstellung
- Reduziere `firecrawl_max_results_per_store`

### Debug-Modus

Aktiviere detailliertes Logging:

```python
# In config.py
log_level: str = "DEBUG"
```

## 📈 Performance-Tipps

1. **Cache nutzen**: Lass `firecrawl_max_age` auf 3600000ms (1 Stunde)
2. **Parallel Processing**: Crawler nutzt automatisch `asyncio.gather()`
3. **Relevanz-Filtering**: Nur Produkte mit Score ≥ 2 werden zurückgegeben
4. **Result-Limits**: Standard 15 Produkte pro Store für optimale Performance

## 🔄 Fallback-Verhalten

Falls Firecrawl nicht verfügbar ist:
1. Warnung wird geloggt
2. Automatischer Fallback zu Mock-Daten
3. Nutzer bemerkt nahtlosen Übergang
4. Betrieb läuft normal weiter

## 🛠️ Erweiterte Nutzung

### Eigene Crawler entwickeln

```python
from app.services.aldi_crawler import AldiCrawler

# Benutzerdefinierte Implementierung
class CustomSupermarketCrawler(AldiCrawler):
    def __init__(self, firecrawl_app=None):
        super().__init__(firecrawl_app)
        self.base_url = "https://example-supermarket.de"
        self.crawl_urls = {
            'offers': f"{self.base_url}/angebote",
            'fresh': f"{self.base_url}/frische-produkte"
        }
```

### Schema-Anpassungen

```python
def _get_custom_schema(self):
    return {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        # Eigene Felder hinzufügen
                        "nutritional_info": {"type": "string"},
                        "ingredients": {"type": "array"}
                    }
                }
            }
        }
    }
```

## 📚 Weitere Ressourcen

- [Firecrawl Dokumentation](https://docs.firecrawl.dev)
- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/)
- [Pydantic Models](https://docs.pydantic.dev/latest/)

## 💡 Support

Bei Fragen oder Problemen:
1. Prüfe Logs: `tail -f logs/backend.log`
2. Teste mit `test_aldi_crawler.py`
3. Überprüfe Konfiguration in `.env`
4. Erstelle Issue im Repository 
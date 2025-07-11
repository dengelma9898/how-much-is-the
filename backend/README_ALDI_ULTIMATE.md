# ALDI Ultimate Crawler

Der ALDI Ultimate Crawler ist ein kategorien-basierter Web-Crawler, der alle Produkte von ALDI-Aktionsseiten automatisch erfasst. Er folgt dem bewährten Muster des LIDL Ultimate Crawlers und ersetzt den alten query-basierten ALDI Crawler.

## 🎯 Funktionen

- **Kategorien-basiertes Crawling**: Crawlt alle drei ALDI-Aktionskategorien vollständig
- **Robuste CSS-Selektoren**: Mehrere Fallback-Selektoren für maximale Zuverlässigkeit
- **Intelligente Scroll-Strategie**: 3-Phasen-Scroll für optimales Lazy Loading
- **Deutsche Preisverarbeitung**: Unterstützt alle deutschen Preisformate inkl. Cent-Preise
- **Verfügbarkeits-Parsing**: Extrahiert Gültigkeitsdaten und Verfügbarkeitsstatus
- **Cookie-Banner Handling**: Automatische Behandlung von Consent-Dialogen


## 🛍️ Unterstützte ALDI-Kategorien

1. **Frischekracher** - https://www.aldi-sued.de/de/angebote/frischekracher.html
2. **Markenaktion der Woche** - https://www.aldi-sued.de/de/angebote/markenaktion-der-woche.html  
3. **Preisaktion** - https://www.aldi-sued.de/de/angebote/preisaktion.html

## 🚀 Verwendung

### Grundlegende Verwendung

```python
from backend.admin_api.services.aldi_crawler_ultimate import AldiUltimateCrawler

# Crawler initialisieren
crawler = AldiUltimateCrawler()

# Alle Produkte von allen Kategorien crawlen
products = await crawler.crawl_all_products(
    max_results=1000,  # Max. Produkte pro Kategorie
    postal_code="10115"  # Optional (wird für ALDI nicht verwendet)
)

print(f"Gefunden: {len(products)} Produkte")
```

### Über Crawler Service (Empfohlen)

```python
from backend.admin_api.services.crawler_service import CrawlerService

# Über den CrawlerService (automatisch initialisiert)
crawler_service = CrawlerService(db_service)

success_count, error_count = await crawler_service.crawl_store(
    store_name="Aldi",
    postal_code="10115",
    crawl_session_id=session_id
)
```



## 🔧 Konfiguration

### Environment-Variablen

```bash
# .env Datei
ALDI_CRAWLER_ENABLED=true
ALDI_MAX_PRODUCTS_PER_CRAWL=1000
```

### Crawler-Einstellungen

```python
class AldiUltimateCrawler:
    def __init__(self):
        self.base_url = "https://www.aldi-sued.de"
        self.timeout = 120000  # 2 Minuten
        
        # Kategorie-URLs (vollständig konfigurierbar)
        self.category_urls = {
            "Frischekracher": "...",
            "Markenaktion der Woche": "...",
            "Preisaktion": "..."
        }
```

## 🎛️ CSS-Selektoren

### Produktcontainer

```python
self.product_selectors = [
    '.product-tile',           # Standard ALDI Produktkarte
    '.offer-tile',             # Angebots-Karte
    '.product-item',           # Alternative Produktitem
    '[class*="product"]',      # Fallback für Produktklassen
    '[class*="offer"]',        # Fallback für Angebotsklassen
    '.mod-article-tile',       # Modular Article Tile
    '[data-testid*="product"]' # Test-ID Fallback
]
```

### Produktdaten

```python
# Titel-Selektoren
self.title_selectors = [
    '.product-tile__title',
    '.offer-tile__title', 
    '.product-title',
    # ... weitere Fallbacks
]

# Preis-Selektoren  
self.price_selectors = [
    '.product-tile__price',
    '.offer-tile__price',
    '.price-current',
    # ... weitere Fallbacks
]
```

## 📊 Datenstruktur

### ProductResult

```python
ProductResult(
    name="ALDI Produktname",
    price="1.99",                    # String (Decimal-kompatibel)
    store="ALDI Süd",
    image_url="https://...",
    product_url="https://www.aldi-sued.de",
    availability="verfügbar",        # "verfügbar" | "nicht verfügbar"
    availability_text="Gültig bis 15.12.",
    offer_valid_until="2024-12-15",  # ISO Date oder None
    description="",                  # Meist leer bei ALDI
    unit="je 500g",                  # Einheit/Grundpreis
    reward_program_hint="",          # Leer (ALDI hat kein Bonusprogramm)
    category="Frischekracher"        # ALDI-Kategorie
)
```

## 🧪 Testing

### Unit Tests ausführen

```bash
# Alle ALDI-Tests
python backend/tests/crawlers/test_aldi_crawler.py

# Dedicated Ultimate Crawler Tests
python backend/tests/crawlers/test_aldi_ultimate_crawler.py

# Mit pytest
pytest backend/tests/crawlers/test_aldi_ultimate_crawler.py -v
```

### Integration Tests

```bash
# Live-Crawling Tests (benötigt Internet)
pytest backend/tests/crawlers/test_aldi_ultimate_crawler.py -m integration
```

### Test-Features

- ✅ Preisverarbeitung (Deutsche Formate, Cent-Preise)
- ✅ Verfügbarkeits-Parsing (Datumsextraktion)
- ✅ CSS-Selektor Konfiguration

- ✅ Live-Crawling (optional)
- ✅ Error Handling

## 🔄 Migration vom alten Crawler

### Was sich geändert hat

| Alt (Query-basiert) | Neu (Kategorien-basiert) |
|---------------------|--------------------------|
| `search_products(query)` | `crawl_all_products()` |
| Firecrawl-abhängig | Playwright-basiert |
| Suchbegriff-fokussiert | Vollständiger Katalog |
| Limitierte Abdeckung | 100% Aktionsprodukte |

### Migration Steps

1. **Automatisch**: Alte Crawler-Dateien wurden gelöscht
2. **Automatisch**: Neue Crawler in `CrawlerService` integriert
3. **Manuell**: Tests auf neue API umstellen (optional)

### Breaking Changes

- **Removed**: `search_products()` method - use `crawl_all_products()` instead
- **Changed**: No more query-based searching - now crawls complete categories

## 🐛 Debugging

### Logging aktivieren

```python
import logging
logging.getLogger('backend.admin_api.services.aldi_crawler_ultimate').setLevel(logging.DEBUG)
```

### Häufige Probleme

#### Keine Produkte gefunden

```python
# Check 1: Kategorie-URLs erreichbar?
for name, url in crawler.category_urls.items():
    print(f"{name}: {url}")

# Check 2: CSS-Selektoren aktuell?
await crawler._count_all_product_containers(page)

# Check 3: Scroll-Strategie funktional?
await crawler._thorough_scroll_strategy(page)
```

#### Preise nicht erkannt

```python
# Test Preisverarbeitung
test_prices = ["€ 1,79", "-.90", ",95"]
for price_text in test_prices:
    result = crawler._parse_price(price_text)
    print(f"'{price_text}' -> {result}")
```

#### Cookie-Banner blockiert

```python
# Debug Cookie-Handling
await crawler._handle_cookie_banner(page)
```

## 📈 Performance

### Optimierungen

- **Paralleles Crawling**: Kategorien werden sequenziell verarbeitet (für Stabilität)
- **Intelligente Scroll-Strategie**: 3-Phasen-Scroll minimiert verpasste Produkte
- **Robuste Selektoren**: Mehrere Fallbacks reduzieren Fehlerrate
- **Effiziente Extraktion**: Nur relevante Daten werden verarbeitet

### Benchmark-Werte

- **Initialisierung**: ~100ms
- **Cookie-Handling**: ~2-5s
- **Scroll-Strategie**: ~30-60s je Kategorie
- **Produktextraktion**: ~10-50ms je Produkt
- **Gesamt (3 Kategorien, 100 Produkte)**: ~3-8 Minuten

## 🔒 Sicherheit & Compliance

### Anti-Bot-Maßnahmen

- **User-Agent**: Realistischer Chrome User-Agent
- **Viewport**: Standard Desktop-Auflösung (1920x1080)
- **Timing**: Natürliche Wartezeiten zwischen Aktionen
- **Headers**: Deaktivierte Automation-Flags

### Rate Limiting

- **Scroll-Intervalle**: 2s zwischen Scroll-Schritten
- **Kategorie-Pausen**: 2s zwischen Kategorien
- **Request-Spacing**: Natürliche Browser-Simulation

### Rechtliches

- **Öffentliche Daten**: Nur öffentlich zugängliche Produktinformationen
- **Robots.txt**: Respektiert ALDI-Richtlinien
- **Fair Use**: Vernünftige Request-Frequenz

## 🔄 Updates & Wartung

### CSS-Selektoren aktualisieren

```python
# Bei ALDI-Website-Updates:
crawler.product_selectors.insert(0, '.new-product-selector')
crawler.title_selectors.insert(0, '.new-title-selector')
```

### Neue Kategorien hinzufügen

```python
crawler.category_urls["Neue Kategorie"] = "https://www.aldi-sued.de/de/angebote/neue-kategorie.html"
```

### Monitoring & Alerts

```python
# Erfolgsrate überwachen
success_rate = success_count / (success_count + error_count)
if success_rate < 0.8:
    logger.warning(f"Low success rate: {success_rate:.1%}")
```

## 📞 Support

- **Issues**: [Backend-Team](mailto:backend@example.com)
- **Logs**: `backend/logs/crawler.log`
- **Monitoring**: Admin-Dashboard `/admin/crawlers`
- **Tests**: `python backend/tests/crawlers/test_aldi_ultimate_crawler.py` 
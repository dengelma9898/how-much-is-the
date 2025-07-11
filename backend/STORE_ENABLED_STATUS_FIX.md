# Store Enabled Status Bug Fix

## Problem

Die dynamische Store-Erstellung beim Crawling ignorierte den `enabled` Status von Stores, was dazu führte, dass auch intentional deaktivierte Stores gecrawlt wurden. Dies betraf sowohl einzelne Store-Crawls als auch die "Crawl all" Funktionalität.

## Root Cause

In den Admin-Routern (`backend/admin-api/routers/admin.py` und `backend/app/routers/admin.py`) wurde nach dem Aufruf von `_ensure_store_exists()` nicht geprüft, ob der Store den Status `enabled=True` hat.

**Problematische Code-Stellen:**
- Zeile 237: `store = await crawler_service._ensure_store_exists(store_name)`
- Zeile 244: `store = await crawler_service._ensure_store_exists(available_store_name)`

## Implementierter Fix

### 1. Einzelner Store Crawl
```python
# Get or create store dynamically 
store = await crawler_service._ensure_store_exists(store_name)

# Check if store is enabled
if not store.enabled:
    raise ValueError(f"Store '{store_name}' is disabled and cannot be crawled")

stores = [store]
```

### 2. "Crawl All" Funktionalität
```python
for available_store_name in crawler_service.crawlers.keys():
    try:
        store = await crawler_service._ensure_store_exists(available_store_name)
        
        # Only add enabled stores to crawl list
        if store.enabled:
            stores.append(store)
        else:
            logger.info(f"Skipping disabled store: {available_store_name}")
            
    except Exception as e:
        logger.warning(f"Could not prepare store {available_store_name}: {e}")
        continue
```

## Verhalten nach dem Fix

### Einzelner Store Crawl
- **Enabled Store (`enabled=true`)**: Crawl wird normal ausgeführt
- **Disabled Store (`enabled=false`)**: Crawl wird mit ValueError abgelehnt
- **Fehlermeldung**: `"Store '{store_name}' is disabled and cannot be crawled"`

### "Crawl All" Funktionalität
- **Enabled Stores**: Werden normal gecrawlt
- **Disabled Stores**: Werden übersprungen und geloggt
- **Log-Nachricht**: `"Skipping disabled store: {store_name}"`
- **Verhalten**: Crawl läuft weiter mit anderen enabled Stores

## Betroffene Dateien

1. **`backend/admin-api/routers/admin.py`**
   - Zeilen 238-240: Enabled-Check für einzelne Store-Crawls
   - Zeilen 248-252: Enabled-Check für "Crawl all"

2. **`backend/app/routers/admin.py`**
   - Zeilen 233-235: Enabled-Check für einzelne Store-Crawls  
   - Zeilen 243-247: Enabled-Check für "Crawl all"

3. **`backend/tests/integration/test_dynamic_store_creation.py`**
   - Neue Test-Klasse `TestStoreEnabledStatusCheck`
   - Tests für enabled/disabled Store Verhalten

4. **`backend/DATABASE_SETUP.md`**
   - Dokumentation des enabled-Field Verhaltens

5. **`backend/test_store_enabled_fix.py`**
   - Verifikationsscript für den Fix

## Testing

### Automatische Tests
```bash
cd backend
python3 -m pytest tests/integration/test_dynamic_store_creation.py::TestStoreEnabledStatusCheck -v
```

### Manueller Test
```bash
cd backend
python3 test_store_enabled_fix.py
```

## API Verhalten

### Einzelner Store Crawl Request
```bash
POST /api/v1/admin/crawl/trigger?store_name=Lidl
```

**Response bei disabled Store:**
```json
{
  "detail": "Store 'Lidl' is disabled and cannot be crawled"
}
```
**HTTP Status:** `500 Internal Server Error`

### "Crawl All" Request
```bash
POST /api/v1/admin/crawl/trigger
```

**Response bei gemischten enabled/disabled Stores:**
```json
{
  "message": "Crawl triggered for all stores",
  "crawl_id": "uuid-here",
  "postal_code": "10115",
  "status": "started"
}
```

**Verhalten:** Nur enabled Stores werden gecrawlt, disabled Stores werden geloggt und übersprungen.

## Backwards Compatibility

- ✅ **Bestehende enabled Stores**: Keine Änderung im Verhalten
- ✅ **Store-Erstellung**: Stores werden weiterhin standardmäßig mit `enabled=true` erstellt
- ✅ **API Endpoints**: Keine Breaking Changes in der API-Struktur
- ⚠️ **Disabled Stores**: Werden jetzt korrekt rejected/übersprungen (erwünschtes neues Verhalten)

## Administrator Actions

### Store deaktivieren
```sql
UPDATE stores SET enabled = false WHERE name = 'StoreName';
```

### Store wieder aktivieren  
```sql
UPDATE stores SET enabled = true WHERE name = 'StoreName';
```

### Alle enabled Stores anzeigen
```bash
GET /api/v1/admin/stores
```

## Sicherheitsaspekte

- **Unautorized Crawling Prevention**: Disabled Stores können nicht mehr versehentlich gecrawlt werden
- **Resource Protection**: Verhindert unnötige Load auf deaktivierten Store-APIs
- **Administrative Control**: Admins haben vollständige Kontrolle über Crawl-Berechtigungen

## Monitoring

- **Logs**: Disabled Stores werden mit `INFO` Level geloggt
- **Metrics**: Crawl-Statistiken reflektieren nur enabled Stores
- **Health Checks**: Store-Status wird in Admin Health Endpoints berücksichtigt

---

**Fix implementiert am:** 2025-01-09  
**Getestete Komponenten:** Admin API, Client API, Database Layer  
**Backwards Compatible:** Ja (mit erwünschten Verhaltensänderungen) 
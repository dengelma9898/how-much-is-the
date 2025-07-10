# Availability & Cleanup System Documentation

## Übersicht

Das erweiterte System verwaltet jetzt Produktverfügbarkeit und Angebots-Enddaten intelligent, um eine automatische Datenbereinigung zu ermöglichen.

## 🔄 Neue Felder

### ProductResult Model (API)
```python
availability: bool = Field(default=True, description="Verfügbarkeitsstatus im Store")
availability_text: Optional[str] = Field(None, description="Verfügbarkeitstext vom Store")
offer_valid_until: Optional[str] = Field(None, description="Bis wann das Angebot gültig ist")
```

### DatabaseProduct Model (Datenbank)
```sql
availability_text VARCHAR(255)    -- Original-Text vom Store
offer_valid_until VARCHAR(10)     -- YYYY-MM-DD Format
```

## 📅 Verfügbarkeits-Parsing

### Unterstützte Textformate

Das System erkennt automatisch Verfügbarkeits- und Datumsinformationen:

```
"nur in der Filiale 07.07. - 12.07."      → available=true, until=2026-07-12
"nur online 15.01. - 20.01."               → available=true, until=2026-01-20
"Verfügbar bis 31.12.2024"                 → available=true, until=2024-12-31
"ausverkauft"                               → available=false, until=null
"nicht verfügbar"                           → available=false, until=null
"vergriffen"                                → available=false, until=null
"Angebot gültig 05.03. - 10.03."          → available=true, until=2026-03-10
```

### Smart Datumslogik

- **Ohne Jahr**: Aktuelles Jahr oder nächstes Jahr (falls >30 Tage in Vergangenheit)
- **Mit Jahr**: Direktes Parsing
- **Vergangene Daten**: Automatisch `availability=false`
- **Mehrere Daten**: Spätestes Datum wird verwendet

## 🧹 Cleanup System

### Cleanup Service Funktionen

#### 1. Abgelaufene Angebote bereinigen
```python
await cleanup_service.cleanup_expired_offers(dry_run=True)
```

**Funktionsweise:**
- Findet Produkte mit `offer_valid_until < heute`
- Markiert als `deleted_at = jetzt` und `availability = false` (Soft Delete)
- Liefert detaillierte Statistiken

#### 2. Alte Produkte bereinigen
```python
await cleanup_service.cleanup_old_products(days_old=30, dry_run=True)
```

**Funktionsweise:**
- Findet Produkte älter als X Tage ohne Enddatum
- Bereinigt "verwaiste" Daten ohne Angebotszeitraum
- Ideal für regelmäßige Maintenance

#### 3. Cleanup-Statistiken
```python
await cleanup_service.get_cleanup_statistics()
```

**Liefert:**
- Anzahl aktiver Produkte
- Produkte mit/ohne Enddatum
- Abgelaufene Angebote
- Bald ablaufende Angebote (7 Tage)
- Coverage-Prozentsatz

## 🌐 Admin API Endpoints

### Cleanup-Statistiken abrufen
```http
GET /api/v1/admin/cleanup/statistics
```

**Response:**
```json
{
  "analysis_date": "2025-07-10",
  "total_active_products": 150,
  "products_with_end_date": 75,
  "products_without_end_date": 75,
  "expired_offers": 12,
  "expiring_soon_offers": 8,
  "deleted_products": 35,
  "cleanup_recommendations": {
    "immediate_cleanup_candidates": 12,
    "requires_attention": 8,
    "coverage": "50.0%"
  }
}
```

### Abgelaufene Angebote bereinigen
```http
POST /api/v1/admin/cleanup/expired?dry_run=true&triggered_by=admin
```

**Dry Run Response:**
```json
{
  "analysis_date": "2025-07-10",
  "total_expired_found": 12,
  "expired_by_store": {
    "LIDL": 8,
    "Aldi Süd": 4
  },
  "expired_products": [
    {
      "id": 123,
      "name": "Bio Vollmilch",
      "store": "LIDL",
      "price": 1.59,
      "offer_valid_until": "2025-07-05",
      "availability_text": "nur in der Filiale 05.07. - 10.07.",
      "created_at": "2025-07-01T10:00:00"
    }
  ],
  "action_taken": "dry_run",
  "triggered_by": "admin",
  "note": "This was a dry run - no data was deleted"
}
```

### Alte Produkte bereinigen
```http
POST /api/v1/admin/cleanup/old-products?days_old=30&dry_run=false&triggered_by=admin
```

**Real Cleanup Response:**
```json
{
  "cutoff_date": "2025-06-10T00:00:00",
  "days_old_threshold": 30,
  "total_old_found": 25,
  "old_by_store": {
    "LIDL": 15,
    "Aldi Süd": 10
  },
  "action_taken": "deleted",
  "deleted_count": 25,
  "cleanup_id": "cleanup_old_1720602000",
  "triggered_by": "admin"
}
```

## 🔧 Integration mit bestehenden Systemen

### Lidl Crawler Integration

Der Lidl Crawler verwendet automatisch die neue Parsing-Logik:

```python
# In lidl_crawler_ultimate.py
availability, parsed_availability_text, offer_valid_until = self._parse_availability_and_date(availability_text)

product = ProductResult(
    name=name,
    price=price,
    store="LIDL",
    availability=availability,
    availability_text=parsed_availability_text,
    offer_valid_until=offer_valid_until,
    # ... andere Felder
)
```

### Datenbank-Migration

```sql
-- Neue Felder hinzugefügt
ALTER TABLE products ADD COLUMN availability_text VARCHAR(255);
ALTER TABLE products ADD COLUMN offer_valid_until VARCHAR(10);

-- Index für Performance
CREATE INDEX idx_products_offer_valid_until ON products(offer_valid_until);
```

## 📊 Monitoring & Wartung

### Empfohlene Cleanup-Routine

1. **Täglich**: Cleanup-Statistiken prüfen
   ```bash
   curl "http://localhost:8000/api/v1/admin/cleanup/statistics"
   ```

2. **Täglich**: Abgelaufene Angebote bereinigen
   ```bash
   curl -X POST "http://localhost:8000/api/v1/admin/cleanup/expired?dry_run=false"
   ```

3. **Wöchentlich**: Alte Produkte bereinigen (30+ Tage)
   ```bash
   curl -X POST "http://localhost:8000/api/v1/admin/cleanup/old-products?days_old=30&dry_run=false"
   ```

### Performance-Optimierungen

- **Indizierte Felder**: `offer_valid_until`, `deleted_at`, `created_at`
- **Soft Deletes**: Keine harten Löschungen für Audit-Trail
- **Batch Processing**: Cleanup läuft als Background-Tasks
- **Rate Limiting**: Schutz vor übermäßiger Bereinigung

## 🧪 Testing

### Verfügbarkeits-Parsing testen
```bash
cd backend
arch -arm64 python3 test_lidl_availability_parsing.py
```

**Test-Abdeckung:**
- 12 verschiedene Verfügbarkeitstext-Formate
- Datumsvalidierung (Vergangenheit/Zukunft)
- ProductResult-Erstellung mit neuen Feldern
- Echte Lidl-Crawler-Integration

### API-Tests
```bash
# Cleanup-Statistiken
curl "http://localhost:8000/api/v1/admin/cleanup/statistics"

# Dry Run Test
curl -X POST "http://localhost:8000/api/v1/admin/cleanup/expired?dry_run=true"

# Real Cleanup Test
curl -X POST "http://localhost:8000/api/v1/admin/cleanup/expired?dry_run=false"
```

## 🚀 Vorteile der neuen Architektur

### 1. Intelligente Datenbereinigung
- **Automatisch**: Abgelaufene Angebote werden erkannt
- **Datenbasiert**: Verwendung echter Store-Informationen
- **Flexibel**: Verschiedene Bereinigungsstrategien

### 2. Verbesserte Datenqualität
- **Aktualität**: Nur gültige Angebote in Suchergebnissen
- **Transparenz**: Original-Verfügbarkeitstext verfügbar
- **Nachverfolgbarkeit**: Soft Deletes mit Timestamps

### 3. Admin-Freundlichkeit
- **Dry Run**: Sichere Analyse vor tatsächlicher Bereinigung
- **Statistiken**: Detaillierte Einblicke in Datenbestand
- **Background Processing**: Keine Blockierung der API

### 4. Store-spezifische Anpassung
- **Lidl-optimiert**: Spezielle Parsing-Logik für Lidl-Texte
- **Erweiterbar**: Aldi und andere Stores später hinzufügbar
- **Robust**: Fallback-Verhalten bei unbekannten Formaten

## 🔮 Zukunftige Erweiterungen

### 1. Automatische Cleanup-Scheduler
```python
# In scheduler_service.py
@scheduler.scheduled_job('cron', hour=2)  # Täglich um 2 Uhr
async def auto_cleanup_expired():
    await cleanup_service.cleanup_expired_offers(dry_run=False)
```

### 2. Warehouse-Integration
- Lagerverfügbarkeit in Echtzeit
- Store-spezifische Verfügbarkeit
- Filial-lokale Angebote

### 3. ML-basierte Preisprognose
- Verwendung historischer Angebotsdaten
- Vorhersage von Preisänderungen
- Optimale Einkaufszeitpunkte

### 4. Push-Benachrichtigungen
- Benachrichtigung bei bald ablaufenden Angeboten
- Preisalerts für Lieblings-Produkte
- Admin-Alerts bei Cleanup-Anomalien

## 📋 Checkliste für Deployment

- [ ] Datenbank-Migration ausgeführt (`add_availability_fields.py`)
- [ ] Lidl Crawler mit neuen Feldern getestet
- [ ] Cleanup Service Funktionalität validiert
- [ ] Admin API Endpoints getestet
- [ ] Monitoring/Logging konfiguriert
- [ ] Backup-Strategie aktualisiert
- [ ] Dokumentation für Ops-Team bereitgestellt

## 💡 Best Practices

1. **Immer mit Dry Run beginnen** vor echten Cleanup-Operationen
2. **Regelmäßige Backup-Erstellung** vor größeren Bereinigungen
3. **Monitoring der Cleanup-Statistiken** für ungewöhnliche Muster
4. **Stufenweise Ausrollung** bei Produktionsumgebungen
5. **Audit-Logs** für alle Cleanup-Operationen führen 
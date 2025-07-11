# Database Integration Setup Guide

This guide covers the database integration for the price comparison application, migrating from live crawling to a database-backed system.

## Overview

The application now supports:
- PostgreSQL database for storing product data
- Automated weekly crawling with APScheduler
- Database-first search with live crawling fallback
- Admin endpoints for manual operations
- Proper data lifecycle management
- **Dynamic store creation** - stores are created only when crawled

## Prerequisites

1. **PostgreSQL Server**
   - Install PostgreSQL 13+ locally or use a cloud service
   - Create a database named `preisvergleich`
   - Create a user with appropriate permissions

2. **Environment Configuration**
   - Update your `.env` file with database settings

## Installation Steps

### 1. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Database Configuration

Create or update your `.env` file:

```env
# Database Settings
DATABASE_URL=postgresql+asyncpg://preisvergleich:password@localhost:5432/preisvergleich
DATABASE_ECHO=false

# Scheduler Settings  
ENABLE_SCHEDULER=true
WEEKLY_CRAWL_HOUR=2
WEEKLY_CRAWL_DAY_OF_WEEK=sunday
MAX_CONCURRENT_CRAWLS=2

# API Settings
DEBUG=true
ENABLE_CRAWLING=true
```

### 3. PostgreSQL Setup

#### Local PostgreSQL Installation (macOS)

```bash
# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Create database and user
psql postgres
CREATE DATABASE preisvergleich;
CREATE USER preisvergleich WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE preisvergleich TO preisvergleich;
\q
```

#### Alternative: Docker PostgreSQL

```bash
docker run --name preisvergleich-db \
  -e POSTGRES_DB=preisvergleich \
  -e POSTGRES_USER=preisvergleich \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:14
```

### 4. Database Migration

Once PostgreSQL is running, apply the database schema:

```bash
cd backend
python3 -m alembic upgrade head
```

### 5. Dynamic Store Creation

**NEW:** Stores are now created automatically when you first crawl them! No manual initialization needed.

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

The first time you trigger a crawl for a store (e.g., "Lidl" or "Aldi"), the store will be automatically created in the database.

## Architecture Overview

### Database Schema

#### Stores Table
- `id`: Primary key
- `name`: Store name (e.g., "Lidl", "Aldi")
- `logo_url`: Store logo URL
- `base_url`: Store website URL
- `enabled`: Whether store is active (default: true)
- Timestamps: `created_at`, `updated_at`

**Note:** Stores are created dynamically when first crawled, ensuring only stores with actual products exist in the database.

**Important:** The `enabled` field controls whether a store can be crawled:
- Enabled stores (`enabled=true`) will be included in crawl operations
- Disabled stores (`enabled=false`) will be skipped during crawling
- Single store crawls will be rejected if the target store is disabled
- "Crawl all" operations will automatically skip disabled stores

#### Products Table
- `id`: Primary key
- `name`: Product name
- `description`: Product description
- `brand`: Product brand
- `category`: Auto-categorized product category
- `store_id`: Foreign key to stores
- `price`: Product price (DECIMAL)
- `unit`: Product unit (e.g., "500g", "1L")
- `availability`: Boolean availability
- `image_url`: Product image URL
- `product_url`: Product page URL
- `postal_code`: Location-specific pricing
- `crawl_session_id`: Link to crawl session
- Timestamps: `created_at`, `updated_at`, `deleted_at` (soft delete)

#### Crawl Sessions Table
- `id`: Primary key
- `store_id`: Foreign key to stores
- `status`: running, completed, failed
- `started_at`, `completed_at`: Timing
- `total_products`, `success_count`, `error_count`: Statistics
- `notes`: Additional information

### Service Architecture

#### DatabaseService
- Repository pattern with separate repositories for stores, products, crawl sessions
- Async SQLAlchemy 2.0 with proper typing
- Transaction management

#### CrawlerService  
- Coordinates existing crawlers (Lidl Ultimate, Aldi Ultimate)
- **Dynamic store creation** - creates stores on first crawl
- Converts crawler results to database format
- Handles deduplication and categorization
- Manages data lifecycle (soft delete old products)

#### SchedulerService
- APScheduler integration with FastAPI
- Weekly automated crawling
- Daily cleanup tasks
- Manual trigger capabilities

## API Endpoints

### Store Management

#### Get All Stores
```
GET /api/v1/admin/stores
```
Returns all stores in the database (created through crawling).

#### Initialize Stores (DEPRECATED)
```
POST /api/v1/admin/stores/initialize
```
**DEPRECATED:** Returns info that stores are now created dynamically.

### Crawling Endpoints

#### Trigger Manual Crawl
```
POST /api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115
```
Triggers crawling for a specific store. If the store doesn't exist in the database, it will be created automatically.

```
POST /api/v1/admin/crawl/trigger?postal_code=10115
```
Triggers crawling for all available stores (based on available crawlers).

### Search Endpoints

#### Primary Search (with database support)
```
GET /api/v1/search/products?query=milch&postal_code=10115&stores=Lidl,Aldi&max_price=2.50&limit=20
```

### Dynamic Store Creation Benefits

1. **Only stores with products** - No empty stores in the database
2. **Automatic management** - No manual initialization required
3. **Clean database** - Only contains stores that are actually crawled
4. **Scalable** - Easy to add new stores by just adding crawlers
5. **Self-maintaining** - Stores are created when needed

### Migration from Static Store Initialization

If you have existing stores from manual initialization, they will continue to work normally. The new system is backward compatible but prevents creation of unused stores.

To clean up manually created unused stores:
```sql
-- Find stores with no products
SELECT s.id, s.name FROM stores s 
LEFT JOIN products p ON s.id = p.store_id 
WHERE p.id IS NULL;

-- Remove if desired (CAUTION: This permanently deletes stores)
-- DELETE FROM stores WHERE id IN (...);
``` 
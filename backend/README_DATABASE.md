# Preisvergleich Backend with Database Integration 🗄️

This README explains how to set up and use the Preisvergleich backend with PostgreSQL database integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Database Management](#database-management)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Preisvergleich backend now includes full database integration with:
- **PostgreSQL** database for persistent storage
- **SQLAlchemy 2.0** with async support
- **Alembic** for database migrations
- **APScheduler** for automated crawling
- **Lidl crawler** for product data collection

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   Database       │────│   PostgreSQL    │
│   (Backend)     │    │   Service Layer  │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │              ┌──────────────────┐
         └──────────────│   Crawler        │
                        │   Service        │
                        └──────────────────┘
```

## 🔧 Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 15+
- Homebrew (on macOS)

### Install Dependencies
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt
```

## 🗄️ Database Setup

### 1. Install PostgreSQL (macOS)

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Add to PATH (add to ~/.zshrc for persistence)
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"

# Start PostgreSQL service
brew services start postgresql@15
```

### 2. Create Database and User

```bash
# Create database
createdb preisvergleich_db

# Create user and grant privileges
psql preisvergleich_db -c "CREATE USER preisvergleich_user WITH PASSWORD 'preisvergleich_password';"
psql preisvergleich_db -c "GRANT ALL PRIVILEGES ON DATABASE preisvergleich_db TO preisvergleich_user;"
psql preisvergleich_db -c "GRANT ALL ON SCHEMA public TO preisvergleich_user;"
```

### 3. Run Database Migrations

```bash
# Run Alembic migrations to create tables
python3 -m alembic upgrade head
```

## ⚙️ Environment Configuration

Create a `.env.local` file in the backend directory:

```env
# Application Settings
APP_ENV=dev
API_TITLE=Preisvergleich API (Development)
API_VERSION=1.0.0
DEBUG=true

# Database Configuration
DATABASE_URL=postgresql+asyncpg://preisvergleich_user:preisvergleich_password@localhost/preisvergleich_db

# CORS Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","http://127.0.0.1:3000","http://127.0.0.1:8080"]

# Crawler Settings
ENABLE_CRAWLING=true
CRAWL_TIMEOUT=60

# Scheduler Settings  
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=Europe/Berlin

# Lidl Crawler
LIDL_CRAWLER_ENABLED=true
LIDL_BASE_URL=https://www.lidl.de

# Logging
LOG_LEVEL=INFO
```

## 🚀 Running the Application

### 1. Start PostgreSQL (if not auto-starting)
```bash
brew services start postgresql@15
```

### 2. Start the FastAPI Server
```bash
# Load environment variables and start server
export $(cat .env.local | xargs) && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Verify Setup
```bash
# Test API
curl http://localhost:8000/

# Initialize default stores
curl -X POST http://localhost:8000/api/v1/admin/stores/initialize
```

## 🗄️ Database Management

### Viewing Database Tables

#### Option 1: Command Line (psql)
```bash
# Connect to database
psql -U preisvergleich_user -d preisvergleich_db -h localhost

# List tables
\dt

# View stores
SELECT * FROM stores;

# View products
SELECT * FROM products LIMIT 10;

# View crawl sessions
SELECT * FROM crawl_sessions;

# Exit
\q
```

#### Option 2: pgAdmin (GUI)
1. Download and install [pgAdmin](https://www.pgadmin.org/)
2. Create new server connection:
   - Host: `localhost`
   - Port: `5432`
   - Database: `preisvergleich_db`
   - Username: `preisvergleich_user`
   - Password: `preisvergleich_password`

#### Option 3: VS Code Extension
Install the "PostgreSQL" extension in VS Code for integrated database management.

### Database Schema

#### Tables Overview
```sql
-- Stores (supermarkets)
stores: id, name, logo_url, base_url, enabled, created_at, updated_at

-- Products (crawled items)
products: id, name, description, brand, category, store_id, price, unit, 
         availability, image_url, product_url, postal_code, crawl_session_id,
         created_at, updated_at, deleted_at

-- Crawl Sessions (tracking crawl runs)
crawl_sessions: id, store_id, status, started_at, completed_at, 
               total_products, success_count, error_count, notes

-- Migration Tracking
alembic_version: version_num
```

### Common Database Operations

```bash
# View table structure
psql -U preisvergleich_user -d preisvergleich_db -h localhost -c "\d products"

# Count products by store
psql -U preisvergleich_user -d preisvergleich_db -h localhost -c "
SELECT s.name, COUNT(p.id) as product_count 
FROM stores s 
LEFT JOIN products p ON s.id = p.store_id 
WHERE p.deleted_at IS NULL 
GROUP BY s.name;"

# View recent crawl sessions
psql -U preisvergleich_user -d preisvergleich_db -h localhost -c "
SELECT cs.*, s.name as store_name 
FROM crawl_sessions cs 
JOIN stores s ON cs.store_id = s.id 
ORDER BY cs.started_at DESC 
LIMIT 5;"
```

## 🌐 API Endpoints

### Health & Info
- `GET /` - API information
- `GET /docs` - Swagger documentation
- `GET /api/v1/health` - Health check

### Search
- `GET /api/v1/stores` - List available stores
- `POST /api/v1/search` - Search products (database + live fallback)
- `GET /api/v1/search/database` - Database-only search

### Admin & Management
- `POST /api/v1/admin/stores/initialize` - Initialize default stores
- `POST /api/v1/admin/crawl/trigger` - Manual crawl trigger
- `GET /api/v1/admin/crawl/status` - Crawl status
- `POST /api/v1/admin/crawl/cleanup` - Clean old data

### Example API Calls

```bash
# Search products in database
curl "http://localhost:8000/api/v1/search/database?query=Milch&postal_code=10115"

# Trigger manual crawl for Lidl
curl -X POST "http://localhost:8000/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115"

# Get crawl statistics
curl "http://localhost:8000/api/v1/admin/crawl/status"
```

## 🔄 Database Migrations

### Creating New Migrations
```bash
# Generate migration for model changes
python3 -m alembic revision --autogenerate -m "Description of changes"

# Apply migrations
python3 -m alembic upgrade head
```

### Migration Management
```bash
# Check current migration version
python3 -m alembic current

# View migration history
python3 -m alembic history

# Rollback to previous migration
python3 -m alembic downgrade -1
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if stopped
brew services start postgresql@15

# Test connection
psql -U preisvergleich_user -d preisvergleich_db -h localhost -c "SELECT 1;"
```

#### 2. Permission Denied
```bash
# Grant additional privileges if needed
psql preisvergleich_db -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO preisvergleich_user;"
psql preisvergleich_db -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO preisvergleich_user;"
```

#### 3. Migration Issues
```bash
# Reset migrations (WARNING: loses data)
python3 -m alembic downgrade base
python3 -m alembic upgrade head

# Or recreate database
dropdb preisvergleich_db
createdb preisvergleich_db
python3 -m alembic upgrade head
```

#### 4. Environment Variables Not Loaded
```bash
# Load manually before starting server
export $(cat .env.local | xargs)

# Or use python-dotenv in code
pip install python-dotenv
```

### Logs and Debugging

```bash
# View application logs
tail -f logs/app.log

# PostgreSQL logs (macOS Homebrew)
tail -f /usr/local/var/log/postgresql@15.log

# Enable SQLAlchemy query logging
export SQLALCHEMY_ECHO=true
```

## 📊 Performance Monitoring

### Database Statistics
```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public';

-- Index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes;
```

### Optimization Tips
1. **Indexes**: Key indexes are automatically created for foreign keys and search fields
2. **Cleanup**: Soft-deleted products are automatically cleaned up by scheduler
3. **Connection Pool**: AsyncPG handles connection pooling efficiently
4. **Monitoring**: Use pgAdmin or monitoring tools for production

## 🔄 Backup and Restore

### Backup Database
```bash
# Full backup
pg_dump -U preisvergleich_user -h localhost preisvergleich_db > backup.sql

# Data-only backup
pg_dump -U preisvergleich_user -h localhost --data-only preisvergleich_db > data_backup.sql
```

### Restore Database
```bash
# Restore full backup
psql -U preisvergleich_user -h localhost preisvergleich_db < backup.sql

# Restore data only
psql -U preisvergleich_user -h localhost preisvergleich_db < data_backup.sql
```

---

## 🎯 Next Steps

1. **Test Crawling**: Trigger manual crawls to populate the database
2. **Monitor Performance**: Watch database growth and query performance
3. **Schedule Automation**: Enable weekly crawling via scheduler
4. **Add More Stores**: Implement additional supermarket crawlers
5. **Frontend Integration**: Connect frontend to database-backed API

For more information, see [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed implementation notes. 
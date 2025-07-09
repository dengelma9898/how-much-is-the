# Database Integration Setup Guide

This guide covers the database integration for the price comparison application, migrating from live crawling to a database-backed system.

## Overview

The application now supports:
- PostgreSQL database for storing product data
- Automated weekly crawling with APScheduler
- Database-first search with live crawling fallback
- Admin endpoints for manual operations
- Proper data lifecycle management

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

### 5. Initialize Default Data

Start the application to initialize default stores:

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

Or manually initialize via API:

```bash
curl -X POST http://localhost:8000/api/v1/admin/stores/initialize
```

## Architecture Overview

### Database Schema

#### Stores Table
- `id`: Primary key
- `name`: Store name (Lidl, and others when implemented)
- `logo_url`: Store logo URL
- `base_url`: Store website URL
- `enabled`: Whether store is active
- Timestamps: `created_at`, `updated_at`

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
- Coordinates existing Lidl crawler (Aldi temporarily disabled)
- Converts crawler results to database format
- Handles deduplication and categorization
- Manages data lifecycle (soft delete old products)

#### SchedulerService
- APScheduler integration with FastAPI
- Weekly automated crawling
- Daily cleanup tasks
- Manual trigger capabilities

## API Endpoints

### Search Endpoints

#### Primary Search (with database support)
```
POST /api/v1/search
{
  "query": "Milch",
  "postal_code": "10115"
}

Query Parameters:
- use_database=true: Use database search first
- fallback_to_live=true: Fallback to live crawling if no DB results
```

#### Database-only Search
```
GET /api/v1/search/database?query=Milch&postal_code=10115
```

### Admin Endpoints

#### Scheduler Management
```
GET /api/v1/admin/scheduler/status
POST /api/v1/admin/scheduler/start
POST /api/v1/admin/scheduler/stop
```

#### Manual Operations
```
POST /api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=10115
POST /api/v1/admin/crawl/cleanup
```

#### Statistics and Monitoring
```
GET /api/v1/admin/crawl/statistics?days=7
GET /api/v1/admin/database/stats
GET /api/v1/admin/stores
```

## Usage Scenarios

### 1. Development Without Database

The application gracefully handles missing database connections:
- Database operations are commented out in startup
- Search falls back to live crawling
- Admin endpoints return appropriate errors

### 2. Production with Database

1. **Initial Setup**: Run migrations, initialize stores
2. **First Crawl**: Trigger manual crawl to populate data
3. **Automated Operation**: Weekly scheduler maintains fresh data
4. **Search**: Fast database searches with live fallback

### 3. Hybrid Mode

- Use database for common queries (fast response)
- Use live crawling for specific/rare queries
- Gradually populate database with more comprehensive data

## Monitoring and Maintenance

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/v1/health

# Admin health with system status  
curl http://localhost:8000/api/v1/admin/health

# Search functionality health
curl http://localhost:8000/api/v1/health/search
```

### Database Maintenance

#### View Recent Crawl Sessions
```sql
SELECT s.name, cs.status, cs.started_at, cs.success_count, cs.error_count
FROM crawl_sessions cs 
JOIN stores s ON cs.store_id = s.id 
ORDER BY cs.started_at DESC LIMIT 10;
```

#### Product Statistics
```sql
SELECT s.name, COUNT(*) as products, AVG(p.price) as avg_price
FROM products p 
JOIN stores s ON p.store_id = s.id 
WHERE p.deleted_at IS NULL 
GROUP BY s.name;
```

#### Cleanup Old Products
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/products/cleanup/30
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection string in `.env`
   - Check user permissions

2. **Migration Errors**
   - Ensure database exists and user has privileges
   - Check Alembic configuration
   - Try `alembic revision --autogenerate` for schema drift

3. **Scheduler Not Working**
   - Check `ENABLE_SCHEDULER=true` in config
   - Verify timezone settings
   - Check logs for APScheduler errors

4. **No Products Found**
   - Run manual crawl first: `POST /api/v1/admin/crawl/trigger`
   - Check crawler services are working
   - Verify store initialization

### Logs and Debugging

The application uses structured logging:
- INFO level for normal operations
- ERROR level for failures
- Crawler progress and statistics logged

Enable database query logging:
```env
DATABASE_ECHO=true
```

## Performance Considerations

### Database Optimization

1. **Indexes**: Pre-configured indexes on commonly searched fields
2. **Soft Deletes**: Old products marked as deleted, not removed immediately
3. **Pagination**: Search results properly paginated
4. **Connection Pooling**: Async connection pooling configured

### Caching Strategy

Future enhancements could include:
- Redis caching for frequent searches  
- CDN for product images
- Search result caching

### Scaling Considerations

- Database: Consider read replicas for heavy search loads
- Crawling: Implement distributed crawling for more stores
- API: Load balancing and rate limiting

## Migration from Live-Only System

### Gradual Migration

1. **Phase 1**: Deploy with database disabled, test compatibility
2. **Phase 2**: Enable database, run alongside live crawling
3. **Phase 3**: Prefer database results, fallback to live
4. **Phase 4**: Full database-first operation

### Data Migration

For existing installations:
1. Deploy new code with database integration
2. Run initial comprehensive crawl
3. Verify data quality and coverage
4. Switch to database-first mode

## Future Enhancements

### Planned Features

1. **Full-Text Search**: PostgreSQL full-text search capabilities
2. **Price History**: Track price changes over time
3. **Alert System**: Price drop notifications
4. **Analytics**: Search patterns and popular products
5. **API Rate Limiting**: Protect against abuse
6. **Multi-Region**: Support for different geographical regions

### Advanced Monitoring

1. **Metrics**: Prometheus/Grafana integration
2. **Alerting**: Failed crawl notifications
3. **Performance**: Query optimization and monitoring
4. **Costs**: Track crawling costs and API usage

This database integration provides a solid foundation for scaling the price comparison service while maintaining the flexibility of the original live crawling approach. 
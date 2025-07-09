import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..core.database import get_async_session
from ..services.database_service import DatabaseService
from ..services.scheduler_service import scheduler_service
from ..services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for database service
async def get_database_service(session = Depends(get_async_session)) -> DatabaseService:
    """Get database service instance"""
    return DatabaseService(session)


@router.get("/health")
async def admin_health():
    """Admin health check with system status"""
    try:
        return {
            "status": "healthy",
            "scheduler": {
                "running": scheduler_service.is_running,
                "status": "enabled" if scheduler_service.is_running else "disabled"
            },
            "database": {
                "status": "connected"  # Will be checked when DB is available
            }
        }
    except Exception as e:
        logger.error(f"Admin health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and job information"""
    try:
        return scheduler_service.get_job_status()
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler service"""
    try:
        if scheduler_service.is_running:
            return {"message": "Scheduler is already running"}
        
        await scheduler_service.start()
        return {"message": "Scheduler started successfully"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler service"""
    try:
        if not scheduler_service.is_running:
            return {"message": "Scheduler is not running"}
        
        await scheduler_service.stop()
        return {"message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")


@router.post("/crawl/trigger")
async def trigger_manual_crawl(
    background_tasks: BackgroundTasks,
    store_name: Optional[str] = None,
    postal_code: str = "10115"
):
    """Manually trigger crawl for specific store or all stores"""
    try:
        # Run crawl in background
        background_tasks.add_task(
            scheduler_service.trigger_crawl_now,
            store_name=store_name,
            postal_code=postal_code
        )
        
        return {
            "message": f"Crawl triggered for {store_name or 'all stores'}",
            "postal_code": postal_code,
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Error triggering manual crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering crawl: {str(e)}")


@router.post("/crawl/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Manually trigger database cleanup"""
    try:
        # Run cleanup in background
        background_tasks.add_task(scheduler_service.trigger_cleanup_now)
        
        return {
            "message": "Cleanup triggered",
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Error triggering cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering cleanup: {str(e)}")


@router.get("/crawl/statistics")
async def get_crawl_statistics(
    days: int = 7,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get crawling statistics for the last N days"""
    try:
        crawler_service = CrawlerService(db_service)
        stats = await crawler_service.get_crawl_statistics(days=days)
        return stats
    except Exception as e:
        logger.error(f"Error getting crawl statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/stores")
async def get_stores(db_service: DatabaseService = Depends(get_database_service)):
    """Get all stores"""
    try:
        stores = await db_service.stores.get_all_enabled()
        return [
            {
                "id": store.id,
                "name": store.name,
                "logo_url": store.logo_url,
                "base_url": store.base_url,
                "enabled": store.enabled,
                "created_at": store.created_at.isoformat(),
                "updated_at": store.updated_at.isoformat()
            }
            for store in stores
        ]
    except Exception as e:
        logger.error(f"Error getting stores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stores: {str(e)}")


@router.post("/stores/initialize")
async def initialize_default_stores(db_service: DatabaseService = Depends(get_database_service)):
    """Initialize default stores (Lidl)"""
    try:
        await db_service.initialize_stores()
        return {"message": "Default stores initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing stores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing stores: {str(e)}")


@router.get("/database/stats")
async def get_database_stats(db_service: DatabaseService = Depends(get_database_service)):
    """Get database statistics"""
    try:
        # Get product counts by store
        from sqlalchemy import select, func
        from ..models.database_models import DatabaseProduct, DatabaseStore
        
        result = await db_service.session.execute(
            select(
                DatabaseStore.name,
                func.count(DatabaseProduct.id).label('product_count'),
                func.count(DatabaseProduct.id).filter(DatabaseProduct.deleted_at.is_(None)).label('active_products'),
                func.avg(DatabaseProduct.price).label('avg_price')
            )
            .outerjoin(DatabaseProduct)
            .group_by(DatabaseStore.id, DatabaseStore.name)
        )
        
        store_stats = []
        for row in result:
            store_stats.append({
                "store_name": row.name,
                "total_products": row.product_count or 0,
                "active_products": row.active_products or 0,
                "average_price": float(row.avg_price) if row.avg_price else 0.0
            })
        
        return {
            "stores": store_stats,
            "last_updated": "2025-01-09"  # Will be dynamic when crawler runs
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {str(e)}")


@router.delete("/products/cleanup/{days}")
async def cleanup_old_products(
    days: int,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Cleanup products older than specified days"""
    if days < 1:
        raise HTTPException(status_code=400, detail="Days must be greater than 0")
    
    try:
        # Run cleanup in background
        async def cleanup_task():
            deleted_count = await db_service.products.hard_delete_old_products(days_old=days)
            await db_service.commit()
            logger.info(f"Manual cleanup: deleted {deleted_count} products older than {days} days")
        
        background_tasks.add_task(cleanup_task)
        
        return {
            "message": f"Cleanup started for products older than {days} days",
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Error triggering product cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering cleanup: {str(e)}")


@router.get("/logs/recent")
async def get_recent_logs():
    """Get recent application logs (placeholder)"""
    # This is a placeholder - in production you might want to integrate with 
    # a proper logging system or read from log files
    return {
        "message": "Log endpoint placeholder",
        "note": "In production, this would return recent application logs",
        "logs": [
            {
                "timestamp": "2025-01-09T12:00:00",
                "level": "INFO",
                "message": "Scheduler service started"
            },
            {
                "timestamp": "2025-01-09T12:01:00", 
                "level": "INFO",
                "message": "Weekly crawl job scheduled"
            }
        ]
    } 
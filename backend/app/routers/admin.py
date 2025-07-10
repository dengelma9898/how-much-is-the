import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from ..core.database import get_async_session
from ..services.database_service import DatabaseService
from ..services.scheduler_service import scheduler_service
from ..services.crawler_service import CrawlerService
from ..services.crawl_status_service import crawl_status_service, CrawlType

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
            },
            "crawl_service": {
                "active_crawls": len(crawl_status_service.get_active_crawls()),
                "can_accept_new_crawls": True
            }
        }
    except Exception as e:
        logger.error(f"Admin health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/system/overview")
async def get_system_overview():
    """Get comprehensive system overview with enhanced metrics"""
    try:
        system_overview = crawl_status_service.get_system_overview()
        scheduler_status = scheduler_service.get_job_status()
        
        return {
            "system_status": "operational",
            "crawl_service": system_overview,
            "scheduler": scheduler_status,
            "timestamp": "2025-01-09T20:00:00Z"  # Will be dynamic
        }
    except Exception as e:
        logger.error(f"Error getting system overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system overview: {str(e)}")


@router.get("/crawl/status/overview")
async def get_crawl_overview():
    """Get real-time overview of all crawl activities"""
    try:
        active_crawls = crawl_status_service.get_active_crawls()
        recent_history = crawl_status_service.get_crawl_history(limit=10)
        system_overview = crawl_status_service.get_system_overview()
        
        return {
            "active_crawls": active_crawls,
            "recent_completed": recent_history,
            "summary": system_overview,
            "refresh_interval_seconds": 5
        }
    except Exception as e:
        logger.error(f"Error getting crawl overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting crawl overview: {str(e)}")


@router.get("/crawl/status/{crawl_id}")
async def get_crawl_status(crawl_id: str):
    """Get detailed status for a specific crawl operation"""
    try:
        status = crawl_status_service.get_crawl_status(crawl_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Crawl {crawl_id} not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crawl status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting crawl status: {str(e)}")


@router.get("/crawl/store/{store_name}/status")
async def get_store_crawl_status(store_name: str):
    """Get comprehensive crawl status for a specific store"""
    try:
        status = crawl_status_service.get_store_status(store_name)
        return status
    except Exception as e:
        logger.error(f"Error getting store status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting store status: {str(e)}")


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
    postal_code: str = "10115",
    triggered_by: str = Query("admin", description="Who triggered this crawl")
):
    """Enhanced manual crawl trigger with progress tracking"""
    try:
        # Pre-check rate limiting and store availability
        if store_name:
            store_status = crawl_status_service.get_store_status(store_name)
            if not store_status["can_crawl_now"]:
                next_allowed = store_status["next_allowed_crawl"]
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded for {store_name}. Next crawl allowed at {next_allowed}"
                )
            
            if store_status["active_crawl"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Store {store_name} is already being crawled"
                )
        
        # Start crawl tracking
        try:
            crawl_id = crawl_status_service.start_crawl(
                store_name=store_name or "all_stores",
                crawl_type=CrawlType.MANUAL,
                postal_code=postal_code,
                triggered_by=triggered_by
            )
        except ValueError as e:
            raise HTTPException(status_code=429, detail=str(e))
        
        # Run enhanced crawl in background
        background_tasks.add_task(
            _enhanced_trigger_crawl,
            crawl_id=crawl_id,
            store_name=store_name,
            postal_code=postal_code
        )
        
        return {
            "message": f"Crawl triggered for {store_name or 'all stores'}",
            "crawl_id": crawl_id,
            "postal_code": postal_code,
            "status": "started",
            "status_endpoint": f"/api/v1/admin/crawl/status/{crawl_id}",
            "triggered_by": triggered_by
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering crawl: {str(e)}")


async def _enhanced_trigger_crawl(crawl_id: str, store_name: Optional[str], postal_code: str):
    """Enhanced crawl execution with progress tracking"""
    try:
        # Update status to initializing
        crawl_status_service.update_crawl_progress(
            crawl_id, 
            status=crawl_status_service.CrawlStatus.INITIALIZING,
            current_step="Initializing crawl session"
        )
        
        # Run the actual crawl
        results = await scheduler_service.trigger_crawl_now(
            store_name=store_name,
            postal_code=postal_code
        )
        
        # Process results and update tracking
        total_products = 0
        total_errors = 0
        all_successful = True
        
        for result in results:
            if result.get("success"):
                total_products += result.get("products_crawled", 0)
                total_errors += result.get("errors", 0)
            else:
                all_successful = False
                total_errors += 1
        
        # Complete the crawl tracking
        final_status = crawl_status_service.CrawlStatus.COMPLETED if all_successful else crawl_status_service.CrawlStatus.FAILED
        
        crawl_status_service.complete_crawl(
            crawl_id,
            status=final_status,
            final_products_count=total_products,
            error_details=None if all_successful else f"Some stores failed. Total errors: {total_errors}"
        )
        
    except Exception as e:
        logger.error(f"Enhanced crawl {crawl_id} failed: {str(e)}")
        crawl_status_service.complete_crawl(
            crawl_id,
            status=crawl_status_service.CrawlStatus.FAILED,
            error_details=str(e)
        )


@router.delete("/crawl/{crawl_id}")
async def cancel_crawl(crawl_id: str, reason: str = Query("Manual cancellation")):
    """Cancel an active crawl operation"""
    try:
        success = crawl_status_service.cancel_crawl(crawl_id, reason)
        if not success:
            raise HTTPException(status_code=404, detail=f"Crawl {crawl_id} not found or already completed")
        
        return {
            "message": f"Crawl {crawl_id} cancelled",
            "reason": reason
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cancelling crawl: {str(e)}")


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
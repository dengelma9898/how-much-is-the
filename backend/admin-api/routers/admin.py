import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from shared.core.database import get_async_session_rw
from shared.services.database_service import DatabaseService
from services.scheduler_service import scheduler_service
from services.crawler_service import CrawlerService
from services.crawl_status_service import crawl_status_service, CrawlType, CrawlStatus
from services.cleanup_service import cleanup_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for read-write database service
async def get_database_service(session = Depends(get_async_session_rw)) -> DatabaseService:
    """Get read-write database service instance for admin operations"""
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
            status=CrawlStatus.INITIALIZING,
            current_step="Initializing crawl session"
        )
        
        # Create a new database session for this background task
        from shared.core.database import async_session_maker_rw
        from shared.services.database_service import DatabaseService
        from services.crawler_service import CrawlerService
        
        async with async_session_maker_rw() as session:
            db_service = DatabaseService(session)
            crawler_service = CrawlerService(db_service)
            
            if store_name:
                # Crawl specific store - validate crawler exists
                if store_name not in crawler_service.crawlers:
                    raise ValueError(f"No crawler available for store: {store_name}")
                
                # Get or create store dynamically 
                store = await crawler_service._ensure_store_exists(store_name)
                stores = [store]
            else:
                # Crawl all available stores (using crawler service knowledge)
                stores = []
                for available_store_name in crawler_service.crawlers.keys():
                    try:
                        store = await crawler_service._ensure_store_exists(available_store_name)
                        stores.append(store)
                    except Exception as e:
                        logger.warning(f"Could not prepare store {available_store_name}: {e}")
                        continue
            
            results = []
            
            for store in stores:
                try:
                    # Start crawl session
                    crawl_session = await db_service.crawl_sessions.create(store.id)
                    await db_service.commit()
                    
                    # Run crawler with enhanced tracking
                    success_count, error_count = await crawler_service.crawl_store(
                        store_name=store.name,
                        postal_code=postal_code,
                        crawl_session_id=crawl_session.id,
                        crawl_id=crawl_id  # Pass the crawl_id for progress tracking
                    )
                    
                    # Update session
                    await db_service.crawl_sessions.complete(
                        session_id=crawl_session.id,
                        total_products=success_count + error_count,
                        success_count=success_count,
                        error_count=error_count,
                        notes="Manual crawl triggered"
                    )
                    
                    results.append({
                        "store": store.name,
                        "success": True,
                        "products_crawled": success_count,
                        "errors": error_count
                    })
                    
                except Exception as e:
                    logger.error(f"Error in enhanced crawl for {store.name}: {str(e)}")
                    
                    # Mark session as failed if it exists
                    if 'crawl_session' in locals():
                        await db_service.crawl_sessions.fail(
                            crawl_session.id,
                            f"Enhanced crawl error: {str(e)}"
                        )
                    
                    results.append({
                        "store": store.name,
                        "success": False,
                        "error": str(e)
                    })
                
                await db_service.commit()
        
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
        final_status = CrawlStatus.COMPLETED if all_successful else CrawlStatus.FAILED
        
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
            status=CrawlStatus.FAILED,
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
    """DEPRECATED: Stores are now created dynamically during crawling"""
    return {
        "message": "Store initialization is now handled automatically during crawling",
        "note": "Stores are created dynamically when first crawled to ensure only stores with products exist",
        "deprecated": True
    }


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


@router.get("/cleanup/statistics")
async def get_cleanup_statistics():
    """Get statistics about products that need cleanup"""
    try:
        stats = await cleanup_service.get_cleanup_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting cleanup statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting cleanup statistics: {str(e)}")


@router.post("/cleanup/expired")
async def cleanup_expired_offers(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(True, description="If true, only analyze without deleting"),
    triggered_by: str = Query("admin", description="Who triggered this cleanup")
):
    """Cleanup expired offers based on offer_valid_until dates"""
    try:
        from datetime import datetime
        
        if dry_run:
            # Immediate analysis for dry run
            result = await cleanup_service.cleanup_expired_offers(dry_run=True)
            return {
                **result,
                "triggered_by": triggered_by,
                "note": "This was a dry run - no data was deleted"
            }
        else:
            # Background cleanup for real deletion
            cleanup_id = f"cleanup_expired_{int(datetime.utcnow().timestamp())}"
            
            background_tasks.add_task(
                _run_expired_cleanup,
                cleanup_id=cleanup_id,
                triggered_by=triggered_by
            )
            
            return {
                "message": "Expired offers cleanup started in background",
                "cleanup_id": cleanup_id,
                "triggered_by": triggered_by,
                "note": "Check logs for completion status"
            }
            
    except Exception as e:
        logger.error(f"Error in expired offers cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in cleanup: {str(e)}")


@router.post("/cleanup/old-products")
async def cleanup_old_products_endpoint(
    background_tasks: BackgroundTasks,
    days_old: int = Query(30, description="Delete products older than X days"),
    dry_run: bool = Query(True, description="If true, only analyze without deleting"),
    triggered_by: str = Query("admin", description="Who triggered this cleanup")
):
    """Cleanup old products without offer end dates"""
    try:
        from datetime import datetime
        
        if dry_run:
            # Immediate analysis for dry run
            result = await cleanup_service.cleanup_old_products(days_old=days_old, dry_run=True)
            return {
                **result,
                "triggered_by": triggered_by,
                "note": "This was a dry run - no data was deleted"
            }
        else:
            # Background cleanup for real deletion
            cleanup_id = f"cleanup_old_{int(datetime.utcnow().timestamp())}"
            
            background_tasks.add_task(
                _run_old_products_cleanup,
                cleanup_id=cleanup_id,
                days_old=days_old,
                triggered_by=triggered_by
            )
            
            return {
                "message": f"Old products cleanup started (older than {days_old} days)",
                "cleanup_id": cleanup_id,
                "triggered_by": triggered_by,
                "note": "Check logs for completion status"
            }
            
    except Exception as e:
        logger.error(f"Error in old products cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in cleanup: {str(e)}")


async def _run_expired_cleanup(cleanup_id: str, triggered_by: str):
    """Background task for expired offers cleanup"""
    try:
        logger.info(f"🧹 Starting expired offers cleanup {cleanup_id} (triggered by {triggered_by})")
        result = await cleanup_service.cleanup_expired_offers(dry_run=False)
        logger.info(f"✅ Expired offers cleanup {cleanup_id} completed: {result}")
    except Exception as e:
        logger.error(f"❌ Expired offers cleanup {cleanup_id} failed: {e}")


async def _run_old_products_cleanup(cleanup_id: str, days_old: int, triggered_by: str):
    """Background task for old products cleanup"""
    try:
        logger.info(f"🧹 Starting old products cleanup {cleanup_id} (triggered by {triggered_by})")
        result = await cleanup_service.cleanup_old_products(days_old=days_old, dry_run=False)
        logger.info(f"✅ Old products cleanup {cleanup_id} completed: {result}")
    except Exception as e:
        logger.error(f"❌ Old products cleanup {cleanup_id} failed: {e}") 
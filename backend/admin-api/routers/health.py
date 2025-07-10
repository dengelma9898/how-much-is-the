import logging
from fastapi import APIRouter, HTTPException

from shared.core.database import async_session_maker_rw
from shared.services.database_service import DatabaseService
from ..services.scheduler_service import scheduler_service
from ..services.crawl_status_service import crawl_status_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def admin_health_check():
    """
    Health check für die Admin API mit erweiterten System-Informationen
    """
    try:
        # Test read-write database connection
        async with async_session_maker_rw() as session:
            db_service = DatabaseService(session)
            # Comprehensive database test
            stores = await db_service.stores.get_all_enabled()
            store_count = len(stores)
        
        return {
            "status": "healthy",
            "service": "admin-api",
            "access_level": "read-write",
            "database": {
                "status": "connected",
                "stores_available": store_count
            },
            "scheduler": {
                "running": scheduler_service.is_running,
                "status": "enabled" if scheduler_service.is_running else "disabled"
            },
            "crawl_service": {
                "active_crawls": len(crawl_status_service.get_active_crawls()),
                "can_accept_new_crawls": True
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"[ADMIN-API] Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "service": "admin-api",
                "error": str(e)
            }
        ) 
import logging
from fastapi import APIRouter, HTTPException, Depends

from shared.core.database import get_async_session_ro
from shared.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check für die Client API
    """
    try:
        # Test read-only database connection
        from shared.core.database import async_session_maker_ro
        async with async_session_maker_ro() as session:
            db_service = DatabaseService(session)
            # Simple database test - get store count
            stores = await db_service.stores.get_all_enabled()
            store_count = len(stores)
        
        return {
            "status": "healthy",
            "service": "client-api",
            "access_level": "read-only",
            "database": {
                "status": "connected",
                "stores_available": store_count
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"[CLIENT-API] Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "service": "client-api",
                "error": str(e)
            }
        ) 
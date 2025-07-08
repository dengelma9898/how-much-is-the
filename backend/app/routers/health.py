from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "service": "Preisvergleich API",
        "version": "1.0.0",
        "firecrawl_enabled": settings.firecrawl_enabled
    } 
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.search import SearchRequest, SearchResponse, StoresResponse
from app.services.search_service import search_service
from app.core.database import get_async_session
from app.services.database_service import DatabaseService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for database service
async def get_database_service(session = Depends(get_async_session)) -> DatabaseService:
    """Get database service instance"""
    return DatabaseService(session)


@router.post("/search", response_model=SearchResponse)
async def search_products(
    search_request: SearchRequest,
    use_database: bool = Query(default=True, description="Use database search instead of live crawling"),
    fallback_to_live: bool = Query(default=True, description="Fallback to live crawling if no database results"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Suche nach Produkten in verschiedenen Supermärkten
    
    - **query**: Suchbegriff (z.B. "Milch", "Oatly", "Haribo")
    - **postal_code**: Deutsche Postleitzahl (5 Ziffern)
    - **use_database**: Verwende Datenbank-Suche (Standard: true)
    - **fallback_to_live**: Bei leeren DB-Ergebnissen live crawlen (Standard: true)
    
    Gibt eine Liste von Produkten sortiert nach Preis zurück.
    """
    try:
        # Try database search first if enabled
        if use_database:
            try:
                logger.info(f"Searching database for query: {search_request.query}")
                
                # Search in database
                db_products = await db_service.search_products(
                    query=search_request.query,
                    postal_code=search_request.postal_code,
                    stores=search_request.stores,
                    max_price=search_request.max_price,
                    limit=50,
                    offset=0
                )
                
                if db_products:
                    logger.info(f"Found {len(db_products)} products in database")
                    return SearchResponse(
                        query=search_request.query,
                        postal_code=search_request.postal_code,
                        products=db_products,
                        source="database",
                        total_products=len(db_products)
                    )
                else:
                    logger.info("No products found in database")
                    if not fallback_to_live:
                        return SearchResponse(
                            query=search_request.query,
                            postal_code=search_request.postal_code,
                            products=[],
                            source="database",
                            total_products=0
                        )
                    
            except Exception as e:
                logger.error(f"Database search failed: {str(e)}")
                if not fallback_to_live:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Database search failed: {str(e)}"
                    )
        
        # Fallback to live crawling or direct live search
        if not use_database or fallback_to_live:
            logger.info(f"Performing live crawl for query: {search_request.query}")
            response = await search_service.search_products(search_request)
            
            # Add source information
            response.source = "live_crawl"
            return response
            
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler bei der Produktsuche: {str(e)}")


@router.get("/search/database")
async def search_database_only(
    query: str,
    postal_code: str,
    stores: Optional[List[str]] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Direkte Datenbank-Suche ohne Fallback zum Live-Crawling
    
    Für schnelle Suchen in bereits gecrawlten Daten.
    """
    try:
        logger.info(f"Database-only search for query: {query}")
        
        products = await db_service.search_products(
            query=query,
            postal_code=postal_code,
            stores=stores,
            max_price=max_price,
            category=category,
            limit=limit,
            offset=offset
        )
        
        return SearchResponse(
            query=query,
            postal_code=postal_code,
            products=products,
            source="database_only",
            total_products=len(products)
        )
        
    except Exception as e:
        logger.error(f"Database search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database search failed: {str(e)}")


@router.get("/stores", response_model=StoresResponse)
async def get_stores(
    use_database: bool = Query(default=True, description="Get stores from database"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Gibt eine Liste aller verfügbaren Supermärkte zurück
    """
    try:
        if use_database:
            try:
                # Get stores from database
                db_stores = await db_service.stores.get_all_enabled()
                
                stores = []
                for db_store in db_stores:
                    stores.append({
                        "name": db_store.name,
                        "logo_url": db_store.logo_url,
                        "enabled": db_store.enabled
                    })
                
                if stores:
                    return StoresResponse(
                        stores=stores,
                        source="database"
                    )
                    
            except Exception as e:
                logger.error(f"Database stores query failed: {str(e)}")
        
        # Fallback to static stores list
        response = await search_service.get_stores()
        response.source = "static"
        return response
        
    except Exception as e:
        logger.error(f"Error getting stores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Stores: {str(e)}")


@router.get("/health/search")
async def search_health():
    """Health check for search functionality"""
    try:
        # Test basic search service
        static_stores = await search_service.get_stores()
        
        return {
            "status": "healthy",
            "search_service": "available",
            "static_stores_count": len(static_stores.stores),
            "database_search": "enabled" if settings.database_url else "disabled",
            "live_crawling": "enabled" if settings.enable_crawling else "disabled"
        }
    except Exception as e:
        logger.error(f"Search health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search health check failed: {str(e)}") 
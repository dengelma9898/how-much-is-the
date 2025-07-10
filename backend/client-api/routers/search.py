import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends

from shared.models.search import SearchRequest, SearchResponse, StoresResponse, Store
from shared.core.database import get_async_session_ro
from shared.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for read-only database service
async def get_database_service(session = Depends(get_async_session_ro)) -> DatabaseService:
    """Get read-only database service instance"""
    return DatabaseService(session)


@router.post("/search", response_model=SearchResponse)
async def search_products(
    search_request: SearchRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Suche nach Produkten in der Datenbank (Read-only)
    
    - **query**: Suchbegriff (z.B. "Milch", "Oatly", "Haribo")
    - **postal_code**: Deutsche Postleitzahl (5 Ziffern)
    - **stores**: Optional - Liste der gewünschten Stores
    - **max_price**: Optional - Maximaler Preis in Euro
    
    Gibt eine Liste von Produkten sortiert nach Preis zurück.
    """
    try:
        logger.info(f"[CLIENT-API] Searching database for query: {search_request.query}")
        
        # Search in database (read-only)
        db_products = await db_service.search_products(
            query=search_request.query,
            postal_code=search_request.postal_code,
            stores=search_request.stores,
            max_price=search_request.max_price,
            limit=50,
            offset=0
        )
        
        logger.info(f"[CLIENT-API] Found {len(db_products)} products in database")
        
        # Return app-compatible response using legacy field names
        return SearchResponse(
            query=search_request.query,
            postal_code=search_request.postal_code,
            products=db_products,
            source="database",
            total_products=len(db_products),
            search_time_ms=0,  # Set to 0 for iOS compatibility
            # Legacy fields for app compatibility
            results=db_products,
            total_results=len(db_products)
        )
        
    except Exception as e:
        logger.error(f"[CLIENT-API] Database search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler bei der Produktsuche: {str(e)}")


@router.get("/stores", response_model=StoresResponse)
async def get_stores(
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    Gibt eine Liste aller verfügbaren Supermärkte aus der Datenbank zurück (Read-only)
    """
    try:
        logger.info("[CLIENT-API] Getting stores from database")
        
        # Get stores from database (read-only)
        db_stores = await db_service.stores.get_all_enabled()
        
        # Convert to app-compatible format
        app_compatible_stores = []
        for db_store in db_stores:
            app_store = Store(
                name=db_store.name,
                logo_url=db_store.logo_url,
                enabled=db_store.enabled,
                # Legacy fields for app compatibility
                id=str(db_store.id),  # Apps expect string ID
                website_url=db_store.base_url,
                category="Supermarkt"  # Default category for app compatibility
            )
            app_compatible_stores.append(app_store)
        
        logger.info(f"[CLIENT-API] Found {len(app_compatible_stores)} enabled stores")
        
        return StoresResponse(
            stores=app_compatible_stores,
            source="database"
        )
        
    except Exception as e:
        logger.error(f"[CLIENT-API] Error getting stores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Stores: {str(e)}") 
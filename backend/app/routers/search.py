from fastapi import APIRouter, HTTPException
from app.models.search import SearchRequest, SearchResponse, StoresResponse
from app.services.search_service import search_service

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_products(search_request: SearchRequest):
    """
    Suche nach Produkten in verschiedenen Supermärkten
    
    - **query**: Suchbegriff (z.B. "Milch", "Oatly", "Haribo")
    - **postal_code**: Deutsche Postleitzahl (5 Ziffern)
    
    Gibt eine Liste von Produkten sortiert nach Preis zurück.
    """
    try:
        response = await search_service.search_products(search_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Produktsuche: {str(e)}")

@router.get("/stores", response_model=StoresResponse)
async def get_stores():
    """
    Gibt eine Liste aller verfügbaren Supermärkte zurück
    """
    try:
        response = await search_service.get_stores()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Stores: {str(e)}") 
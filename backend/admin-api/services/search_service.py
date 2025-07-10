"""
Preisvergleich Search Service - Nur Datenbanksuche, kein Crawling!
Der SearchService liest ausschließlich aus der Datenbank und crawlt niemals.
"""

import time
import logging
from typing import List
from shared.models.search import SearchRequest, SearchResponse, ProductResult, Store, StoresResponse
from shared.services.database_service import DatabaseService
from shared.core.database import get_async_session
from .mock_data import mock_data_service

logger = logging.getLogger(__name__)

class SearchService:
    """Search Service - Nur Datenbanksuche, kein Crawling!"""
    
    def __init__(self):
        logger.info("🔍 SearchService initialisiert - NUR DATENBANKSUCHE, KEIN CRAWLING!")
    
    async def search_products(self, search_request: SearchRequest) -> SearchResponse:
        """Hauptmethode für Produktsuche - NUR aus Datenbank"""
        start_time = time.time()
        
        # Suche nur in der Datenbank
        results = await self._search_in_database(search_request)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=results,
            query=search_request.query,
            postal_code=search_request.postal_code,
            total_results=len(results),  # Legacy field
            total_products=len(results),  # New field
            search_time_ms=search_time_ms,
            source="database"
        )
    
    async def get_stores(self) -> StoresResponse:
        """Gibt verfügbare Stores zurück"""
        stores = mock_data_service.get_stores()
        return StoresResponse(stores=stores)
    
    async def _search_in_database(self, search_request: SearchRequest) -> List[ProductResult]:
        """Suche in der Datenbank - KEIN CRAWLING"""
        try:
            # Verwende den korrekten async session maker
            from shared.core.database import async_session_maker
            
            async with async_session_maker() as session:
                db_service = DatabaseService(session)
                
                logger.info(f"🔍 Suche in Datenbank nach Query: '{search_request.query}'")
                
                # Suche in der Datenbank nach bereits gecrawlten Produkten
                products = await db_service.search_products(
                    query=search_request.query,
                    postal_code=search_request.postal_code,
                    stores=search_request.stores,  # Liste von Store-Namen
                    limit=1000  # Alle verfügbaren Ergebnisse
                )
                
                logger.info(f"✅ {len(products)} Produkte aus Datenbank gefunden")
                return products
                
        except Exception as e:
            logger.error(f"❌ Datenbankfehler: {e}")
            # Fallback zu Mock-Daten nur bei Datenbankfehlern
            return await self._emergency_fallback(search_request)
    
    async def _emergency_fallback(self, search_request: SearchRequest) -> List[ProductResult]:
        """Notfall-Fallback zu Mock-Daten bei Datenbankfehlern"""
        logger.warning("🚨 NOTFALL-FALLBACK zu Mock-Daten wegen Datenbankfehler!")
        
        # Verwende Mock-Daten
        results = mock_data_service.search_products(
            query=search_request.query,
            postal_code=search_request.postal_code
        )

        # Filter anwenden
        if search_request.stores:
            results = [r for r in results if r.store.lower() in [s.lower() for s in search_request.stores]]

        return results

# Service-Instanz erstellen
search_service = SearchService() 
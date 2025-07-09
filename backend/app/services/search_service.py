"""
Preisvergleich Search Service - Playwright Ultimate Crawler als Standard
Saubere Implementierung ohne Legacy-Fallbacks
"""

import time
import logging
from typing import List
from app.models.search import SearchRequest, SearchResponse, ProductResult, Store, StoresResponse
from app.services.mock_data import mock_data_service
from app.services.lidl_crawler_ultimate import LidlUltimateCrawler
from app.services.lidl_mock_data import LidlMockData
from app.core.config import settings

logger = logging.getLogger(__name__)

class SearchService:
    """Search Service mit Ultimate Crawlern als Standard"""
    
    def __init__(self):
        # Nur Lidl Crawler für jetzt
        self.lidl_crawler_ultimate = LidlUltimateCrawler()  # Ultimate Playwright Crawler
        logger.info("🚀 SearchService initialisiert mit Lidl Ultimate Crawler")
    
    async def search_products(self, search_request: SearchRequest) -> SearchResponse:
        """Hauptmethode für Produktsuche"""
        start_time = time.time()
        
        # Verwende IMMER echte Crawler (keine Mock-Daten außer als absoluter Fallback)
        results = await self._search_with_real_crawlers(search_request)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=results,
            query=search_request.query,
            postal_code=search_request.postal_code,
            total_results=len(results),
            search_time_ms=search_time_ms
        )
    
    async def get_stores(self) -> StoresResponse:
        """Gibt verfügbare Stores zurück"""
        stores = mock_data_service.get_stores()
        return StoresResponse(stores=stores)
    
    async def _search_with_real_crawlers(self, search_request: SearchRequest) -> List[ProductResult]:
        """Suche mit echten Crawlern - Ultimate Versions Only"""
        try:
            results = []
            
            # Prüfe Store-Filter für Lidl (only store we support now)
            should_search_lidl = (
                not search_request.selected_stores or 
                'lidl' in [store.lower() for store in search_request.selected_stores]
            )
            
            # Verwende Ultimate LIDL-Crawler (Playwright-basiert)
            if should_search_lidl and self.lidl_crawler_ultimate:
                logger.info(f"🛒 Crawle LIDL-Produkte mit Ultimate Playwright Crawler für Query: {search_request.query}")
                try:
                    lidl_results = await self.lidl_crawler_ultimate.search_products(
                        query=search_request.query,
                        max_results=120  # Alle verfügbaren Produkte
                    )
                    results.extend(lidl_results)
                    logger.info(f"✅ LIDL-Ultimate-Crawler: {len(lidl_results)} Ergebnisse")
                except Exception as e:
                    logger.error(f"❌ LIDL-Ultimate-Crawler Fehler: {e}")
                    # Kein Fallback - bei Fehlern soll deutlich werden was nicht funktioniert
            
            # Filter anwenden
            if search_request.unit:
                original_count = len(results)
                results = [r for r in results if r.unit and r.unit.lower() == search_request.unit.lower()]
                logger.info(f"🔍 Unit-Filter '{search_request.unit}': {original_count} → {len(results)} Produkte")
                
            if search_request.max_price:
                original_count = len(results)
                results = [r for r in results if r.price <= search_request.max_price]
                logger.info(f"💰 Price-Filter '≤€{search_request.max_price}': {original_count} → {len(results)} Produkte")
            
            logger.info(f"🎯 FINALE Ergebnisse: {len(results)} Produkte")
            return results
            
        except Exception as e:
            logger.error(f"❌ Schwerwiegender Fehler bei Real Crawlers: {e}")
            # Als absoluter Fallback: Mock-Daten mit Filter
            return await self._emergency_fallback(search_request)
    
    async def _emergency_fallback(self, search_request: SearchRequest) -> List[ProductResult]:
        """Notfall-Fallback zu Mock-Daten (nur bei schwerwiegenden Fehlern)"""
        logger.warning("🚨 NOTFALL-FALLBACK zu Mock-Daten!")
        
        # Simuliere API-Delay
        import asyncio
        await asyncio.sleep(0.5)
        
        # Verwende Mock-Daten
        results = mock_data_service.search_products(
            query=search_request.query,
            postal_code=search_request.postal_code
        )

        # Ergänze Lidl Mock-Daten
        lidl_results = LidlMockData.get_products_for_query(
            query=search_request.query,
            max_results=10
        )
        results.extend(lidl_results)

        # Filter anwenden
        if search_request.selected_stores:
            results = [r for r in results if r.store.lower() in [s.lower() for s in search_request.selected_stores]]
        if search_request.unit:
            results = [r for r in results if r.unit and r.unit.lower() == search_request.unit.lower()]
        if search_request.max_price:
            results = [r for r in results if r.price <= search_request.max_price]

        return results

# Service-Instanz erstellen
search_service = SearchService() 
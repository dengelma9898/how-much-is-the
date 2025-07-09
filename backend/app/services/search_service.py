import time
import logging
from typing import List
from app.models.search import SearchRequest, SearchResponse, ProductResult, Store, StoresResponse
from app.services.mock_data import mock_data_service
from app.services.aldi_crawler import create_aldi_crawler
from app.services.lidl_crawler_bs4 import create_intelligent_lidl_crawler
from app.services.lidl_mock_data import LidlMockData
from app.core.config import settings

logger = logging.getLogger(__name__)

class SearchService:
    """Service für Produktsuche mit Firecrawl-Integration"""
    
    def __init__(self):
        self.firecrawl_enabled = settings.firecrawl_enabled
        
        # Initialisiere Aldi-Crawler falls verfügbar
        self.aldi_crawler = create_aldi_crawler()
        
        # Initialisiere intelligenten Lidl-Crawler (BeautifulSoup + Ollama)
        self.lidl_crawler = create_intelligent_lidl_crawler()
        
        # Legacy Firecrawl-Initialisierung für Fallback
        if self.firecrawl_enabled and settings.firecrawl_api_key:
            try:
                from firecrawl import FirecrawlApp
                self.firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
            except ImportError:
                logger.warning("Warning: firecrawl-py nicht installiert. Verwende Mock-Daten.")
                self.firecrawl_enabled = False
        else:
            self.firecrawl_enabled = False
    
    async def search_products(self, search_request: SearchRequest) -> SearchResponse:
        """Hauptmethode für Produktsuche"""
        start_time = time.time()
        
        if self.firecrawl_enabled:
            results = await self._search_with_firecrawl(search_request)
        else:
            results = await self._search_with_mock_data(search_request)
        
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
    
    async def _search_with_mock_data(self, search_request: SearchRequest) -> List[ProductResult]:
        """Suche mit Mock-Daten inkl. Filter"""
        # Simuliere API-Delay
        await self._simulate_delay()
        
        # Verwende Mock-Daten von REWE/etc.
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

        # Filter: selected_stores
        if search_request.selected_stores:
            results = [r for r in results if r.store.lower() in [s.lower() for s in search_request.selected_stores]]
        # Filter: unit
        if search_request.unit:
            results = [r for r in results if r.unit and r.unit.lower() == search_request.unit.lower()]
        # Filter: max_price
        if search_request.max_price:
            results = [r for r in results if r.price <= search_request.max_price]

        return results
    
    async def _search_with_firecrawl(self, search_request: SearchRequest) -> List[ProductResult]:
        """Suche mit Firecrawl - echte Implementierung mit Aldi-Crawler"""
        try:
            results = []
            
            # Prüfe Store-Filter für Aldi
            should_search_aldi = (
                not search_request.selected_stores or 
                any(store.lower() in ['aldi', 'aldi süd', 'aldi-süd'] for store in search_request.selected_stores)
            )
            
            # Verwende Aldi-Crawler falls verfügbar und gewünscht
            if self.aldi_crawler and should_search_aldi:
                logger.info(f"Crawle Aldi-Produkte für Query: {search_request.query}")
                aldi_results = await self.aldi_crawler.search_products(
                    query=search_request.query,
                    max_results=15  # Maximal 15 Produkte von Aldi
                )
                results.extend(aldi_results)
                logger.info(f"Aldi-Crawler lieferte {len(aldi_results)} Ergebnisse")
            
            # Prüfe Store-Filter für Lidl
            should_search_lidl = (
                not search_request.selected_stores or 
                'lidl' in [store.lower() for store in search_request.selected_stores]
            )
            
            # Verwende Lidl-Crawler falls verfügbar und gewünscht
            lidl_results = []
            if should_search_lidl:
                if self.lidl_crawler:
                    logger.info(f"Crawle Lidl-Produkte für Query: {search_request.query}")
                    try:
                        async with self.lidl_crawler:
                            lidl_results = await self.lidl_crawler.search_products(
                                query=search_request.query,
                                max_results=15  # Maximal 15 Produkte von Lidl
                            )
                        logger.info(f"Lidl-Crawler lieferte {len(lidl_results)} Ergebnisse")
                    except Exception as e:
                        logger.warning(f"Lidl-Crawler fehlgeschlagen: {e}")
                        lidl_results = []
                
                            # Echte Crawling-Ergebnisse verwenden - KEINE Mock-Fallbacks!
            if lidl_results:
                results.extend(lidl_results)
                logger.info(f"Lidl-Crawler lieferte {len(lidl_results)} echte Ergebnisse")
            else:
                logger.info(f"Lidl-Crawler fand keine Ergebnisse für '{search_request.query}' - das ist OK")
            
            # Zusätzliche Filter anwenden (Unit, Max Price)
            if search_request.unit:
                results = [r for r in results if r.unit and r.unit.lower() == search_request.unit.lower()]
            if search_request.max_price:
                results = [r for r in results if r.price <= search_request.max_price]
            
            # Echte Crawler-Ergebnisse - leere Liste ist OK wenn nichts gefunden
            if not results:
                logger.info(f"Keine echten Ergebnisse für '{search_request.query}' gefunden - das ist in Ordnung")
            
            return results
            
        except Exception as e:
            logger.error(f"Fehler beim Firecrawl-Search: {e}")
            # Fallback zu Mock-Daten bei Fehlern
            return await self._search_with_mock_data(search_request)
    
    async def _simulate_delay(self):
        """Simuliert API-Delay für realistische Erfahrung"""
        import asyncio
        import random
        delay = random.uniform(0.2, 0.8)  # 200-800ms Delay
        await asyncio.sleep(delay)

search_service = SearchService() 
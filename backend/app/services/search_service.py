import time
from typing import List
from app.models.search import SearchRequest, SearchResponse, ProductResult, Store, StoresResponse
from app.services.mock_data import mock_data_service
from app.core.config import settings

class SearchService:
    """Service für Produktsuche mit Firecrawl-Integration"""
    
    def __init__(self):
        self.firecrawl_enabled = settings.firecrawl_enabled
        if self.firecrawl_enabled and settings.firecrawl_api_key:
            try:
                from firecrawl import FirecrawlApp
                self.firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
            except ImportError:
                print("Warning: firecrawl-py nicht installiert. Verwende Mock-Daten.")
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
        
        results = mock_data_service.search_products(
            query=search_request.query,
            postal_code=search_request.postal_code
        )

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
        """Suche mit Firecrawl (für zukünftige Implementierung)"""
        # TODO: Implementiere echte Firecrawl-Integration
        # Für jetzt fallback zu Mock-Daten
        return await self._search_with_mock_data(search_request)
        
        # Zukünftige Firecrawl-Implementierung:
        # 1. Definiere Target-URLs für verschiedene Supermärkte
        # 2. Crawle Produktseiten mit Suchbegriff
        # 3. Extrahiere Produktdaten (Name, Preis, etc.)
        # 4. Normalisiere und strukturiere Daten
        # 5. Gebe ProductResult-Liste zurück
    
    async def _simulate_delay(self):
        """Simuliert API-Delay für realistische Erfahrung"""
        import asyncio
        import random
        delay = random.uniform(0.2, 0.8)  # 200-800ms Delay
        await asyncio.sleep(delay)

search_service = SearchService() 
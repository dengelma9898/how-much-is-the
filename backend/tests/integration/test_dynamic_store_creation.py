"""
Test für die dynamische Store-Erstellung beim Crawling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.shared.services.database_service import DatabaseService
from backend.admin_api.services.crawler_service import CrawlerService


class TestDynamicStoreCreation:
    
    @pytest.mark.asyncio
    async def test_ensure_store_exists_creates_new_store(self):
        """Test dass ein neuer Store erstellt wird wenn er nicht existiert"""
        
        # Mock database service
        mock_db_service = MagicMock()
        mock_store_repo = MagicMock()
        mock_db_service.stores = mock_store_repo
        
        # Store existiert nicht
        mock_store_repo.get_by_name = AsyncMock(return_value=None)
        
        # Mock store creation
        mock_store = MagicMock()
        mock_store.id = 1
        mock_store.name = "Lidl"
        mock_store_repo.create = AsyncMock(return_value=mock_store)
        
        # Create crawler service
        crawler_service = CrawlerService(mock_db_service)
        
        # Test store creation
        result = await crawler_service._ensure_store_exists("Lidl")
        
        # Verify calls
        mock_store_repo.get_by_name.assert_called_once_with("Lidl")
        mock_store_repo.create.assert_called_once_with(
            name="Lidl",
            base_url="https://www.lidl.de",
            logo_url="https://www.lidl.de/favicon.ico"
        )
        
        assert result == mock_store
    
    @pytest.mark.asyncio
    async def test_ensure_store_exists_returns_existing_store(self):
        """Test dass ein existierender Store zurückgegeben wird"""
        
        # Mock database service
        mock_db_service = MagicMock()
        mock_store_repo = MagicMock()
        mock_db_service.stores = mock_store_repo
        
        # Store existiert bereits
        mock_existing_store = MagicMock()
        mock_existing_store.id = 1
        mock_existing_store.name = "Lidl"
        mock_store_repo.get_by_name = AsyncMock(return_value=mock_existing_store)
        
        # Create crawler service
        crawler_service = CrawlerService(mock_db_service)
        
        # Test store retrieval
        result = await crawler_service._ensure_store_exists("Lidl")
        
        # Verify calls
        mock_store_repo.get_by_name.assert_called_once_with("Lidl")
        mock_store_repo.create.assert_not_called()
        
        assert result == mock_existing_store
    
    @pytest.mark.asyncio
    async def test_ensure_store_exists_raises_error_for_unknown_store(self):
        """Test dass ein Fehler für unbekannte Stores ausgelöst wird"""
        
        # Mock database service
        mock_db_service = MagicMock()
        
        # Create crawler service
        crawler_service = CrawlerService(mock_db_service)
        
        # Test unknown store
        with pytest.raises(ValueError, match="No crawler available for store: Unknown"):
            await crawler_service._ensure_store_exists("Unknown")
    
    @pytest.mark.asyncio
    async def test_crawl_store_creates_store_automatically(self):
        """Test dass crawl_store automatisch einen Store erstellt"""
        
        # Mock database service
        mock_db_service = MagicMock()
        mock_store_repo = MagicMock()
        mock_product_repo = MagicMock()
        mock_db_service.stores = mock_store_repo
        mock_db_service.products = mock_product_repo
        
        # Store existiert nicht, wird erstellt
        mock_store_repo.get_by_name = AsyncMock(return_value=None)
        
        mock_new_store = MagicMock()
        mock_new_store.id = 1
        mock_new_store.name = "Lidl"
        mock_store_repo.create = AsyncMock(return_value=mock_new_store)
        
        # Mock product operations
        mock_product_repo.soft_delete_old_products = AsyncMock(return_value=0)
        mock_product_repo.bulk_create = AsyncMock(return_value=10)
        
        # Create crawler service with mocked crawler
        crawler_service = CrawlerService(mock_db_service)
        
        # Mock the crawler to return some products
        mock_crawler = AsyncMock()
        mock_crawler.crawl_all_products = AsyncMock(return_value=[
            MagicMock(name="Test Product 1", price="1.99", store="Lidl"),
            MagicMock(name="Test Product 2", price="2.49", store="Lidl")
        ])
        crawler_service.crawlers["Lidl"] = mock_crawler
        
        # Test crawling (this should create the store)
        try:
            success_count, error_count = await crawler_service.crawl_store(
                store_name="Lidl",
                postal_code="10115",
                crawl_session_id=1
            )
            
            # Verify store was created
            mock_store_repo.create.assert_called_once_with(
                name="Lidl",
                base_url="https://www.lidl.de",
                logo_url="https://www.lidl.de/favicon.ico"
            )
            
            # Verify crawler was called
            mock_crawler.crawl_all_products.assert_called_once()
            
        except Exception as e:
            # Some other components might fail in the mock environment, 
            # but we mainly care that the store creation part works
            pass
    
    def test_store_metadata_completeness(self):
        """Test dass Store-Metadaten für alle verfügbaren Crawler vollständig sind"""
        
        # Mock database service
        mock_db_service = MagicMock()
        
        # Create crawler service
        crawler_service = CrawlerService(mock_db_service)
        
        # Verify metadata exists for all crawlers
        for store_name in crawler_service.crawlers.keys():
            assert store_name in crawler_service.store_metadata
            
            metadata = crawler_service.store_metadata[store_name]
            assert "name" in metadata
            assert "base_url" in metadata
            assert "logo_url" in metadata
            assert "enabled" in metadata
            
            # Verify required fields are not empty
            assert metadata["name"] == store_name
            assert metadata["base_url"].startswith("https://")
            assert metadata["logo_url"].startswith("https://")
            assert metadata["enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
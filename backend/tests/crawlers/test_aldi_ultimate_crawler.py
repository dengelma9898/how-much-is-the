#!/usr/bin/env python3
"""
Dedicated Test für ALDI Ultimate Crawler
Testet alle Funktionen des neuen kategorien-basierten ALDI Crawlers
"""

import pytest
import asyncio
import logging
from decimal import Decimal
from typing import List

from app.services.aldi_crawler_ultimate import AldiUltimateCrawler
from app.models.search import ProductResult

logger = logging.getLogger(__name__)

class TestAldiUltimateCrawler:
    """Test-Suite für ALDI Ultimate Crawler"""
    
    @pytest.fixture
    def crawler(self):
        """Erstellt eine Crawler-Instanz für Tests"""
        return AldiUltimateCrawler()
    
    def test_crawler_initialization(self, crawler):
        """Testet die Initialisierung des Crawlers"""
        assert crawler.base_url == "https://www.aldi-sued.de"
        assert crawler.timeout == 120000
        assert len(crawler.category_urls) == 3
        
        # Prüfe alle Kategorien
        expected_categories = ["Frischekracher", "Markenaktion der Woche", "Preisaktion"]
        for category in expected_categories:
            assert category in crawler.category_urls
            assert crawler.category_urls[category].startswith("https://www.aldi-sued.de")
    
    def test_price_parsing(self, crawler):
        """Testet die Preisverarbeitung"""
        test_cases = [
            # Standard ALDI Formate
            ("€ 1,79", Decimal("1.79")),
            ("€ 2,99", Decimal("2.99")),
            ("1,49", Decimal("1.49")),
            
            # Cent-Preise (Ultimate Features)
            ("-.90", Decimal("0.90")),
            (",95", Decimal("0.95")),
            ("-,85", Decimal("0.85")),
            (".99", Decimal("0.99")),
            
            # Mit Währung
            ("€2,50", Decimal("2.50")),
            ("4,99 €", Decimal("4.99")),
            
            # Edge Cases
            ("", None),
            ("invalid", None),
            ("€ -1,50", Decimal("1.50")),  # Negativ zu positiv
        ]
        
        for price_text, expected in test_cases:
            result = crawler._parse_price(price_text)
            if expected is None:
                assert result is None, f"Expected None for '{price_text}', got {result}"
            else:
                assert result == expected, f"Expected {expected} for '{price_text}', got {result}"
    
    def test_availability_parsing(self, crawler):
        """Testet das Parsing von Verfügbarkeitsinformationen"""
        test_cases = [
            # Standard Verfügbarkeit
            ("Gültig bis 15.12.", True, "Gültig bis 15.12.", "2024-12-15"),
            ("Verfügbar bis 23.12.2024", True, "Verfügbar bis 23.12.2024", "2024-12-23"),
            
            # Nicht verfügbar
            ("ausverkauft", False, "ausverkauft", None),
            ("nicht verfügbar", False, "nicht verfügbar", None),
            ("vergriffen", False, "vergriffen", None),
            
            # Regional/temporär verfügbar
            ("nur in der Filiale 07.07. - 12.07.", True, "nur in der Filiale 07.07. - 12.07.", "2024-07-12"),
            ("Regional verfügbar", True, "Regional verfügbar", None),
            
            # Edge Cases
            ("", True, None, None),
            (None, True, None, None)
        ]
        
        for availability_text, expected_available, expected_text, expected_until in test_cases:
            available, parsed_text, valid_until = crawler._parse_availability_and_date(availability_text)
            
            assert available == expected_available, f"Available mismatch for '{availability_text}'"
            assert parsed_text == expected_text, f"Text mismatch for '{availability_text}'"
            
            # Datum-Check flexibler gestalten (Jahr kann variieren)
            if expected_until:
                assert valid_until is not None, f"Expected date for '{availability_text}'"
                assert expected_until[-5:] in valid_until, f"Date mismatch for '{availability_text}'"
    
    def test_selectors_configuration(self, crawler):
        """Testet die CSS-Selektor Konfiguration"""
        # Prüfe dass alle Selektor-Listen gefüllt sind
        assert len(crawler.product_selectors) > 0
        assert len(crawler.title_selectors) > 0
        assert len(crawler.price_selectors) > 0
        assert len(crawler.unit_selectors) > 0
        
        # Prüfe auf typische ALDI-Selektoren
        assert '.product-tile' in crawler.product_selectors
        assert '.offer-tile' in crawler.product_selectors
        assert '.product-tile__title' in crawler.title_selectors
        assert '.product-tile__price' in crawler.price_selectors
    


# Integration Tests (nur wenn Live-Crawling aktiviert ist)
class TestAldiUltimateCrawlerIntegration:
    """Integration Tests für Live-Crawling (optional)"""
    
    @pytest.fixture
    def crawler(self):
        return AldiUltimateCrawler()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_live_category_crawling(self, crawler):
        """Testet Live-Crawling einer Kategorie (nur bei aktiviertem Test)"""
        # Reduzierte Anzahl für schnelle Tests
        results = await crawler.crawl_all_products(max_results=5)
        
        # Grundlegende Checks
        assert isinstance(results, list)
        
        if results:
            # Prüfe erstes Produkt
            product = results[0]
            assert hasattr(product, 'name')
            assert hasattr(product, 'price')
            assert hasattr(product, 'store')
            assert hasattr(product, 'category')
            
            # Store sollte ALDI Süd sein
            assert product.store == "ALDI Süd"
            
            # Kategorie sollte eine der erwarteten sein
            expected_categories = ["Frischekracher", "Markenaktion der Woche", "Preisaktion"]
            assert product.category in expected_categories
            
            # Preis sollte parsebar sein
            try:
                price_value = float(product.price)
                assert price_value > 0
            except ValueError:
                pytest.fail(f"Price '{product.price}' is not a valid number")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_live_error_handling(self, crawler):
        """Testet Error Handling bei Live-Crawling"""
        # Teste mit ungültiger URL (für Error Handling)
        original_urls = crawler.category_urls.copy()
        crawler.category_urls = {
            "Test Invalid": "https://invalid-url-that-does-not-exist.com"
        }
        
        try:
            results = await crawler.crawl_all_products(max_results=5)
            # Sollte leere Liste zurückgeben bei Fehlern
            assert isinstance(results, list)
            # Kann leer sein oder einzelne Errors
        finally:
            # Restore original URLs
            crawler.category_urls = original_urls

if __name__ == "__main__":
    # Direkter Aufruf für Development
    print("🧪 Starte ALDI Ultimate Crawler Tests...")
    
    # Unit Tests
    crawler = AldiUltimateCrawler()
    test_suite = TestAldiUltimateCrawler()
    
    print("✅ Teste Initialisierung...")
    test_suite.test_crawler_initialization(crawler)
    
    print("✅ Teste Preisverarbeitung...")
    test_suite.test_price_parsing(crawler)
    
    print("✅ Teste Verfügbarkeitsverarbeitung...")
    test_suite.test_availability_parsing(crawler)
    
    print("✅ Teste Selektor-Konfiguration...")
    test_suite.test_selectors_configuration(crawler)
    

    
    print("🎉 Alle Unit Tests erfolgreich!")
    print("💡 Für Integration Tests: pytest -m integration") 
"""
Test-Skript für den intelligenten Lidl-Crawler mit BeautifulSoup + LLM-Integration

WICHTIGER HINWEIS:
Der intelligente Lidl-Crawler verwendet crawl_all_products() ohne Query-Parameter.
Für spezifische Produktsuchen verwenden Sie den SearchService, der in der Datenbank sucht.
Dieser Test zeigt das allgemeine Crawling-Verhalten ohne spezifische Suchanfragen.
"""

import asyncio
import logging
import sys
import os
from pprint import pprint

# Pfad zum app-Ordner hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler_bs4 import create_intelligent_lidl_crawler
from app.models.search import SearchRequest
from app.services.search_service import search_service

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_crawler_data_collection():
    """Testet die Datensammlung des intelligenten Lidl-Crawlers"""
    try:
        logger.info("🧠 Starte Datensammlung mit intelligentem Lidl-Crawler...")
        
        # Intelligenten Lidl-Crawler erstellen
        crawler = create_intelligent_lidl_crawler()
        
        if not crawler:
            logger.error("❌ Intelligenter Lidl-Crawler konnte nicht initialisiert werden")
            return []
        
        logger.info("✅ Intelligenter Lidl-Crawler erfolgreich initialisiert")
        
        # Async context manager verwenden
        async with crawler:
            # Da crawl_all_products keine Query akzeptiert, führen wir einen allgemeinen Crawl durch
            logger.info("🔍 Starte allgemeinen Produktcrawl (crawl_all_products)")
            try:
                results = await crawler.crawl_all_products(max_results=20)
                
                if results:
                    logger.info(f"🎯 Gefunden: {len(results)} Produkte insgesamt")
                    
                    # Gruppiere Produkte nach potentiellen Kategorien/Typen
                    categories = {}
                    for product in results:
                        # Einfache Kategorisierung basierend auf Produktnamen
                        category = "Sonstiges"
                        name_lower = product.name.lower()
                        if any(word in name_lower for word in ['milch', 'joghurt', 'butter', 'käse']):
                            category = "Milchprodukte"
                        elif any(word in name_lower for word in ['brot', 'brötchen', 'semmel']):
                            category = "Backwaren"
                        elif any(word in name_lower for word in ['apfel', 'banane', 'orange', 'obst']):
                            category = "Obst"
                        elif any(word in name_lower for word in ['fleisch', 'wurst', 'hack']):
                            category = "Fleisch"
                            
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(product)
                    
                    logger.info(f"📊 Gefundene Kategorien: {list(categories.keys())}")
                    
                    # Zeige Beispiele aus jeder Kategorie
                    for category, products in categories.items():
                        logger.info(f"\n📦 {category} ({len(products)} Produkte):")
                        for i, product in enumerate(products[:3], 1):  # Zeige nur erste 3 pro Kategorie
                            logger.info(f"  {i}. {product.name} - €{product.price} ({product.store})")
                            if product.unit:
                                logger.info(f"     Einheit: {product.unit}")
                            if product.brand:
                                logger.info(f"     Marke: {product.brand}")
                            if product.available_until:
                                logger.info(f"     Verfügbar: {product.available_until}")
                        if len(products) > 3:
                            logger.info(f"     ... und {len(products) - 3} weitere Produkte")
                else:
                    logger.info("📊 Keine Produkte gefunden")
                        
            except Exception as e:
                logger.error(f"❌ Fehler beim Crawling: {e}")
        
        return results
                
    except Exception as e:
        logger.error(f"❌ Fehler beim Crawling: {e}")
        return []

async def test_search_functionality():
    """Testet die Suchfunktionalität mit verschiedenen Queries"""
    try:
        logger.info("\n🔍 Teste Suchfunktionalität mit verschiedenen Queries...")
        
        # Test-Queries
        test_queries = [
            "milch",
            "brot", 
            "käse",
            "apfel",
            "fleisch"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Teste Query: '{query}'")
            try:
                # SearchRequest erstellen
                search_request = SearchRequest(
                    query=query,
                    postal_code="10115",
                    stores=["lidl"]  # Nur LIDL-Produkte
                )
                
                # Suche ausführen
                response = await search_service.search_products(search_request)
                
                if response.results:
                    logger.info(f"🎯 Gefunden: {len(response.results)} Produkte für '{query}'")
                    for i, product in enumerate(response.results[:3], 1):  # Zeige nur die ersten 3
                        logger.info(f"  {i}. {product.name} - €{product.price} ({product.store})")
                        if product.unit:
                            logger.info(f"     Einheit: {product.unit}")
                        if product.brand:
                            logger.info(f"     Marke: {product.brand}")
                else:
                    logger.info(f"📊 Keine Produkte für '{query}' in der Datenbank gefunden")
                    
            except Exception as e:
                logger.error(f"❌ Fehler bei Query '{query}': {e}")
            
            # Kurze Pause zwischen Requests
            await asyncio.sleep(0.5)
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Testen der Suchfunktionalität: {e}")

async def test_raw_extraction():
    """Testet nur die rohe HTML-Extraktion ohne LLM"""
    try:
        logger.info("\n🔧 Teste rohe HTML-Extraktion...")
        
        crawler = create_intelligent_lidl_crawler()
        if not crawler:
            return
        
        async with crawler:
            # HTML-Inhalt laden
            html_content = await crawler._fetch_page_content()
            if html_content:
                logger.info(f"✅ HTML geladen: {len(html_content)} Zeichen")
                
                # Rohe Produktdaten extrahieren
                raw_products = await crawler._extract_raw_products(html_content)
                logger.info(f"📦 Rohe Produktelemente: {len(raw_products)}")
                
                # Erste 5 Elemente anzeigen
                for i, raw_product in enumerate(raw_products[:5], 1):
                    logger.info(f"\n--- Rohprodukt {i} ---")
                    logger.info(f"Text: {raw_product.text_content[:200]}...")
                    logger.info(f"Preise: {raw_product.price_candidates}")
                    logger.info(f"Namen: {raw_product.name_candidates[:3]}")
            else:
                logger.error("❌ Kein HTML-Inhalt erhalten")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei roher Extraktion: {e}", exc_info=True)

if __name__ == "__main__":
    async def main():
        # Teste zuerst rohe Extraktion
        await test_raw_extraction()
        
        print("\n" + "="*50 + "\n")
        
        # Dann sammle Daten mit dem Crawler
        crawled_products = await test_crawler_data_collection()
        
        print("\n" + "="*50 + "\n")
        
        # Teste Suchfunktionalität (funktioniert nur wenn Daten in DB sind)
        await test_search_functionality()
        
        logger.info("🎉 Alle Tests abgeschlossen!")
    
    # Führe Tests aus
    asyncio.run(main()) 
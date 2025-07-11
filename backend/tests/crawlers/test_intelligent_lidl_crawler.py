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

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_intelligent_lidl_crawler():
    """Testet den intelligenten Lidl-Crawler"""
    try:
        logger.info("🧠 Starte Test für intelligenten Lidl-Crawler...")
        
        # Intelligenten Lidl-Crawler erstellen
        crawler = create_intelligent_lidl_crawler()
        
        if not crawler:
            logger.error("❌ Intelligenter Lidl-Crawler konnte nicht initialisiert werden")
            return
        
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
        
        logger.info("🎉 Intelligenter Lidl-Crawler Test abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Test: {e}", exc_info=True)

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
    # Teste zuerst rohe Extraktion
    asyncio.run(test_raw_extraction())
    
    print("\n" + "="*50 + "\n")
    
    # Dann vollständigen intelligenten Test
    asyncio.run(test_intelligent_lidl_crawler()) 
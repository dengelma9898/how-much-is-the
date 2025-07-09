"""
Test-Skript für den Lidl-Crawler
Testet die Grundfunktionalität des Lidl-Crawlers
"""

import asyncio
import logging
from app.services.lidl_crawler import create_lidl_crawler

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_lidl_crawler():
    """Testet den Lidl-Crawler mit verschiedenen Suchbegriffen"""
    try:
        logger.info("🧪 Starte Lidl-Crawler Test...")
        
        # Lidl-Crawler erstellen
        lidl_crawler = create_lidl_crawler()
        
        if not lidl_crawler:
            logger.error("❌ Lidl-Crawler konnte nicht initialisiert werden")
            return
        
        logger.info("✅ Lidl-Crawler erfolgreich initialisiert")
        
        # Test-Queries
        test_queries = [
            "milch",
            "brot",
            "käse"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Teste Query: '{query}'")
            
            try:
                results = await lidl_crawler.search_products(query, max_results=5)
                
                logger.info(f"📊 Ergebnisse für '{query}': {len(results)} Produkte")
                
                for i, product in enumerate(results, 1):
                    logger.info(f"  {i}. {product.name}")
                    logger.info(f"     Preis: €{product.price}")
                    logger.info(f"     Store: {product.store}")
                    logger.info(f"     Partner-App: {product.partner_program}")
                    logger.info(f"     Verfügbar bis: {product.available_until}")
                    if product.unit:
                        logger.info(f"     Einheit: {product.unit}")
                    if product.discount:
                        logger.info(f"     Rabatt: {product.discount}")
                    logger.info("")
                        
            except Exception as e:
                logger.error(f"❌ Fehler bei Query '{query}': {e}")
        
        logger.info("🎉 Lidl-Crawler Test abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim Testen: {e}")

if __name__ == "__main__":
    asyncio.run(test_lidl_crawler()) 
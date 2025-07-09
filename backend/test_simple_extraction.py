"""
Test-Skript für direkte Firecrawl-Extraktion von der Lidl-Seite
"""

import asyncio
import logging
import sys
import os
from pprint import pprint

# Pfad zum app-Ordner hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler import create_lidl_crawler

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_extraction():
    """Testet die direkte Extraktion von der Lidl-Seite"""
    try:
        logger.info("🔍 Teste direkte Lidl-Extraktion...")
        
        # Lidl-Crawler erstellen
        lidl_crawler = create_lidl_crawler()
        
        if not lidl_crawler:
            logger.error("❌ Lidl-Crawler konnte nicht initialisiert werden")
            return
        
        logger.info("✅ Lidl-Crawler erfolgreich initialisiert")
        
        # Einfache Extraktion ohne komplexes Schema
        logger.info("📡 Starte einfache Extraktion...")
        
        # Einfaches Schema für bessere Diagnose
        simple_schema = {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        simple_prompt = """
        Finde ALLE Produkte mit Preisen auf dieser Lidl-Seite.
        Schaue nach allen Elementen die wie Produktangebote aussehen:
        - Name des Produkts
        - Preis (egal in welcher Form)
        
        Beispiel aus der Seite:
        - Deutsche Radieschen mit Preis -.49
        - Rote Paprika mit Preis 1.29
        - Kiwi Gold mit Preis -.55
        
        Erfasse ALLE solchen Einträge!
        """
        
        response = lidl_crawler.firecrawl_app.scrape_url(
            lidl_crawler.billiger_montag_url,
            formats=["extract"],
            extract={
                "schema": simple_schema,
                "prompt": simple_prompt
            },
            onlyMainContent=False,
            waitFor=2000,
            timeout=30000
        )
        
        if response and hasattr(response, 'extract'):
            logger.info("📊 Rohe Extraktionsergebnisse:")
            pprint(response.extract)
            
            products = response.extract.get('products', [])
            logger.info(f"🎯 Gefundene Produkte: {len(products)}")
            
            for i, product in enumerate(products[:10], 1):
                logger.info(f"  {i}. {product}")
                
        else:
            logger.error("❌ Keine Extraktionsdaten erhalten")
            logger.info(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei der Extraktion: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_simple_extraction()) 
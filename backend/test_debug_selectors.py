"""
Debug-Script um herauszufinden, welche CSS-Selektoren für Lidl-Produkte funktionieren
"""

import asyncio
import logging
import sys
import os
import re
from bs4 import BeautifulSoup

# Pfad zum app-Ordner hinzufügen
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler_bs4 import create_intelligent_lidl_crawler

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_lidl_selectors():
    """Debuggt verschiedene CSS-Selektoren für Lidl-Produkte"""
    try:
        logger.info("🔧 Debug: Finde die richtigen CSS-Selektoren für Lidl...")
        
        crawler = create_intelligent_lidl_crawler()
        if not crawler:
            return
        
        async with crawler:
            # HTML-Inhalt laden
            html_content = await crawler._fetch_page_content()
            if not html_content:
                logger.error("❌ Kein HTML-Inhalt erhalten")
                return
            
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.info(f"✅ HTML geparst, Größe: {len(html_content)} Zeichen")
            
            # Suche nach verschiedenen Produktindikatoren
            debug_selectors = [
                # Lidl-spezifische Klassen
                ('div[class*="product"]', 'Divs mit "product" in der Klasse'),
                ('div[class*="offer"]', 'Divs mit "offer" in der Klasse'),  
                ('div[class*="tile"]', 'Divs mit "tile" in der Klasse'),
                ('div[class*="item"]', 'Divs mit "item" in der Klasse'),
                ('div[class*="campaign"]', 'Divs mit "campaign" in der Klasse'),
                ('div[class*="AThe"]', 'Divs mit Lidl-spezifischen "AThe" Klassen'),
                
                # Preisbasierte Selektoren
                ('*:contains("€")', 'Elemente mit Euro-Symbol'),
                ('*[class*="price"]', 'Elemente mit "price" in der Klasse'),
                ('span[class*="Price"]', 'Spans mit "Price" in der Klasse'),
                
                # Allgemeine Content-Container
                ('article', 'Article-Elemente'),
                ('section', 'Section-Elemente'),
                ('main *', 'Elemente im Main-Bereich'),
            ]
            
            for selector, description in debug_selectors:
                try:
                    if ':contains(' in selector:
                        # BeautifulSoup unterstützt :contains nicht direkt
                        elements = soup.find_all(text=re.compile('€'))
                        elements = [elem.parent for elem in elements if elem.parent][:10]
                        count = len(elements)
                    else:
                        elements = soup.select(selector)
                        count = len(elements)
                    
                    logger.info(f"🎯 {description}: {count} Elemente")
                    
                    # Zeige erste 3 Elemente als Beispiel
                    for i, element in enumerate(elements[:3], 1):
                        if hasattr(element, 'get_text'):
                            text_preview = element.get_text(strip=True)[:100]
                            classes = element.get('class', [])
                            logger.info(f"   {i}. Klassen: {classes}")
                            logger.info(f"      Text: {text_preview}...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Selector '{selector}' fehlgeschlagen: {e}")
            
            # Spezielle Suche nach Preis-Mustern im gesamten Text
            logger.info("\n💰 Suche nach Preis-Mustern im gesamten HTML:")
            price_patterns = [
                (r'€\s*\d+[,\.]\d{2}', 'Euro + Preis'),
                (r'\d+[,\.]\d{2}\s*€', 'Preis + Euro'),
                (r'-\.\d{2}', 'Lidl-Style Preise (-.49)'),
                (r'\d+[,\.]\d{2}(?=\s)', 'Dezimalpreise mit Leerzeichen')
            ]
            
            for pattern, description in price_patterns:
                matches = re.findall(pattern, html_content)
                logger.info(f"   {description}: {len(matches)} Treffer")
                if matches:
                    logger.info(f"      Beispiele: {matches[:5]}")
            
            # Suche nach typischen Lidl-Produktnamen
            logger.info("\n🏷️ Suche nach typischen Produktnamen:")
            product_keywords = ['milch', 'brot', 'käse', 'fleisch', 'wurst', 'apfel', 'banane']
            for keyword in product_keywords:
                if keyword.lower() in html_content.lower():
                    logger.info(f"   ✅ '{keyword}' gefunden im HTML")
                    # Kontext um das Keyword finden
                    pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    contexts = re.findall(pattern, html_content, re.IGNORECASE)
                    for context in contexts[:2]:
                        logger.info(f"      Kontext: {context.strip()}")
                else:
                    logger.info(f"   ❌ '{keyword}' nicht gefunden")
        
    except Exception as e:
        logger.error(f"❌ Debug-Fehler: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_lidl_selectors()) 
"""
Debug-Skript für Lidl HTML-Struktur Analyse
"""

import asyncio
import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_lidl_html():
    """Analysiert die HTML-Struktur der Lidl-Seite"""
    
    url = "https://www.lidl.de/c/billiger-montag/a10006065"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; PriceBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'de-DE,de;q=0.5'
    }
    
    try:
        logger.info(f"🔍 Lade Lidl-Seite für HTML-Analyse...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP-Fehler: {response.status_code}")
            return
            
        html_content = response.text
        logger.info(f"✅ HTML geladen: {len(html_content)} Zeichen")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Suche nach Elementen mit Preismustern
        logger.info("\n🔍 Analysiere Elemente mit Preismustern...")
        price_patterns = [r'€-\.\d{2}', r'-\.\d{2}', r'€\d+\.\d{2}', r'\d+\.\d{2}']
        
        price_elements = []
        for pattern in price_patterns:
            elements = soup.find_all(string=re.compile(pattern))
            for element in elements:
                parent = element.parent if element.parent else None
                if parent:
                    price_elements.append({
                        'text': element.strip(),
                        'tag': parent.name,
                        'classes': parent.get('class', []),
                        'id': parent.get('id', ''),
                        'data_attrs': {k: v for k, v in parent.attrs.items() if k.startswith('data-')}
                    })
        
        logger.info(f"📊 Gefunden: {len(price_elements)} Elemente mit Preismustern")
        
        # Zeige erste 10 Preis-Elemente
        for i, elem in enumerate(price_elements[:10], 1):
            logger.info(f"\n--- Preis-Element {i} ---")
            logger.info(f"Text: {elem['text']}")
            logger.info(f"Tag: {elem['tag']}")
            logger.info(f"Classes: {elem['classes']}")
            logger.info(f"ID: {elem['id']}")
            logger.info(f"Data-Attrs: {elem['data_attrs']}")
        
        # 2. Suche nach Elementen mit typischen Produktnamen
        logger.info("\n🔍 Analysiere Elemente mit Produktnamen...")
        product_names = ['Kiwi', 'Granatapfel', 'Galiamelone', 'Grapefruit', 'Gold', 'lose']
        
        product_elements = []
        for name in product_names:
            elements = soup.find_all(string=re.compile(name, re.IGNORECASE))
            for element in elements:
                parent = element.parent if element.parent else None
                if parent:
                    product_elements.append({
                        'text': element.strip(),
                        'tag': parent.name,
                        'classes': parent.get('class', []),
                        'id': parent.get('id', ''),
                        'data_attrs': {k: v for k, v in parent.attrs.items() if k.startswith('data-')}
                    })
        
        logger.info(f"📊 Gefunden: {len(product_elements)} Elemente mit Produktnamen")
        
        # Zeige erste 10 Produkt-Elemente
        for i, elem in enumerate(product_elements[:10], 1):
            logger.info(f"\n--- Produkt-Element {i} ---")
            logger.info(f"Text: {elem['text']}")
            logger.info(f"Tag: {elem['tag']}")
            logger.info(f"Classes: {elem['classes']}")
            logger.info(f"ID: {elem['id']}")
            logger.info(f"Data-Attrs: {elem['data_attrs']}")
        
        # 3. Sammle alle einzigartigen CSS-Klassen
        logger.info("\n🔍 Analysiere CSS-Klassen...")
        all_classes = set()
        for elem in soup.find_all(attrs={'class': True}):
            classes = elem.get('class', [])
            if isinstance(classes, list):
                all_classes.update(classes)
        
        # Filtere nach produktbezogenen Klassen
        product_related_classes = [cls for cls in all_classes 
                                 if any(keyword in cls.lower() 
                                      for keyword in ['product', 'card', 'tile', 'offer', 'price', 'item', 'grid'])]
        
        logger.info(f"📊 Produkt-relevante CSS-Klassen ({len(product_related_classes)}):")
        for cls in sorted(product_related_classes)[:20]:
            logger.info(f"  • {cls}")
        
        # 4. Analysiere data-* Attribute
        logger.info("\n🔍 Analysiere data-* Attribute...")
        data_attrs = set()
        for elem in soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys())):
            for attr in elem.attrs:
                if attr.startswith('data-'):
                    data_attrs.add(f"{attr}={elem.attrs[attr]}")
        
        product_related_data = [attr for attr in data_attrs 
                              if any(keyword in attr.lower() 
                                   for keyword in ['product', 'price', 'offer', 'item'])]
        
        logger.info(f"📊 Produkt-relevante data-* Attribute ({len(product_related_data)}):")
        for attr in sorted(product_related_data)[:20]:
            logger.info(f"  • {attr}")
        
        logger.info("\n🎉 HTML-Analyse abgeschlossen!")
        
    except Exception as e:
        logger.error(f"❌ Fehler bei HTML-Analyse: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(analyze_lidl_html()) 
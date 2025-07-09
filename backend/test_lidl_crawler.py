#!/usr/bin/env python3
"""
Test-Script für den LIDL Ultimate Crawler (Playwright)
Testet den bereinigten Ultimate Crawler ohne Legacy-Fallbacks
"""

import asyncio
import logging
import sys
import os

# Füge das App-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler_ultimate import LidlUltimateCrawler
from app.core.config import settings

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ultimate_crawler():
    """Testet den LIDL Ultimate Crawler (Playwright)"""
    
    print("🚀 LIDL Ultimate Crawler Test (Playwright)")
    print("=" * 60)
    
    # Ultimate Crawler erstellen
    crawler = LidlUltimateCrawler()
    
    print(f"✅ LIDL Ultimate Crawler erfolgreich erstellt")
    print(f"   - Base URL: {settings.lidl_base_url}")
    print(f"   - Billiger Montag URL: {settings.lidl_billiger_montag_url}")
    print(f"   - Max Results: {settings.lidl_max_results}")
    print(f"   - Timeout: {settings.lidl_timeout}s")
    print()
    
    # Test-Queries
    test_queries = [
        "milch",
        "brot", 
        "produkte",  # Allgemeine Suche
        "obst",
        "gemüse"
    ]
    
    for query in test_queries:
        print(f"🔍 Teste Ultimate Crawler Suche nach: '{query}'")
        print("-" * 40)
        
        try:
            # Suche ausführen
            results = await crawler.search_products(query, max_results=10)
            
            if results:
                print(f"✅ {len(results)} Produkte gefunden:")
                
                # Gruppiere nach Kategorien
                categories = {}
                for product in results:
                    cat = product.category or "Sonstiges"
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(product)
                
                print(f"📊 Kategorien: {list(categories.keys())}")
                
                # Zeige erste 5 Produkte
                for i, product in enumerate(results[:5], 1):
                    print(f"  {i}. {product.name}")
                    print(f"     Preis: €{product.price}")
                    if product.unit:
                        print(f"     Einheit: {product.unit}")
                    if product.category:
                        print(f"     Kategorie: {product.category}")
                    if product.description:
                        print(f"     Beschreibung: {product.description}")
                    print()
                
                if len(results) > 5:
                    print(f"     ... und {len(results) - 5} weitere Produkte")
                    
            else:
                print(f"ℹ️  Keine Produkte für '{query}' gefunden")
                
        except Exception as e:
            print(f"❌ Fehler bei Suche nach '{query}': {e}")
            logger.exception(f"Detaillierter Fehler für '{query}':")
        
        print()
    
    print("✅ Ultimate Crawler Test abgeschlossen!")

async def test_comprehensive_search():
    """Führt eine umfassende Suche durch um die Leistung zu testen"""
    print("🎯 Umfassender Produktscan (alle verfügbaren Produkte)")
    print("=" * 60)
    
    crawler = LidlUltimateCrawler()
    
    try:
        # Suche nach "produkte" um alle Produkte zu finden
        print("🔍 Lade alle verfügbaren LIDL-Produkte...")
        results = await crawler.search_products("produkte", max_results=120)
        
        if results:
            print(f"🎉 INSGESAMT {len(results)} Produkte gefunden!")
            
            # Statistiken
            categories = {}
            price_ranges = {"unter €1": 0, "€1-€5": 0, "€5-€10": 0, "über €10": 0}
            
            for product in results:
                # Kategorien
                cat = product.category or "Sonstiges"
                categories[cat] = categories.get(cat, 0) + 1
                
                # Preisbereiche
                if product.price < 1:
                    price_ranges["unter €1"] += 1
                elif product.price < 5:
                    price_ranges["€1-€5"] += 1
                elif product.price < 10:
                    price_ranges["€5-€10"] += 1
                else:
                    price_ranges["über €10"] += 1
            
            print("\n📊 KATEGORIEN:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {cat}: {count} Produkte")
            
            print("\n💰 PREISBEREICHE:")
            for range_name, count in price_ranges.items():
                print(f"   {range_name}: {count} Produkte")
            
            # Günstigste und teuerste Produkte
            sorted_by_price = sorted(results, key=lambda x: x.price)
            print("\n💵 GÜNSTIGSTE PRODUKTE:")
            for product in sorted_by_price[:3]:
                print(f"   €{product.price} - {product.name}")
            
            print("\n💎 TEUERSTE PRODUKTE:")
            for product in sorted_by_price[-3:]:
                print(f"   €{product.price} - {product.name}")
                
        else:
            print("❌ Keine Produkte gefunden - das sollte nicht passieren!")
            
    except Exception as e:
        print(f"❌ Fehler bei umfassender Suche: {e}")
        logger.exception("Detaillierter Fehler:")

if __name__ == "__main__":
    print("🚀 Starte LIDL Ultimate Crawler Tests...")
    print(f"Python: {sys.version}")
    print(f"Arbeitsverzeichnis: {os.getcwd()}")
    print()
    
    # Führe Tests aus
    try:
        # Test 1: Grundfunktionalität
        asyncio.run(test_ultimate_crawler())
        print()
        
        # Test 2: Umfassende Suche
        asyncio.run(test_comprehensive_search())
        
    except KeyboardInterrupt:
        print("\n⚠️  Test durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        logger.exception("Detaillierter Fehler:") 
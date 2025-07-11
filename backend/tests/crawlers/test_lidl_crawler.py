#!/usr/bin/env python3
"""
Test-Script für den LIDL Ultimate Crawler (Playwright)
Testet den bereinigten Ultimate Crawler ohne Legacy-Fallbacks

WICHTIGER HINWEIS:
Der LidlUltimateCrawler wurde so konzipiert, dass er ALLE verfügbaren Produkte crawlt.
Er akzeptiert keine spezifischen Query-Parameter in crawl_all_products().
Für spezifische Produktsuchen verwenden Sie den SearchService, der in der Datenbank sucht.

TESTS:
1. test_ultimate_crawler() - Testet das allgemeine Crawling mit verschiedenen Produktmengen
2. test_comprehensive_search() - Führt einen umfassenden Crawl durch
3. test_search_service_queries() - Zeigt spezifische Produktsuchen über SearchService
"""

import asyncio
import logging
import sys
import os

# Füge das App-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler_ultimate import LidlUltimateCrawler
from app.services.search_service import SearchService
from app.models.search import SearchRequest
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
    
    # Da crawl_all_products keine Query akzeptiert, führen wir verschiedene Tests durch
    test_scenarios = [
        {"name": "Kleiner Test", "max_results": 5, "description": "Schneller Test mit wenigen Produkten"},
        {"name": "Mittlerer Test", "max_results": 15, "description": "Mittlerer Test für bessere Abdeckung"},
        {"name": "Großer Test", "max_results": 30, "description": "Umfassender Test für vollständige Produktpalette"}
    ]
    
    for scenario in test_scenarios:
        print(f"🔍 {scenario['name']}: {scenario['description']}")
        print("-" * 40)
        
        try:
            # Crawl ausführen
            results = await crawler.crawl_all_products(max_results=scenario['max_results'])
            
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
                print(f"ℹ️  Keine Produkte gefunden")
                
        except Exception as e:
            print(f"❌ Fehler bei {scenario['name']}: {e}")
            logger.exception(f"Detaillierter Fehler für {scenario['name']}:")
        
        print()
    
    print("✅ Ultimate Crawler Test abgeschlossen!")

async def test_comprehensive_search():
    """Führt eine umfassende Suche durch um die Leistung zu testen"""
    print("🎯 Umfassender Produktscan (alle verfügbaren Produkte)")
    print("=" * 60)
    
    crawler = LidlUltimateCrawler()
    
    try:
        # Da crawl_all_products keine Query akzeptiert, laden wir alle verfügbaren Produkte
        print("🔍 Lade alle verfügbaren LIDL-Produkte...")
        results = await crawler.crawl_all_products(max_results=120)
        
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

async def test_search_service_queries():
    """Testet spezifische Produktsuchen mit dem SearchService (Datenbanksuche)"""
    print("🔍 SearchService Test (Spezifische Produktsuchen)")
    print("=" * 60)
    
    search_service = SearchService()
    
    # Test-Queries für spezifische Produktsuchen
    test_queries = [
        "milch",
        "brot", 
        "käse",
        "apfel",
        "fleisch"
    ]
    
    for query in test_queries:
        print(f"🔍 Suche nach: '{query}'")
        print("-" * 40)
        
        try:
            search_request = SearchRequest(
                query=query,
                postal_code="10115",
                stores=["Lidl"]  # Nur Lidl-Produkte
            )
            
            # Führe Datenbanksuche durch
            response = await search_service.search_products(search_request)
            
            if response.results:
                print(f"✅ {len(response.results)} Produkte in Datenbank gefunden:")
                
                for i, product in enumerate(response.results[:5], 1):
                    print(f"  {i}. {product.name}")
                    print(f"     Preis: €{product.price}")
                    print(f"     Store: {product.store}")
                    if product.unit:
                        print(f"     Einheit: {product.unit}")
                    if product.category:
                        print(f"     Kategorie: {product.category}")
                    print()
                
                if len(response.results) > 5:
                    print(f"     ... und {len(response.results) - 5} weitere Produkte")
                    
                print(f"📊 Suchzeit: {response.search_time_ms}ms")
                print(f"📊 Quelle: {response.source}")
                    
            else:
                print(f"ℹ️  Keine Produkte für '{query}' in Datenbank gefunden")
                print("   💡 Hinweis: Eventuell müssen erst Produkte gecrawlt werden")
                
        except Exception as e:
            print(f"❌ Fehler bei Suche nach '{query}': {e}")
            logger.exception(f"Detaillierter Fehler für '{query}':")
        
        print()
    
    print("✅ SearchService Test abgeschlossen!")
    print("💡 Für spezifische Produktsuchen verwenden Sie den SearchService")
    print("💡 Für vollständiges Crawling verwenden Sie crawl_all_products")

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
        
        # Test 3: SearchService-Tests
        asyncio.run(test_search_service_queries())
        
    except KeyboardInterrupt:
        print("\n⚠️  Test durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        logger.exception("Detaillierter Fehler:") 
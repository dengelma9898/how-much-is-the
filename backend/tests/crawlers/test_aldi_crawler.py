#!/usr/bin/env python3
"""
Test-Script für ALDI Ultimate Crawler - Kategorien-basiert

Dieses Script testet die vollständige Funktionalität des neuen ALDI Ultimate Crawlers
der kategorien-basiert alle Produkte von ALDI-Aktionsseiten crawlt.

Verwendung:
    python test_aldi_crawler.py
"""

import asyncio
import time
import sys
import os
from decimal import Decimal
from typing import List

# Pfad für Importe hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.aldi_crawler_ultimate import AldiUltimateCrawler
from app.models.search import ProductResult

def print_header():
    """Druckt einen schönen Header"""
    print("🔥" + "="*60)
    print("🔥 Teste ALDI Ultimate Crawler (Kategorien-basiert)")
    print("🔥 Crawlt: Frischekracher, Markenaktion, Preisaktion")
    print("🔥" + "="*60)
    print()

def print_config_status():
    """Überprüft und zeigt die aktuelle Konfiguration an"""
    print("⚙️  Konfiguration:")
    print(f"   - Environment: {settings.app_env}")
    print(f"   - ALDI-Crawler: {settings.aldi_crawler_enabled}")
    print(f"   - Max. Produkte per Kategorie: {settings.aldi_max_products_per_crawl}")
    
    crawler = AldiUltimateCrawler()
    print("   - ALDI-Kategorien:")
    for category_name, category_url in crawler.category_urls.items():
        print(f"     • {category_name}: {category_url}")
    print()

async def test_category_crawling(crawler):
    """Testet das kategorien-basierte Crawling aller ALDI-Seiten"""
    print("🛒 Teste ALDI Ultimate Crawling (alle Kategorien)")
    print("   📋 Crawlt alle Produkte von allen Kategorieseiten")
    
    start_time = time.time()
    try:
        # Test mit begrenzter Anzahl für schnellere Tests
        results = await crawler.crawl_all_products(max_results=50)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"   ⏱️  Crawling-Zeit: {duration:.1f}s")
        print(f"   📊 Gefunden: {len(results)} Produkte")
        
        if results:
            # Kategorien-Verteilung anzeigen
            categories = {}
            for product in results:
                cat = product.category or "Unbekannt"
                categories[cat] = categories.get(cat, 0) + 1
            
            print("   📂 Kategorien-Verteilung:")
            for category, count in categories.items():
                print(f"      • {category}: {count} Produkte")
            
            # Preisbereich anzeigen
            prices = [float(p.price) for p in results]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            print(f"   💰 Preise: €{min_price:.2f} - €{max_price:.2f} (Ø €{avg_price:.2f})")
            
            # Erste 5 Produkte detailliert anzeigen
            print("   📋 Beispiel-Produkte:")
            for i, product in enumerate(results[:5]):
                unit_info = f" | {product.unit}" if product.unit else ""
                availability_info = f" | {product.availability}" if product.availability else ""
                
                print(f"      {i+1}. {product.name}")
                print(f"         💰 €{product.price}{unit_info}")
                print(f"         🏪 Kategorie: {product.category}{availability_info}")
                
                if product.availability_text:
                    print(f"         📅 Verfügbarkeit: {product.availability_text}")
                if product.offer_valid_until:
                    print(f"         ⏰ Gültig bis: {product.offer_valid_until}")
                print()
        else:
            print("   ❌ Keine Produkte gefunden")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        print(f"   📋 Details: {traceback.format_exc()}")
    
    print()

async def test_single_category(crawler, category_name: str = "Frischekracher"):
    """Testet das Crawling einer einzelnen Kategorie"""
    print(f"🎯 Teste einzelne Kategorie: {category_name}")
    
    if category_name not in crawler.category_urls:
        print(f"   ❌ Kategorie '{category_name}' nicht gefunden")
        return
    
    category_url = crawler.category_urls[category_name]
    print(f"   🌐 URL: {category_url}")
    
    start_time = time.time()
    try:
        # Simuliere einzelnes Kategorie-Crawling durch Modifikation
        original_urls = crawler.category_urls.copy()
        crawler.category_urls = {category_name: category_url}
        
        results = await crawler.crawl_all_products(max_results=20)
        end_time = time.time()
        
        # Wiederherstellen
        crawler.category_urls = original_urls
        
        duration = end_time - start_time
        print(f"   ⏱️  Crawling-Zeit: {duration:.1f}s")
        print(f"   📊 Gefunden: {len(results)} Produkte")
        
        if results:
            print("   📋 Beispiel-Produkte:")
            for i, product in enumerate(results[:3]):
                print(f"      {i+1}. {product.name} - €{product.price}")
                if product.unit:
                    print(f"         📦 {product.unit}")
        else:
            print("   ❌ Keine Produkte gefunden")
            
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        print(f"   📋 Details: {traceback.format_exc()}")
    
    print()

def test_price_parsing():
    """Testet die Preisverarbeitung mit verschiedenen deutschen Formaten"""
    print("💰 Teste deutsche Preisverarbeitung:")
    
    crawler = AldiUltimateCrawler()
    
    test_prices = [
        # ALDI-typische Formate
        ("€ 1,79", 1.79),
        ("€ 2,55", 2.55),
        ("€ 1,35", 1.35),
        ("2,19", 2.19),
        ("1,85", 1.85),
        
        # Verschiedene deutsche Formate
        ("€ 12,99*", 12.99),
        ("4,99 €", 4.99),
        ("€2,50", 2.50),
        ("0,89", 0.89),
        
        # Cent-Preise (neue ALDI-Ultimate Features)
        ("-.90", 0.90),
        (",95", 0.95),
        ("-,85", 0.85),
        (".99", 0.99),
        
        # Edge Cases
        ("invalid", None),
        ("", None),
        ("€ -1,50", 1.50)  # Wird zu positivem Preis konvertiert
    ]
    
    success_count = 0
    total_count = len(test_prices)
    
    for price_str, expected in test_prices:
        result = crawler._parse_price(price_str)
        
        # Exaktere Vergleichslogik für Decimal
        if expected is None:
            success = result is None
        else:
            success = result is not None and abs(float(result) - expected) < 0.001
        
        if success:
            success_count += 1
            
        status = "✅" if success else "❌"
        result_str = f"€{result}" if result else "None"
        expected_str = f"€{expected}" if expected else "None"
        print(f"   {status} '{price_str}' → {result_str} (erwartet: {expected_str})")
    
    print(f"   📊 Erfolgsrate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    print()

def test_availability_parsing():
    """Testet die Verfügbarkeits- und Datums-Parsing"""
    print("📅 Teste Verfügbarkeits-Parsing:")
    
    crawler = AldiUltimateCrawler()
    
    test_cases = [
        ("Gültig bis 15.12.", True, "15.12."),
        ("Verfügbar bis 23.12.2024", True, "23.12.2024"),
        ("nur in der Filiale 07.07. - 12.07.", True, "12.07."),
        ("ausverkauft", False, "ausverkauft"),
        ("nicht verfügbar", False, "nicht verfügbar"),
        ("", True, None),
        ("Regional verfügbar", True, "Regional verfügbar")
    ]
    
    for availability_text, expected_available, expected_text in test_cases:
        available, parsed_text, valid_until = crawler._parse_availability_and_date(availability_text)
        
        status = "✅" if available == expected_available else "❌"
        print(f"   {status} '{availability_text}' → verfügbar: {available}, bis: {valid_until}")
    
    print()

def analyze_results(results: List[ProductResult]):
    """Analysiert die Crawling-Ergebnisse und zeigt Statistiken"""
    if not results:
        return
    
    print(f"📊 Detailanalyse ({len(results)} Produkte):")
    
    # Kategorien, Einheiten sammeln
    categories = {}
    units = {}
    price_ranges = {"0-2€": 0, "2-5€": 0, "5-10€": 0, "10€+": 0}
    availability_stats = {"verfügbar": 0, "nicht verfügbar": 0, "unbekannt": 0}
    
    for product in results:
        # Kategorien
        if product.category:
            categories[product.category] = categories.get(product.category, 0) + 1
        
        # Einheiten
        if product.unit:
            # Vereinfache Einheiten
            unit = product.unit.split('(')[0].strip() if '(' in product.unit else product.unit
            units[unit] = units.get(unit, 0) + 1
        
        # Preisverteilung
        price = float(product.price)
        if price < 2:
            price_ranges["0-2€"] += 1
        elif price < 5:
            price_ranges["2-5€"] += 1
        elif price < 10:
            price_ranges["5-10€"] += 1
        else:
            price_ranges["10€+"] += 1
        
        # Verfügbarkeit
        if product.availability == "verfügbar":
            availability_stats["verfügbar"] += 1
        elif product.availability == "nicht verfügbar":
            availability_stats["nicht verfügbar"] += 1
        else:
            availability_stats["unbekannt"] += 1
    
    # Top 3 anzeigen
    print("   📂 Top Kategorien:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"      • {category}: {count} Produkte")
    
    print("   💰 Preisverteilung:")
    for range_name, count in price_ranges.items():
        percentage = count / len(results) * 100
        print(f"      • {range_name}: {count} ({percentage:.1f}%)")
    
    print("   📦 Verfügbarkeit:")
    for status, count in availability_stats.items():
        percentage = count / len(results) * 100
        print(f"      • {status}: {count} ({percentage:.1f}%)")
    
    print()



async def run_comprehensive_tests():
    """Führt alle Tests für den ALDI Ultimate Crawler durch"""
    print_header()
    print_config_status()
    
    # Crawler initialisieren
    crawler = AldiUltimateCrawler()
    
    # Tests durchführen
    test_price_parsing()
    test_availability_parsing()
    
    # Live-Tests (nur wenn aktiviert)
    if settings.aldi_crawler_enabled:
        await test_category_crawling(crawler)
        await test_single_category(crawler, "Frischekracher")
        
        # Umfassender Test mit Analyse
        print("🔍 Umfassender Crawling-Test:")
        start_time = time.time()
        all_results = await crawler.crawl_all_products(max_results=100)
        end_time = time.time()
        
        print(f"   ⏱️  Gesamtzeit: {end_time - start_time:.1f}s")
        analyze_results(all_results)
    else:
        print("⚠️  ALDI-Crawler ist deaktiviert. Überspringe Live-Tests.")
    
    print("🎉 Alle Tests abgeschlossen!")

def check_environment():
    """Überprüft die Umgebung und gibt Hinweise zur Konfiguration"""
    print("🔧 Umgebungs-Check:")
    
    missing_items = []
    
    if not settings.aldi_crawler_enabled:
        missing_items.append("ALDI_CRAWLER_ENABLED=true")
    
    # Playwright Check
    try:
        from playwright.async_api import async_playwright
        print("   ✅ Playwright verfügbar")
    except ImportError:
        missing_items.append("pip install playwright")
        print("   ❌ Playwright nicht installiert")
    
    if missing_items:
        print("\n   📋 Fehlende Konfiguration:")
        for item in missing_items:
            print(f"      {item}")
        print()
    
    # Mögliche env-Variablen für .env Datei anzeigen
    relevant_vars = ['ALDI_CRAWLER_ENABLED', 'ALDI_MAX_PRODUCTS_PER_CRAWL']
    
    print("   📄 Empfohlene .env Einstellungen:")
    for var in relevant_vars:
        if var == 'ALDI_CRAWLER_ENABLED':
            print(f"      {var}=true")
        elif var == 'ALDI_MAX_PRODUCTS_PER_CRAWL':
            print(f"      {var}=1000")
    print()

if __name__ == "__main__":
    print("🚀 Starte ALDI Ultimate Crawler Tests...")
    check_environment()
    asyncio.run(run_comprehensive_tests()) 
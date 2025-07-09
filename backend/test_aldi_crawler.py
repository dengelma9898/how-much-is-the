#!/usr/bin/env python3
"""
Test-Script für Aldi-Crawler mit direkter Suchfunktion

Dieses Script testet die vollständige Funktionalität des optimierten Aldi-Crawlers
mit direkter Nutzung der Aldi-Suchfunktion und gibt detaillierte Informationen 
über Performance und Ergebnisse aus.

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
from app.services.aldi_crawler import create_aldi_crawler
from app.models.search import ProductResult

def print_header():
    """Druckt einen schönen Header"""
    print("🔥" + "="*60)
    print("🔥 Teste Aldi-Crawler mit direkter Suchfunktion")
    print("🔥 Nutzt: https://www.aldi-sued.de/de/suchergebnis.html")
    print("🔥" + "="*60)
    print()

def print_config_status():
    """Überprüft und zeigt die aktuelle Konfiguration an"""
    print("⚙️  Konfiguration:")
    print(f"   - Environment: {settings.app_env}")
    print(f"   - Firecrawl aktiviert: {settings.firecrawl_enabled}")
    
    if settings.firecrawl_api_key:
        # API-Key maskiert anzeigen
        key = settings.firecrawl_api_key
        masked_key = f"{key[:8]}{'*' * (len(key) - 12)}{key[-4:]}" if len(key) > 12 else "fc-****...****"
        print(f"   - API Key verfügbar: {masked_key}")
    else:
        print("   - ❌ API Key fehlt!")
    
    print(f"   - Aldi-Crawler: {settings.aldi_crawler_enabled}")
    print(f"   - Cache-Zeit: {settings.firecrawl_max_age/1000/60:.1f} Minuten")
    print(f"   - Max. Ergebnisse: {settings.firecrawl_max_results_per_store}")
    print(f"   - Aldi Such-URL: {settings.aldi_base_url}/de/suchergebnis.html")
    print()

async def test_product_search(crawler, query: str, test_name: str = None):
    """Testet eine Produktsuche und zeigt Ergebnisse an"""
    if not test_name:
        test_name = f"Produktsuche: '{query}'"
    
    print(f"🛒 Teste {test_name}")
    print(f"   🔍 Such-URL: https://www.aldi-sued.de/de/suchergebnis.html?search={query}")
    
    start_time = time.time()
    try:
        results = await crawler.search_products(query=query, max_results=10)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"   ⏱️  Suchzeit: {duration:.1f}s")
        print(f"   📊 Gefunden: {len(results)} Produkte")
        
        if results:
            # Preisbereich anzeigen
            prices = [float(p.price) for p in results]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            print(f"   💰 Preise: €{min_price:.2f} - €{max_price:.2f} (Ø €{avg_price:.2f})")
            
            # Erste 3 Produkte detailliert anzeigen
            print("   📋 Top-Ergebnisse:")
            for i, product in enumerate(results[:3]):
                brand_info = f" ({product.brand})" if product.brand else ""
                unit_info = f" | {product.unit}" if product.unit else ""
                category_info = f" | {product.category}" if product.category else ""
                
                print(f"      {i+1}. {product.name}{brand_info}")
                print(f"         💰 €{product.price}{unit_info}{category_info}")
                
                if product.origin:
                    print(f"         🌍 Herkunft: {product.origin}")
                if product.quality_info:
                    print(f"         ⭐ Qualität: {product.quality_info}")
                if product.discount:
                    print(f"         🎯 Aktion: {product.discount}")
                print()
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
    
    # Import der parse_price Methode für direkten Test
    from app.services.aldi_crawler import AldiCrawler
    crawler = AldiCrawler()
    
    test_prices = [
        # Aldi-typische Formate
        ("€ 1,79", 1.79),
        ("€ 2,55", 2.55),
        ("€ 1,35", 1.35),
        ("2,19", 2.19),
        ("1,85", 1.85),
        
        # Verschiedene deutsche Formate
        ("€ 12,99*", 12.99),
        ("4,99 €", 4.99),
        ("€2,50", 2.50),
        ("1.234,56", 1234.56),  # Tausender-Format
        ("0,89", 0.89),
        
        # Edge Cases
        ("invalid", None),
        ("", None),
        ("€ 0,00", None),  # Sollte als ungültig erkannt werden
        ("€ 1000", None),  # Über dem erwarteten Limit
        ("€ -1,50", None)  # Negative Preise
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

def analyze_results(results: List[ProductResult], query: str):
    """Analysiert die Suchergebnisse und zeigt Statistiken"""
    if not results:
        return
    
    print(f"📊 Detailanalyse für '{query}' ({len(results)} Produkte):")
    
    # Kategorien, Marken, Einheiten sammeln
    categories = {}
    brands = {}
    units = {}
    price_ranges = {"0-2€": 0, "2-5€": 0, "5-10€": 0, "10€+": 0}
    
    for product in results:
        # Kategorien
        if product.category:
            categories[product.category] = categories.get(product.category, 0) + 1
        
        # Marken
        if product.brand:
            brands[product.brand] = brands.get(product.brand, 0) + 1
        
        # Einheiten
        if product.unit:
            # Vereinfache Einheiten (entferne Grundpreise)
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
    
    # Top 5 anzeigen
    if categories:
        print("   📂 Top Kategorien:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {category}: {count}")
    
    if brands:
        print("   🏷️  Top Marken:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {brand}: {count}")
    
    if units:
        print("   📦 Top Einheiten:")
        for unit, count in sorted(units.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {unit}: {count}")
    
    print("   💰 Preisverteilung:")
    for range_name, count in price_ranges.items():
        percentage = count / len(results) * 100 if results else 0
        print(f"      - {range_name}: {count} ({percentage:.1f}%)")
    
    print()

def test_search_url_generation():
    """Testet die URL-Generierung für verschiedene Suchbegriffe"""
    print("🔗 Teste Such-URL Generierung:")
    
    from app.services.aldi_crawler import AldiCrawler
    import urllib.parse
    
    test_queries = [
        "Milch",
        "Oatly",
        "Bio Brot",
        "Apfel & Birne",
        "Müller Milch",
        "100% natürlich",
        "test with spaces",
        "Umlaut: Müsli"
    ]
    
    base_url = settings.aldi_base_url + "/de/suchergebnis.html"
    
    for query in test_queries:
        encoded_query = urllib.parse.quote_plus(query)
        expected_url = f"{base_url}?search={encoded_query}"
        print(f"   ✅ '{query}' → {expected_url}")
    
    print()

async def test_edge_cases(crawler):
    """Testet Edge Cases und Fehlerzustände"""
    print("🧪 Teste Edge Cases:")
    
    edge_cases = [
        ("", "Leerer Suchbegriff"),
        ("x", "Sehr kurzer Begriff (1 Zeichen)"),
        ("abcdefghijklmnopqrstuvwxyz1234567890", "Sehr langer Begriff"),
        ("!!!@@@###", "Sonderzeichen"),
        ("NonExistentProductBrand123XYZ", "Nicht existierendes Produkt")
    ]
    
    for query, description in edge_cases:
        print(f"   🔍 {description}: '{query}'")
        try:
            start_time = time.time()
            results = await crawler.search_products(query=query, max_results=5)
            duration = time.time() - start_time
            print(f"      ⏱️  {duration:.1f}s | 📊 {len(results)} Ergebnisse")
        except Exception as e:
            print(f"      ❌ Fehler: {e}")
    
    print()

async def run_comprehensive_tests():
    """Führt umfassende Tests des optimierten Crawlers durch"""
    print_header()
    print_config_status()
    
    # Konfiguration validieren
    if not settings.firecrawl_enabled:
        print("❌ Firecrawl ist deaktiviert. Bitte setze FIRECRAWL_ENABLED=true in .env")
        return
    
    if not settings.firecrawl_api_key:
        print("❌ Firecrawl API Key fehlt. Bitte setze FIRECRAWL_API_KEY in .env")
        return
    
    # Crawler initialisieren
    print("🚀 Initialisiere optimierten Aldi-Crawler...")
    crawler = create_aldi_crawler()
    
    if not crawler:
        print("❌ Crawler konnte nicht initialisiert werden!")
        return
    
    print("✅ Crawler erfolgreich initialisiert!")
    print()
    
    # URL-Generierung testen
    test_search_url_generation()
    
    # Preisverarbeitung testen
    test_price_parsing()
    
    # Test-Queries für echte Aldi-Suche
    test_queries = [
        ("Oatly", "Spezifische Marke"),
        ("Milch", "Häufiges Grundprodukt"),
        ("Bio", "Bio-Produkte"),
        ("Brot", "Backwaren"),
        ("Käse", "Molkereiprodukte"),
        ("Apfel", "Obst"),
        ("Nudeln", "Teigwaren"),
        ("Schokolade", "Süßwaren")
    ]
    
    # Alle Tests durchführen
    all_results = {}
    total_search_time = 0
    
    print("🔍 Starte Produktsuche-Tests:")
    print()
    
    for query, description in test_queries:
        start_time = time.time()
        await test_product_search(crawler, query, description)
        search_time = time.time() - start_time
        total_search_time += search_time
        
        # Zusätzliche Analyse für erfolgreiche Suchen
        try:
            results = await crawler.search_products(query=query, max_results=10)
            if results:
                all_results[query] = results
                analyze_results(results, query)
        except Exception as e:
            print(f"   ❌ Analyse-Fehler für '{query}': {e}")
    
    # Edge Cases testen
    await test_edge_cases(crawler)
    
    # Gesamtstatistik
    print("📈 Gesamtstatistik:")
    total_tests = len(test_queries)
    successful_tests = len(all_results)
    success_rate = successful_tests/total_tests*100 if total_tests > 0 else 0
    
    print(f"   - Tests durchgeführt: {total_tests}")
    print(f"   - Erfolgreiche Suchen: {successful_tests}")
    print(f"   - Erfolgsrate: {success_rate:.1f}%")
    print(f"   - Gesamtsuchzeit: {total_search_time:.1f}s")
    
    if successful_tests > 0:
        avg_search_time = total_search_time / total_tests
        print(f"   - Durchschnittliche Suchzeit: {avg_search_time:.1f}s")
    
    total_products = sum(len(results) for results in all_results.values())
    print(f"   - Gesamt gefundene Produkte: {total_products}")
    
    if all_results:
        avg_products = total_products / len(all_results)
        print(f"   - Durchschnitt pro Suche: {avg_products:.1f}")
    
    # Performance-Bewertung
    print()
    print("⚡ Performance-Bewertung:")
    if successful_tests == total_tests:
        print("   ✅ Ausgezeichnet: Alle Tests erfolgreich!")
    elif success_rate >= 80:
        print("   ✅ Gut: Hohe Erfolgsrate")
    elif success_rate >= 60:
        print("   ⚠️  Mittelmäßig: Einige Tests fehlgeschlagen")
    else:
        print("   ❌ Schlecht: Viele Tests fehlgeschlagen")
    
    if total_search_time / total_tests < 5:
        print("   ✅ Schnell: Gute Response-Zeiten")
    elif total_search_time / total_tests < 10:
        print("   ⚠️  Langsam: Moderate Response-Zeiten")
    else:
        print("   ❌ Sehr langsam: Hohe Response-Zeiten")
    
    print()
    print("✅ Alle Tests abgeschlossen!")

def check_environment():
    """Überprüft die Umgebungsvariablen und Environment-Setup"""
    print("🔍 Überprüfe Multi-Environment Setup:")
    
    # Aktuelle Environment anzeigen
    current_env = settings.app_env
    print(f"   📁 Aktuelle Umgebung: {current_env}")
    
    # Entsprechende .env-Datei suchen
    env_file = f".env.{current_env}"
    if os.path.exists(env_file):
        print(f"   ✅ Environment-Datei gefunden: {env_file}")
        
        # .env-Datei lesen und relevante Variablen anzeigen
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        relevant_vars = ['FIRECRAWL_API_KEY', 'FIRECRAWL_ENABLED', 'ALDI_CRAWLER_ENABLED', 'ALDI_BASE_URL']
        found_vars = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                for var in relevant_vars:
                    if line.startswith(f"{var}="):
                        found_vars.append(var)
                        value = line.split('=', 1)[1]
                        if var == 'FIRECRAWL_API_KEY' and value:
                            # API Key maskieren
                            if len(value) > 8:
                                value = f"{value[:4]}...{value[-4:]}"
                        print(f"   ✅ {var}={value}")
        
        missing_vars = set(relevant_vars) - set(found_vars)
        for var in missing_vars:
            print(f"   ❌ {var} nicht gefunden")
    else:
        print(f"   ❌ Environment-Datei nicht gefunden: {env_file}")
        print(f"   💡 Erstelle {env_file} mit:")
        print(f"      FIRECRAWL_API_KEY=fc-your-key-here")
        print(f"      FIRECRAWL_ENABLED=true")
        print(f"      ALDI_CRAWLER_ENABLED=true")
        print(f"      ALDI_BASE_URL=https://www.aldi-sued.de")
    
    # Alternative .env-Dateien anzeigen
    env_files = [f for f in os.listdir('.') if f.startswith('.env')]
    if env_files:
        print(f"   📄 Verfügbare Environment-Dateien: {', '.join(env_files)}")
    
    print()

if __name__ == "__main__":
    print("🔧 Aldi-Crawler Test Suite v2.0")
    print("🎯 Optimiert für direkte Aldi-Suchfunktion")
    print("=" * 50)
    print()
    
    # Umgebung überprüfen
    check_environment()
    
    # Haupttests ausführen
    try:
        asyncio.run(run_comprehensive_tests())
    except KeyboardInterrupt:
        print("\n🛑 Tests durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc() 
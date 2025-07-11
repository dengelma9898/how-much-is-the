#!/usr/bin/env python3
"""
Test für die neue Verfügbarkeits- und Datums-Parsing-Logik des Lidl Crawlers
Testet verschiedene Availability-Text-Formate und die Extraktion von Enddaten

WICHTIGER HINWEIS:
Der LidlUltimateCrawler verwendet crawl_all_products() ohne Query-Parameter.
Der Test für echte Lidl-Suche zeigt das allgemeine Crawling-Verhalten.
Für spezifische Produktsuchen verwenden Sie den SearchService.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from app.services.lidl_crawler_ultimate import LidlUltimateCrawler

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_availability_parsing():
    """Testet die _parse_availability_and_date Methode mit verschiedenen Beispielen"""
    
    crawler = LidlUltimateCrawler()
    
    # Test-Fälle für verschiedene Verfügbarkeits-Texte
    test_cases = [
        # (input_text, expected_available, expected_valid_until_should_exist)
        ("nur in der Filiale 07.07. - 12.07.", True, True),
        ("nur online 15.01. - 20.01.", True, True),
        ("Verfügbar bis 31.12.2024", True, True),
        ("ausverkauft", False, False),
        ("nicht verfügbar", False, False),
        ("vergriffen", False, False),
        ("Lieferbar ab 01.02.", True, True),
        ("", True, False),  # Leerer Text = verfügbar
        ("Regulär verfügbar", True, False),  # Kein Datum
        ("Angebot gültig 05.03. - 10.03.", True, True),
        ("nur in der Filiale 07.07.2024 - 12.07.2024", True, True),  # Mit Jahr
        ("Aktion 28.02. - 05.03.", True, True),  # Über Monatsgrenze
    ]
    
    print("=== Test der Verfügbarkeits-Parsing-Logik ===\n")
    
    for i, (input_text, expected_available, should_have_date) in enumerate(test_cases, 1):
        try:
            is_available, availability_text, offer_valid_until = crawler._parse_availability_and_date(input_text)
            
            print(f"Test {i:2d}: '{input_text}'")
            print(f"         -> Verfügbar: {is_available} (erwartet: {expected_available})")
            print(f"         -> Text: '{availability_text}'")
            print(f"         -> Gültig bis: {offer_valid_until}")
            
            # Validierung
            if is_available != expected_available:
                print(f"         ❌ FEHLER: Verfügbarkeit erwartet {expected_available}, erhalten {is_available}")
            elif should_have_date and not offer_valid_until:
                print(f"         ⚠️  WARNUNG: Datum erwartet, aber nicht gefunden")
            elif not should_have_date and offer_valid_until:
                print(f"         ⚠️  INFO: Unerwartetes Datum gefunden: {offer_valid_until}")
            else:
                print(f"         ✅ OK")
                
            print()
            
        except Exception as e:
            print(f"Test {i:2d}: ❌ FEHLER bei '{input_text}': {e}\n")

def test_date_validation():
    """Testet die Datumsvalidierung mit Edge Cases"""
    
    crawler = LidlUltimateCrawler()
    
    print("=== Test der Datumsvalidierung ===\n")
    
    # Test mit Datum in der Vergangenheit
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.")
    past_text = f"Angebot gültig bis {yesterday}"
    
    is_available, availability_text, offer_valid_until = crawler._parse_availability_and_date(past_text)
    print(f"Vergangenes Datum: '{past_text}'")
    print(f"-> Verfügbar: {is_available} (sollte False sein)")
    print(f"-> Gültig bis: {offer_valid_until}")
    print()
    
    # Test mit Datum in der Zukunft
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.")
    future_text = f"Angebot gültig bis {tomorrow}"
    
    is_available, availability_text, offer_valid_until = crawler._parse_availability_and_date(future_text)
    print(f"Zukünftiges Datum: '{future_text}'")
    print(f"-> Verfügbar: {is_available} (sollte True sein)")
    print(f"-> Gültig bis: {offer_valid_until}")
    print()

async def test_real_lidl_search():
    """Testet eine echte Lidl-Suche mit dem aktualisierten Crawler"""
    
    print("=== Test echter Lidl-Produktsuche ===\n")
    
    crawler = LidlUltimateCrawler()
    
    try:
        # Da crawl_all_products keine Query akzeptiert, führen wir einen allgemeinen Crawl durch
        results = await crawler.crawl_all_products(max_results=5)
        
        print(f"Gefundene Produkte: {len(results)}")
        print()
        
        for i, product in enumerate(results, 1):
            print(f"Produkt {i}:")
            print(f"  Name: {product.name}")
            print(f"  Preis: €{product.price}")
            print(f"  Store: {product.store}")
            print(f"  Verfügbar: {product.availability}")
            print(f"  Verfügbarkeits-Text: '{product.availability_text}'")
            print(f"  Gültig bis: {product.offer_valid_until}")
            print(f"  Einheit: {product.unit}")
            print(f"  Beschreibung: {product.description}")
            print()
            
    except Exception as e:
        print(f"❌ Fehler bei echter Suche: {e}")

def test_product_result_creation():
    """Testet die Erstellung von ProductResult-Objekten mit den neuen Feldern"""
    
    print("=== Test ProductResult-Erstellung ===\n")
    
    from app.models.search import ProductResult
    
    try:
        # Test mit allen neuen Feldern
        product = ProductResult(
            name="Test Milch",
            price="1.59",  # Convert to string
            store="LIDL",
            availability="verfügbar",  # Convert to string
            availability_text="nur in der Filiale 07.07. - 12.07.",
            offer_valid_until="2024-07-12",
            description="1L Vollmilch",
            unit="1L"
        )
        
        print("ProductResult erfolgreich erstellt:")
        print(f"  Name: {product.name}")
        print(f"  Preis: €{product.price}")
        print(f"  Verfügbar: {product.availability}")
        print(f"  Verfügbarkeits-Text: '{product.availability_text}'")
        print(f"  Gültig bis: {product.offer_valid_until}")
        print("✅ Alle neuen Felder funktionieren korrekt\n")
        
    except Exception as e:
        print(f"❌ Fehler bei ProductResult-Erstellung: {e}\n")

async def main():
    """Hauptfunktion für alle Tests"""
    
    print("🧪 Lidl Crawler Availability & Date Parsing Tests\n")
    print("=" * 60)
    
    # 1. Test der Parsing-Logik
    test_availability_parsing()
    
    # 2. Test der Datumsvalidierung
    test_date_validation()
    
    # 3. Test ProductResult-Erstellung
    test_product_result_creation()
    
    # 4. Test echter Lidl-Suche (optional, braucht Internet)
    try_real_search = input("Echte Lidl-Suche testen? (benötigt Internet) [y/N]: ").lower().strip()
    if try_real_search in ['y', 'yes', 'ja']:
        await test_real_lidl_search()
    
    print("✅ Alle Tests abgeschlossen!")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Test Script für die korrekten LIDL CSS-Selektoren
Testet die neuen, korrekten Selektoren die der User angegeben hat
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.lidl_crawler_ultimate import LidlUltimateCrawler

# Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_correct_selectors():
    """Test der korrekten LIDL CSS-Selektoren"""
    
    print("🧪 LIDL CSS-Selektoren Validation Test")
    print("=" * 60)
    print("Validiere die korrekten CSS-Selektoren:")
    print("✅ odsc-tile__inner - Hauptselektor für Produktkarten")
    print("✅ product-grid-box__title - Produktname")
    print("✅ product-grid-box__desc - Zusätzliche Beschreibung (optional)")
    print("✅ ods-price__value - Preis (z.B. 10,99 oder -,90)")
    print("✅ ods-price__lidl-plus-hint - Supermarket Reward Program")
    print("✅ product-grid-box__availabilities - Verfügbarkeit (DD.MM. - DD.MM.)")
    print("✅ ods-price__footer :first-child - Einheit")
    print("✅ .odsc-image-gallery img - Produktbild")
    print("=" * 60)
    
    crawler = LidlUltimateCrawler()
    
    print(f"🏪 Starte Test mit korrekten Selektoren...")
    print(f"🌐 URL: {crawler.billiger_montag_url}")
    
    # Teste mit begrenzter Anzahl für Validierung
    max_test_results = 20
    
    try:
        products = await crawler.crawl_all_products(
            max_results=max_test_results, 
            postal_code="10115"
        )
        
        print(f"\n📊 TESTERGEBNISSE:")
        print(f"   🎯 Gefundene Produkte: {len(products)}")
        
        if products:
            print(f"\n📋 BEISPIEL-PRODUKTE (erste 3):")
            print("-" * 80)
            
            for i, product in enumerate(products[:3], 1):
                print(f"\n🛒 PRODUKT {i}:")
                print(f"   📛 Name: {product.name}")
                print(f"   💰 Preis: {product.price}€")
                print(f"   📄 Beschreibung: {product.description or 'Keine'}")
                print(f"   📱 Einheit: {product.unit or 'Keine'}")
                print(f"   🏪 Verfügbarkeit: {product.availability}")
                print(f"   📅 Verfügbarkeitstext: {product.availability_text or 'Keine'}")
                print(f"   ⏰ Gültig bis: {product.offer_valid_until or 'Unbekannt'}")
                print(f"   🎁 LIDL Plus: {product.reward_program_hint or 'Keine'}")
                print(f"   🖼️  Bild: {product.image_url[:80]}{'...' if len(product.image_url) > 80 else ''}")
                print("-" * 80)
                
            # Validiere kritische Felder
            print(f"\n🔍 FELDVALIDIERUNG:")
            products_with_price = sum(1 for p in products if p.price and p.price > 0)
            products_with_image = sum(1 for p in products if p.image_url)
            products_with_availability = sum(1 for p in products if p.availability_text)
            products_with_unit = sum(1 for p in products if p.unit)
            products_with_lidl_plus = sum(1 for p in products if p.reward_program_hint)
            products_with_description = sum(1 for p in products if p.description)
            
            print(f"   💰 Produkte mit Preis: {products_with_price}/{len(products)} ({products_with_price/len(products)*100:.1f}%)")
            print(f"   🖼️  Produkte mit Bild: {products_with_image}/{len(products)} ({products_with_image/len(products)*100:.1f}%)")
            print(f"   📅 Produkte mit Verfügbarkeit: {products_with_availability}/{len(products)} ({products_with_availability/len(products)*100:.1f}%)")
            print(f"   📱 Produkte mit Einheit: {products_with_unit}/{len(products)} ({products_with_unit/len(products)*100:.1f}%)")
            print(f"   🎁 Produkte mit LIDL Plus: {products_with_lidl_plus}/{len(products)} ({products_with_lidl_plus/len(products)*100:.1f}%)")
            print(f"   📄 Produkte mit Beschreibung: {products_with_description}/{len(products)} ({products_with_description/len(products)*100:.1f}%)")
            
            # Erfolgs-Bewertung
            success_rate = products_with_price / len(products) * 100
            print(f"\n📈 ERFOLGSRATE:")
            if success_rate >= 90:
                print(f"   ✅ AUSGEZEICHNET: {success_rate:.1f}% der Produkte haben valide Preise")
            elif success_rate >= 70:
                print(f"   ⚠️  GUT: {success_rate:.1f}% der Produkte haben valide Preise")
            else:
                print(f"   ❌ VERBESSERUNG NÖTIG: Nur {success_rate:.1f}% der Produkte haben valide Preise")
                
        else:
            print("   ❌ KEINE PRODUKTE GEFUNDEN - CSS-Selektoren müssen überprüft werden!")
            return False
            
    except Exception as e:
        print(f"   ❌ TEST FEHLER: {e}")
        return False
    
    print(f"\n✅ CSS-Selektoren Test abgeschlossen!")
    return True

if __name__ == "__main__":
    print("🚀 Starte LIDL CSS-Selektoren Validation...")
    success = asyncio.run(test_correct_selectors())
    
    if success:
        print("🎉 Test erfolgreich abgeschlossen!")
        sys.exit(0)
    else:
        print("💥 Test fehlgeschlagen!")
        sys.exit(1) 
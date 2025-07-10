#!/usr/bin/env python3
"""
Direkter Test für den neuen LIDL Billiger Montag Crawler
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.lidl_crawler_ultimate import LidlUltimateCrawler

async def test_lidl_crawler():
    print("🧪 Teste neuen LIDL Billiger Montag Crawler")
    print("=" * 60)
    
    crawler = LidlUltimateCrawler()
    
    print(f"🌐 Ziel-URL: {crawler.billiger_montag_url}")
    print(f"🕒 Timeout: {crawler.timeout} ms")
    print(f"🔍 CSS-Selektoren: {len(crawler.product_selectors)}")
    
    for i, selector in enumerate(crawler.product_selectors, 1):
        print(f"   {i}. {selector}")
    
    print("\n📡 Starte Crawling...")
    try:
        products = await crawler.crawl_all_products(max_results=50)
        
        print(f"\n✅ ERGEBNIS: {len(products)} Produkte gefunden")
        
        if products:
            print("\n📋 Erste 3 Produkte:")
            for i, product in enumerate(products[:3], 1):
                print(f"\n{i}. 📦 {product.name}")
                print(f"   💰 Preis: €{product.price}")
                print(f"   🏪 Store: {product.store}")
                print(f"   📂 Kategorie: {product.category}")
                print(f"   ✅ Verfügbar: {product.availability}")
                if product.availability_text:
                    print(f"   📝 Verfügbarkeitstext: {product.availability_text}")
                if product.offer_valid_until:
                    print(f"   📅 Gültig bis: {product.offer_valid_until}")
        else:
            print("\n❌ Keine Produkte gefunden")
            print("🔍 Mögliche Ursachen:")
            print("   - CSS-Selektoren sind falsch")
            print("   - Seite lädt nicht korrekt")
            print("   - Anti-Bot-Schutz aktiv")
            print("   - Produkt-Extraktion fehlerhaft")
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lidl_crawler()) 
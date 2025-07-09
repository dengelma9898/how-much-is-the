#!/usr/bin/env python3
"""
Test der Lidl Mock-Daten Integration
"""

import asyncio
import json
from decimal import Decimal
from app.services.lidl_mock_data import LidlMockData
from app.services.search_service import SearchService
from app.models.search import SearchRequest

async def test_lidl_mock_data():
    """Teste Lidl Mock-Daten direkt"""
    print("🧪 Teste Lidl Mock-Daten...")
    
    # Test 1: Alle Mock-Produkte
    all_products = LidlMockData.get_mock_products()
    print(f"📦 Gesamt Mock-Produkte: {len(all_products)}")
    
    # Test 2: Filtere nach "milch"
    milch_products = LidlMockData.get_products_for_query("milch")
    print(f"🥛 Milch-Produkte: {len(milch_products)}")
    for product in milch_products:
        print(f"  - {product.name} ({product.price}€) - {product.available_until}")
    
    # Test 3: Filtere nach "käse"
    kaese_products = LidlMockData.get_products_for_query("käse")
    print(f"🧀 Käse-Produkte: {len(kaese_products)}")
    for product in kaese_products:
        print(f"  - {product.name} ({product.price}€)")
    
    # Test 4: Filtere nach "apfel"
    apfel_products = LidlMockData.get_products_for_query("apfel")
    print(f"🍎 Apfel-Produkte: {len(apfel_products)}")
    for product in apfel_products:
        print(f"  - {product.name} ({product.price}€) - {product.origin}")

async def test_search_service_integration():
    """Teste Integration in SearchService"""
    print("\n🔍 Teste SearchService Integration...")
    
    search_service = SearchService()
    
    # Test verschiedene Queries
    test_queries = ["milch", "brot", "apfel", "hackfleisch", "cola"]
    
    for query in test_queries:
        search_request = SearchRequest(
            query=query,
            postal_code="90402",
            selected_stores=None,
            unit=None,
            max_price=None
        )
        
        response = await search_service.search_products(search_request)
        
        print(f"\n📈 Query: '{query}'")
        print(f"   Ergebnisse: {response.total_results}")
        print(f"   Suchzeit: {response.search_time_ms}ms")
        
        # Zeige Lidl-Produkte
        lidl_results = [r for r in response.results if r.store == "Lidl"]
        print(f"   Lidl-Produkte: {len(lidl_results)}")
        
        for product in lidl_results[:3]:  # Zeige nur erste 3
            partner_info = " [Partner]" if product.partner_program else ""
            print(f"     • {product.name} - {product.price}€{partner_info}")

async def test_partner_program_flag():
    """Teste Partner-Program Flag"""
    print("\n🤝 Teste Partner-Program Flags...")
    
    all_products = LidlMockData.get_mock_products()
    partner_products = [p for p in all_products if p.partner_program]
    
    print(f"Partner-Programm Produkte: {len(partner_products)}/{len(all_products)}")
    
    # Zeige verfügbare Zeiträume
    availability_types = {}
    for product in partner_products:
        avail = product.available_until or "Nicht angegeben"
        if avail not in availability_types:
            availability_types[avail] = 0
        availability_types[avail] += 1
    
    print("Verfügbarkeitszeiträume:")
    for avail, count in availability_types.items():
        print(f"  - {avail}: {count} Produkte")

async def main():
    """Hauptfunktion für alle Tests"""
    print("=== LIDL MOCK-DATEN TESTS ===\n")
    
    await test_lidl_mock_data()
    await test_search_service_integration()
    await test_partner_program_flag()
    
    print("\n✅ Alle Tests abgeschlossen!")

if __name__ == "__main__":
    asyncio.run(main()) 
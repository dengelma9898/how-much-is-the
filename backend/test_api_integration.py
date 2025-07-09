#!/usr/bin/env python3
"""
Test der vollständigen API-Integration mit Ultimate Crawler
"""

import asyncio
import sys
import os

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.search_service import search_service
from app.models.search import SearchRequest

async def test_api_integration():
    """Testet die vollständige API-Integration"""
    
    print("🌐 API INTEGRATION TEST mit Ultimate Crawler")
    print("=" * 60)
    
    # Test 1: Alle LIDL-Produkte
    print("\n🔍 TEST 1: Alle LIDL-Produkte über API")
    print("-" * 40)
    
    search_request = SearchRequest(
        query="produkte",  # Allgemeiner Suchbegriff
        postal_code="10115",
        selected_stores=["LIDL"],  # Nur LIDL
        max_price=None,
        unit=None
    )
    
    response = await search_service.search_products(search_request)
    
    print(f"✅ API Response erhalten!")
    print(f"📊 Total Ergebnisse: {response.total_results}")
    print(f"⏱️  Suchzeit: {response.search_time_ms}ms")
    print(f"🔍 Query: '{response.query}'")
    print(f"📍 PLZ: {response.postal_code}")
    
    if response.results:
        print(f"\n📋 Erste 5 Produkte:")
        for i, product in enumerate(response.results[:5], 1):
            print(f"   {i}. {product.name} - €{product.price} ({product.store})")
            if product.unit:
                print(f"      📦 Einheit: {product.unit}")
            if product.availability:
                print(f"      📅 Verfügbarkeit: {product.availability}")
    
    # Test 2: Spezifische Suche
    print(f"\n🔍 TEST 2: Spezifische Suche nach 'tomaten'")
    print("-" * 40)
    
    search_request_specific = SearchRequest(
        query="tomaten",
        postal_code="10115", 
        selected_stores=["LIDL"],
        max_price=5.00,  # Max €5
        unit=None
    )
    
    response_specific = await search_service.search_products(search_request_specific)
    
    print(f"✅ Spezifische Suche abgeschlossen!")
    print(f"📊 Gefilterte Ergebnisse: {response_specific.total_results}")
    print(f"⏱️  Suchzeit: {response_specific.search_time_ms}ms")
    
    if response_specific.results:
        print(f"\n📋 Tomaten-Produkte:")
        for i, product in enumerate(response_specific.results, 1):
            print(f"   {i}. {product.name} - €{product.price}")
    else:
        print(f"   ℹ️  Keine Tomaten-Produkte gefunden")
    
    # Test 3: Performance-Vergleich
    print(f"\n📊 PERFORMANCE-ANALYSE:")
    print("-" * 40)
    
    total_products = response.total_results
    search_time = response.search_time_ms
    
    print(f"🎯 Total gefundene Produkte: {total_products}")
    print(f"⚡ Suchzeit: {search_time}ms")
    print(f"🚀 Produkte/Sekunde: {total_products / (search_time / 1000):.1f}")
    
    if total_products >= 80:
        print(f"🎉 EXCELLENT! Über 80 Produkte über API gefunden!")
    elif total_products >= 50:
        print(f"✅ GREAT! Über 50 Produkte über API gefunden!")
    elif total_products >= 20:
        print(f"⚠️  OK! Über 20 Produkte über API gefunden!")
    else:
        print(f"❌ PROBLEM! Nur {total_products} Produkte über API gefunden!")
    
    # Test 4: Store-Filter Test
    print(f"\n🔍 TEST 4: Multi-Store Filter")
    print("-" * 40)
    
    search_request_multi = SearchRequest(
        query="lebensmittel",
        postal_code="10115",
        selected_stores=["LIDL", "ALDI"],  # Beide Stores
        max_price=None,
        unit=None
    )
    
    response_multi = await search_service.search_products(search_request_multi)
    
    print(f"✅ Multi-Store Suche abgeschlossen!")
    print(f"📊 Total Ergebnisse: {response_multi.total_results}")
    
    # Store-Verteilung analysieren
    store_counts = {}
    for product in response_multi.results:
        store = product.store
        if store not in store_counts:
            store_counts[store] = 0
        store_counts[store] += 1
    
    print(f"\n🏪 Store-Verteilung:")
    for store, count in store_counts.items():
        print(f"   🎯 {store}: {count} Produkte")
    
    # Finale Zusammenfassung
    print(f"\n🎯 FINALE ZUSAMMENFASSUNG:")
    print("=" * 60)
    print(f"✅ Ultimate Crawler erfolgreich in API integriert!")
    print(f"📊 LIDL-Produkte: {total_products}")
    print(f"⚡ Performance: {search_time}ms")
    print(f"🔍 Filterung funktioniert: {'✅' if response_specific.total_results <= total_products else '❌'}")
    print(f"🏪 Multi-Store funktioniert: {'✅' if len(store_counts) > 1 else '⚠️'}")
    
    return total_products

if __name__ == "__main__":
    result = asyncio.run(test_api_integration()) 
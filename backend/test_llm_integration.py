#!/usr/bin/env python3
"""
Test der LLM-Integration für Lidl-Crawler
"""

import asyncio
import json
from app.services.lidl_llm_interpreter import lidl_llm_interpreter
from app.core.config import settings

async def test_llm_interpreter_mock():
    """Teste LLM-Interpreter mit Mock-HTML-Daten"""
    print("🧪 Teste LLM-Interpreter mit Mock-Daten...")
    
    # Mock HTML-Inhalte (Lidl-ähnlich)
    mock_html = """
    <div class="AThe product-container">
        <h3 class="product-title">Milbona Frische Vollmilch</h3>
        <span class="price">-.65 €</span>
        <span class="unit">1 Liter</span>
        <span class="discount">-23%</span>
        <span class="availability">Nur Montag</span>
    </div>
    
    <div class="AThe product-container">
        <h3 class="product-title">Grafschafter Vollkornbrot</h3>
        <span class="price">-1.49 €</span>
        <span class="unit">750g</span>
        <span class="discount">-25%</span>
        <span class="availability">Nur Montag</span>
    </div>
    """
    
    # Mock Raw Products
    mock_raw_products = [
        {
            "text": "Milbona Frische Vollmilch -.65 € 1 Liter -23% Nur Montag",
            "price_candidates": ["-.65", "-.65 €"],
            "name_candidates": ["Milbona Frische Vollmilch", "Frische Vollmilch"],
            "context": "Milchprodukte Billiger Montag"
        },
        {
            "text": "Grafschafter Vollkornbrot -1.49 € 750g -25% Nur Montag",
            "price_candidates": ["-1.49", "-1.49 €"],
            "name_candidates": ["Grafschafter Vollkornbrot", "Vollkornbrot"],
            "context": "Backwaren Billiger Montag"
        }
    ]
    
    # Teste verschiedene Suchbegriffe
    test_queries = ["milch", "brot", "lebensmittel"]
    
    for query in test_queries:
        print(f"\n🔍 Teste Query: '{query}'")
        
        if not settings.openai_api_key:
            print("⚠️ OpenAI API Key nicht gesetzt - überspringe LLM-Test")
            print("   💡 Setze OPENAI_API_KEY in der .env.local für echte LLM-Tests")
            continue
        
        try:
            result = await lidl_llm_interpreter.interpret_html_data(
                html_content=mock_html,
                raw_products=mock_raw_products,
                search_query=query
            )
            
            print(f"   ✅ Confidence: {result.confidence}")
            print(f"   ✅ Method: {result.extraction_method}")
            print(f"   ✅ Products: {len(result.products)}")
            
            for product in result.products:
                print(f"     • {product.name} - {product.price}€")
                if product.available_until:
                    print(f"       📅 {product.available_until}")
                if product.discount:
                    print(f"       💰 {product.discount}")
            
        except Exception as e:
            print(f"   ❌ Fehler: {e}")

async def test_price_patterns():
    """Teste Preismuster-Extraktion"""
    print("\n🧪 Teste Preismuster-Extraktion...")
    
    test_html = """
    Verschiedene Preisformate:
    -.65 €
    -1.49 €
    €2.99
    1,99 EUR
    3.50
    4€
    5,90 €
    -.99
    """
    
    # Simuliere Preismuster-Extraktion
    interpreter = lidl_llm_interpreter
    price_patterns = interpreter._extract_price_patterns(test_html)
    
    print(f"Gefundene Preismuster: {len(price_patterns)}")
    for pattern in price_patterns:
        print(f"  - {pattern}")

async def test_json_structures():
    """Teste JSON-Struktur-Extraktion"""
    print("\n🧪 Teste JSON-Struktur-Extraktion...")
    
    test_html_with_json = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Lidl Milch",
        "offers": {
            "@type": "Offer",
            "price": "0.65",
            "priceCurrency": "EUR"
        }
    }
    </script>
    
    <script>
    var productData = {"name": "Test Produkt", "price": 1.99};
    </script>
    """
    
    interpreter = lidl_llm_interpreter
    json_structures = interpreter._extract_json_structures(test_html_with_json)
    
    print(f"Gefundene JSON-Strukturen: {len(json_structures)}")
    for structure in json_structures:
        print(f"  - {json.dumps(structure, indent=2)}")

async def test_config_check():
    """Teste Konfigurationsstatus"""
    print("\n🔧 Teste Konfiguration...")
    
    print(f"OpenAI API Key gesetzt: {'✅' if settings.openai_api_key else '❌'}")
    print(f"Lidl Crawler aktiviert: {'✅' if settings.lidl_crawler_enabled else '❌'}")
    print(f"Lidl Base URL: {settings.lidl_base_url}")
    
    if not settings.openai_api_key:
        print("\n💡 Für LLM-Tests OpenAI API Key setzen:")
        print("   export OPENAI_API_KEY='your_api_key_here'")
        print("   # oder in .env.local: OPENAI_API_KEY=your_api_key_here")

async def main():
    """Hauptfunktion für alle Tests"""
    print("=== LLM-INTEGRATION TESTS ===\n")
    
    await test_config_check()
    await test_price_patterns()
    await test_json_structures() 
    await test_llm_interpreter_mock()
    
    print("\n✅ Alle Tests abgeschlossen!")

if __name__ == "__main__":
    asyncio.run(main()) 
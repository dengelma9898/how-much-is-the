import random
from decimal import Decimal
from typing import List
from shared.models.search import ProductResult, Store

class MockDataService:
    """Service für Mock-Daten während der Entwicklung"""
    
    def __init__(self):
        self.stores = [
            Store(id="lidl", name="Lidl", category="Discounter",
                  logo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Lidl-Logo.svg/200px-Lidl-Logo.svg.png",
                  website_url="https://www.lidl.de"),
            # Additional stores can be added later when their crawlers are implemented
        ]
        
        # Mock-Produktdaten mit verschiedenen Kategorien
        self.product_templates = {
            "milch": [
                {"name": "Vollmilch 3,5%", "unit": "1L", "base_price": 1.09},
                {"name": "H-Milch 3,5%", "unit": "1L", "base_price": 0.89},
                {"name": "Bio Vollmilch", "unit": "1L", "base_price": 1.49},
                {"name": "Laktosefreie Milch", "unit": "1L", "base_price": 1.29},
            ],
            "eier": [
                {"name": "Freilandeier", "unit": "6 Stück", "base_price": 2.49},
                {"name": "Bio-Eier", "unit": "6 Stück", "base_price": 2.99},
                {"name": "Bodenhaltung Eier", "unit": "10 Stück", "base_price": 2.89},
            ],
            "oatly": [
                {"name": "Oatly Haferdrink Original", "unit": "1L", "base_price": 2.79},
                {"name": "Oatly Barista Edition", "unit": "1L", "base_price": 2.99},
                {"name": "Oatly Chocolate", "unit": "1L", "base_price": 3.29},
            ],
            "haribo": [
                {"name": "Haribo Goldbären", "unit": "200g", "base_price": 1.49},
                {"name": "Haribo Color-Rado", "unit": "175g", "base_price": 1.69},
                {"name": "Haribo Phantasia", "unit": "200g", "base_price": 1.89},
                {"name": "Haribo Saure Pommes", "unit": "200g", "base_price": 1.79},
            ],
            "brot": [
                {"name": "Vollkornbrot", "unit": "500g", "base_price": 2.49},
                {"name": "Körnerbrot", "unit": "750g", "base_price": 2.99},
                {"name": "Weißbrot", "unit": "500g", "base_price": 1.99},
            ],
            "joghurt": [
                {"name": "Naturjoghurt 3,5%", "unit": "500g", "base_price": 0.89},
                {"name": "Griechischer Joghurt", "unit": "150g", "base_price": 1.19},
                {"name": "Bio Joghurt", "unit": "500g", "base_price": 1.49},
            ]
        }
    
    def get_stores(self) -> List[Store]:
        """Gibt Liste aller verfügbaren Stores zurück"""
        return self.stores
    
    def search_products(self, query: str, postal_code: str) -> List[ProductResult]:
        """Generiert Mock-Suchergebnisse basierend auf Suchbegriff"""
        results = []
        query_lower = query.lower()
        
        # Finde passende Produktvorlagen
        matching_templates = []
        for category, templates in self.product_templates.items():
            if category in query_lower or any(query_lower in template["name"].lower() for template in templates):
                matching_templates.extend(templates)
        
        # Falls keine spezifischen Matches, verwende allgemeine Produktkategorien
        if not matching_templates:
            # Suche nach allgemeinen Begriffen
            for category, templates in self.product_templates.items():
                if any(word in category for word in query_lower.split()):
                    matching_templates.extend(templates[:2])  # Nur erste 2 pro Kategorie
        
        # Falls immer noch keine Matches, verwende zufällige Produkte
        if not matching_templates:
            all_templates = []
            for templates in self.product_templates.values():
                all_templates.extend(templates)
            matching_templates = random.sample(all_templates, min(3, len(all_templates)))
        
        # Generiere Ergebnisse für verschiedene Stores
        for template in matching_templates[:5]:  # Max 5 verschiedene Produkte
            # Jedes Produkt in 3-5 verschiedenen Stores
            available_stores = random.sample(self.stores, random.randint(3, 5))
            
            for store in available_stores:
                # Preisvariation basierend auf Store-Typ und PLZ
                price_modifier = self._get_price_modifier(store.category, postal_code)
                final_price = Decimal(str(template["base_price"])) * Decimal(str(price_modifier))
                final_price = final_price.quantize(Decimal('0.01'))
                
                # Berechne Preis pro Einheit falls möglich
                price_per_unit = None
                if template.get("unit"):
                    unit_str = template["unit"]
                    # Extrahiere Zahl aus Einheit für Grundpreis-Berechnung
                    import re
                    numbers = re.findall(r'\d+', unit_str)
                    if numbers:
                        unit_amount = int(numbers[0])
                        if 'kg' in unit_str or 'g' in unit_str:
                            # Umrechnung auf 100g
                            if 'kg' in unit_str:
                                price_per_unit = (final_price / unit_amount * 100).quantize(Decimal('0.01'))
                            else:
                                price_per_unit = (final_price / unit_amount * 100).quantize(Decimal('0.01'))
                        elif 'L' in unit_str or 'ml' in unit_str:
                            # Umrechnung auf 1L
                            if 'L' in unit_str:
                                price_per_unit = (final_price / unit_amount).quantize(Decimal('0.01'))
                            else:
                                price_per_unit = (final_price / unit_amount * 1000).quantize(Decimal('0.01'))
                
                result = ProductResult(
                    name=template["name"],
                    price=final_price,
                    store=store.name,
                    store_logo_url=store.logo_url,
                    product_url=f"{store.website_url}/products/{template['name'].lower().replace(' ', '-')}",
                    image_url=f"https://via.placeholder.com/200x200?text={template['name'].replace(' ', '+')}",
                    unit=template.get("unit"),
                    price_per_unit=price_per_unit,
                    availability="verfügbar"
                )
                results.append(result)
        
        # Sortiere nach Preis (günstigster zuerst)
        results.sort(key=lambda x: x.price)
        
        return results
    
    def _get_price_modifier(self, store_category: str, postal_code: str) -> float:
        """Berechnet Preismodifikator basierend auf Store-Typ und Region"""
        base_modifier = 1.0
        
        # Store-Typ Modifier
        if store_category == "Discounter":
            base_modifier = 0.85  # 15% günstiger
        elif store_category == "Supermarkt":
            base_modifier = 1.05  # 5% teurer
        elif store_category == "Drogerie":
            base_modifier = 1.10  # 10% teurer
        
        # Regional-Modifier basierend auf PLZ (vereinfacht)
        first_digit = int(postal_code[0])
        regional_modifier = 1.0
        
        if first_digit in [1, 2]:  # Hamburg, Bremen, etc. (teurer)
            regional_modifier = 1.10
        elif first_digit in [8, 9]:  # Bayern, Baden-Württemberg (teurer)
            regional_modifier = 1.08
        elif first_digit in [3, 4, 5]:  # NRW, Niedersachsen (durchschnittlich)
            regional_modifier = 1.00
        else:  # Ostdeutschland (günstiger)
            regional_modifier = 0.95
        
        # Kleine zufällige Variation ±5%
        random_modifier = random.uniform(0.95, 1.05)
        
        return base_modifier * regional_modifier * random_modifier

mock_data_service = MockDataService() 
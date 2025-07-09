"""
Mock-Daten für Lidl-Produkte während der Entwicklung
Simuliert realistische "Billiger Montag" Angebote
"""

from decimal import Decimal
from typing import List
from app.models.search import ProductResult

class LidlMockData:
    """Mock-Datenklasse für Lidl-Produkte"""
    
    @staticmethod
    def get_mock_products() -> List[ProductResult]:
        """Liefert realistische Mock-Produkte für Lidl 'Billiger Montag'"""
        return [
            # Milchprodukte
            ProductResult(
                name="Milbona Frische Vollmilch",
                price=Decimal("0.65"),
                store="Lidl",
                unit="1 Liter",
                brand="Milbona",
                category="Milch & Molkereiprodukte",
                partner_program=True,
                available_until="Nur Montag",
                discount="-23%",
                origin="Deutschland",
                quality_info="3,5% Fett"
            ),
            
            ProductResult(
                name="Milbona Joghurt Natur",
                price=Decimal("0.39"),
                store="Lidl",
                unit="500g",
                brand="Milbona",
                category="Milch & Molkereiprodukte", 
                partner_program=True,
                available_until="Nur Montag",
                discount="-35%"
            ),
            
            ProductResult(
                name="Müller Milch Vanille",
                price=Decimal("0.99"),
                store="Lidl",
                unit="400ml",
                brand="Müller",
                category="Milch & Molkereiprodukte",
                partner_program=True,
                available_until="07.07. - 12.07.",
                discount="-15%"
            ),
            
            # Backwaren
            ProductResult(
                name="Grafschafter Vollkornbrot",
                price=Decimal("1.49"),
                store="Lidl",
                unit="750g",
                brand="Grafschafter",
                category="Brot & Backwaren",
                partner_program=True,
                available_until="Nur Montag",
                discount="-25%"
            ),
            
            ProductResult(
                name="Lidl Aufbackbrötchen",
                price=Decimal("0.89"),
                store="Lidl",
                unit="6 Stück",
                brand="Lidl",
                category="Brot & Backwaren",
                partner_program=True,
                available_until="Nur Montag"
            ),
            
            # Käse & Wurst
            ProductResult(
                name="Dulano Gouda Scheiben",
                price=Decimal("1.79"),
                store="Lidl",
                unit="200g",
                brand="Dulano",
                category="Käse & Molkerei",
                partner_program=True,
                available_until="Nur Montag",
                discount="-30%"
            ),
            
            ProductResult(
                name="Dulano Salami",
                price=Decimal("2.29"),
                store="Lidl", 
                unit="300g",
                brand="Dulano",
                category="Fleisch & Wurst",
                partner_program=True,
                available_until="07.07. - 12.07.",
                discount="-20%"
            ),
            
            # Obst & Gemüse
            ProductResult(
                name="Deutsche Radieschen",
                price=Decimal("0.49"),
                store="Lidl",
                unit="1 Bund",
                brand=None,
                category="Obst & Gemüse",
                partner_program=True,
                available_until="Nur Montag",
                discount="-38%",
                origin="Deutschland"
            ),
            
            ProductResult(
                name="Rote Paprika",
                price=Decimal("1.29"),
                store="Lidl",
                unit="500g",
                brand=None,
                category="Obst & Gemüse",
                partner_program=True,
                available_until="Nur Montag",
                discount="-19%",
                origin="Spanien"
            ),
            
            ProductResult(
                name="Kiwi Gold",
                price=Decimal("0.55"),
                store="Lidl",
                unit="1 Stück",
                brand=None,
                category="Obst & Gemüse",
                partner_program=True,
                available_until="07.07. - 12.07.",
                origin="Neuseeland"
            ),
            
            ProductResult(
                name="Äpfel Elstar",
                price=Decimal("1.99"),
                store="Lidl",
                unit="1kg",
                brand=None,
                category="Obst & Gemüse",
                partner_program=True,
                available_until="Nur Montag",
                discount="-33%",
                origin="Deutschland"
            ),
            
            # Fleisch
            ProductResult(
                name="Frisches Hackfleisch gemischt",
                price=Decimal("4.99"),
                store="Lidl",
                unit="500g",
                brand=None,
                category="Fleisch & Wurst",
                partner_program=True,
                available_until="Nur Montag",
                discount="-17%",
                origin="Deutschland",
                quality_info="80/20 Rind/Schwein"
            ),
            
            ProductResult(
                name="Hähnchenbrust-Filet",
                price=Decimal("6.99"),
                store="Lidl",
                unit="1kg",
                brand=None,
                category="Fleisch & Wurst",
                partner_program=True,
                available_until="07.07. - 12.07.",
                discount="-25%",
                origin="Deutschland"
            ),
            
            # Getränke
            ProductResult(
                name="Freeway Cola",
                price=Decimal("0.79"),
                store="Lidl",
                unit="1,5 Liter",
                brand="Freeway",
                category="Getränke",
                partner_program=True,
                available_until="Nur Montag",
                discount="-21%"
            ),
            
            ProductResult(
                name="Saskia Mineralwasser",
                price=Decimal("0.19"),
                store="Lidl",
                unit="1,5 Liter",
                brand="Saskia",
                category="Getränke",
                partner_program=True,
                available_until="Nur Montag",
                discount="-24%"
            ),
            
            # Tiefkühlprodukte
            ProductResult(
                name="Freshona Pommes Frites",
                price=Decimal("1.39"),
                store="Lidl",
                unit="1kg",
                brand="Freshona",
                category="Tiefkühl",
                partner_program=True,
                available_until="07.07. - 12.07.",
                discount="-22%"
            ),
            
            ProductResult(
                name="Freshona Gemüsemischung",
                price=Decimal("1.19"),
                store="Lidl",
                unit="750g",
                brand="Freshona",
                category="Tiefkühl",
                partner_program=True,
                available_until="Nur Montag",
                discount="-29%"
            )
        ]
    
    @staticmethod
    def filter_by_query(products: List[ProductResult], query: str) -> List[ProductResult]:
        """Filtert Mock-Produkte nach Suchbegriff"""
        if not query:
            return products
        
        query_lower = query.lower()
        filtered = []
        
        for product in products:
            # Suche in Name, Kategorie und Marke (erweiterte Suche)
            search_text = f"{product.name} {product.category or ''} {product.brand or ''}".lower()
            
            # Zusätzliche Suchbegriffe für bessere Matches
            if "apfel" in query_lower and "äpfel" in search_text:
                filtered.append(product)
            elif "kaese" in query_lower and "käse" in search_text:
                filtered.append(product)
            elif "brot" in query_lower and ("brot" in search_text or "backware" in search_text):
                filtered.append(product)
            elif query_lower in search_text:
                filtered.append(product)
        
        return filtered
    
    @staticmethod
    def get_products_for_query(query: str, max_results: int = 15) -> List[ProductResult]:
        """Liefert gefilterte Mock-Produkte für eine Suchanfrage"""
        all_products = LidlMockData.get_mock_products()
        filtered_products = LidlMockData.filter_by_query(all_products, query)
        
        # Sortiere nach Relevanz (einfacher String-Match)
        def relevance_score(product: ProductResult) -> float:
            name_lower = product.name.lower()
            query_lower = query.lower()
            
            if name_lower.startswith(query_lower):
                return 3.0
            elif query_lower in name_lower:
                return 2.0
            elif query_lower in (product.category or '').lower():
                return 1.5
            elif query_lower in (product.brand or '').lower():
                return 1.0
            else:
                return 0.5
        
        sorted_products = sorted(filtered_products, key=relevance_score, reverse=True)
        return sorted_products[:max_results] 
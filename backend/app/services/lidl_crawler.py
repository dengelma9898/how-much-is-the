"""
Lidl-spezifischer Web-Crawler mit Firecrawl-Integration
Crawlt die "Billiger Montag" Seite und filtert nach Suchbegriff
Update für Firecrawl v2.15.0 API
"""

import asyncio
import logging
import re
import urllib.parse
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any
from app.models.search import ProductResult
from app.core.config import settings

logger = logging.getLogger(__name__)

class LidlCrawler:
    """Lidl-spezifischer Crawler für "Billiger Montag" Angebote (Firecrawl v2.15.0)"""
    
    def __init__(self, firecrawl_app=None):
        self.firecrawl_app = firecrawl_app
        self.base_url = settings.lidl_base_url
        self.billiger_montag_url = settings.lidl_billiger_montag_url
        self.enabled = settings.lidl_crawler_enabled
        
    async def search_products(self, query: str, max_results: int = 15) -> List[ProductResult]:
        """Hauptmethode für Produktsuche bei Lidl über "Billiger Montag" Seite"""
        if not self.enabled or not self.firecrawl_app:
            logger.warning("Lidl-Crawler ist deaktiviert oder Firecrawl nicht verfügbar")
            return []
            
        if not query or len(query.strip()) < 2:
            logger.warning("Suchbegriff zu kurz für Lidl-Suche")
            return []
            
        try:
            logger.info(f"Starte Lidl-Produktsuche für Query: '{query}' auf Billiger Montag Seite")
            
            logger.debug(f"Lidl-URL: {self.billiger_montag_url}")
            
            # Firecrawl v2.15.0 API-Aufruf - optimiert für Stabilität und Vollständigkeit
            response = self.firecrawl_app.scrape_url(
                self.billiger_montag_url,
                formats=["extract"],
                extract={
                    "schema": self._get_billiger_montag_schema(),
                    "prompt": self._get_extraction_prompt(),
                    "systemPrompt": "Du bist ein Experte für E-Commerce-Produktdaten. Extrahiere präzise Produktinformationen aus Lidl-Angeboten. Erfasse ALLE Produkte auf der Seite. Achte besonders auf korrekte Preise, Verfügbarkeitsdaten und Einheiten."
                },
                onlyMainContent=False,  # Erfasse gesamte Seite
                waitFor=3000,  # Optimierte Wartezeit
                timeout=30000,  # Stabiles 30 Sekunden Timeout
                maxAge=300000  # 5 Minuten Cache
            )
            
            # Neue v2.15.0 Response-Struktur (ScrapeResponse-Objekt)
            if not response or not hasattr(response, 'extract') or not response.extract:
                logger.warning(f"Keine Daten von Lidl Billiger Montag Seite erhalten")
                return []
                
            extracted_data = response.extract
            logger.debug(f"Lidl-Extraktion erfolgreich: {extracted_data}")
            
            # Produktdaten verarbeiten und nach Query filtern
            products = self._process_billiger_montag_results(extracted_data, query)
            
            # Ergebnisse limitieren
            limited_products = products[:max_results]
            
            logger.info(f"Lidl-Suche für '{query}': {len(limited_products)} passende Produkte gefunden")
            return limited_products
            
        except Exception as e:
            logger.error(f"Fehler bei Lidl-Produktsuche für '{query}': {e}")
            return []
    
    def _get_billiger_montag_schema(self) -> Dict[str, Any]:
        """JSON Schema für Lidl Billiger Montag Extraktion - Optimiert für maximale Produkterfassung"""
        return {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "minItems": 10,  # Erwarte mindestens 10 Produkte
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Vollständiger Produktname wie angezeigt (z.B. 'Deutsche Radieschen', 'Rote Paprika', 'Kiwi Gold, lose')"
                            },
                            "price": {
                                "type": "string",
                                "description": "Aktueller Angebotspreis - nur die Zahl ohne Währung (z.B. '0.49', '1.29', '2.49')"
                            },
                            "unit": {
                                "type": "string", 
                                "description": "Einheit/Verpackungsangabe (z.B. 'Je Bund', 'Je 500 g', 'Je Stück', 'kg-Preis', '100-g-Preis')"
                            },
                            "availability": {
                                "type": "string",
                                "description": "Verfügbarkeitszeitraum (z.B. '07.07. - 12.07.', 'nur in der Filiale', 'Dauerhaft im Sortiment')"
                            },
                            "original_price": {
                                "type": "string",
                                "description": "Durchgestrichener ursprünglicher Preis falls vorhanden (z.B. '-.59')"
                            },
                            "category": {
                                "type": "string",
                                "description": "Produktkategorie basierend auf Seitenbereich (z.B. 'Frische vom Rekordsieger', 'Backwaren', 'XXL Family Pack')"
                            },
                            "discount_percentage": {
                                "type": "string",
                                "description": "Rabatt in Prozent falls angezeigt (z.B. '-16%')"
                            },
                            "price_detail": {
                                "type": "string",
                                "description": "Zusätzliche Preisangabe (z.B. '1 kg = 2.58', '1 kg = 1.66')"
                            }
                        },
                        "required": ["name", "price"]
                    }
                },
                "page_info": {
                    "type": "object",
                    "properties": {
                        "offer_period": {
                            "type": "string",
                            "description": "Gesamter Gültigkeitszeitraum der Angebote (z.B. '07.07.–20.07.2025')"
                        },
                        "total_products_found": {
                            "type": "number",
                            "description": "Anzahl der gefundenen Produkte auf der Seite"
                        }
                    }
                }
            },
            "required": ["products"]
        }
    
    def _get_extraction_prompt(self) -> str:
        """Generiert einen optimierten Extraction-Prompt für Lidl Billiger Montag"""
        return """
        Du bist ein Experte für das Extrahieren von Produktdaten aus Lidl-Webseiten. 
        Extrahiere ALLE sichtbaren Produktangebote von der Lidl "Billiger Montag" Seite.
        
        WICHTIG: Scrolle durch die GESAMTE Seite und erfasse ALLE Produkte in ALLEN Kategorien:
        - "Frische vom Rekordsieger – Lohnt sich ab Montag"
        - "Frische vom Rekordsieger – Lohnt sich" 
        - "Nr. 1 für Backwaren – Lohnt sich"
        - "Mehr Qualität und Frische – Lohnt sich"
        - "Weiter mit den Tiefpreisen – Lohnt sich"
        - "XXL Family Pack"
        - "Bunte Blumenvielfalt – Lohnt sich"
        - "Lidl Plus Angebote – Lohnt sich"
        - Alle anderen Produktsektionen
        
        Für jedes Produkt extrahiere:
        - name: Vollständiger Produktname (z.B. "Deutsche Radieschen", "Rote Paprika 500g")
        - price: Nur die Zahl des aktuellen Preises (z.B. "0.49", "1.29", "2.49")
        - unit: Einheit/Verpackung (z.B. "Je Bund", "Je 500 g", "Je 1,5 kg", "kg-Preis")
        - availability: Verfügbarkeitszeitraum (z.B. "07.07. - 12.07.", "nur in der Filiale")
        - original_price: Durchgestrichener Preis falls vorhanden (z.B. "-.59")
        - category: Kategoriebereich falls erkennbar
        
        IGNORIERE:
        - Werbebanner, Buttons, Navigation
        - Texte wie "Mitmachen und gewinnen", "Lohnt sich", "Exklusive Coupons"
        - Rechtliche Hinweise und Fußnoten
        
        ZIEL: Mindestens 15-30 echte Produktangebote finden, nicht nur 3!
        """
    
    def _process_billiger_montag_results(self, extracted_data: Dict[str, Any], query: str) -> List[ProductResult]:
        """Verarbeitet Lidl Billiger Montag Ergebnisse zu ProductResult-Objekten und filtert nach Query"""
        products = []
        
        try:
            # Produktdaten extrahieren
            products_data = extracted_data.get('products', [])
            page_info = extracted_data.get('page_info', {})
            offer_period = page_info.get('offer_period', 'Billiger Montag')
            
            logger.debug(f"Verarbeite {len(products_data)} Lidl Billiger Montag Produkte")
            
            for result_data in products_data:
                try:
                    # Grunddaten validieren
                    name = result_data.get('name', '').strip()
                    price_str = result_data.get('price', '').strip()
                    
                    if not name or not price_str:
                        logger.debug(f"Überspringe Produkt ohne Namen oder Preis: {result_data}")
                        continue
                    
                    # Prüfe ob der Produktname zum Suchbegriff passt
                    if not self._matches_query(name, query):
                        logger.debug(f"Produkt '{name}' passt nicht zu Query '{query}'")
                        continue
                    
                    # Preis parsen
                    price = self._parse_price(price_str)
                    if not price:
                        logger.debug(f"Kann Preis nicht parsen: '{price_str}'")
                        continue
                    
                    # Unit-String verarbeiten
                    unit_str = result_data.get('unit', '').strip()
                    unit = unit_str if unit_str else None
                    
                    # Verfügbarkeitsinformation
                    availability_str = result_data.get('availability', '').strip()
                    available_until = availability_str if availability_str else offer_period
                    
                    # Rabatt berechnen falls Originalpreis vorhanden
                    discount = None
                    original_price_str = result_data.get('original_price', '').strip()
                    if original_price_str:
                        original_price = self._parse_price(original_price_str)
                        if original_price and original_price > price:
                            discount_percent = int(((original_price - price) / original_price) * 100)
                            discount = f"-{discount_percent}%"
                    
                    # ProductResult erstellen
                    product = ProductResult(
                        name=name,
                        price=price,
                        store="Lidl",
                        unit=unit,
                        brand=self._extract_brand_from_name(name),
                        category=result_data.get('category'),
                        discount=discount,
                        
                        # Lidl-spezifische Felder
                        partner_program=True,  # Billiger Montag ist ein spezielles Angebot
                        available_until=available_until,
                        
                        # Standard-Felder
                        origin=None,
                        quality_info=None
                    )
                    
                    products.append(product)
                    logger.debug(f"Produkt erfolgreich verarbeitet: {name} - €{price}")
                    
                except Exception as e:
                    logger.error(f"Fehler beim Verarbeiten von Produktdaten {result_data}: {e}")
                    continue
            
            # Nach Relevanz sortieren
            sorted_products = self._sort_by_relevance(products, query)
            
            return sorted_products
            
        except Exception as e:
            logger.error(f"Fehler beim Verarbeiten der Lidl Billiger Montag Ergebnisse: {e}")
            return []
    
    def _matches_query(self, product_name: str, query: str) -> bool:
        """Prüft ob ein Produktname zum Suchbegriff passt"""
        if not product_name or not query:
            return False
            
        # Normalisiere beide Strings
        product_lower = product_name.lower()
        query_lower = query.lower()
        
        # Direkte Übereinstimmung
        if query_lower in product_lower:
            return True
            
        # Wort-basierte Suche
        query_words = query_lower.split()
        return all(word in product_lower for word in query_words if len(word) > 2)
    
    def _parse_price(self, price_str: str) -> Optional[Decimal]:
        """Parst deutsche Preisformate von Lidl zu Decimal"""
        if not price_str:
            return None
            
        try:
            # Entferne alle Nicht-Digit Zeichen außer Komma
            clean_price = re.sub(r'[^\d,]', '', price_str.strip())
            
            if not clean_price:
                return None
            
            # Deutsche Dezimalnotation: Komma als Dezimaltrennzeichen
            if ',' in clean_price:
                clean_price = clean_price.replace(',', '.')
            
            return Decimal(clean_price)
            
        except (InvalidOperation, ValueError) as e:
            logger.debug(f"Fehler beim Parsen des Preises '{price_str}': {e}")
            return None
    
    def _sort_by_relevance(self, products: List[ProductResult], query: str) -> List[ProductResult]:
        """Sortiert Produkte nach Relevanz zum Suchbegriff"""
        if not products or not query:
            return products
            
        def calculate_score(product: ProductResult) -> float:
            name_lower = product.name.lower()
            query_lower = query.lower()
            
            score = 0.0
            
            # Exakte Übereinstimmung
            if query_lower == name_lower:
                score += 100
            # Anfang des Namens
            elif name_lower.startswith(query_lower):
                score += 80
            # Enthält den kompletten Suchbegriff
            elif query_lower in name_lower:
                score += 60
            
            # Bonus für Wortübereinstimmungen
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2 and word in name_lower:
                    score += 20
            
            # Strafe für sehr lange Namen (meist weniger relevant)
            if len(product.name) > 50:
                score -= 5
                
            return score
        
        return sorted(products, key=calculate_score, reverse=True)
    
    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extrahiert Markenname aus Produktname (vereinfacht)"""
        if not name:
            return None
            
        # Häufige Lidl-Eigenmarken
        lidl_brands = [
            'Milbona', 'Duc de Coeur', 'Fairglobe', 'Freeway', 'Lupilu',
            'Piazza d\'Oro', 'Silvercrest', 'Ultimate Speed', 'Parkside',
            'Crofton', 'Tower Kitchen', 'Ernesto'
        ]
        
        name_lower = name.lower()
        for brand in lidl_brands:
            if brand.lower() in name_lower:
                return brand
                
        # Fallback: Erstes Wort als potentielle Marke
        words = name.split()
        if words and len(words[0]) > 2:
            return words[0]
            
        return None

def create_lidl_crawler() -> Optional[LidlCrawler]:
    """Factory-Funktion für Lidl-Crawler mit Firecrawl-Integration"""
    try:
        if not settings.lidl_crawler_enabled:
            logger.info("Lidl-Crawler ist in der Konfiguration deaktiviert")
            return None
            
        if not settings.firecrawl_enabled or not settings.firecrawl_api_key:
            logger.warning("Firecrawl ist nicht konfiguriert - Lidl-Crawler nicht verfügbar")
            return None
            
        # Firecrawl initialisieren
        from firecrawl import FirecrawlApp
        firecrawl_app = FirecrawlApp(api_key=settings.firecrawl_api_key)
        
        lidl_crawler = LidlCrawler(firecrawl_app=firecrawl_app)
        logger.info("Lidl-Crawler erfolgreich initialisiert")
        return lidl_crawler
        
    except ImportError as e:
        logger.error(f"Firecrawl-Bibliothek nicht verfügbar: {e}")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Lidl-Crawlers: {e}")
        return None 
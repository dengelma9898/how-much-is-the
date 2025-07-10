"""
Aldi-spezifischer Web-Crawler mit Firecrawl-Integration
Verwendet die direkte Aldi-Suchfunktion für effiziente Produktsuche
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

class AldiCrawler:
    """Aldi-spezifischer Crawler mit direkter Suchfunktion (Firecrawl v2.15.0)"""
    
    def __init__(self, firecrawl_app=None):
        self.firecrawl_app = firecrawl_app
        self.base_url = settings.aldi_base_url
        self.enabled = settings.aldi_crawler_enabled
        
        # Aldi-Such-URL für direkte Produktsuche
        self.search_url = f"{self.base_url}/de/suchergebnis.html"
        
    async def search_products(self, query: str, max_results: int = 15) -> List[ProductResult]:
        """Hauptmethode für Produktsuche bei Aldi über die offizielle Suchfunktion"""
        if not self.enabled or not self.firecrawl_app:
            logger.warning("Aldi-Crawler ist deaktiviert oder Firecrawl nicht verfügbar")
            return []
            
        if not query or len(query.strip()) < 2:
            logger.warning("Suchbegriff zu kurz für Aldi-Suche")
            return []
            
        try:
            logger.info(f"Starte Aldi-Produktsuche für Query: '{query}'")
            
            # URL-encode den Suchbegriff
            encoded_query = urllib.parse.quote_plus(query.strip())
            search_url = f"{self.search_url}?search={encoded_query}"
            
            logger.debug(f"Aldi-Such-URL: {search_url}")
            
            # Firecrawl v2.15.0 API-Aufruf mit direkten Parametern
            response = self.firecrawl_app.scrape_url(
                search_url,
                formats=["extract"],
                extract={
                    "schema": self._get_search_result_schema(),
                    "prompt": self._get_search_extraction_prompt(query),
                    "systemPrompt": "Du bist ein Experte für E-Commerce-Produktdaten. Extrahiere präzise Produktinformationen aus Aldi-Suchergebnissen. Achte besonders auf korrekte Preise und Einheiten."
                },
                maxAge=settings.firecrawl_max_age,  # Cache für Performance
                onlyMainContent=True  # Nur Hauptinhalt, keine Navigation
            )
            
            # Neue v2.15.0 Response-Struktur (ScrapeResponse-Objekt)
            if not response or not hasattr(response, 'extract') or not response.extract:
                logger.warning(f"Keine Suchergebnisse von Aldi für '{query}' erhalten")
                return []
                
            extracted_data = response.extract
            logger.debug(f"Aldi-Extraktion erfolgreich: {extracted_data}")
            
            # Produktdaten verarbeiten
            products = self._process_search_results(extracted_data, query)
            
            # Ergebnisse limitieren
            limited_products = products[:max_results]
            
            logger.info(f"Aldi-Suche für '{query}': {len(limited_products)} Produkte gefunden")
            return limited_products
            
        except Exception as e:
            logger.error(f"Fehler bei Aldi-Produktsuche für '{query}': {e}")
            return []
    
    def _get_search_result_schema(self) -> Dict[str, Any]:
        """JSON Schema für Aldi-Suchergebnis-Extraktion (vereinfacht für bessere Performance)"""
        return {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Vollständiger Produktname/Titel"
                            },
                            "price": {
                                "type": "string",
                                "description": "Hauptpreis in Euro (z.B. '€ 1,79', '€ 2,50')"
                            },
                            "unit": {
                                "type": "string", 
                                "description": "Verpackungseinheit und Grundpreis (z.B. 'je (1 L = € 1,35)')"
                            },
                            "availability": {
                                "type": "string",
                                "description": "Verfügbarkeitsstatus falls sichtbar"
                            }
                        },
                        "required": ["name", "price"]
                    }
                }
            },
            "required": ["products"]
        }
    
    def _get_search_extraction_prompt(self, query: str) -> str:
        """Generiert einen optimierten Extraction-Prompt für Aldi-Suchergebnisse"""
        return f"""
        Extrahiere alle Produktinformationen aus den Aldi-Suchergebnissen für "{query}".
        
        Wichtige Regeln:
        - Extrahiere jeden sichtbaren Produkteintrag in der Suchergebnisliste
        - Produktname: Vollständiger Titel wie angezeigt
        - Preis: Hauptpreis in Euro (€ 1,79, € 2,50, etc.)
        - Einheit: Verpackungsangabe und Grundpreis (z.B. "je (1 L = € 1,35)")
        - Verfügbarkeit: Status wie "Regional verfügbar" falls sichtbar
        - Ignoriere Werbebanner, Navigation und Seitenelemente
        - Jedes Produkt muss mindestens Namen und Preis haben
        
        Ziel: Vollständige Erfassung aller Produktlistings auf der Suchergebnisseite.
        """
    
    def _process_search_results(self, extracted_data: Dict[str, Any], query: str) -> List[ProductResult]:
        """Verarbeitet Aldi-Suchergebnisse zu ProductResult-Objekten"""
        products = []
        
        try:
            # Vereinfachte Struktur: direkt auf products zugreifen
            products_data = extracted_data.get('products', [])
            
            logger.debug(f"Verarbeite {len(products_data)} Aldi-Suchergebnisse")
            
            for result_data in products_data:
                try:
                    # Grunddaten validieren
                    name = result_data.get('name', '').strip()
                    price_str = result_data.get('price', '').strip()
                    
                    if not name or not price_str:
                        logger.debug(f"Überspringe Produkt ohne Namen oder Preis: {result_data}")
                        continue
                    
                    # Preis parsen
                    price = self._parse_price(price_str)
                    if not price:
                        logger.debug(f"Kann Preis nicht parsen: '{price_str}'")
                        continue
                    
                    # Unit-String verarbeiten (kann Grundpreis enthalten)
                    unit_str = result_data.get('unit', '').strip()
                    unit = None
                    if unit_str and unit_str != 'je':
                        unit = unit_str
                    
                    # ProductResult erstellen
                    product = ProductResult(
                        name=name,
                        price=price,
                        store="Aldi Süd",
                        unit=unit,
                        brand=self._extract_brand_from_name(name),
                        category=None,  # Meist nicht in Suchergebnissen verfügbar
                        discount=None,  # Vereinfacht für bessere Performance
                        
                        # Aldi-spezifische Felder
                        partner_program=False,  # Normale Aldi-Produkte benötigen keine Partner-App
                        available_until=None,  # Reguläre Produkte haben keine begrenzte Verfügbarkeit
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
            logger.error(f"Fehler beim Verarbeiten der Aldi-Suchergebnisse: {e}")
            return []
    
    def _parse_price(self, price_str: str) -> Optional[Decimal]:
        """Parst deutsche Preisformate von Aldi zu Decimal"""
        if not price_str:
            return None
            
        try:
            # Entferne €-Symbol und Leerzeichen
            cleaned = re.sub(r'[€\s*]', '', price_str)
            
            # Deutsche Zahlenformate: 1,79 oder 1.99
            if ',' in cleaned and '.' not in cleaned:
                # Format: 1,79
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned and '.' in cleaned:
                # Format: 1.234,56 -> 1234.56
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Letztes Komma ist Dezimaltrennzeichen
                    integer_part = parts[0].replace('.', '')
                    decimal_part = parts[1]
                    cleaned = f"{integer_part}.{decimal_part}"
            
            # Zu Decimal konvertieren
            price = Decimal(cleaned)
            
            # Validierung: Preis sollte zwischen 0.01 und 999.99 liegen
            if 0.01 <= price <= 999.99:
                return price
            else:
                logger.debug(f"Preis außerhalb des erwarteten Bereichs: {price}")
                return None
                
        except (InvalidOperation, ValueError, AttributeError) as e:
            logger.debug(f"Kann Preis nicht parsen: '{price_str}' - {e}")
            return None
    
    def _sort_by_relevance(self, products: List[ProductResult], query: str) -> List[ProductResult]:
        """Sortiert Produkte nach Relevanz zum Suchbegriff"""
        query_lower = query.lower()
        query_words = query_lower.split()
        
        def calculate_score(product: ProductResult) -> float:
            score = 0.0
            name_lower = product.name.lower()
            
            # Exakte Übereinstimmung (höchste Priorität)
            if query_lower in name_lower:
                score += 10.0
            
            # Wort-für-Wort Übereinstimmung
            for word in query_words:
                if word in name_lower:
                    score += 5.0
            
            # Marke berücksichtigen
            if product.brand and query_lower in product.brand.lower():
                score += 3.0
            
            # Kategorie berücksichtigen
            if product.category and query_lower in product.category.lower():
                score += 1.0
            
            return score
        
        # Sortiere nach Score (absteigend)
        scored_products = [(calculate_score(p), p) for p in products]
        scored_products.sort(key=lambda x: x[0], reverse=True)
        
        return [product for score, product in scored_products]

    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extrahiert Markennamen aus dem Produktnamen"""
        try:
            # Einfache Markenextraktion basierend auf häufigen Mustern
            name_upper = name.upper()
            
            # Bekannte Aldi-Marken
            aldi_brands = [
                'SCHWARZWALDMILCH', 'FAIR & GUT', 'BESTES AUS DER REGION',
                'BIO', 'NEVER OUT OF STOCK', 'SIMPLY', 'LACURA'
            ]
            
            for brand in aldi_brands:
                if brand in name_upper:
                    return brand.title()
            
            # Erste Wörter als potentielle Marke (bis zu 2 Wörter)
            words = name.split()[:2]
            if words and len(words[0]) > 2:
                return ' '.join(words)
                
            return None
            
        except Exception:
            return None


def create_aldi_crawler() -> Optional[AldiCrawler]:
    """Factory-Funktion zum Erstellen eines Aldi-Crawlers"""
    try:
        # Firecrawl importieren und initialisieren
        from firecrawl import FirecrawlApp
        
        if not settings.firecrawl_api_key:
            logger.warning("Kein Firecrawl API-Key konfiguriert - Aldi-Crawler deaktiviert")
            return None
            
        if not settings.firecrawl_enabled:
            logger.info("Firecrawl ist deaktiviert - Aldi-Crawler nicht verfügbar")
            return None
            
        # Firecrawl-App initialisieren
        firecrawl_app = FirecrawlApp(api_key=settings.firecrawl_api_key)
        
        # Aldi-Crawler erstellen
        crawler = AldiCrawler(firecrawl_app)
        logger.info("Aldi-Crawler erfolgreich initialisiert")
        return crawler
        
    except ImportError:
        logger.error("Firecrawl-Package nicht installiert - Aldi-Crawler nicht verfügbar")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Aldi-Crawlers: {e}")
        return None 
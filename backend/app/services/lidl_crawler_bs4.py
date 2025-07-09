"""
Lidl-Crawler mit BeautifulSoup + intelligenter LLM-basierter Dateninterpretation
Hybrid-Ansatz: Schnelles HTML-Parsing + KI-gestützte Produkterkennung
"""

import asyncio
import logging
import re
import json
import aiohttp
from bs4 import BeautifulSoup, Tag
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from app.models.search import ProductResult
from app.core.config import settings
from app.services.lidl_llm_interpreter import lidl_llm_interpreter
import openai

logger = logging.getLogger(__name__)

# Ollama Integration - kostenlose lokale LLM Alternative
import json
import re
import aiohttp
import logging
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag

from app.models.search import ProductResult
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class RawProductData:
    """Rohe Produktdaten vor der Interpretation"""
    html_element: str
    text_content: str
    price_candidates: List[str]
    name_candidates: List[str]
    context: str

class OllamaLLMClient:
    """Lokaler Ollama-Client als kostenlose OpenAI-Alternative"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        self.base_url = base_url
        self.model = model
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Chat completion mit Ollama API"""
        try:
            prompt = messages[-1]["content"] if messages else ""
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json" if "json" in prompt.lower() else ""
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama API Fehler: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ollama-Fehler: {e}")
            return None

class IntelligentLidlCrawler:
    """
    Lidl-Crawler mit intelligenter Datenextraktion
    
    Dual-Strategie:
    1. BeautifulSoup für schnelle HTML-Struktur-Extraktion  
    2. Lokales LLM (Ollama) für intelligente Dateninterpretation
    """
    
    def __init__(self, llm_client=None):
        self.base_url = settings.lidl_base_url
        self.billiger_montag_url = settings.lidl_billiger_montag_url
        self.enabled = settings.lidl_crawler_enabled
        
        # LLM Client (Ollama oder OpenAI)
        self.llm_client = llm_client or self._create_llm_client()
        
        # HTTP Session für bessere Performance
        self.session = None
        
        # Spezifische CSS-Selektoren für Lidl-Produktkarten
        self.product_selectors = [
            # Produktkarten-spezifische Selektoren
            'div[data-testid*="product"]',  # Product test IDs
            'div[class*="product-card"]',   # Produktkarten
            'div[class*="ProductCard"]',    # React-Style Produktkarten
            'div[class*="product-tile"]',   # Produkt-Kacheln
            'div[class*="offer-tile"]',     # Angebots-Kacheln
            'div[class*="grid-tile"]',      # Grid-Kacheln
            
            # Container mit Produktinformationen
            'div[class*="price-label"]',    # Preis-Labels
            'article[class*="product"]',    # Produkt-Articles
            'section[class*="product"]',    # Produkt-Sections
            
            # Lidl-spezifische Klassen (häufige Patterns)
            'div[class*="ACampaignProductCard"]',     # Lidl Campaign Cards
            'div[class*="ProductListItem"]',          # Produktlisten-Items
            'div[class*="WeeklyOfferCard"]',          # Wochenangebots-Karten
            'div[class*="OfferCard"]',                # Angebotskarten
            'div[class*="ProductOffer"]',             # Produktangebote
            
            # Fallback für generische Karten-Layouts
            '.card',                        # Generische Cards
            '.tile',                        # Kacheln
            'div[class*="item-"]',         # Item-Pattern
        ]
        
    def _create_llm_client(self):
        """Erstelle LLM Client - bevorzuge Ollama, Fallback zu OpenAI"""
        try:
            # 1. Versuche Ollama (kostenlos, lokal)
            ollama_client = OllamaLLMClient()
            return ollama_client
        except Exception:
            # 2. Fallback zu OpenAI falls verfügbar
            try:
                if settings.openai_api_key:
                    import openai
                    return openai.AsyncOpenAI(api_key=settings.openai_api_key)
            except Exception:
                pass
        return None
        
    async def __aenter__(self):
        """Async context manager für HTTP session"""
        # Einfachere Header um Header-Size-Probleme zu vermeiden
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PriceBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup"""
        if self.session:
            await self.session.close()
    
    async def search_products(self, query: str, max_results: int = 15) -> List[ProductResult]:
        """Hauptmethode für intelligente Lidl-Produktsuche"""
        if not self.enabled:
            logger.warning("Intelligent Lidl-Crawler ist deaktiviert")
            return []
            
        if not query or len(query.strip()) < 2:
            logger.warning("Suchbegriff zu kurz für Lidl-Suche")
            return []
            
        try:
            logger.info(f"🔍 Starte intelligente Lidl-Suche für: '{query}'")
            
            # 1. HTML-Inhalte crawlen
            raw_html = await self._fetch_page_content()
            if not raw_html:
                return []
            
            # 2. Rohe Produktdaten extrahieren
            raw_products = await self._extract_raw_products(raw_html)
            logger.info(f"📦 {len(raw_products)} rohe Produktelemente gefunden")
            
            # 3. Intelligente Interpretation der Rohdaten
            interpreted_products = await self._interpret_products_intelligently(raw_products)
            logger.info(f"🔧 {len(interpreted_products)} Produkte rule-based interpretiert")
            
            # 4. Nach Query filtern
            filtered_products = self._filter_by_query(interpreted_products, query)
            logger.info(f"🎯 {len(filtered_products)} Produkte passen zu '{query}'")
            
            # 5. Ergebnisse limitieren und sortieren
            final_products = self._finalize_results(filtered_products, query, max_results)
            
            logger.info(f"✅ Lidl-Suche abgeschlossen: {len(final_products)} Ergebnisse")
            return final_products
            
        except Exception as e:
            logger.error(f"❌ Fehler bei intelligenter Lidl-Suche: {e}", exc_info=True)
            return []
    
    async def _fetch_page_content(self) -> Optional[str]:
        """Fetcht HTML-Inhalt der Lidl-Seite"""
        try:
            logger.debug(f"📡 Lade Lidl-Seite: {self.billiger_montag_url}")
            
            # Einfachere URL für bessere Kompatibilität
            simple_url = "https://www.lidl.de/c/billiger-montag/a10006065"
            
            try:
                async with self.session.get(simple_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        logger.debug(f"✅ HTML geladen: {len(html_content)} Zeichen")
                        return html_content
                    else:
                        logger.error(f"❌ HTTP-Fehler: {response.status}")
                        return None
            except Exception as aio_error:
                logger.warning(f"⚠️ aiohttp-Fehler: {aio_error}, versuche requests...")
                # Fallback zu requests
                return await self._fetch_with_requests_fallback(simple_url)
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Seite: {e}")
            return None
    
    async def _fetch_with_requests_fallback(self, url: str) -> Optional[str]:
        """Fallback mit requests für problematische Seiten"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; PriceBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'de-DE,de;q=0.5'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                logger.debug(f"✅ Requests Fallback erfolgreich: {len(response.text)} Zeichen")
                return response.text
            else:
                logger.error(f"❌ Requests Fallback-Fehler: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Requests Fallback fehlgeschlagen: {e}")
            return None
    
    async def _extract_raw_products(self, html_content: str) -> List[RawProductData]:
        """Extrahiert rohe Produktdaten mit BeautifulSoup + JSON-Parsing"""
        raw_products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Erste Priorität: JSON-Datenstrukturen extrahieren
            json_products = self._extract_json_products(html_content, soup)
            raw_products.extend(json_products)
            logger.info(f"🔍 JSON-Extraktion: {len(json_products)} Produkte gefunden")
            
            # 2. Falls nicht genug Daten: HTML-Parsing als Fallback
            if len(raw_products) < 10:
                html_products = self._extract_html_products(soup)
                raw_products.extend(html_products)
                logger.info(f"🔍 HTML-Extraktion: {len(html_products)} zusätzliche Produkte")
            
            # Duplikate entfernen basierend auf Text-Content
            unique_products = self._deduplicate_products(raw_products)
            
            logger.info(f"📊 Rohdaten extrahiert: {len(unique_products)} einzigartige Produktelemente")
            return unique_products
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Produktextraktion: {e}")
            return []
    
    def _extract_json_products(self, html_content: str, soup: BeautifulSoup) -> List[RawProductData]:
        """Extrahiert Produktdaten aus eingebetteten JSON-Strukturen"""
        json_products = []
        
        try:
            # 1. Suche nach JSON-LD Scripts
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        products = self._parse_json_ld_data(data)
                        json_products.extend(products)
                    except json.JSONDecodeError:
                        continue
            
            # 2. Suche nach JavaScript-Variablen mit Produktdaten
            js_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__NUXT__\s*=\s*({.+?});',
                r'var\s+products\s*=\s*(\[.+?\]);',
                r'"products"\s*:\s*(\[.+?\])',
                r'"items"\s*:\s*(\[.+?\])'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # Bereinige JavaScript zu valides JSON
                        clean_json = self._clean_javascript_to_json(match)
                        if clean_json:
                            data = json.loads(clean_json)
                            products = self._parse_javascript_data(data)
                            json_products.extend(products)
                    except (json.JSONDecodeError, Exception):
                        continue
            
            # 3. Suche nach Produktnamen und Preisen in allen Script-Tags
            all_scripts = soup.find_all('script')
            for script in all_scripts:
                if script.string and 'product' in script.string.lower():
                    text_content = script.string
                    if any(keyword in text_content.lower() for keyword in ['milch', 'brot', 'käse', 'preis', '€']):
                        # Extrahiere Produktinformationen aus dem Script
                        products = self._extract_products_from_script_text(text_content)
                        json_products.extend(products)
            
            return json_products[:50]  # Limitiere für Performance
            
        except Exception as e:
            logger.error(f"❌ JSON-Extraktion fehlgeschlagen: {e}")
            return []
    
    def _parse_json_ld_data(self, data: Dict[str, Any]) -> List[RawProductData]:
        """Parst JSON-LD Strukturierte Daten"""
        products = []
        
        if isinstance(data, dict):
            # Product Schema
            if data.get('@type') == 'Product':
                product = self._create_raw_product_from_json(data)
                if product:
                    products.append(product)
            
            # ItemList Schema
            elif data.get('@type') == 'ItemList':
                items = data.get('itemListElement', [])
                for item in items:
                    if isinstance(item, dict):
                        product = self._create_raw_product_from_json(item)
                        if product:
                            products.append(product)
        
        return products
    
    def _parse_javascript_data(self, data: Any) -> List[RawProductData]:
        """Parst JavaScript-Datenstrukturen"""
        products = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    product = self._create_raw_product_from_json(item)
                    if product:
                        products.append(product)
        
        elif isinstance(data, dict):
            # Suche nach Produkt-Arrays in der Datenstruktur
            for key, value in data.items():
                if key.lower() in ['products', 'items', 'offers', 'data'] and isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            product = self._create_raw_product_from_json(item)
                            if product:
                                products.append(product)
        
        return products
    
    def _create_raw_product_from_json(self, item: Dict[str, Any]) -> Optional[RawProductData]:
        """Erstellt RawProductData aus JSON-Objekten"""
        try:
            # Extrahiere potentielle Namen
            name_candidates = []
            for name_field in ['name', 'title', 'productName', 'description', 'label']:
                if item.get(name_field):
                    name_candidates.append(str(item[name_field]))
            
            # Extrahiere potentielle Preise
            price_candidates = []
            for price_field in ['price', 'priceValue', 'amount', 'cost']:
                if item.get(price_field):
                    price_candidates.append(str(item[price_field]))
            
            # Prüfe offers-Struktur
            if item.get('offers'):
                offers = item['offers']
                if isinstance(offers, dict) and offers.get('price'):
                    price_candidates.append(str(offers['price']))
                elif isinstance(offers, list):
                    for offer in offers:
                        if isinstance(offer, dict) and offer.get('price'):
                            price_candidates.append(str(offer['price']))
            
            # Nur verwenden wenn wir sowohl Namen als auch Preise haben
            if name_candidates and price_candidates:
                text_content = f"JSON: {' | '.join(name_candidates)} - {' | '.join(price_candidates)}"
                
                return RawProductData(
                    html_element=json.dumps(item)[:500],
                    text_content=text_content,
                    price_candidates=price_candidates,
                    name_candidates=name_candidates,
                    context="JSON-Datenquelle"
                )
        
        except Exception as e:
            logger.debug(f"⚠️ JSON-Produkterstellung fehlgeschlagen: {e}")
        
        return None
    
    def _extract_products_from_script_text(self, script_text: str) -> List[RawProductData]:
        """Extrahiert Produktdaten aus Script-Text mit Regex"""
        products = []
        
        try:
            # Suche nach Produktnamen + Preisen in unmittelbarer Nähe
            product_patterns = [
                r'"([^"]*(?:milch|brot|käse|fleisch|wurst|apfel)[^"]*)"[^"]*"([-.0-9,]+)"',
                r'"name"\s*:\s*"([^"]+)"[^}]*"price"\s*:\s*"?([-.0-9,]+)"?',
                r'"([A-Za-zäöüß\s]+)"\s*[,:].*?"([-.0-9,]+)"'
            ]
            
            for pattern in product_patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                for name, price in matches:
                    if len(name) > 3 and any(c.isalpha() for c in name):
                        raw_product = RawProductData(
                            html_element=f"Script-Match: {name} - {price}",
                            text_content=f"Script: {name} - {price}",
                            price_candidates=[price],
                            name_candidates=[name],
                            context="Script-Text-Extraktion"
                        )
                        products.append(raw_product)
                        
                        if len(products) >= 20:  # Limitiere für Performance
                            break
        
        except Exception as e:
            logger.debug(f"⚠️ Script-Text-Extraktion fehlgeschlagen: {e}")
        
        return products
    
    def _clean_javascript_to_json(self, js_text: str) -> Optional[str]:
        """Bereinigt JavaScript-Code zu valides JSON"""
        try:
            # Einfache Bereinigungen
            cleaned = js_text.strip()
            
            # Entferne undefined, function calls, etc.
            cleaned = re.sub(r'\bundefined\b', 'null', cleaned)
            cleaned = re.sub(r'\bfunction\([^)]*\)\s*{[^}]*}', 'null', cleaned)
            cleaned = re.sub(r'new\s+Date\([^)]*\)', '""', cleaned)
            
            # Validiere dass es JSON-like aussieht
            if cleaned.startswith(('{', '[')) and cleaned.endswith(('}', ']')):
                return cleaned
        
        except Exception:
            pass
        
        return None
    
    def _extract_html_products(self, soup: BeautifulSoup) -> List[RawProductData]:
        """Fallback: HTML-basierte Produktextraktion"""
        html_products = []
        
        # Verwende die ursprüngliche HTML-Parsing-Logik
        for selector in self.product_selectors:
            if 'script' in selector:
                continue  # Skip script selectors hier
                
            elements = soup.select(selector)
            if elements:
                logger.debug(f"🎯 HTML-Selector '{selector}': {len(elements)} Elemente")
                
                for element in elements:
                    raw_product = self._parse_element_to_raw_data(element)
                    if raw_product:
                        html_products.append(raw_product)
                
                if len(html_products) > 20:
                    break
        
        return html_products
    
    def _deduplicate_products(self, products: List[RawProductData]) -> List[RawProductData]:
        """Entfernt Duplikate basierend auf Text-Content"""
        seen_content = set()
        unique_products = []
        
        for product in products:
            content_hash = hash(product.text_content.strip()[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_products.append(product)
        
        return unique_products
    
    def _parse_element_to_raw_data(self, element: Tag) -> Optional[RawProductData]:
        """Parsed ein HTML-Element zu rohen Produktdaten"""
        try:
            # Text-Content extrahieren
            text_content = element.get_text(separator=' ', strip=True)
            
            # Zu kurze oder leere Inhalte ignorieren
            if len(text_content.strip()) < 10:
                return None
            
            # HTML für Kontext behalten
            html_element = str(element)[:500]  # Limitiert für Performance
            
            # Preiskandidaten finden
            price_candidates = self._extract_price_candidates(text_content)
            
            # Namenskandidaten finden
            name_candidates = self._extract_name_candidates(text_content, element)
            
            # Kontext aus umgebenden Elementen
            context = self._extract_context(element)
            
            return RawProductData(
                html_element=html_element,
                text_content=text_content,
                price_candidates=price_candidates,
                name_candidates=name_candidates,
                context=context
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Fehler beim Parsen von Element: {e}")
            return None
    
    def _extract_price_candidates(self, text: str) -> List[str]:
        """Findet alle möglichen Preisangaben im Text - optimiert für Lidl-Formate"""
        price_patterns = [
            # Lidl-spezifische Formate (wie im Bild)
            r'€-\.\d{2}',                             # €-.55, €-.69 (Lidl-Format)
            r'-\.\d{2}',                              # -.55, -.69 (ohne €)
            r'€\d+\.\d{2}',                           # €1.79, €1.65 (mit Punkt)
            r'\d+\.\d{2}',                            # 1.79, 1.65 (nur Zahlen mit Punkt)
            
            # Standard-Formate
            r'\d+[,\.]\d{2}\s*€',                     # 1,99 €, 1.79 €
            r'€\s*\d+[,\.]\d{2}',                     # € 1,99, € 1.79
            r'\d+[,\.]\d{2}',                         # 1,99, 1.79 (standalone)
            
            # Weitere Lidl-Varianten
            r'-€\.\d{2}',                             # -€.55 (alternative Schreibweise)
            r'€\s*-\.\d{2}',                          # € -.55 (mit Leerzeichen)
        ]
        
        candidates = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            candidates.extend(matches)
        
        # Spezielle Bereinigung für Lidl-Preise
        cleaned_candidates = []
        for candidate in candidates:
            # Normalisiere €-.55 Format
            if candidate.startswith('€-'):
                cleaned_candidates.append(candidate)
            elif candidate.startswith('-'):
                cleaned_candidates.append('€' + candidate)
            else:
                cleaned_candidates.append(candidate)
        
        return list(set(cleaned_candidates))  # Duplikate entfernen
    
    def _extract_name_candidates(self, text: str, element: Tag) -> List[str]:
        """Findet mögliche Produktnamen"""
        candidates = []
        
        # Längere Textpassagen als Namenskandidaten
        words = text.split()
        for i in range(len(words)):
            for j in range(i + 2, min(i + 8, len(words) + 1)):
                candidate = ' '.join(words[i:j])
                if len(candidate) > 8 and len(candidate) < 100:
                    candidates.append(candidate)
        
        # HTML-Attribute als zusätzliche Quelle
        for attr in ['title', 'alt', 'data-name', 'aria-label']:
            if element.get(attr):
                candidates.append(element.get(attr))
        
        return candidates[:10]  # Limitiere für Performance
    
    def _extract_context(self, element: Tag) -> str:
        """Extrahiert Kontext aus umgebenden Elementen"""
        context_parts = []
        
        # Parent-Container
        parent = element.parent
        if parent:
            parent_text = parent.get_text(strip=True)[:200]
            context_parts.append(f"Parent: {parent_text}")
        
        # CSS-Klassen als Kontext
        classes = element.get('class', [])
        if classes:
            context_parts.append(f"Classes: {' '.join(classes)}")
        
        return ' | '.join(context_parts)
    
    def _find_product_container(self, element: Tag) -> Optional[Tag]:
        """Findet den Produkt-Container für ein Element"""
        current = element
        for _ in range(5):  # Max 5 Ebenen nach oben
            if current.parent:
                current = current.parent
                # Prüfe ob das ein Produkt-Container sein könnte
                classes = current.get('class', [])
                class_text = ' '.join(classes).lower()
                if any(keyword in class_text for keyword in ['product', 'offer', 'item', 'tile']):
                    return current
        return element  # Fallback
    
    async def _interpret_products_intelligently(self, raw_products: List[RawProductData]) -> List[ProductResult]:
        """Interpretiert rohe Produktdaten intelligent mit LLM-Unterstützung"""
        interpreted = []
        
        # Erst versuchen mit einfachen Regeln
        for raw_product in raw_products:
            simple_result = self._interpret_with_rules(raw_product)
            if simple_result:
                interpreted.append(simple_result)
        
        # Bei wenigen Ergebnissen: LLM-Interpretation für komplexere Fälle
        if len(interpreted) < 5:
            logger.info("🧠 Verwende LLM-Interpreter für komplexere Produktinterpretation...")
            
            # Bereite HTML-Kontext vor
            html_context = "\n".join([rp.html_element[:500] for rp in raw_products[:10]])
            raw_product_dicts = [
                {
                    "text": rp.text_content,
                    "price_candidates": rp.price_candidates,
                    "name_candidates": rp.name_candidates,
                    "context": rp.context
                }
                for rp in raw_products[:10]
            ]
            
            # Verwende den dedizierten LLM-Interpreter
            llm_result = await lidl_llm_interpreter.interpret_html_data(
                html_content=html_context,
                raw_products=raw_product_dicts,
                search_query="lidl_products"  # Allgemeine Suche für alle Produkte
            )
            
            if llm_result.products:
                interpreted.extend(llm_result.products)
                logger.info(f"🧠 LLM-Interpreter lieferte {len(llm_result.products)} zusätzliche Produkte")
        
        return interpreted
    
    def _interpret_with_rules(self, raw_product: RawProductData) -> Optional[ProductResult]:
        """Einfache regelbasierte Interpretation"""
        try:
            # Preis finden und parsen
            price = None
            for price_candidate in raw_product.price_candidates:
                parsed_price = self._parse_price_string(price_candidate)
                if parsed_price and parsed_price > 0:
                    price = parsed_price
                    break
            
            if not price:
                return None
            
            # Namen finden (längster sinnvoller Kandidat)
            name = None
            for name_candidate in raw_product.name_candidates:
                clean_name = self._clean_product_name(name_candidate)
                if clean_name and len(clean_name) > 5:
                    name = clean_name
                    break
            
            if not name:
                # Fallback: Ersten Teil des Texts verwenden
                text_words = raw_product.text_content.split()[:5]
                name = ' '.join(text_words)
                name = self._clean_product_name(name)
            
            if not name or len(name) < 3:
                return None
            
            # ProductResult erstellen
            return ProductResult(
                name=name,
                price=price,
                store="Lidl",
                partner_program=True,
                available_until="Billiger Montag",
                unit=self._extract_unit_from_text(raw_product.text_content),
                brand=self._extract_brand_from_name(name),
                category="Billiger Montag Angebot"
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Regel-Interpretation fehlgeschlagen: {e}")
            return None
    
    async def _interpret_with_llm(self, raw_products: List[RawProductData]) -> List[ProductResult]:
        """LLM-basierte Interpretation für komplexe Fälle"""
        if not self.llm_client: # Changed from self.openai_client to self.llm_client
            return []
        
        try:
            # Bereite Daten für LLM vor
            products_data = []
            for i, raw_product in enumerate(raw_products[:10]):  # Limitiere für API-Kosten
                products_data.append({
                    'id': i,
                    'text': raw_product.text_content[:300],
                    'price_candidates': raw_product.price_candidates,
                    'name_candidates': raw_product.name_candidates[:5]
                })
            
            # LLM-Prompt
            prompt = f"""
Du bist ein Experte für E-Commerce-Produktdaten. Analysiere diese HTML-Inhalte von der Lidl "Billiger Montag" Seite und extrahiere strukturierte Produktinformationen.

Produktdaten:
{json.dumps(products_data, indent=2, ensure_ascii=False)}

Für jedes Produkt extrahiere:
- name: Hauptproduktname (bereinigt, ohne Preise)
- price: Preis als Dezimalzahl (z.B. 1.99, nicht "1,99 €")
- unit: Einheit falls erkennbar (z.B. "kg", "Stück", "500g")
- category: Produktkategorie falls erkennbar

Antworte nur mit validen JSON:
{{"products": [{{"id": 0, "name": "...", "price": 1.99, "unit": "...", "category": "..."}}, ...]}}

Ignoriere Elemente ohne klaren Produktcharakter oder Preis.
"""

            # API-Call
            response = await self.llm_client.chat_completion(messages=[{"role": "user", "content": prompt}]) # Changed from _call_openai_async to llm_client.chat_completion
            if not response:
                return []
            
            # Response parsen
            llm_products = self._parse_llm_response(response)
            
            # Zu ProductResult konvertieren
            results = []
            for llm_product in llm_products:
                try:
                    result = ProductResult(
                        name=llm_product.get('name', ''),
                        price=Decimal(str(llm_product.get('price', 0))),
                        store="Lidl",
                        partner_program=True,
                        available_until="Billiger Montag",
                        unit=llm_product.get('unit'),
                        category=llm_product.get('category'),
                        brand=self._extract_brand_from_name(llm_product.get('name', ''))
                    )
                    results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ LLM-Ergebnis konnte nicht konvertiert werden: {e}")
                    continue
            
            logger.info(f"🧠 LLM interpretierte {len(results)} Produkte")
            return results
            
        except Exception as e:
            logger.error(f"❌ LLM-Interpretation fehlgeschlagen: {e}")
            return []
    
    # Removed _call_openai_async as it's now handled by llm_client.chat_completion
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parst LLM-Response zu Produktliste"""
        try:
            # JSON extrahieren
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data.get('products', [])
            return []
        except Exception as e:
            logger.debug(f"⚠️ LLM-Response konnte nicht geparst werden: {e}")
            return []
    
    def _parse_price_string(self, price_str: str) -> Optional[Decimal]:
        """Parst Preis-String zu Decimal - optimiert für Lidl-Formate"""
        try:
            # Bereinige Preis-String von Symbolen
            clean_price = re.sub(r'[€\s]', '', price_str)  # Entferne € und Leerzeichen
            clean_price = clean_price.replace(',', '.')    # Normalisiere Dezimaltrennzeichen
            
            # Handle Lidl-spezifische Formate
            if clean_price.startswith('-.'):
                # -.55 → 0.55
                clean_price = '0' + clean_price[1:]
            elif clean_price.startswith('-'):
                # -55 → 55 (falls ohne Punkt)
                clean_price = clean_price[1:]
            
            # Validiere dass es eine gültige Dezimalzahl ist
            if re.match(r'^\d+\.?\d*$', clean_price):
                return Decimal(clean_price)
            else:
                logger.debug(f"⚠️ Ungültiges Preisformat: '{price_str}' → '{clean_price}'")
                return None
            
        except (InvalidOperation, ValueError) as e:
            logger.debug(f"⚠️ Preis-Parsing fehlgeschlagen für '{price_str}': {e}")
            return None
    
    def _clean_product_name(self, name: str) -> str:
        """Bereinigt Produktnamen"""
        if not name:
            return ""
        
        # Entferne Preisangaben und Sonderzeichen
        clean = re.sub(r'[€$£]?\s*\d+[,\.]\d{2}', '', name)
        clean = re.sub(r'[€$£]', '', clean)
        clean = re.sub(r'[-]{2,}', '', clean)
        clean = ' '.join(clean.split())  # Normalisiere Whitespace
        
        return clean.strip()[:100]  # Limitiere Länge
    
    def _extract_unit_from_text(self, text: str) -> Optional[str]:
        """Extrahiert Einheit aus Text"""
        unit_patterns = [
            r'\d+\s*(kg|g|l|ml|stück|bund|pack)',
            r'(je|per|pro)\s+(kg|g|l|ml|stück|bund)',
            r'(\d+\s*-?\s*(g|kg|ml|l)-preis)'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group()
        
        return None
    
    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extrahiert Marke aus Produktname"""
        lidl_brands = ['Lidl', 'Dulano', 'Milbona', 'Combino', 'Vitakrone', 'Freshona']
        
        for brand in lidl_brands:
            if brand.lower() in name.lower():
                return brand
        
        # Erstes Wort als potentielle Marke
        words = name.split()
        if words and len(words[0]) > 2:
            return words[0]
        
        return None
    
    def _filter_by_query(self, products: List[ProductResult], query: str) -> List[ProductResult]:
        """Filtert Produkte nach Suchbegriff"""
        filtered = []
        query_lower = query.lower()
        
        for product in products:
            name_lower = product.name.lower()
            if query_lower in name_lower:
                filtered.append(product)
        
        return filtered
    
    def _finalize_results(self, products: List[ProductResult], query: str, max_results: int) -> List[ProductResult]:
        """Finalisiert und sortiert Ergebnisse"""
        # Sortiere nach Relevanz (einfacher String-Match-Score)
        def relevance_score(product: ProductResult) -> float:
            name = product.name.lower()
            query_lower = query.lower()
            
            if name.startswith(query_lower):
                return 3.0
            elif query_lower in name:
                return 2.0
            else:
                return 1.0
        
        sorted_products = sorted(products, key=relevance_score, reverse=True)
        return sorted_products[:max_results]


def create_intelligent_lidl_crawler() -> Optional[IntelligentLidlCrawler]:
    """Factory-Funktion für intelligenten Lidl-Crawler"""
    try:
        # LLM-Client erstellen - bevorzuge Ollama, fallback zu OpenAI
        llm_client = None
        
        # Versuche Ollama zuerst
        try:
            llm_client = OllamaLLMClient()
            logger.info("🦙 Ollama-LLM-Client wird verwendet")
        except Exception as e:
            logger.warning(f"⚠️ Ollama nicht verfügbar: {e}")
            
            # Fallback zu OpenAI falls verfügbar
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                import openai
                llm_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("🤖 OpenAI-LLM-Client wird verwendet")
        
        crawler = IntelligentLidlCrawler(llm_client=llm_client)
        logger.info("✅ Intelligenter Lidl-Crawler erfolgreich initialisiert")
        return crawler
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des intelligenten Lidl-Crawlers: {e}")
        return None 
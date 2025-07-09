"""
Verbesserter Lidl-Crawler mit Ollama-Integration
Verwendet BeautifulSoup + lokales LLM (Ollama) als kostenlose OpenAI-Alternative
"""

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

class ImprovedLidlCrawler:
    """
    Verbesserter Lidl-Crawler mit lokaler LLM-Integration
    
    Strategie:
    1. Verbesserte HTML-Selektoren für echte Produktelemente
    2. Rule-based Interpretation als Hauptstrategie
    3. Ollama (lokal) als kostenlose LLM-Alternative zu OpenAI
    """
    
    def __init__(self, llm_client=None):
        self.base_url = settings.lidl_base_url
        self.billiger_montag_url = settings.lidl_billiger_montag_url
        self.enabled = settings.lidl_crawler_enabled
        
        # LLM Client (Ollama bevorzugt)
        self.llm_client = llm_client or self._create_llm_client()
        
        # HTTP Session
        self.session = None
        
    def _create_llm_client(self):
        """Erstelle LLM Client - bevorzuge Ollama (kostenlos)"""
        try:
            # 1. Versuche Ollama (kostenlos, lokal)
            return OllamaLLMClient()
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
        """Context manager setup"""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PriceBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'de-DE,de;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup"""
        if self.session:
            await self.session.close()
    
    async def search_products(self, query: str, max_results: int = 15) -> List[ProductResult]:
        """Hauptmethode für Lidl-Produktsuche"""
        if not self.enabled:
            logger.warning("Lidl-Crawler ist deaktiviert")
            return []
            
        if not query or len(query.strip()) < 2:
            logger.warning("Suchbegriff zu kurz")
            return []
            
        try:
            logger.info(f"🔍 Starte verbesserte Lidl-Suche für: '{query}'")
            
            # 1. HTML laden
            html_content = await self._fetch_page_content()
            if not html_content:
                return []
            
            # 2. Verbesserte Produktextraktion
            raw_products = await self._extract_products_with_price_focus(html_content)
            logger.info(f"📦 {len(raw_products)} Produktkandidaten gefunden")
            
            # 3. Rule-based Interpretation (Hauptstrategie)
            interpreted_products = self._interpret_products_rule_based(raw_products)
            logger.info(f"🔧 {len(interpreted_products)} Produkte interpretiert")
            
            # 4. Nach Query filtern
            filtered_products = self._filter_by_query(interpreted_products, query)
            logger.info(f"🎯 {len(filtered_products)} passende Produkte")
            
            # 5. Ergebnisse finalisieren
            final_products = self._finalize_results(filtered_products, query, max_results)
            
            logger.info(f"✅ Lidl-Suche erfolgreich: {len(final_products)} Ergebnisse")
            return final_products
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Lidl-Suche: {e}", exc_info=True)
            return []

    async def _fetch_page_content(self) -> Optional[str]:
        """Lade HTML-Inhalt der Lidl-Seite"""
        try:
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
                return await self._fetch_with_requests_fallback(simple_url)
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}")
            return None

    async def _fetch_with_requests_fallback(self, url: str) -> Optional[str]:
        """Requests Fallback"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; PriceBot/1.0)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'de-DE,de;q=0.9'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                logger.debug(f"✅ Requests Fallback erfolgreich")
                return response.text
            else:
                logger.error(f"❌ Requests Fallback-Fehler: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Requests Fallback fehlgeschlagen: {e}")
            return None

    async def _extract_products_with_price_focus(self, html_content: str) -> List[RawProductData]:
        """Verbesserte Extraktion mit Fokus auf Preis-Elemente"""
        raw_products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Finde alle Elemente mit Preismustern
            price_elements = self._find_price_elements(soup)
            logger.info(f"🔍 {len(price_elements)} Preis-Elemente gefunden")
            
            # 2. Extrahiere Produktdaten für jedes Preis-Element
            for element in price_elements:
                product_data = self._extract_product_data(element)
                if product_data and self._is_valid_product_data(product_data):
                    raw_products.append(product_data)
            
            # Duplikate entfernen
            unique_products = self._deduplicate_products(raw_products)
            return unique_products[:30]  # Limitiere für Performance
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Produktextraktion: {e}")
            return []

    def _find_price_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """Finde alle Elemente die Preise enthalten"""
        price_elements = []
        
        # Verbesserte Preis-Patterns (excludiert CSS-Dimensionen)
        price_patterns = [
            r'\d+[,\.]\d{2}\s*€',  # 1,99 €
            r'€\s*\d+[,\.]\d{2}',  # € 1,99
            r'-\.\d{2}(?!\w)',     # -.49 (aber nicht -.49rem)
            r'\d+[,\.]\d{2}[*]',   # 1,99* (mit Stern)
            r'(?<!\w)\d+[,\.]\d{2}(?!\w|rem|px|em)',  # 1,99 (aber nicht CSS)
        ]
        
        # Suche in allen Text-Knoten (excludiert CSS/Script)
        for text_node in soup.find_all(string=True):
            if text_node.parent:
                parent_tag = text_node.parent.name.lower()
                
                # Ignoriere Style, Script und Meta-Tags
                if parent_tag in ['style', 'script', 'meta', 'link', 'noscript']:
                    continue
                
                text = text_node.strip()
                if text and len(text) > 2:
                    # Ignoriere CSS-ähnlichen Text
                    if self._looks_like_css(text):
                        continue
                        
                    for pattern in price_patterns:
                        if re.search(pattern, text):
                            price_elements.append(text_node.parent)
                            break
        
        # Entferne Duplikate und filtere ungültige
        unique_elements = []
        seen_texts = set()
        
        for elem in price_elements:
            if elem and hasattr(elem, 'get_text'):
                text = elem.get_text(strip=True)[:200]
                text_key = text.lower()
                
                if (text_key not in seen_texts and 
                    not self._is_invalid_element(elem)):
                    seen_texts.add(text_key)
                    unique_elements.append(elem)
        
        return unique_elements[:50]  # Limitiere

    def _looks_like_css(self, text: str) -> bool:
        """Prüfe ob Text CSS-Code ist"""
        text_lower = text.lower()
        
        # CSS-Indikatoren
        css_indicators = [
            'rem', 'px', 'em', 'vh', 'vw', '%',
            'margin:', 'padding:', 'width:', 'height:', 'border:',
            'background:', 'color:', 'font-', 'calc(', 'rgba(',
            '{', '}', ';', 'data-v-', '@media', '.class'
        ]
        
        css_count = sum(1 for indicator in css_indicators if indicator in text_lower)
        
        # Wenn mehr als 2 CSS-Indikatoren → wahrscheinlich CSS
        return css_count >= 2

    def _is_invalid_element(self, element: Tag) -> bool:
        """Prüfe ob Element ungültig ist (Navigation, etc.)"""
        if not element or not hasattr(element, 'get_text'):
            return True
            
        text = element.get_text(strip=True).lower()
        
        # Filtere bekannte UI/Navigation-Elemente
        invalid_keywords = [
            'tabulator', 'steuerung', 'onlineshop', 'menü', 'menu',
            'navigation', 'header', 'footer', 'browser', 'javascript',
            'helfer gegen hitze', 'weekaction', 'campaign', 'stage',
            'diese woche', 'nächste woche', 'lohnt sich'
        ]
        
        for keyword in invalid_keywords:
            if keyword in text:
                return True
        
        # Prüfe auf Mindestlänge
        if len(text) < 5:
            return True
            
        return False

    def _extract_product_data(self, element: Tag) -> Optional[RawProductData]:
        """Extrahiere Produktdaten aus einem Element"""
        try:
            # Versuche das übergeordnete Produkt-Container zu finden
            container = self._find_product_container(element)
            if not container:
                container = element
            
            # Text extrahieren
            text_content = container.get_text(separator=' ', strip=True)
            
            if len(text_content) < 10:
                return None
            
            # Preise extrahieren
            price_candidates = self._extract_price_candidates(text_content)
            
            # Namen extrahieren
            name_candidates = self._extract_name_candidates(text_content)
            
            return RawProductData(
                html_element=str(container)[:500],
                text_content=text_content[:800],
                price_candidates=price_candidates,
                name_candidates=name_candidates,
                context=""
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Fehler bei Datenextraktion: {e}")
            return None

    def _find_product_container(self, element: Tag) -> Optional[Tag]:
        """Finde übergeordnetes Produkt-Container"""
        current = element
        max_depth = 5
        depth = 0
        
        while current and current.parent and depth < max_depth:
            parent = current.parent
            
            # Prüfe ob Parent ein Produkt-Container sein könnte
            if hasattr(parent, 'get'):
                class_str = str(parent.get('class', []))
                id_str = str(parent.get('id', ''))
                
                if any(keyword in class_str.lower() for keyword in ['product', 'item', 'offer', 'card']):
                    return parent
                if any(keyword in id_str.lower() for keyword in ['product', 'item', 'offer']):
                    return parent
            
            current = parent
            depth += 1
        
        return element

    def _extract_price_candidates(self, text: str) -> List[str]:
        """Extrahiere Preis-Kandidaten aus Text"""
        patterns = [
            r'\d+[,\.]\d{2}(?:\s*€)?',  # 1,99 oder 1,99 €
            r'-\.\d{2}',                # -.49
            r'€\s*\d+[,\.]\d{2}',       # € 1,99
        ]
        
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            candidates.extend(matches)
        
        # Bereinige und dedupliziere
        clean_candidates = []
        for candidate in candidates:
            clean = re.sub(r'[€\s]', '', candidate).strip()
            if clean and clean not in clean_candidates:
                clean_candidates.append(clean)
        
        return clean_candidates[:5]

    def _extract_name_candidates(self, text: str) -> List[str]:
        """Extrahiere Name-Kandidaten aus Text"""
        # Entferne Preise und bereinige
        clean_text = re.sub(r'\d+[,\.]\d{2}\s*€?', '', text)
        clean_text = re.sub(r'€\s*\d+[,\.]\d{2}', '', clean_text)
        clean_text = re.sub(r'-\.\d{2}', '', clean_text)
        
        # Teile in Wörter und bilde Kandidaten
        words = clean_text.split()
        candidates = []
        
        # Verschiedene Kombinationen
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                candidate = ' '.join(words[i:j])
                candidate = candidate.strip()
                if len(candidate) >= 3 and len(candidate) <= 50:
                    candidates.append(candidate)
        
        return candidates[:10]

    def _is_valid_product_data(self, product_data: RawProductData) -> bool:
        """Prüfe ob Produktdaten gültig sind"""
        if not product_data.price_candidates:
            return False
        
        if not product_data.name_candidates:
            return False
        
        # Prüfe auf gültige Preise
        for price_str in product_data.price_candidates:
            try:
                clean_price = re.sub(r'[^\d,.]', '', price_str)
                clean_price = clean_price.replace(',', '.')
                price = float(clean_price)
                if 0.10 <= price <= 100.00:  # Sinnvoller Preisbereich
                    return True
            except:
                continue
        
        return False

    def _deduplicate_products(self, products: List[RawProductData]) -> List[RawProductData]:
        """Entferne Duplikate"""
        unique_products = []
        seen_texts = set()
        
        for product in products:
            # Verwende ersten 100 Zeichen als Schlüssel
            key = product.text_content[:100].lower().strip()
            if key not in seen_texts:
                seen_texts.add(key)
                unique_products.append(product)
        
        return unique_products

    def _interpret_products_rule_based(self, raw_products: List[RawProductData]) -> List[ProductResult]:
        """Rule-based Interpretation ohne LLM"""
        interpreted_products = []
        
        for raw_product in raw_products:
            result = self._interpret_single_product(raw_product)
            if result:
                interpreted_products.append(result)
        
        return interpreted_products

    def _interpret_single_product(self, raw_product: RawProductData) -> Optional[ProductResult]:
        """Interpretiere ein einzelnes Produkt mit Regeln"""
        try:
            # Finde besten Preis
            price = self._find_best_price(raw_product.price_candidates)
            if not price:
                return None
            
            # Finde besten Namen
            name = self._find_best_name(raw_product.name_candidates)
            if not name or len(name) < 3:
                return None
            
            # Bereinige Namen
            clean_name = self._clean_product_name(name)
            if len(clean_name) < 3:
                return None
            
            return ProductResult(
                name=clean_name,
                price=price,
                store="Lidl",
                partner_program=True,
                available_until="Billiger Montag",
                unit=self._extract_unit(raw_product.text_content),
                brand=self._extract_brand(clean_name),
                category="Billiger Montag"
            )
            
        except Exception as e:
            logger.debug(f"⚠️ Interpretation fehlgeschlagen: {e}")
            return None

    def _find_best_price(self, price_candidates: List[str]) -> Optional[Decimal]:
        """Finde den besten Preis aus Kandidaten"""
        valid_prices = []
        
        for candidate in price_candidates:
            try:
                clean_price = re.sub(r'[^\d,.]', '', candidate)
                clean_price = clean_price.replace(',', '.')
                
                # Handle -.49 Format
                if clean_price.startswith('.'):
                    clean_price = '0' + clean_price
                
                price = Decimal(clean_price)
                if 0.10 <= price <= 100.00:
                    valid_prices.append(price)
            except:
                continue
        
        if valid_prices:
            return min(valid_prices)  # Nimm den niedrigsten Preis
        return None

    def _find_best_name(self, name_candidates: List[str]) -> Optional[str]:
        """Finde den besten Namen aus Kandidaten"""
        if not name_candidates:
            return None
        
        # Bevorzuge mittlere Längen (5-30 Zeichen)
        scored_names = []
        for name in name_candidates:
            clean = name.strip()
            if 5 <= len(clean) <= 30:
                score = len(clean)  # Bevorzuge längere Namen (mehr Info)
                scored_names.append((score, clean))
        
        if scored_names:
            scored_names.sort(key=lambda x: x[0], reverse=True)
            return scored_names[0][1]
        
        # Fallback: Erster Kandidat
        return name_candidates[0] if name_candidates else None

    def _clean_product_name(self, name: str) -> str:
        """Bereinige Produktname"""
        if not name:
            return ""
        
        # Entferne Preise und Sonderzeichen
        clean = re.sub(r'[€$]\s*\d+[,\.]\d{2}', '', name)
        clean = re.sub(r'\d+[,\.]\d{2}\s*€', '', clean)
        clean = re.sub(r'[-]{2,}', ' ', clean)
        clean = re.sub(r'[^\w\s\-,.]', ' ', clean)
        
        # Normalisiere Whitespace
        clean = ' '.join(clean.split())
        
        return clean.strip()[:80]

    def _extract_unit(self, text: str) -> Optional[str]:
        """Extrahiere Einheit aus Text"""
        unit_patterns = [
            r'\d+\s*(kg|g|l|ml|stück|pack|bund)',
            r'(je|per|pro)\s+(kg|g|l|ml|stück)',
            r'(\d+\s*-?\s*(g|kg|ml|l))'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group().strip()
        
        return None

    def _extract_brand(self, name: str) -> Optional[str]:
        """Extrahiere Marke aus Name"""
        lidl_brands = ['Lidl', 'Dulano', 'Milbona', 'Combino', 'Vitakrone', 'Freshona']
        
        name_lower = name.lower()
        for brand in lidl_brands:
            if brand.lower() in name_lower:
                return brand
        
        # Fallback: Erstes Wort
        words = name.split()
        if words and len(words[0]) > 2:
            return words[0]
        
        return None

    def _filter_by_query(self, products: List[ProductResult], query: str) -> List[ProductResult]:
        """Filtere Produkte nach Suchbegriff"""
        if not query:
            return products
        
        query_lower = query.lower()
        query_words = query_lower.split()
        
        filtered = []
        for product in products:
            name_lower = product.name.lower()
            
            # Direkte Übereinstimmung
            if query_lower in name_lower:
                filtered.append(product)
                continue
            
            # Wort-basierte Suche
            if all(word in name_lower for word in query_words if len(word) > 2):
                filtered.append(product)
        
        return filtered

    def _finalize_results(self, products: List[ProductResult], query: str, max_results: int) -> List[ProductResult]:
        """Finalisiere Ergebnisse"""
        if not products:
            return []
        
        # Sortiere nach Relevanz
        def relevance_score(product: ProductResult) -> float:
            name_lower = product.name.lower()
            query_lower = query.lower()
            
            score = 0.0
            if query_lower == name_lower:
                score += 100
            elif name_lower.startswith(query_lower):
                score += 80
            elif query_lower in name_lower:
                score += 60
            
            # Bonus für Wortübereinstimmungen
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2 and word in name_lower:
                    score += 20
            
            return score
        
        products.sort(key=relevance_score, reverse=True)
        return products[:max_results]


def create_improved_lidl_crawler() -> Optional[ImprovedLidlCrawler]:
    """Factory-Funktion für verbesserten Lidl-Crawler"""
    try:
        if not settings.lidl_crawler_enabled:
            logger.info("Lidl-Crawler ist deaktiviert")
            return None
        
        crawler = ImprovedLidlCrawler()
        logger.info("✅ Verbesserter Lidl-Crawler erfolgreich initialisiert")
        return crawler
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Initialisieren des verbesserten Lidl-Crawlers: {e}")
        return None 
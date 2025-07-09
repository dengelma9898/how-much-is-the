"""
LLM-basierter Interpreter für Lidl-Produktdaten
Verwendet OpenAI GPT für intelligente Datenextraktion
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from dataclasses import dataclass
import asyncio
import aiohttp
from app.models.search import ProductResult
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class LLMExtractionResult:
    """Ergebnis der LLM-Extraktion"""
    products: List[ProductResult]
    confidence: float
    extraction_method: str
    raw_interpretation: Optional[str] = None

class LidlLLMInterpreter:
    """LLM-basierter Interpreter für Lidl-Produktdaten"""
    
    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    async def interpret_html_data(self, 
                                 html_content: str, 
                                 raw_products: List[Dict],
                                 search_query: str) -> LLMExtractionResult:
        """
        Interpretiert HTML-Inhalte mit LLM-Unterstützung
        """
        try:
            # Bereite Eingabedaten für LLM vor
            context_data = self._prepare_context_data(html_content, raw_products, search_query)
            
            # Erstelle LLM-Prompt
            prompt = self._create_interpretation_prompt(context_data, search_query)
            
            # Führe LLM-Anfrage aus
            llm_response = await self._call_openai_api(prompt)
            
            # Parse LLM-Antwort
            products = self._parse_llm_response(llm_response)
            
            return LLMExtractionResult(
                products=products,
                confidence=0.8,  # Hochvertrauen für LLM-basierte Extraktion
                extraction_method="llm_interpretation",
                raw_interpretation=llm_response
            )
            
        except Exception as e:
            logger.error(f"LLM-Interpretation fehlgeschlagen: {e}")
            return LLMExtractionResult(
                products=[],
                confidence=0.0,
                extraction_method="llm_failed"
            )
    
    def _prepare_context_data(self, 
                             html_content: str, 
                             raw_products: List[Dict],
                             search_query: str) -> Dict[str, Any]:
        """Bereitet Kontextdaten für LLM vor"""
        
        # Extrahiere relevante HTML-Abschnitte
        relevant_snippets = self._extract_relevant_html_snippets(html_content, search_query)
        
        # Sammle JSON-ähnliche Datenstrukturen
        json_structures = self._extract_json_structures(html_content)
        
        # Sammle Preis-Patterns
        price_patterns = self._extract_price_patterns(html_content)
        
        return {
            "search_query": search_query,
            "html_snippets": relevant_snippets[:5],  # Top 5 relevante Schnipsel
            "raw_products": raw_products[:10],  # Top 10 raw products
            "json_structures": json_structures[:3],  # Top 3 JSON-Strukturen
            "price_patterns": price_patterns[:20],  # Top 20 Preismuster
            "total_html_length": len(html_content)
        }
    
    def _extract_relevant_html_snippets(self, html_content: str, search_query: str) -> List[str]:
        """Extrahiert relevante HTML-Abschnitte basierend auf Suchbegriff"""
        snippets = []
        
        # Suche nach Abschnitten die den Suchbegriff enthalten
        pattern = re.compile(f'.{{0,200}}{re.escape(search_query.lower())}.{{0,200}}', re.IGNORECASE)
        matches = pattern.findall(html_content.lower())
        
        for match in matches[:10]:
            # Bereinige HTML-Tags für bessere Lesbarkeit
            clean_match = re.sub(r'<[^>]+>', ' ', match)
            clean_match = re.sub(r'\s+', ' ', clean_match).strip()
            if len(clean_match) > 20:
                snippets.append(clean_match)
        
        return snippets
    
    def _extract_json_structures(self, html_content: str) -> List[Dict]:
        """Extrahiert JSON-ähnliche Strukturen aus HTML"""
        json_structures = []
        
        # Suche nach JSON in <script>-Tags
        script_pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL)
        script_matches = script_pattern.findall(html_content)
        
        for script_content in script_matches:
            # Suche nach JSON-ähnlichen Strukturen
            json_pattern = re.compile(r'\{[^{}]*"[^"]*"[^{}]*\}')
            json_matches = json_pattern.findall(script_content)
            
            for json_match in json_matches:
                try:
                    parsed = json.loads(json_match)
                    if isinstance(parsed, dict) and len(parsed) > 1:
                        json_structures.append(parsed)
                except:
                    continue
        
        return json_structures[:5]
    
    def _extract_price_patterns(self, html_content: str) -> List[str]:
        """Extrahiert Preismuster aus HTML"""
        # Lidl-spezifische Preismuster
        price_patterns = [
            r'[-.]?\d+[,.]?\d*\s*€',  # Standard-Preise
            r'€\s*\d+[,.]?\d*',       # Euro-Symbol vor Preis
            r'\d+[,.]?\d*\s*EUR',     # EUR-Suffix
            r'[-.]?\d+[,.]?\d*',      # Nur Zahlen (Lidl-Style)
        ]
        
        found_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, html_content)
            found_prices.extend(matches[:10])
        
        return found_prices
    
    def _create_interpretation_prompt(self, context_data: Dict[str, Any], search_query: str) -> str:
        """Erstellt den LLM-Interpretations-Prompt"""
        
        return f"""Du bist ein Experte für die Extraktion von Produktdaten aus Lidl-Webseiten.

AUFGABE: Extrahiere Produktinformationen für die Suchanfrage "{search_query}" aus den bereitgestellten Daten.

KONTEXT:
- Suchbegriff: {search_query}
- HTML-Länge: {context_data['total_html_length']} Zeichen
- Gefundene Raw Products: {len(context_data['raw_products'])}
- JSON-Strukturen: {len(context_data['json_structures'])}

RELEVANTE HTML-ABSCHNITTE:
{chr(10).join(f"- {snippet}" for snippet in context_data['html_snippets'])}

RAW PRODUCT DATEN:
{json.dumps(context_data['raw_products'], indent=2)}

GEFUNDENE PREISMUSTER:
{', '.join(context_data['price_patterns'])}

JSON-STRUKTUREN:
{json.dumps(context_data['json_structures'], indent=2)}

AUFGABE:
Extrahiere alle Produkte die zum Suchbegriff "{search_query}" passen und gib sie im folgenden JSON-Format zurück:

{{
  "products": [
    {{
      "name": "Produktname",
      "price": "1.99",
      "unit": "1kg",
      "brand": "Marke oder null",
      "category": "Kategorie",
      "discount": "-20%" oder null,
      "available_until": "Nur Montag" oder Datum,
      "origin": "Deutschland" oder null,
      "quality_info": "Bio, 3,5% Fett" oder null
    }}
  ],
  "confidence": 0.8,
  "reasoning": "Kurze Erklärung der Extraktion"
}}

WICHTIGE REGELN:
1. Nur Produkte extrahieren die wirklich zum Suchbegriff passen
2. Preise als Dezimalzahl (z.B. "1.99")
3. Verwende "Lidl" nicht als Marke (nur für echte Marken)
4. partner_program ist immer true für Lidl-Angebote
5. Bei Unsicherheit: confidence reduzieren
6. Maximal 10 Produkte

Antwort NUR als valides JSON:"""
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Führt OpenAI API-Aufruf aus"""
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API Key nicht konfiguriert")
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",  # Günstigeres Modell für Extraktion
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für Produktdatenextraktion aus Webseiten. Antworte immer nur mit validem JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1  # Niedrige Temperatur für konsistente Extraktion
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API Fehler {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    def _parse_llm_response(self, llm_response: str) -> List[ProductResult]:
        """Parsed LLM-Antwort zu ProductResult-Objekten"""
        try:
            # Versuche JSON zu parsen
            response_data = json.loads(llm_response)
            
            products = []
            for product_data in response_data.get("products", []):
                try:
                    product = ProductResult(
                        name=product_data["name"],
                        price=Decimal(str(product_data["price"])),
                        store="Lidl",
                        unit=product_data.get("unit"),
                        brand=product_data.get("brand"),
                        category=product_data.get("category"),
                        partner_program=True,  # Immer true für Lidl-Angebote
                        available_until=product_data.get("available_until"),
                        discount=product_data.get("discount"),
                        origin=product_data.get("origin"),
                        quality_info=product_data.get("quality_info")
                    )
                    products.append(product)
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen von Produkt: {e}")
                    continue
            
            logger.info(f"LLM extrahierte {len(products)} Produkte")
            return products
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM-Antwort ist kein valides JSON: {e}")
            logger.debug(f"LLM-Response: {llm_response}")
            return []
        except Exception as e:
            logger.error(f"Fehler beim Parsen der LLM-Antwort: {e}")
            return []

# Singleton-Instanz
lidl_llm_interpreter = LidlLLMInterpreter() 
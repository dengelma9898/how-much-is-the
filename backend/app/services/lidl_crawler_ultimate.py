"""
LIDL Ultimate Crawler mit progressivem Scrollen
Basiert auf den Debug-Erkenntnissen für 120+ Produkte
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page
from decimal import Decimal, InvalidOperation
import re

from ..models.search import ProductResult

logger = logging.getLogger(__name__)

class LidlUltimateCrawler:
    """Ultimate LIDL Crawler mit progressivem Scrollen für alle Produkte"""
    
    def __init__(self):
        self.base_url = "https://www.lidl.de/c/billiger-montag/a10006065?channel=store&tabCode=Current_Sales_Week"
        self.timeout = 60000
        self.max_retries = 3
    
    async def search_products(self, query: str = "", max_results: int = 100, postal_code: str = "10115") -> List[ProductResult]:
        """
        Sucht Produkte auf LIDL mit ultimativem progressivem Scrollen
        
        Args:
            query: Suchbegriff (für LIDL nicht verwendet, aber für Konsistenz)
            max_results: Maximum Anzahl Ergebnisse
            postal_code: Postleitzahl (für LIDL nicht verwendet)
        
        Returns:
            Liste der gefundenen Produkte
        """
        products = []
        
        try:
            async with async_playwright() as p:
                # Browser mit Anti-Detection Einstellungen
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                page = await browser.new_page(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                logger.info(f"🌐 Navigiere zu LIDL: {self.base_url}")
                await page.goto(self.base_url, timeout=self.timeout)
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(3000)
                
                # 🍪 Cookie-Banner behandeln
                await self._handle_cookie_banner(page)
                
                # ⏳ Kurz warten nach Cookie-Accept
                await page.wait_for_timeout(3000)
                
                # 📜 PROGRESSIVES SCROLLEN für alle Produkte
                await self._progressive_scroll_to_load_all(page)
                
                # 🔍 Produkte extrahieren
                products = await self._extract_all_products(page, query, max_results)
                
                logger.info(f"✅ {len(products)} Produkte erfolgreich extrahiert")
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ LIDL Crawler Fehler: {e}")
            
        return products
    
    async def _handle_cookie_banner(self, page: Page) -> bool:
        """Behandelt Cookie-Banner intelligent"""
        try:
            logger.info("🍪 Suche Cookie-Banner...")
            
            # Warte auf Cookie-Dialog
            cookie_selectors = [
                '[role="dialog"]',
                '.consent-banner',
                '[class*="cookie"]',
                '[class*="consent"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    dialogs = await page.query_selector_all(selector)
                    for dialog in dialogs:
                        if await dialog.is_visible():
                            dialog_text = await dialog.inner_text()
                            
                            if any(word in dialog_text.lower() for word in ['zustimmen', 'consent', 'cookie']):
                                logger.info(f"   🎯 Cookie-Dialog gefunden: {dialog_text[:50]}...")
                                
                                # Finde ZUSTIMMEN Button
                                zustimmen_btn = await dialog.query_selector('button:has-text("ZUSTIMMEN")')
                                if zustimmen_btn and await zustimmen_btn.is_visible():
                                    logger.info("   🔘 Klicke ZUSTIMMEN...")
                                    await zustimmen_btn.click()
                                    await page.wait_for_timeout(2000)
                                    logger.info("   ✅ Cookie-Banner erfolgreich geschlossen!")
                                    return True
                except:
                    continue
                    
            logger.info("   ℹ️  Kein Cookie-Banner gefunden")
            return False
            
        except Exception as e:
            logger.error(f"   ❌ Cookie-Banner Fehler: {e}")
            return False
    
    async def _progressive_scroll_to_load_all(self, page: Page) -> None:
        """Progressives Scrollen um ALLE Produkte zu laden"""
        try:
            logger.info("📜 Starte progressives Scrollen...")
            
            previous_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            while scroll_attempts < max_scroll_attempts:
                # Aktuelle Produktanzahl
                current_products = await page.query_selector_all('.product-grid-box')
                current_count = len(current_products)
                
                logger.info(f"   📊 Scroll {scroll_attempts + 1}: {current_count} Produkte")
                
                # Wenn keine neuen Produkte mehr laden, sind wir fertig
                if current_count == previous_count and scroll_attempts > 2:
                    logger.info(f"   ✅ Scrollen beendet - keine neuen Produkte mehr")
                    break
                
                previous_count = current_count
                
                # Scroll-Position berechnen
                scroll_height = await page.evaluate("document.body.scrollHeight")
                scroll_step = scroll_height // 10  # 10% Schritte
                
                new_scroll_pos = (scroll_attempts + 1) * scroll_step
                await page.evaluate(f"window.scrollTo(0, {new_scroll_pos})")
                
                # Warte auf Lazy Loading
                await page.wait_for_timeout(1500)
                
                scroll_attempts += 1
            
            # Finale Scroll ganz nach unten
            logger.info("   📜 Finale Scroll ganz nach unten...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
            final_products = await page.query_selector_all('.product-grid-box')
            logger.info(f"   🎯 FINALE Produktanzahl: {len(final_products)}")
            
        except Exception as e:
            logger.error(f"   ❌ Scroll-Fehler: {e}")
    
    async def _extract_all_products(self, page: Page, query: str, max_results: int) -> List[ProductResult]:
        """Extrahiert alle Produkte von der Seite"""
        products = []
        
        try:
            # Alle Produktcontainer finden
            product_containers = await page.query_selector_all('.product-grid-box')
            logger.info(f"🔍 Extrahiere {len(product_containers)} Produktcontainer...")
            
            for i, container in enumerate(product_containers[:max_results]):
                try:
                    product = await self._extract_single_product(container, page)
                    if product:
                        # Flexible Query-Filter anwenden
                        should_include = (
                            not query or  # Keine Query = alle Produkte
                            query.lower() in product.name.lower() or  # Name enthält Query
                            query.lower() in product.description.lower() or  # Beschreibung enthält Query
                            any(word in product.name.lower() for word in query.lower().split()) or  # Ein Wort der Query im Namen
                            query.lower() in ['produkte', 'lebensmittel', 'artikel', 'angebote', 'waren']  # Allgemeine Begriffe = alle zeigen
                        )
                        
                        if should_include:
                            products.append(product)
                            
                except Exception as e:
                    logger.warning(f"   ⚠️  Fehler bei Produkt {i+1}: {e}")
                    continue
            
            logger.info(f"✅ {len(products)} Produkte erfolgreich extrahiert")
            
        except Exception as e:
            logger.error(f"❌ Produktextraktion Fehler: {e}")
        
        return products
    
    async def _extract_single_product(self, container, page: Page) -> Optional[ProductResult]:
        """Extrahiert ein einzelnes Produkt aus dem Container"""
        try:
            # Produktname
            title_elem = await container.query_selector('.product-grid-box__title')
            if not title_elem:
                return None
            name = await title_elem.inner_text()
            name = name.strip()
            
            if not name or len(name) < 2:
                return None
            
            # Preis
            price_elem = await container.query_selector('.ods-price__value')
            if not price_elem:
                return None
            price_text = await price_elem.inner_text()
            price = self._parse_price(price_text)
            
            if price is None:
                return None
            
            # Beschreibung (optional)
            description = ""
            desc_elem = await container.query_selector('.product-grid-box__desc')
            if desc_elem:
                desc_text = await desc_elem.inner_text()
                if desc_text:
                    description = desc_text.strip()
            
            # Bild URL
            image_url = ""
            img_elem = await container.query_selector('img')
            if img_elem:
                img_src = await img_elem.get_attribute('src')
                if img_src:
                    if img_src.startswith('//'):
                        image_url = f"https:{img_src}"
                    elif img_src.startswith('/'):
                        image_url = f"https://www.lidl.de{img_src}"
                    else:
                        image_url = img_src
            
            # Verfügbarkeit
            availability = "Verfügbar"
            avail_elem = await container.query_selector('.product-grid-box__availabilities')
            if avail_elem:
                avail_text = await avail_elem.inner_text()
                if avail_text:
                    availability = avail_text.strip()
            
            # Einheit
            unit = ""
            unit_elem = await container.query_selector('.ods-price__footer')
            if unit_elem:
                unit_text = await unit_elem.inner_text()
                if unit_text:
                    unit = unit_text.strip()
            
            # LIDL Plus Hinweis
            reward_program_hint = ""
            reward_elem = await container.query_selector('.ods-price__lidl-plus-hint')
            if reward_elem:
                reward_text = await reward_elem.inner_text()
                if reward_text:
                    reward_program_hint = reward_text.strip()
            
            return ProductResult(
                name=name,
                price=price,
                store="LIDL",
                image_url=image_url,
                product_url=self.base_url,
                availability=availability,
                description=description,
                unit=unit,
                reward_program_hint=reward_program_hint
            )
            
        except Exception as e:
            logger.warning(f"Einzelprodukt-Extraktion Fehler: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[Decimal]:
        """Parst Preistext zu Decimal mit korrekter Behandlung von Cent-Preisen"""
        if not price_text:
            return None
            
        try:
            # Entferne Währungszeichen aber behalte Zahlen, Punkte, Kommas und Minuszeichen
            clean_price = re.sub(r'[^\d,.-]', '', price_text.strip())
            
            # Spezialfall: Führender Punkt/Komma (z.B. "-.90" oder ",90") 
            # Behandle nur Preise die mit Punkt/Komma beginnen oder "-.XX" Format haben
            if clean_price.startswith('-.') and len(clean_price) <= 4:
                # "-.90" wird zu "0.90" (nur für 1-2 stellige Zahlen nach dem Punkt)
                clean_price = '0' + clean_price[1:]
            elif clean_price.startswith('.') and len(clean_price) <= 3:
                # ".90" wird zu "0.90" (nur für 1-2 stellige Zahlen nach dem Punkt)
                clean_price = '0' + clean_price
            elif clean_price.startswith('-,') and len(clean_price) <= 4:
                # "-,90" wird zu "0.90"
                clean_price = '0.' + clean_price[2:]
            elif clean_price.startswith(',') and len(clean_price) <= 3:
                # ",90" wird zu "0.90" (nur für 1-2 stellige Zahlen nach dem Komma)
                clean_price = '0.' + clean_price[1:]
            
            # Normalisiere Kommas zu Punkten
            clean_price = clean_price.replace(',', '.')
            
            # Extrahiere Preismuster: optional Minus, Ziffern, optional Punkt, optional Ziffern
            price_match = re.search(r'(-?\d*\.?\d+)', clean_price)
            if price_match:
                price_str = price_match.group(1)
                price_value = Decimal(price_str)
                
                # Stelle sicher, dass der Preis positiv ist (Sicherheitscheck)
                if price_value < 0:
                    price_value = abs(price_value)
                
                return price_value
                
        except (InvalidOperation, ValueError, AttributeError) as e:
            logger.warning(f"Preisparsung fehlgeschlagen für '{price_text}': {e}")
            
        return None 
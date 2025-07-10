#!/usr/bin/env python3
"""
LIDL Ultimate Crawler - Kategorien-basiert (nicht Query-basiert)
Crawlt ALLE Produkte aus ALLEN Kategorien und speichert sie in der DB
"""

import asyncio
import logging
import re
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
from app.models.search import ProductResult

# Logger Setup
logger = logging.getLogger(__name__)

class LidlUltimateCrawler:
    """Ultimativer LIDL Crawler mit kategorien-basiertem Ansatz"""
    
    def __init__(self):
        self.base_url = "https://www.lidl.de"
        self.timeout = 120000  # 2 Minuten für gründliches Crawling
        
        # LIDL Billiger Montag Aktionsseite (die richtige URL!)
        self.billiger_montag_url = "https://www.lidl.de/c/billiger-montag/a10006065?channel=store&tabCode=Current_Sales_Week"
        
        # KORREKTE CSS-Selektoren für LIDL-Produkte
        self.product_selectors = [
            '.odsc-tile__inner',  # Hauptselektor für Produktkarten
            '[class*="odsc-tile__inner"]',  # Fallback mit Teilstring-Match
            '.product-grid-box',  # Fallback-Selektor
            '[data-testid*="product"]'  # Zusätzlicher Fallback
        ]

    async def crawl_all_products(self, max_results: int = 1000, postal_code: str = "10115") -> List[ProductResult]:
        """
        Crawlt ALLE Produkte von der LIDL Billiger Montag Aktionsseite
        
        Args:
            max_results: Maximum Anzahl Ergebnisse
            postal_code: Postleitzahl (für LIDL nicht verwendet)
        
        Returns:
            Liste ALLER gefundenen Produkte von der Aktionsseite
        """
        all_products = []
        
        try:
            async with async_playwright() as p:
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
                
                logger.info(f"🏪 Starte LIDL Billiger Montag Crawling")
                logger.info(f"🌐 URL: {self.billiger_montag_url}")
                
                # Navigiere zur Billiger Montag Seite
                await page.goto(self.billiger_montag_url, timeout=self.timeout)
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(5000)  # 5 Sekunden für vollständiges Laden
                
                # Cookie-Banner behandeln
                await self._handle_cookie_banner(page)
                await page.wait_for_timeout(3000)
                
                # GRÜNDLICHES SCROLLEN in 3 Phasen
                await self._thorough_scroll_strategy(page)
                
                # Produkte extrahieren
                all_products = await self._extract_products_from_page(page, max_results)
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ LIDL Billiger Montag Crawler Fehler: {e}")
            
        logger.info(f"🎯 GESAMT: {len(all_products)} Produkte von Billiger Montag gecrawlt")
        return all_products
    
    async def _thorough_scroll_strategy(self, page: Page) -> None:
        """
        Gründliche 3-Phasen Scroll-Strategie für offline Crawling:
        1. Runter scrollen (alle Produkte laden)
        2. Hoch scrollen (versteckte Produkte aktivieren)  
        3. Nochmal runter scrollen (finale Ladung)
        """
        try:
            logger.info("📜 Starte gründliche 3-Phasen Scroll-Strategie...")
            
            # PHASE 1: Langsam nach unten scrollen
            logger.info("   📜 Phase 1: Scrollen nach unten...")
            await self._scroll_down_thoroughly(page)
            
            # PHASE 2: Langsam nach oben scrollen
            logger.info("   📜 Phase 2: Scrollen nach oben...")
            await self._scroll_up_thoroughly(page)
            
            # PHASE 3: Nochmal nach unten scrollen
            logger.info("   📜 Phase 3: Nochmal nach unten scrollen...")
            await self._scroll_down_thoroughly(page)
            
            # Finale Wartzeit für Lazy Loading
            await page.wait_for_timeout(5000)
            
            # Finale Produktanzahl prüfen
            final_containers = await self._count_all_product_containers(page)
            logger.info(f"   🎯 FINALE Produktcontainer nach 3-Phasen-Scroll: {final_containers}")
            
        except Exception as e:
            logger.error(f"   ❌ Scroll-Strategie Fehler: {e}")
    
    async def _scroll_down_thoroughly(self, page: Page) -> None:
        """Scröllt langsam und gründlich nach unten"""
        try:
            scroll_step = 300  # Kleinere Schritte für besseres Lazy Loading
            max_scrolls = 50   # Mehr Scroll-Versuche
            previous_height = 0
            no_change_count = 0
            
            for i in range(max_scrolls):
                # Scrollen
                await page.evaluate(f"window.scrollBy(0, {scroll_step})")
                await page.wait_for_timeout(2000)  # 2 Sekunden warten
                
                # Aktuelle Höhe prüfen
                current_height = await page.evaluate("document.body.scrollHeight")
                
                if current_height == previous_height:
                    no_change_count += 1
                    if no_change_count >= 3:  # 3 mal keine Änderung = Ende
                        logger.info(f"      📜 Scroll-Ende erreicht nach {i+1} Schritten")
                        break
                else:
                    no_change_count = 0
                    
                previous_height = current_height
                
                # Produktanzahl logging alle 10 Schritte
                if i % 10 == 0:
                    container_count = await self._count_all_product_containers(page)
                    logger.info(f"      📊 Scroll {i+1}: {container_count} Container")
            
            # Ganz nach unten scrollen
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            logger.error(f"      ❌ Runter-Scroll Fehler: {e}")
    
    async def _scroll_up_thoroughly(self, page: Page) -> None:
        """Scröllt langsam nach oben um versteckte Elemente zu aktivieren"""
        try:
            current_pos = await page.evaluate("window.pageYOffset")
            scroll_step = 400
            
            while current_pos > 0:
                new_pos = max(0, current_pos - scroll_step)
                await page.evaluate(f"window.scrollTo(0, {new_pos})")
                await page.wait_for_timeout(1500)  # 1.5 Sekunden warten
                current_pos = new_pos
            
            # Ganz nach oben
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)
            
            logger.info(f"      📜 Zurück nach oben gescrollt")
            
        except Exception as e:
            logger.error(f"      ❌ Hoch-Scroll Fehler: {e}")
    
    async def _count_all_product_containers(self, page: Page) -> int:
        """Zählt alle gefundenen Produktcontainer mit allen Selektoren"""
        total_count = 0
        for selector in self.product_selectors:
            try:
                containers = await page.query_selector_all(selector)
                if containers:
                    count = len(containers)
                    if count > total_count:
                        total_count = count
            except:
                continue
        return total_count
    
    async def _extract_products_from_page(self, page: Page, max_results: int) -> List[ProductResult]:
        """Extrahiert Produkte von der Billiger Montag Seite mit erweiterten Selektoren"""
        products = []
        
        try:
            logger.info(f"🔍 Suche Produktcontainer mit {len(self.product_selectors)} verschiedenen Selektoren...")
            
            # Finde den besten Selektor
            best_selector = None
            max_found = 0
            
            for selector in self.product_selectors:
                try:
                    containers = await page.query_selector_all(selector)
                    count = len(containers)
                    logger.info(f"   🔍 Selektor '{selector}': {count} Container")
                    
                    if count > max_found:
                        max_found = count
                        best_selector = selector
                        
                except Exception as e:
                    logger.warning(f"   ⚠️  Selektor '{selector}' Fehler: {e}")
                    continue
            
            if not best_selector or max_found == 0:
                logger.error("❌ Keine Produktcontainer mit keinem Selektor gefunden!")
                return products
            
            logger.info(f"🎯 Bester Selektor: '{best_selector}' mit {max_found} Containern")
            
            # Verwende den besten Selektor für Extraktion
            product_containers = await page.query_selector_all(best_selector)
            logger.info(f"🔍 Extrahiere {len(product_containers)} Produktcontainer...")
            
            for i, container in enumerate(product_containers[:max_results]):
                try:
                    product = await self._extract_single_product(container, page)
                    if product:
                        # Füge Billiger Montag Kategorie hinzu
                        product.category = "Billiger Montag"
                        products.append(product)
                        
                        # Logging alle 20 Produkte
                        if (i + 1) % 20 == 0:
                            logger.info(f"   📊 Fortschritt: {i+1}/{len(product_containers)} Container, {len(products)} erfolgreiche Extraktion")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️  Fehler bei Container {i+1}: {e}")
                    continue
            
            logger.info(f"✅ {len(products)} Produkte erfolgreich extrahiert")
            
        except Exception as e:
            logger.error(f"❌ Produktextraktion Fehler: {e}")
        
        return products

    # Legacy-Methode für Rückwärtskompatibilität (wird durch crawl_all_products ersetzt)
    async def search_products(self, query: str = "", max_results: int = 100, postal_code: str = "10115") -> List[ProductResult]:
        """
        DEPRECATED: Legacy-Methode für Kompatibilität
        Nutze crawl_all_products() für das neue kategorien-basierte System
        """
        logger.warning("⚠️  search_products() ist deprecated. Nutze crawl_all_products() für bessere Ergebnisse.")
        return await self.crawl_all_products(max_results, postal_code)
    
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
    
    async def _extract_single_product(self, container, page: Page) -> Optional[ProductResult]:
        """Extrahiert ein einzelnes Produkt aus dem Container mit korrekten LIDL CSS-Selektoren"""
        try:
            # Produktname - KORREKT: product-grid-box__title
            title_elem = await container.query_selector('.product-grid-box__title')
            if not title_elem:
                return None
            name = await title_elem.inner_text()
            name = name.strip()
            
            if not name or len(name) < 2:
                return None
            
            # Preis - KORREKT: ods-price__value
            price_elem = await container.query_selector('.ods-price__value')
            if not price_elem:
                return None
            price_text = await price_elem.inner_text()
            price = self._parse_price(price_text)
            
            if price is None:
                return None
            
            # Zusätzliche Beschreibung - KORREKT: product-grid-box__desc (optional)
            description = ""
            desc_elem = await container.query_selector('.product-grid-box__desc')
            if desc_elem:
                desc_text = await desc_elem.inner_text()
                if desc_text:
                    description = desc_text.strip()
            
            # Bild URL - KORREKT: img tag innerhalb odsc-image-gallery
            image_url = ""
            img_elem = await container.query_selector('.odsc-image-gallery img')
            if img_elem:
                img_src = await img_elem.get_attribute('src')
                if img_src:
                    if img_src.startswith('//'):
                        image_url = f"https:{img_src}"
                    elif img_src.startswith('/'):
                        image_url = f"https://www.lidl.de{img_src}"
                    else:
                        image_url = img_src
            
            # Verfügbarkeit - KORREKT: product-grid-box__availabilities
            availability_text = ""
            avail_elem = await container.query_selector('.product-grid-box__availabilities')
            if avail_elem:
                availability_text = await avail_elem.inner_text()
                if availability_text:
                    availability_text = availability_text.strip()
            
            # Parse Verfügbarkeit und Enddatum
            availability, parsed_availability_text, offer_valid_until = self._parse_availability_and_date(availability_text)
            
            # Einheit - KORREKT: Erstes Element in ods-price__footer
            unit = ""
            unit_elem = await container.query_selector('.ods-price__footer')
            if unit_elem:
                # Nehme das erste Element innerhalb des Footer
                first_child = await unit_elem.query_selector(':first-child')
                if first_child:
                    unit_text = await first_child.inner_text()
                    if unit_text:
                        unit = unit_text.strip()
                else:
                    # Fallback: Direkter Text des Footer-Elements
                    unit_text = await unit_elem.inner_text()
                    if unit_text:
                        unit = unit_text.strip()
            
            # LIDL Plus Hinweis - KORREKT: ods-price__lidl-plus-hint
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
                availability_text=parsed_availability_text,
                offer_valid_until=offer_valid_until,
                description=description,
                unit=unit,
                reward_program_hint=reward_program_hint
            )
            
        except Exception as e:
            logger.warning(f"Einzelprodukt-Extraktion Fehler: {e}")
            return None
    
    def _parse_availability_and_date(self, availability_text: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Parst Verfügbarkeitstext und extrahiert Enddatum
        
        Args:
            availability_text: Text wie "nur in der Filiale 07.07. - 12.07." oder "Verfügbar"
            
        Returns:
            Tuple (is_available: bool, availability_text: str, valid_until: str)
        """
        if not availability_text:
            return True, None, None
            
        availability_text = availability_text.strip()
        
        # Standardmäßig verfügbar, es sei denn, es gibt Hinweise auf Nichtverfügbarkeit
        is_available = True
        valid_until = None
        
        # Prüfe auf Nichtverfügbarkeit
        unavailable_indicators = ['nicht verfügbar', 'ausverkauft', 'vergriffen', 'nicht lieferbar']
        if any(indicator in availability_text.lower() for indicator in unavailable_indicators):
            is_available = False
            
        # Extrahiere Datumsangaben im Format DD.MM. oder DD.MM.YYYY
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{1,2})\.(\d{1,2})\.',         # DD.MM.
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, availability_text)
            for match in matches:
                try:
                    if len(match) == 3:  # DD.MM.YYYY
                        day, month, year = int(match[0]), int(match[1]), int(match[2])
                    else:  # DD.MM.
                        day, month = int(match[0]), int(match[1])
                        # Nehme aktuelles Jahr oder nächstes Jahr falls Datum in der Vergangenheit
                        current_year = datetime.now().year
                        current_date = datetime.now().date()
                        try:
                            test_date = datetime(current_year, month, day).date()
                            # Wenn das Datum mehr als 30 Tage in der Vergangenheit liegt, nehme nächstes Jahr
                            # Das behandelt Edge Cases um Jahreswechsel besser
                            days_diff = (current_date - test_date).days
                            if days_diff > 30:
                                year = current_year + 1
                            else:
                                year = current_year
                        except ValueError:
                            year = current_year
                    
                    # Validiere Datum
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        date_obj = datetime(year, month, day)
                        dates_found.append(date_obj)
                        
                except (ValueError, IndexError):
                    continue
        
        # Nehme das späteste Datum als Enddatum
        if dates_found:
            latest_date = max(dates_found)
            valid_until = latest_date.strftime('%Y-%m-%d')
            
            # Wenn das Datum in der Vergangenheit liegt, ist das Produkt nicht mehr verfügbar
            if latest_date.date() < datetime.now().date():
                is_available = False
        
        logger.debug(f"Parsed availability: '{availability_text}' -> available={is_available}, until={valid_until}")
        return is_available, availability_text, valid_until

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
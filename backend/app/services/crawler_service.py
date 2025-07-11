import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from decimal import Decimal

from .database_service import DatabaseService
from .lidl_crawler_ultimate import LidlUltimateCrawler
from .aldi_crawler_ultimate import AldiUltimateCrawler
from .crawl_status_service import crawl_status_service, CrawlStatus
from ..models.search import ProductResult
from ..core.config import settings

logger = logging.getLogger(__name__)


class CrawlerService:
    """Enhanced service for coordinating crawlers with progress tracking"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.crawlers = {
            "Lidl": LidlUltimateCrawler(),
            "Aldi": AldiUltimateCrawler()
        }
        # Store metadata for dynamic creation
        self.store_metadata = {
            "Lidl": {
                "name": "Lidl",
                "base_url": "https://www.lidl.de",
                "logo_url": "https://www.lidl.de/favicon.ico",
                "enabled": True
            },
            "Aldi": {
                "name": "Aldi",
                "base_url": "https://www.aldi-sued.de", 
                "logo_url": "https://www.aldi-sued.de/favicon.ico",
                "enabled": True
            }
        }
        logger.info("Ultimate crawlers (Lidl, Aldi) successfully initialized")
    
    async def _ensure_store_exists(self, store_name: str) -> object:
        """
        Ensures the store exists in the database, creating it if necessary.
        Only creates stores that we actually crawl.
        Handles race conditions by retrying store lookup if creation fails due to unique constraint.
        
        Args:
            store_name: Name of the store to ensure exists
            
        Returns:
            Store object from database
            
        Raises:
            ValueError: If store_name is not in our supported crawlers
        """
        if store_name not in self.crawlers:
            raise ValueError(f"No crawler available for store: {store_name}")
        
        # Try to get existing store
        store = await self.db_service.stores.get_by_name(store_name)
        
        if store:
            logger.debug(f"Store '{store_name}' already exists in database")
            return store
        
        # Store doesn't exist, create it dynamically
        if store_name not in self.store_metadata:
            raise ValueError(f"No metadata available for store: {store_name}")
        
        metadata = self.store_metadata[store_name]
        logger.info(f"🏪 Creating new store '{store_name}' in database (first crawl)")
        
        try:
            # Create store in database with all metadata including enabled status
            store = await self.db_service.stores.create(
                name=metadata["name"],
                base_url=metadata["base_url"],
                logo_url=metadata["logo_url"],
                enabled=metadata["enabled"]
            )
            logger.info(f"✅ Store '{store_name}' successfully created with ID {store.id}")
            
        except Exception as e:
            # Check if this is a unique constraint violation (race condition)
            error_str = str(e).lower()
            is_unique_constraint_error = any(indicator in error_str for indicator in [
                "unique constraint",
                "duplicate key",
                "integrity constraint",
                "violates unique constraint",
                "duplicate entry"
            ])
            
            if is_unique_constraint_error:
                # Handle race condition: another process created the store concurrently
                logger.info(f"Store creation failed due to race condition: {str(e)}")
                logger.info(f"Retrying store lookup for '{store_name}'")
                
                store = await self.db_service.stores.get_by_name(store_name)
                if store:
                    logger.info(f"✅ Store '{store_name}' found after retry (created by concurrent process)")
                else:
                    # If we still can't find it, re-raise the original error
                    logger.error(f"Failed to create or find store '{store_name}' after retry")
                    raise
            else:
                # This is not a race condition - it's a validation error, connection issue, etc.
                logger.error(f"Failed to create store '{store_name}' due to non-race-condition error: {str(e)}")
                raise
        
        return store
    
    async def crawl_store(
        self, 
        store_name: str, 
        postal_code: str, 
        crawl_session_id: int,
        query: str = None,
        crawl_id: Optional[str] = None,
        progress_callback=None
    ) -> Tuple[int, int]:
        """
        Enhanced crawl store method with progress tracking
        
        Args:
            store_name: Name of the store to crawl
            postal_code: Postal code for location-specific crawling
            crawl_session_id: Database session ID
            query: Optional specific query to search for
            crawl_id: Optional crawl tracking ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success_count, error_count)
        """
        
        if store_name not in self.crawlers:
            raise ValueError(f"No crawler available for store: {store_name}")
        
        logger.info(f"Starting enhanced crawl for store: {store_name}")
        
        # Update progress if tracking enabled
        if crawl_id:
            crawl_status_service.update_crawl_progress(
                crawl_id,
                status=CrawlStatus.INITIALIZING,
                current_step=f"Initializing {store_name} crawler"
            )
        
        # Ensure store exists in database (create if needed)
        store = await self._ensure_store_exists(store_name)
        
        crawler = self.crawlers[store_name]
        success_count = 0
        error_count = 0
        
        try:
            # Update progress
            if crawl_id:
                crawl_status_service.update_crawl_progress(
                    crawl_id,
                    status=CrawlStatus.CRAWLING,
                    current_step="Starting product crawl",
                    progress_percentage=10.0
                )
            
            # NEUE ARCHITEKTUR: Crawle ALLE Produkte ohne Query-basierte Logik
            all_products = []
            
            try:
                logger.info(f"Crawling ALL products from {store_name} (no query-based approach)")
                
                # Update progress
                if crawl_id:
                    crawl_status_service.update_crawl_progress(
                        crawl_id,
                        current_step=f"Crawling ALL products from {store_name}",
                        progress_percentage=20.0
                    )
                
                # Call the appropriate crawler with new architecture
                if store_name == "Lidl":
                    products = await crawler.crawl_all_products(
                        max_results=settings.lidl_max_products_per_crawl, 
                        postal_code=postal_code
                    )
                elif store_name == "Aldi":
                    # Aldi verwendet jetzt auch das neue Ultimate-System
                    products = await crawler.crawl_all_products(
                        max_results=settings.aldi_max_products_per_crawl, 
                        postal_code=postal_code
                    )
                else:
                    logger.error(f"Unknown crawler implementation for {store_name}")
                    products = []
                
                if products:
                    all_products.extend(products)
                    logger.info(f"✅ Found {len(products)} products from {store_name}")
                    
                    # Update products found count
                    if crawl_id:
                        crawl_status_service.update_crawl_progress(
                            crawl_id,
                            current_step=f"Successfully crawled {len(products)} products",
                            progress_percentage=60.0,
                            products_found=len(all_products)
                        )
                else:
                    logger.warning(f"⚠️  No products found from {store_name}")
                    
            except Exception as e:
                logger.error(f"Error crawling {store_name}: {str(e)}")
                error_count += 1
                
                # Update error count
                if crawl_id:
                    crawl_status_service.update_crawl_progress(
                        crawl_id,
                        errors_count=error_count
                    )
            
            # Update progress for processing
            if crawl_id:
                crawl_status_service.update_crawl_progress(
                    crawl_id,
                    status=CrawlStatus.PROCESSING,
                    current_step="Processing and deduplicating products",
                    progress_percentage=60.0
                )
            
            # Remove duplicates based on name and store
            unique_products = self._deduplicate_products(all_products)
            logger.info(f"After deduplication: {len(unique_products)} unique products")
            
            # Convert to database format and save
            if unique_products:
                # Update progress for database operations
                if crawl_id:
                    crawl_status_service.update_crawl_progress(
                        crawl_id,
                        current_step="Cleaning old products",
                        progress_percentage=70.0
                    )
                
                # Soft delete old products for this store (older than 7 days)
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                deleted_count = await self.db_service.products.soft_delete_old_products(
                    store_id=store.id, 
                    cutoff_date=cutoff_date
                )
                logger.info(f"Soft deleted {deleted_count} old products for {store_name}")
                
                # Update progress for product conversion
                if crawl_id:
                    crawl_status_service.update_crawl_progress(
                        crawl_id,
                        current_step="Converting products to database format",
                        progress_percentage=80.0
                    )
                
                # Prepare products for database
                product_data_list = []
                total_products = len(unique_products)
                
                for idx, product in enumerate(unique_products):
                    try:
                        product_data = self._convert_product_to_db_format(
                            product, 
                            store.id, 
                            postal_code
                        )
                        product_data_list.append(product_data)
                        success_count += 1
                        
                        # Update progress periodically during conversion
                        if crawl_id and idx % 20 == 0:  # Update every 20 products
                            conversion_progress = 80.0 + (idx / total_products) * 15.0  # 80-95%
                            crawl_status_service.update_crawl_progress(
                                crawl_id,
                                current_step=f"Converting products ({idx+1}/{total_products})",
                                progress_percentage=conversion_progress,
                                products_processed=len(product_data_list)
                            )
                            
                    except Exception as e:
                        logger.error(f"Error converting product to DB format: {str(e)}")
                        error_count += 1
                        
                        # Update error count
                        if crawl_id:
                            crawl_status_service.update_crawl_progress(
                                crawl_id,
                                errors_count=error_count
                            )
                
                # Final database save
                if product_data_list:
                    if crawl_id:
                        crawl_status_service.update_crawl_progress(
                            crawl_id,
                            current_step="Saving products to database",
                            progress_percentage=95.0
                        )
                    
                    inserted_count = await self.db_service.products.bulk_create(
                        product_data_list, 
                        crawl_session_id
                    )
                    logger.info(f"Inserted {inserted_count} products into database")
                
                await self.db_service.commit()
                
                # Final progress update
                if crawl_id:
                    crawl_status_service.update_crawl_progress(
                        crawl_id,
                        current_step="Crawl completed successfully",
                        progress_percentage=100.0,
                        products_processed=success_count
                    )
            
        except Exception as e:
            logger.error(f"Error in crawl_store for {store_name}: {str(e)}")
            await self.db_service.rollback()
            
            # Update error status
            if crawl_id:
                crawl_status_service.update_crawl_progress(
                    crawl_id,
                    current_step=f"Error: {str(e)}",
                    errors_count=error_count + 1
                )
            
            raise
        
        logger.info(
            f"Enhanced crawl completed for {store_name}: "
            f"{success_count} products processed, {error_count} errors"
        )
        
        return success_count, error_count
    
    def _get_default_queries(self, store_name: str) -> List[str]:
        """Get default search queries for a store - optimized for reasonable crawl times"""
        
        # Reduced set of most important categories for faster, focused crawling
        base_queries = [
            "Milch",           # Dairy - high-frequency item
            "Brot",            # Bread - essential item
            "Obst",            # Fruits - broad category
            "Gemüse",          # Vegetables - broad category
            "Fleisch"          # Meat - essential category
        ]
        
        # Store-specific queries for brand products (only 1-2 per store)
        if store_name == "Lidl":
            base_queries.extend([
                "Milbona"          # Lidl's popular dairy brand
            ])
        elif store_name == "Aldi":
            base_queries.extend([
                "Simply"           # Aldi brand
            ])
        
        logger.info(f"Using {len(base_queries)} search queries for {store_name}: {base_queries}")
        return base_queries
    
    def _deduplicate_products(self, products: List[ProductResult]) -> List[ProductResult]:
        """Remove duplicate products based on name and normalize"""
        
        seen_products = {}
        unique_products = []
        
        for product in products:
            # Create a key for deduplication
            # Note: product.store is a string, not an object
            store_name = product.store.lower() if product.store else ""
            key = (
                product.name.lower().strip(),
                store_name,
                str(product.price) if product.price else "no_price"
            )
            
            if key not in seen_products:
                seen_products[key] = product
                unique_products.append(product)
            else:
                # Keep the one with more information (description, image, etc.)
                existing = seen_products[key]
                if (product.description and not existing.description) or \
                   (product.image_url and not existing.image_url):
                    seen_products[key] = product
                    # Replace in unique_products list
                    unique_products = [p for p in unique_products if p != existing]
                    unique_products.append(product)
        
        return unique_products
    
    def _convert_product_to_db_format(
        self, 
        product: ProductResult, 
        store_id: int, 
        postal_code: str
    ) -> Dict[str, Any]:
        """Convert Product model to database format"""
        
        # Extract price as Decimal
        price = None
        if product.price is not None:
            try:
                price = Decimal(str(product.price))
            except (ValueError, TypeError):
                logger.warning(f"Invalid price format: {product.price}")
        
        # Extract category from description or name if available
        category = self._extract_category(product)
        
        # Extract brand if not already set
        brand = product.brand or self._extract_brand(product)
        
        # Convert availability from string to boolean for database
        availability_bool = True  # Default
        if product.availability is not None:
            if isinstance(product.availability, str):
                availability_bool = product.availability.lower() not in ["nicht verfügbar", "ausverkauft", "vergriffen", "nicht lieferbar"]
            else:
                availability_bool = bool(product.availability)

        return {
            "name": product.name[:255],  # Ensure max length
            "description": product.description[:1000] if product.description else None,
            "brand": brand[:100] if brand else None,
            "category": category[:100] if category else None,
            "store_id": store_id,
            "price": price,
            "unit": product.unit[:50] if product.unit else None,
            "availability": availability_bool,
            "availability_text": product.availability_text[:255] if product.availability_text else None,
            "offer_valid_until": product.offer_valid_until,
            "image_url": product.image_url[:500] if product.image_url else None,
            "product_url": product.product_url[:500] if product.product_url else None,
            "postal_code": postal_code
        }
    
    def _extract_category(self, product: ProductResult) -> str:
        """Extract product category from name or description"""
        
        if product.category:
            return product.category
        
        # Simple category mapping based on keywords
        category_keywords = {
            "Milchprodukte": ["milch", "käse", "joghurt", "quark", "sahne", "butter"],
            "Fleisch & Wurst": ["fleisch", "wurst", "hähnchen", "schwein", "rind", "salami", "schinken"],
            "Obst & Gemüse": ["obst", "gemüse", "apfel", "banane", "tomate", "kartoffel", "zwiebel"],
            "Backwaren": ["brot", "brötchen", "kuchen", "keks", "gebäck"],
            "Getränke": ["wasser", "saft", "limonade", "cola", "bier", "wein", "kaffee", "tee"],
            "Tiefkühl": ["pizza", "eis", "tiefkühl", "gefroren"],
            "Süßwaren": ["schokolade", "bonbon", "gummi", "süß", "zucker"],
            "Nudeln & Reis": ["nudeln", "pasta", "reis", "spaghetti"],
            "Konserven": ["dose", "konserve", "eingemacht"],
            "Hygiene": ["shampoo", "seife", "zahnpasta", "duschgel"]
        }
        
        text_to_check = (product.name + " " + (product.description or "")).lower()
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return category
        
        return "Sonstiges"
    
    def _extract_brand(self, product: ProductResult) -> str:
        """Extract brand from product name or description"""
        
        # Common German brand names
        known_brands = [
            "Coca-Cola", "Pepsi", "Nutella", "Kinder", "Ferrero",
            "Knorr", "Maggi", "Nestlé", "Danone", "Müller",
            "Ja!", "Gut & Günstig", "Simply", "K-Classic", "Milbona",
                            "Freeway", "Lidl"
        ]
        
        text_to_check = product.name + " " + (product.description or "")
        
        for brand in known_brands:
            if brand.lower() in text_to_check.lower():
                return brand
        
        # Try to extract first word as potential brand if it's capitalized
        words = product.name.split()
        if words and words[0][0].isupper() and len(words[0]) > 2:
            return words[0]
        
        return None
    
    async def get_crawl_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get crawling statistics for the last N days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            # Get all crawl sessions in the time period
            async with self.db_service.session as session:
                from sqlalchemy import select, func
                from ..models.database_models import DatabaseCrawlSession, DatabaseStore
                
                result = await session.execute(
                    select(
                        DatabaseStore.name,
                        func.count(DatabaseCrawlSession.id).label('session_count'),
                        func.sum(DatabaseCrawlSession.success_count).label('total_products'),
                        func.sum(DatabaseCrawlSession.error_count).label('total_errors'),
                        func.max(DatabaseCrawlSession.started_at).label('last_crawl')
                    )
                    .join(DatabaseStore)
                    .where(DatabaseCrawlSession.started_at >= cutoff_date)
                    .group_by(DatabaseStore.name)
                )
                
                statistics = {
                    "period_days": days,
                    "stores": []
                }
                
                for row in result:
                    store_stats = {
                        "store_name": row.name,
                        "crawl_sessions": row.session_count,
                        "products_crawled": row.total_products or 0,
                        "errors": row.total_errors or 0,
                        "last_crawl": row.last_crawl.isoformat() if row.last_crawl else None
                    }
                    statistics["stores"].append(store_stats)
                
                return statistics
                
        except Exception as e:
            logger.error(f"Error getting crawl statistics: {str(e)}")
            return {"error": str(e)} 
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.database_models import DatabaseStore, DatabaseProduct, DatabaseCrawlSession
from ..models.search import ProductResult, Store


class StoreRepository:
    """Repository for store operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_enabled(self) -> List[DatabaseStore]:
        """Get all enabled stores"""
        result = await self.session.execute(
            select(DatabaseStore).where(DatabaseStore.enabled == True)
        )
        return result.scalars().all()
    
    async def get_by_id(self, store_id: int) -> Optional[DatabaseStore]:
        """Get store by ID"""
        result = await self.session.execute(
            select(DatabaseStore).where(DatabaseStore.id == store_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[DatabaseStore]:
        """Get store by name"""
        result = await self.session.execute(
            select(DatabaseStore).where(DatabaseStore.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, name: str, logo_url: str = None, base_url: str = None) -> DatabaseStore:
        """Create a new store"""
        store = DatabaseStore(
            name=name,
            logo_url=logo_url,
            base_url=base_url
        )
        self.session.add(store)
        await self.session.flush()
        return store


class CrawlSessionRepository:
    """Repository for crawl session operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, store_id: int) -> DatabaseCrawlSession:
        """Create a new crawl session"""
        session = DatabaseCrawlSession(
            store_id=store_id,
            status="running"
        )
        self.session.add(session)
        await self.session.flush()
        return session
    
    async def complete(
        self, 
        session_id: int, 
        total_products: int, 
        success_count: int, 
        error_count: int, 
        notes: str = None
    ) -> Optional[DatabaseCrawlSession]:
        """Mark crawl session as completed"""
        result = await self.session.execute(
            select(DatabaseCrawlSession).where(DatabaseCrawlSession.id == session_id)
        )
        crawl_session = result.scalar_one_or_none()
        
        if crawl_session:
            crawl_session.status = "completed"
            crawl_session.completed_at = datetime.utcnow()
            crawl_session.total_products = total_products
            crawl_session.success_count = success_count
            crawl_session.error_count = error_count
            crawl_session.notes = notes
            
        return crawl_session
    
    async def fail(self, session_id: int, notes: str = None) -> Optional[DatabaseCrawlSession]:
        """Mark crawl session as failed"""
        result = await self.session.execute(
            select(DatabaseCrawlSession).where(DatabaseCrawlSession.id == session_id)
        )
        crawl_session = result.scalar_one_or_none()
        
        if crawl_session:
            crawl_session.status = "failed"
            crawl_session.completed_at = datetime.utcnow()
            crawl_session.notes = notes
            
        return crawl_session
    
    async def get_latest_for_store(self, store_id: int) -> Optional[DatabaseCrawlSession]:
        """Get the latest crawl session for a store"""
        result = await self.session.execute(
            select(DatabaseCrawlSession)
            .where(DatabaseCrawlSession.store_id == store_id)
            .order_by(DatabaseCrawlSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class ProductRepository:
    """Repository for product operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def search(
        self, 
        query: str, 
        postal_code: str = None,
        store_ids: List[int] = None,
        max_price: Decimal = None,
        category: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DatabaseProduct]:
        """Search products with filters"""
        
        # Base query - only active products (not soft deleted)
        stmt = (
            select(DatabaseProduct)
            .options(selectinload(DatabaseProduct.store))
            .where(DatabaseProduct.deleted_at.is_(None))
            .where(DatabaseProduct.availability == True)
        )
        
        # Full text search on name and description
        if query:
            search_filter = or_(
                DatabaseProduct.name.ilike(f"%{query}%"),
                DatabaseProduct.description.ilike(f"%{query}%"),
                DatabaseProduct.brand.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        # Filter by postal code
        if postal_code:
            stmt = stmt.where(DatabaseProduct.postal_code == postal_code)
        
        # Filter by stores
        if store_ids:
            stmt = stmt.where(DatabaseProduct.store_id.in_(store_ids))
        
        # Filter by max price
        if max_price:
            stmt = stmt.where(DatabaseProduct.price <= max_price)
        
        # Filter by category
        if category:
            stmt = stmt.where(DatabaseProduct.category.ilike(f"%{category}%"))
        
        # Order by price (ascending)
        stmt = stmt.order_by(DatabaseProduct.price.asc())
        
        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def bulk_create(self, products: List[Dict[str, Any]], crawl_session_id: int) -> int:
        """Bulk create products"""
        product_objects = []
        
        for product_data in products:
            product = DatabaseProduct(
                name=product_data["name"],
                description=product_data.get("description"),
                brand=product_data.get("brand"),
                category=product_data.get("category"),
                store_id=product_data["store_id"],
                price=product_data.get("price"),
                unit=product_data.get("unit"),
                availability=product_data.get("availability", True),
                image_url=product_data.get("image_url"),
                product_url=product_data.get("product_url"),
                postal_code=product_data.get("postal_code"),
                crawl_session_id=crawl_session_id
            )
            product_objects.append(product)
        
        self.session.add_all(product_objects)
        await self.session.flush()
        
        return len(product_objects)
    
    async def soft_delete_old_products(self, store_id: int, cutoff_date: datetime) -> int:
        """Soft delete products older than cutoff date for a store"""
        stmt = (
            select(DatabaseProduct)
            .where(
                and_(
                    DatabaseProduct.store_id == store_id,
                    DatabaseProduct.created_at < cutoff_date,
                    DatabaseProduct.deleted_at.is_(None)
                )
            )
        )
        
        result = await self.session.execute(stmt)
        products_to_delete = result.scalars().all()
        
        now = datetime.utcnow()
        for product in products_to_delete:
            product.deleted_at = now
        
        return len(products_to_delete)
    
    async def hard_delete_old_products(self, days_old: int = 30) -> int:
        """Permanently delete soft-deleted products older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        stmt = delete(DatabaseProduct).where(
            and_(
                DatabaseProduct.deleted_at.is_not(None),
                DatabaseProduct.deleted_at < cutoff_date
            )
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount


class DatabaseService:
    """Main service class that coordinates all repositories"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stores = StoreRepository(session)
        self.crawl_sessions = CrawlSessionRepository(session)
        self.products = ProductRepository(session)
    
    async def commit(self):
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        await self.session.rollback()
    
    async def refresh(self, instance):
        """Refresh instance from database"""
        await self.session.refresh(instance)
    
    # Convenience methods
    
    async def search_products(
        self, 
        query: str, 
        postal_code: str = None,
        stores: List[str] = None,
        max_price: float = None,
        category: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductResult]:
        """Search products and return as Pydantic models"""
        
        # Convert store names to IDs if provided
        store_ids = None
        if stores:
            store_results = await self.session.execute(
                select(DatabaseStore.id).where(DatabaseStore.name.in_(stores))
            )
            store_ids = [row[0] for row in store_results]
        
        # Convert max_price to Decimal
        max_price_decimal = Decimal(str(max_price)) if max_price else None
        
        # Search products
        db_products = await self.products.search(
            query=query,
            postal_code=postal_code,
            store_ids=store_ids,
            max_price=max_price_decimal,
            category=category,
            limit=limit,
            offset=offset
        )
        
        # Convert to Pydantic models
        result = []
        for db_product in db_products:
            # Convert boolean availability to string for app compatibility
            availability_text = "verfügbar" if db_product.availability else "nicht verfügbar"
            
            product = ProductResult(
                name=db_product.name,
                price=str(db_product.price) if db_product.price else None,  # Convert to string for iOS compatibility
                unit=db_product.unit,
                image_url=db_product.image_url,
                product_url=db_product.product_url,
                description=db_product.description,
                store=db_product.store.name,  # Just the store name, not Store object
                store_logo_url=db_product.store.logo_url,
                availability=availability_text,  # Convert boolean to string for app compatibility
                brand=db_product.brand,
                category=db_product.category,
                offer_valid_until=db_product.offer_valid_until  # Add missing offer_valid_until field
            )
            result.append(product)
        
        return result
    
    async def initialize_stores(self):
        """Initialize default stores if they don't exist"""
        stores_to_create = [
            {"name": "Lidl", "base_url": "https://www.lidl.de"}
        ]
        
        for store_data in stores_to_create:
            existing_store = await self.stores.get_by_name(store_data["name"])
            if not existing_store:
                await self.stores.create(
                    name=store_data["name"],
                    base_url=store_data["base_url"]
                )
        
        await self.commit() 
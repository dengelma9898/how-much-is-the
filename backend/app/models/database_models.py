from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, DECIMAL, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DatabaseStore(Base):
    """Database model for stores/supermarkets"""
    __tablename__ = "stores"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255))
    base_url: Mapped[Optional[str]] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    products: Mapped[List["DatabaseProduct"]] = relationship(
        "DatabaseProduct", 
        back_populates="store",
        cascade="all, delete-orphan"
    )
    crawl_sessions: Mapped[List["DatabaseCrawlSession"]] = relationship(
        "DatabaseCrawlSession",
        back_populates="store",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Store(id={self.id}, name='{self.name}')>"


class DatabaseCrawlSession(Base):
    """Database model for tracking crawl sessions"""
    __tablename__ = "crawl_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running, completed, failed
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    total_products: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    store: Mapped["DatabaseStore"] = relationship("DatabaseStore", back_populates="crawl_sessions")
    products: Mapped[List["DatabaseProduct"]] = relationship(
        "DatabaseProduct",
        back_populates="crawl_session"
    )

    def __repr__(self) -> str:
        return f"<CrawlSession(id={self.id}, store_id={self.store_id}, status='{self.status}')>"


class DatabaseProduct(Base):
    """Database model for products"""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    availability: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    product_url: Mapped[Optional[str]] = mapped_column(String(500))
    postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    crawl_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("crawl_sessions.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    store: Mapped["DatabaseStore"] = relationship("DatabaseStore", back_populates="products")
    crawl_session: Mapped[Optional["DatabaseCrawlSession"]] = relationship(
        "DatabaseCrawlSession", 
        back_populates="products"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_products_store_name', 'store_id', 'name'),
        Index('idx_products_price', 'price'),
        Index('idx_products_category', 'category'),
        Index('idx_products_postal_code', 'postal_code'),
        Index('idx_products_availability', 'availability'),
        Index('idx_products_deleted_at', 'deleted_at'),
        Index('idx_products_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', store_id={self.store_id})>" 
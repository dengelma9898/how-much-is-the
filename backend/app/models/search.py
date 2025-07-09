from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class SearchRequest(BaseModel):
    """Request-Modell für Produktsuche"""
    query: str = Field(..., min_length=1, max_length=100, description="Suchbegriff für Produkte")
    postal_code: str = Field(..., min_length=5, max_length=5, pattern=r"^\d{5}$", description="Deutsche Postleitzahl")
    stores: Optional[List[str]] = Field(None, description="Namen der ausgewählten Supermärkte. Wenn nicht gesetzt, werden alle durchsucht.")
    max_price: Optional[float] = Field(None, gt=0, description="Maximaler Preis in Euro. Optional.")

class ProductResult(BaseModel):
    """Modell für ein Suchergebnis"""
    name: str = Field(..., description="Produktname")
    price: Optional[float] = Field(None, ge=0, description="Preis in Euro")
    store: str = Field(..., description="Name des Supermarkts")
    store_logo_url: Optional[str] = Field(None, description="URL zum Store-Logo")
    product_url: Optional[str] = Field(None, description="URL zum Produkt")
    image_url: Optional[str] = Field(None, description="URL zum Produktbild")
    availability: bool = Field(default=True, description="Verfügbarkeitsstatus")
    unit: Optional[str] = Field(None, description="Einheit/Verpackung (z.B. '1L', '500g', 'Stück')")
    category: Optional[str] = Field(None, description="Produktkategorie")
    brand: Optional[str] = Field(None, description="Marke oder Eigenmarke")
    description: Optional[str] = Field(None, description="Produktbeschreibung")
    
    # Legacy fields for compatibility
    price_per_unit: Optional[float] = Field(None, description="Preis pro Einheit")
    origin: Optional[str] = Field(None, description="Herkunft des Produkts")
    discount: Optional[str] = Field(None, description="Rabatt-Information (z.B. '-20%')")
    quality_info: Optional[str] = Field(None, description="Qualitätsinformationen (z.B. 'Bio', 'Klasse I')")
    partner_program: bool = Field(default=False, description="Ob der Preis über eine Partner-App verfügbar ist")
    available_until: Optional[str] = Field(None, description="Bis wann das Angebot verfügbar ist")
    reward_program_hint: Optional[str] = Field(None, description="Hinweis auf Treueprogramm")

class SearchResponse(BaseModel):
    """Response-Modell für Produktsuche"""
    query: str = Field(..., description="Verwendeter Suchbegriff")
    postal_code: str = Field(..., description="Verwendete Postleitzahl")
    products: List[ProductResult] = Field(default=[], description="Liste der gefundenen Produkte")
    total_products: int = Field(..., description="Anzahl der gefundenen Produkte")
    source: Optional[str] = Field(None, description="Datenquelle: 'database', 'live_crawl', etc.")
    search_time_ms: Optional[int] = Field(None, description="Suchzeit in Millisekunden")
    
    # Legacy field for compatibility
    results: Optional[List[ProductResult]] = Field(None, description="Legacy field - use 'products'")
    total_results: Optional[int] = Field(None, description="Legacy field - use 'total_products'")

class Store(BaseModel):
    """Modell für einen Supermarkt"""
    name: str = Field(..., description="Name des Supermarkts")
    logo_url: Optional[str] = Field(None, description="URL zum Logo")
    enabled: bool = Field(default=True, description="Ob der Store aktiv ist")
    
    # Legacy fields for compatibility
    id: Optional[str] = Field(None, description="Legacy field - store ID")
    website_url: Optional[str] = Field(None, description="Website des Supermarkts")
    category: Optional[str] = Field(None, description="Kategorie (z.B. 'Supermarkt', 'Discounter')")

class StoresResponse(BaseModel):
    """Response-Modell für verfügbare Stores"""
    stores: List[Store] = Field(..., description="Liste verfügbarer Supermärkte")
    source: Optional[str] = Field(None, description="Datenquelle: 'database', 'static', etc.") 
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class SearchRequest(BaseModel):
    """Request-Modell für Produktsuche"""
    query: str = Field(..., min_length=1, max_length=100, description="Suchbegriff für Produkte")
    postal_code: str = Field(..., min_length=5, max_length=5, pattern=r"^\d{5}$", description="Deutsche Postleitzahl")
    selected_stores: Optional[List[str]] = Field(None, description="IDs der ausgewählten Supermärkte. Wenn nicht gesetzt, werden alle durchsucht.")
    unit: Optional[str] = Field(None, description="Filter für die Einheit, z.B. '1L', '500g'. Optional.")
    max_price: Optional[Decimal] = Field(None, gt=0, description="Maximaler Preis in Euro. Optional.")

class ProductResult(BaseModel):
    """Modell für ein Suchergebnis"""
    name: str = Field(..., description="Produktname")
    price: Decimal = Field(..., gt=0, description="Preis in Euro")
    store: str = Field(..., description="Name des Supermarkts")
    store_logo_url: Optional[str] = Field(None, description="URL zum Store-Logo")
    product_url: Optional[str] = Field(None, description="URL zum Produkt")
    image_url: Optional[str] = Field(None, description="URL zum Produktbild")
    availability: str = Field(default="verfügbar", description="Verfügbarkeitsstatus")
    price_per_unit: Optional[Decimal] = Field(None, description="Preis pro Einheit")
    # Zusätzliche Felder für erweiterte Produktinformationen
    unit: Optional[str] = Field(None, description="Einheit/Verpackung (z.B. '1L', '500g', 'Stück')")
    category: Optional[str] = Field(None, description="Produktkategorie")
    brand: Optional[str] = Field(None, description="Marke oder Eigenmarke")
    origin: Optional[str] = Field(None, description="Herkunft des Produkts")
    discount: Optional[str] = Field(None, description="Rabatt-Information (z.B. '-20%')")
    quality_info: Optional[str] = Field(None, description="Qualitätsinformationen (z.B. 'Bio', 'Klasse I')")
    partner_program: bool = Field(default=False, description="Ob der Preis über eine Partner-App verfügbar ist")
    available_until: Optional[str] = Field(None, description="Bis wann das Angebot verfügbar ist (z.B. 'Nur Montag')")

class SearchResponse(BaseModel):
    """Response-Modell für Produktsuche"""
    results: List[ProductResult] = Field(..., description="Liste der gefundenen Produkte")
    query: str = Field(..., description="Verwendeter Suchbegriff")
    postal_code: str = Field(..., description="Verwendete Postleitzahl")
    total_results: int = Field(..., description="Anzahl der gefundenen Ergebnisse")
    search_time_ms: int = Field(..., description="Suchzeit in Millisekunden")

class Store(BaseModel):
    """Modell für einen Supermarkt"""
    id: str = Field(..., description="Eindeutige Store-ID")
    name: str = Field(..., description="Name des Supermarkts")
    logo_url: Optional[str] = Field(None, description="URL zum Logo")
    website_url: Optional[str] = Field(None, description="Website des Supermarkts")
    category: str = Field(..., description="Kategorie (z.B. 'Supermarkt', 'Discounter', 'Drogerie')")

class StoresResponse(BaseModel):
    """Response-Modell für verfügbare Stores"""
    stores: List[Store] = Field(..., description="Liste verfügbarer Supermärkte") 
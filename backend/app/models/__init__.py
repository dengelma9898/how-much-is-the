# Import all models here to ensure they are registered with SQLAlchemy
from .search import *
from .database_models import *

# Export all model classes for easy importing
__all__ = [
    "SearchRequest",
    "SearchResponse", 
    "Product",
    "Store",
    "CrawlSession",
    "DatabaseProduct",
    "DatabaseStore",
    "DatabaseCrawlSession",
] 
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Anwendungseinstellungen"""
    
    # API-Konfiguration
    api_v1_str: str = "/api/v1"
    project_name: str = "Preisvergleich API"
    
    # Firecrawl-Konfiguration
    firecrawl_api_key: Optional[str] = None
    firecrawl_enabled: bool = False
    
    # Server-Konfiguration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 
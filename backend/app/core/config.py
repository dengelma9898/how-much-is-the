import os
from pydantic_settings import BaseSettings
from typing import Optional

def get_env_file() -> str:
    """
    Bestimmt welche .env-Datei geladen werden soll basierend auf:
    1. Kommandozeilen-Argument --env
    2. Environment-Variable APP_ENV
    3. Default: .env.local
    """
    import sys
    
    # 1. Prüfe Kommandozeilen-Argumente
    if "--env" in sys.argv:
        try:
            env_index = sys.argv.index("--env")
            if env_index + 1 < len(sys.argv):
                env_name = sys.argv[env_index + 1]
                return f".env.{env_name}"
        except (ValueError, IndexError):
            pass
    
    # 2. Prüfe Environment-Variable
    app_env = os.getenv("APP_ENV", "local")
    
    # 3. Return .env.{environment}
    return f".env.{app_env}"

class Settings(BaseSettings):
    # API Settings
    api_title: str = "Preisvergleich API"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # CORS Settings
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://preisvergleich:password@localhost:5432/preisvergleich"
    database_echo: bool = False
    
    # Crawler Settings
    enable_crawling: bool = True
    crawl_timeout: int = 30
    crawl_delay: float = 1.0
    
    # Scheduler Settings
    enable_scheduler: bool = True
    weekly_crawl_hour: int = 2  # 2 AM
    weekly_crawl_day_of_week: str = "sunday"
    max_concurrent_crawls: int = 2
    
    # Cache Settings
    cache_ttl_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 
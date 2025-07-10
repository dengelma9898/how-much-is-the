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
    
    # API Server Configuration
    client_api_port: int = 8001
    client_api_host: str = "0.0.0.0"
    admin_api_port: int = 8002
    admin_api_host: str = "0.0.0.0"
    
    # CORS Settings
    backend_cors_origins: list = ["http://localhost:3000", "http://localhost:8001"]
    admin_cors_origins: Optional[list] = None  # Falls nicht gesetzt, wird backend_cors_origins verwendet
    
    # Database Settings (Split Architecture)
    database_url: str = os.getenv(
        "DATABASE_URL", 
        # Default: Generic PostgreSQL URL for development
        # For Homebrew PostgreSQL on Mac, use your username instead of 'preisvergleich_user'
        f"postgresql+asyncpg://{os.getenv('USER', 'preisvergleich_user')}:@localhost:5432/preisvergleich_dev"
    )
    
    # Read-only Database URL für Client API
    database_url_readonly: Optional[str] = os.getenv("DATABASE_URL_READONLY")
    
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
    
    # Rate Limiting Settings
    manual_crawl_rate_limit_minutes: int = 5
    crawl_timeout_minutes: int = 30

    # Enhanced Monitoring Settings
    crawl_status_history_limit: int = 50
    crawl_status_cleanup_hours: int = 24
    enable_detailed_crawl_logging: bool = True
    enable_progress_tracking: bool = True

    # Store-specific Settings
    lidl_crawler_enabled: bool = True
    lidl_base_url: str = "https://www.lidl.de"
    lidl_max_products_per_crawl: int = 1000  # Erhöht für vollständige Extraktion aller verfügbaren Produkte
    lidl_timeout_seconds: int = 60

    aldi_crawler_enabled: bool = True
    aldi_base_url: str = "https://www.aldi-sued.de"
    aldi_max_products_per_crawl: int = 1000  # Erhöht für vollständige Extraktion

    # Firecrawl Settings (for Aldi)
    firecrawl_enabled: bool = False
    firecrawl_api_key: Optional[str] = None
    firecrawl_max_age: int = 3600000  # 1 hour cache
    firecrawl_max_results_per_store: int = 15

    # Admin Interface Settings
    admin_dashboard_enabled: bool = True
    admin_auto_refresh_interval: int = 5  # seconds
    admin_max_log_entries: int = 100

    class Config:
        # Dynamic env_file loading für Split-Architecture
        @staticmethod
        def env_file():
            # Bestimme das Backend-Verzeichnis (ein Level über dem aktuellen wenn in client-api/ oder admin-api/)
            current_dir = os.getcwd()
            backend_dir = current_dir if not (current_dir.endswith('client-api') or current_dir.endswith('admin-api')) else os.path.dirname(current_dir)
            
            # Prüfe nach spezifischen API Environment-Dateien basierend auf dem aktuellen Arbeitsverzeichnis
            client_env = os.path.join(backend_dir, ".env.client")
            admin_env = os.path.join(backend_dir, ".env.admin")
            
            # Entscheide basierend auf dem aktuellen Arbeitsverzeichnis
            if current_dir.endswith('client-api') and os.path.exists(client_env):
                return client_env
            elif current_dir.endswith('admin-api') and os.path.exists(admin_env):
                return admin_env
            elif os.path.exists(client_env):
                return client_env  # Client als Fallback wenn beide existieren
            elif os.path.exists(admin_env):
                return admin_env
            else:
                # Fallback auf allgemeine Environment-Datei
                app_env = os.getenv("APP_ENV", "local")
                env_file = os.path.join(backend_dir, f".env.{app_env}")
                if os.path.exists(env_file):
                    return env_file
                else:
                    return os.path.join(backend_dir, ".env")  # Last fallback
        
        case_sensitive = False

# Global settings instance
settings = Settings(_env_file=Settings.Config.env_file()) 
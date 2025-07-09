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
    """Anwendungseinstellungen"""
    
    # Environment Info
    app_env: str = os.getenv("APP_ENV", "local")
    
    # API-Konfiguration
    api_v1_str: str = "/api/v1"
    project_name: str = "Preisvergleich API"
    
    # Firecrawl-Konfiguration
    firecrawl_api_key: Optional[str] = None
    firecrawl_enabled: bool = False
    
    # Erweiterte Firecrawl-Einstellungen
    firecrawl_max_age: int = 3600000  # 1 Stunde Cache in Millisekunden
    firecrawl_max_results_per_store: int = 15  # Max Ergebnisse pro Supermarkt
    
    # Aldi-spezifische Einstellungen
    aldi_crawler_enabled: bool = True  # Aldi-Crawler aktivieren
    aldi_base_url: str = "https://www.aldi-sued.de"
    
    # Lidl-spezifische Einstellungen
    lidl_crawler_enabled: bool = True  # Lidl-Crawler aktivieren
    lidl_base_url: str = "https://www.lidl.de"
    lidl_billiger_montag_url: str = "https://www.lidl.de/c/billiger-montag/a10006065?channel=store&tabCode=Current_Sales_Week"
    
    # OpenAI-Konfiguration für intelligente Dateninterpretation
    openai_api_key: Optional[str] = None  # OpenAI API Key für LLM-basierte Extraktion
    
    # Server-Konfiguration
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = get_env_file()
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Log welche .env-Datei geladen wurde
        print(f"🔧 Loaded configuration from: {self.Config.env_file}")
        if not os.path.exists(self.Config.env_file):
            print(f"⚠️  Warning: {self.Config.env_file} not found, using defaults")

settings = Settings() 
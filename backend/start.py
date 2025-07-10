#!/usr/bin/env python3
"""
Backend Start-Script mit Multi-Environment Support

Dieses Script startet das FastAPI-Backend mit verschiedenen Umgebungskonfigurationen.

Verwendung:
    python start.py --env local     # Lädt .env.local
    python start.py --env dev       # Lädt .env.dev
    python start.py --env prod      # Lädt .env.prod
    
    # Oder mit Environment-Variable
    APP_ENV=dev python start.py
    
    # Mit zusätzlichen uvicorn-Optionen
    python start.py --env prod --host 0.0.0.0 --port 8080
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

def parse_arguments():
    """Parse Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(
        description="Starte das Preisvergleich-Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python start.py --env local                    # Lokale Entwicklung
  python start.py --env dev --reload            # Dev mit Auto-Reload
  python start.py --env prod --host 0.0.0.0     # Production
  
Environment-Dateien:
  .env.local   - Lokale Entwicklung (default)
  .env.dev     - Development-Server  
  .env.prod    - Production-Server
        """
    )
    
    # Environment-Auswahl
    parser.add_argument(
        "--env", 
        choices=["local", "dev", "prod"],
        default=os.getenv("APP_ENV", "local"),
        help="Environment (.env.{env} Datei wird geladen)"
    )
    
    # Uvicorn-spezifische Argumente
    parser.add_argument("--host", default=None, help="Host IP (default aus .env)")
    parser.add_argument("--port", type=int, default=None, help="Port (default aus .env)")
    parser.add_argument("--reload", action="store_true", help="Auto-reload bei Dateiänderungen")
    parser.add_argument("--workers", type=int, default=None, help="Anzahl Worker-Prozesse")
    parser.add_argument("--log-level", choices=["debug", "info", "warning", "error"], 
                       default=None, help="Log-Level")
    
    return parser.parse_args()

def check_env_file(env_name: str) -> bool:
    """Prüft ob die Environment-Datei existiert"""
    env_file = f".env.{env_name}"
    return Path(env_file).exists()

def create_sample_env_files():
    """Erstellt Beispiel-Environment-Dateien falls sie nicht existieren"""
    env_templates = {
        ".env.local": """# Lokale Entwicklungsumgebung
# FastAPI-Konfiguration
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-local-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=3600000
FIRECRAWL_MAX_RESULTS_PER_STORE=15

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
""",
        
        ".env.dev": """# Development-Server-Umgebung
# FastAPI-Konfiguration
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-dev-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=1800000
FIRECRAWL_MAX_RESULTS_PER_STORE=20

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de
""",
        
        ".env.prod": """# Production-Server-Umgebung
# FastAPI-Konfiguration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=WARNING

# Firecrawl-Konfiguration
FIRECRAWL_API_KEY=fc-your-production-api-key-here
FIRECRAWL_ENABLED=true
FIRECRAWL_MAX_AGE=7200000
FIRECRAWL_MAX_RESULTS_PER_STORE=30

# Aldi-Crawler
ALDI_CRAWLER_ENABLED=true
ALDI_BASE_URL=https://www.aldi-sued.de

# Production-spezifische Einstellungen
# Hier können weitere Prod-Einstellungen hinzugefügt werden
"""
    }
    
    created_files = []
    for file_path, content in env_templates.items():
        if not Path(file_path).exists():
            with open(file_path, 'w') as f:
                f.write(content)
            created_files.append(file_path)
    
    return created_files

def load_env_config(env_name: str) -> dict:
    """Lädt Konfiguration aus .env-Datei"""
    env_file = f".env.{env_name}"
    config = {}
    
    if Path(env_file).exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def build_uvicorn_command(args, env_config: dict) -> list:
    """Baut den uvicorn-Befehl zusammen (ARM64-optimiert für M1 Mac)"""
    # Für M1 Mac: Nutze explizit ARM64-Architektur um Kompatibilitätsprobleme zu vermeiden
    import platform
    if platform.machine() == 'arm64':
        cmd = ["arch", "-arm64", sys.executable, "-m", "uvicorn", "app.main:app"]
    else:
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app"]
    
    # Host
    host = args.host or env_config.get('HOST', '127.0.0.1')
    cmd.extend(["--host", host])
    
    # Port
    port = args.port or int(env_config.get('PORT', '8000'))
    cmd.extend(["--port", str(port)])
    
    # Reload (nur für local und dev)
    if args.reload or (args.env in ['local', 'dev'] and env_config.get('DEBUG', '').lower() == 'true'):
        cmd.append("--reload")
    
    # Workers (nur für prod empfohlen)
    if args.workers:
        cmd.extend(["--workers", str(args.workers)])
    elif args.env == 'prod' and not args.reload:
        # Default 4 workers für Production
        cmd.extend(["--workers", "4"])
    
    # Log-Level
    log_level = args.log_level or env_config.get('LOG_LEVEL', 'info').lower()
    cmd.extend(["--log-level", log_level])
    
    return cmd

def main():
    """Hauptfunktion"""
    args = parse_arguments()
    
    print(f"🚀 Starte Preisvergleich-Backend")
    print(f"📁 Environment: {args.env}")
    print(f"📋 Config-Datei: .env.{args.env}")
    print()
    
    # Prüfe ob Environment-Datei existiert
    if not check_env_file(args.env):
        print(f"⚠️  Environment-Datei .env.{args.env} nicht gefunden!")
        
        # Erstelle Beispiel-Dateien
        created_files = create_sample_env_files()
        if created_files:
            print(f"✅ Beispiel-Environment-Dateien erstellt:")
            for file in created_files:
                print(f"   - {file}")
            print()
            print("💡 Bitte bearbeite die .env-Dateien mit deinen echten API-Keys!")
            print("   Besonders wichtig: FIRECRAWL_API_KEY")
        
        if not check_env_file(args.env):
            print(f"❌ Kann ohne .env.{args.env} nicht starten!")
            sys.exit(1)
    
    # Setze APP_ENV Environment-Variable
    os.environ["APP_ENV"] = args.env
    
    # Lade Environment-Konfiguration
    env_config = load_env_config(args.env)
    
    # Wichtig: Setze alle Environment-Variablen aus der .env-Datei
    for key, value in env_config.items():
        os.environ[key] = value
    
    # Zeige wichtige Konfiguration an
    print("⚙️  Konfiguration:")
    print(f"   - Host: {args.host or env_config.get('HOST', '127.0.0.1')}")
    print(f"   - Port: {args.port or env_config.get('PORT', '8000')}")
    print(f"   - Debug: {env_config.get('DEBUG', 'false')}")
    print(f"   - Log-Level: {args.log_level or env_config.get('LOG_LEVEL', 'info')}")
    print(f"   - Firecrawl: {env_config.get('FIRECRAWL_ENABLED', 'false')}")
    
    if env_config.get('FIRECRAWL_API_KEY'):
        key = env_config['FIRECRAWL_API_KEY']
        masked_key = f"{key[:8]}{'*' * (len(key) - 12)}{key[-4:]}" if len(key) > 12 else "fc-****"
        print(f"   - API-Key: {masked_key}")
    else:
        print(f"   - ⚠️  API-Key: Nicht gesetzt!")
    
    print()
    
    # Baue uvicorn-Befehl
    cmd = build_uvicorn_command(args, env_config)
    
    print(f"🔧 Ausgeführter Befehl:")
    print(f"   {' '.join(cmd)}")
    print()
    print("🌐 Backend wird gestartet...")
    print("   Drücke Ctrl+C zum Beenden")
    print()
    
    try:
        # Starte uvicorn
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Backend gestoppt")
    except Exception as e:
        print(f"\n❌ Fehler beim Starten: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
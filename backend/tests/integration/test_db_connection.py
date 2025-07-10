#!/usr/bin/env python3
"""
Datenbank-Verbindungstest für Preisvergleich Backend
Testet verschiedene PostgreSQL-Konfigurationen und zeigt Debugging-Infos
"""

import asyncio
import sys
import os
from typing import Optional

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_database_urls():
    """Test verschiedene häufige PostgreSQL-Konfigurationen"""
    
    # Häufige Mac PostgreSQL-Setups
    test_configs = [
        # Docker-basierte Setups
        ("Docker Standard", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"),
        ("Docker Custom", "postgresql+asyncpg://postgres:password@localhost:5432/postgres"),
        
        # Homebrew-Installationen  
        ("Homebrew Default", "postgresql+asyncpg://$(whoami):@localhost:5432/postgres"),
        ("Homebrew User DB", "postgresql+asyncpg://$(whoami):@localhost:5432/$(whoami)"),
        
        # Postgres.app (beliebte Mac-App)
        ("Postgres.app Default", "postgresql+asyncpg://postgres:@localhost:5432/postgres"),
        ("Postgres.app User", "postgresql+asyncpg://$(whoami):@localhost:5432/postgres"),
        
        # Verschiedene Ports
        ("Alternative Port 5433", "postgresql+asyncpg://postgres:postgres@localhost:5433/postgres"),
        ("Alternative Port 5434", "postgresql+asyncpg://postgres:postgres@localhost:5434/postgres"),
        
        # Ohne Authentication
        ("No Auth", "postgresql+asyncpg://:@localhost:5432/postgres"),
        ("No Auth Alt Port", "postgresql+asyncpg://:@localhost:5433/postgres"),
    ]
    
    current_user = os.getenv('USER', 'unknown')
    
    for name, url_template in test_configs:
        # Replace $(whoami) with actual username
        url = url_template.replace('$(whoami)', current_user)
        print(f"\n🔍 Teste {name}: {url}")
        
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            
            async def test_single_connection(test_url):
                engine = create_async_engine(test_url, echo=False)
                try:
                    async with engine.begin() as conn:
                        # Basic connection test
                        result = await conn.execute(text('SELECT version(), current_user, current_database()'))
                        version, user, db = result.fetchone()
                        
                        print(f"   ✅ Verbindung erfolgreich!")
                        print(f"   📊 PostgreSQL: {version.split(',')[0]}")
                        print(f"   👤 User: {user}")
                        print(f"   🗄️  Database: {db}")
                        
                        # Check for our app database
                        result = await conn.execute(text("""
                            SELECT datname FROM pg_database 
                            WHERE datname LIKE '%preisvergleich%'
                        """))
                        app_dbs = [row[0] for row in result.fetchall()]
                        if app_dbs:
                            print(f"   🎯 Preisvergleich DBs gefunden: {app_dbs}")
                        else:
                            print(f"   ⚠️  Keine Preisvergleich-Datenbank gefunden")
                        
                        # Check user permissions
                        result = await conn.execute(text("""
                            SELECT rolname, rolsuper, rolcreaterole, rolcreatedb 
                            FROM pg_roles WHERE rolname = current_user
                        """))
                        role_info = result.fetchone()
                        if role_info:
                            rolname, super_user, create_role, create_db = role_info
                            print(f"   🔐 Berechtigungen: Super={super_user}, CreateDB={create_db}")
                        
                        return url, True
                        
                except Exception as e:
                    print(f"   ❌ Verbindung fehlgeschlagen: {e}")
                    return url, False
                finally:
                    await engine.dispose()
            
            # Run the async test
            result_url, success = asyncio.run(test_single_connection(url))
            if success:
                print(f"\n🎉 FUNKTIONIERT! Verwende diese URL:")
                print(f"DATABASE_URL={result_url}")
                return result_url
                
        except Exception as e:
            print(f"   💥 Setup-Fehler: {e}")
    
    print(f"\n❌ Keine funktionierende Datenbank-Konfiguration gefunden!")
    print(f"\n💡 Lösungsvorschläge:")
    print(f"1. Prüfe deine pgAdmin-Verbindungsdaten")
    print(f"2. Erstelle einen 'postgres' user: CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';")
    print(f"3. Erstelle die App-Datenbank: CREATE DATABASE preisvergleich_dev;")
    print(f"4. Oder teile mir deine pgAdmin-Verbindungsdaten mit")
    
    return None

def create_database_if_missing(working_url: str) -> bool:
    """Erstelle die App-Datenbank falls sie nicht existiert"""
    
    async def create_db():
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            
            # Connect to the working database (usually postgres)
            engine = create_async_engine(working_url, echo=False, isolation_level="AUTOCOMMIT")
            
            async with engine.begin() as conn:
                # Check if our app database exists
                result = await conn.execute(text("""
                    SELECT 1 FROM pg_database WHERE datname = 'preisvergleich_dev'
                """))
                
                if result.fetchone():
                    print("✅ preisvergleich_dev Datenbank existiert bereits")
                    return True
                else:
                    print("🔨 Erstelle preisvergleich_dev Datenbank...")
                    await conn.execute(text("CREATE DATABASE preisvergleich_dev"))
                    print("✅ preisvergleich_dev Datenbank erstellt!")
                    return True
                    
        except Exception as e:
            print(f"❌ Konnte Datenbank nicht erstellen: {e}")
            return False
        finally:
            await engine.dispose()
    
    return asyncio.run(create_db())

if __name__ == "__main__":
    print("🔍 Teste Datenbankverbindung für Preisvergleich Backend\n")
    
    working_url = test_database_urls()
    
    if working_url:
        # Try to create our app database
        app_url = working_url.replace('/postgres', '/preisvergleich_dev')
        
        if create_database_if_missing(working_url):
            print(f"\n🎯 Finale Datenbank-URL:")
            print(f"DATABASE_URL={app_url}")
            
            # Test the final URL
            print(f"\n🧪 Teste finale App-Datenbank...")
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            
            async def test_app_db():
                engine = create_async_engine(app_url, echo=False)
                try:
                    async with engine.begin() as conn:
                        await conn.execute(text('SELECT 1'))
                        print("✅ App-Datenbank funktioniert!")
                        return True
                except Exception as e:
                    print(f"❌ App-Datenbank Fehler: {e}")
                    return False
                finally:
                    await engine.dispose()
            
            if asyncio.run(test_app_db()):
                print(f"\n🚀 Backend kann gestartet werden mit:")
                print(f"export DATABASE_URL='{app_url}'")
                print(f"arch -arm64 python3 start.py")
    else:
        print(f"\n🔧 Starte Backend im Mock-Modus (ohne Datenbank):")
        print(f"export DATABASE_URL='sqlite+aiosqlite:///./test.db'")
        print(f"arch -arm64 python3 start.py") 
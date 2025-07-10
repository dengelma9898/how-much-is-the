-- Database User Separation Setup für Split Backend Architecture
-- Führe dieses Script als PostgreSQL Superuser aus

-- =====================================
-- 1. Read-only User für Client API
-- =====================================

-- Erstelle readonly User falls nicht vorhanden
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'preisvergleich_readonly') THEN
        CREATE USER preisvergleich_readonly WITH PASSWORD 'readonly_secure_password_2024';
    END IF;
END
$$;

-- Basis-Berechtigungen für readonly User
GRANT CONNECT ON DATABASE preisvergleich_dev TO preisvergleich_readonly;
GRANT USAGE ON SCHEMA public TO preisvergleich_readonly;

-- Nur SELECT-Rechte auf alle bestehenden Tabellen
GRANT SELECT ON ALL TABLES IN SCHEMA public TO preisvergleich_readonly;

-- Automatische SELECT-Rechte für zukünftige Tabellen
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO preisvergleich_readonly;

-- Spezifische Rechte für Sequences (für ID-Generierung in Abfragen)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO preisvergleich_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO preisvergleich_readonly;

-- =====================================
-- 2. Read-write User für Admin API
-- =====================================

-- Erstelle admin User falls nicht vorhanden
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'preisvergleich_admin') THEN
        CREATE USER preisvergleich_admin WITH PASSWORD 'admin_secure_password_2024';
    END IF;
END
$$;

-- Vollzugriff für admin User
GRANT CONNECT ON DATABASE preisvergleich_dev TO preisvergleich_admin;
GRANT USAGE ON SCHEMA public TO preisvergleich_admin;
GRANT CREATE ON SCHEMA public TO preisvergleich_admin;

-- Alle Rechte auf bestehende Tabellen
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO preisvergleich_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO preisvergleich_admin;

-- Automatische Rechte für zukünftige Objekte
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO preisvergleich_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO preisvergleich_admin;

-- =====================================
-- 3. Sicherheits-Konfiguration
-- =====================================

-- Entferne öffentliche Rechte (optional, je nach Setup)
-- REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
-- REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- =====================================
-- 4. Verifikation der Berechtigungen
-- =====================================

-- Zeige User-Berechtigungen an
\echo '=== READ-ONLY USER PERMISSIONS ==='
SELECT 
    grantee, 
    table_name, 
    privilege_type 
FROM information_schema.table_privileges 
WHERE grantee = 'preisvergleich_readonly'
ORDER BY table_name, privilege_type;

\echo '=== ADMIN USER PERMISSIONS ==='
SELECT 
    grantee, 
    table_name, 
    privilege_type 
FROM information_schema.table_privileges 
WHERE grantee = 'preisvergleich_admin'
ORDER BY table_name, privilege_type;

\echo '=== SETUP COMPLETE ==='
\echo 'Readonly User: preisvergleich_readonly (SELECT only)'
\echo 'Admin User: preisvergleich_admin (FULL access)'
\echo ''
\echo 'Update your .env files:'
\echo 'CLIENT_DATABASE_URL=postgresql+asyncpg://preisvergleich_readonly:readonly_secure_password_2024@localhost:5432/preisvergleich_dev'
\echo 'ADMIN_DATABASE_URL=postgresql+asyncpg://preisvergleich_admin:admin_secure_password_2024@localhost:5432/preisvergleich_dev' 
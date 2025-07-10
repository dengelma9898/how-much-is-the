#!/bin/bash

# Environment Setup Script für Preisvergleich Split Backend
# Erstellt die notwendigen .env-Dateien aus den Templates

echo "🔧 Setting up Environment Files für Split Backend Architecture"
echo ""

# Funktion um Benutzereingabe zu bekommen
get_input() {
    local prompt="$1"
    local default="$2"
    read -p "$prompt [$default]: " input
    echo "${input:-$default}"
}

# Funktion um sichere Passwörter zu generieren
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 1. CLIENT ENVIRONMENT SETUP
echo "📱 CLIENT API ENVIRONMENT SETUP"
echo "================================"

if [ ! -f ".env.client" ]; then
    echo "Creating .env.client from template..."
    cp env.client.example .env.client
    
    # Basic Configuration
    echo "Configure database for CLIENT API (readonly access):"
    db_host=$(get_input "Database Host" "localhost")
    db_port=$(get_input "Database Port" "5432")
    db_name=$(get_input "Database Name" "preisvergleich_dev")
    db_readonly_user=$(get_input "Readonly Username" "preisvergleich_readonly")
    db_readonly_pass=$(get_input "Readonly Password" "readonly_password")
    
    # Update .env.client
    sed -i.bak "s|postgresql+asyncpg://preisvergleich_readonly:readonly_password@localhost:5432/preisvergleich_dev|postgresql+asyncpg://${db_readonly_user}:${db_readonly_pass}@${db_host}:${db_port}/${db_name}|g" .env.client
    
    # Client API Setup complete
    
    echo "✅ .env.client created and configured!"
else
    echo "⚠️  .env.client already exists, skipping..."
fi

echo ""

# 2. ADMIN ENVIRONMENT SETUP  
echo "🔧 ADMIN API ENVIRONMENT SETUP"
echo "==============================="

if [ ! -f ".env.admin" ]; then
    echo "Creating .env.admin from template..."
    cp env.admin.example .env.admin
    
    # Database Configuration (same host/port as client, but admin user)
    echo "Configure database for ADMIN API (full access):"
    db_admin_user=$(get_input "Admin Username" "preisvergleich_admin")
    db_admin_pass=$(get_input "Admin Password" "admin_password")
    
    # Update .env.admin
    sed -i.bak "s|postgresql+asyncpg://preisvergleich_admin:admin_password@localhost:5432/preisvergleich_dev|postgresql+asyncpg://${db_admin_user}:${db_admin_pass}@${db_host}:${db_port}/${db_name}|g" .env.admin
    sed -i.bak "s|postgresql+asyncpg://preisvergleich_readonly:readonly_password@localhost:5432/preisvergleich_dev|postgresql+asyncpg://${db_readonly_user}:${db_readonly_pass}@${db_host}:${db_port}/${db_name}|g" .env.admin
    
    # Firecrawl API Key (optional)
    echo ""
    echo "Optional: Firecrawl API Key für Aldi Web-Scraping"
    firecrawl_key=$(get_input "Firecrawl API Key (leave empty to disable)" "")
    if [ ! -z "$firecrawl_key" ]; then
        sed -i.bak "s|FIRECRAWL_ENABLED=false|FIRECRAWL_ENABLED=true|g" .env.admin
        sed -i.bak "s|# FIRECRAWL_API_KEY=your_firecrawl_api_key_here|FIRECRAWL_API_KEY=${firecrawl_key}|g" .env.admin
    fi
    
    echo "✅ .env.admin created and configured!"
else
    echo "⚠️  .env.admin already exists, skipping..."
fi

echo ""

# 3. CLEANUP
echo "🧹 Cleaning up backup files..."
rm -f .env.client.bak .env.admin.bak

# 4. FINAL SUMMARY
echo "🎉 ENVIRONMENT SETUP COMPLETE!"
echo "==============================="
echo ""
echo "📋 Created Files:"
[ -f ".env.client" ] && echo "   ✅ .env.client (Client API - Read-only)"
[ -f ".env.admin" ] && echo "   ✅ .env.admin (Admin API - Full access)"
echo ""
echo "🚀 Next Steps:"
echo "   1. Review and adjust the .env files if needed"
echo "   2. Create database users: psql -f setup_database_users.sql"
echo "   3. Start APIs:"
echo "      ./start-client-api.sh    # Client API (Port 8001)"
echo "      ./start-admin-api.sh     # Admin API (Port 8002)"
echo ""
echo "🔐 Security Notes:"
echo "   - Client API: Read-only database access (Port 8001)"
echo "   - Admin API: Full database access + crawler functions (Port 8002)"
echo "   - Keep .env files secure and out of version control"
echo ""

# Check if database users exist
echo "💡 TIP: Run this to create database users:"
echo "   psql -U your_superuser -d ${db_name:-preisvergleich_dev} -f setup_database_users.sql" 
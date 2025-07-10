#!/bin/bash

# Preisvergleich Backend API Test Script
# 
# Dieses Skript testet alle wichtigen API-Endpoints mit curl
# Verwendung: ./test_api.sh [test_name]
# 
# Beispiele:
#   ./test_api.sh health     # Nur Health-Check
#   ./test_api.sh search     # Nur Search-Tests
#   ./test_api.sh crawl      # Nur Crawl-Tests
#   ./test_api.sh all        # Alle Tests (default)

set -e  # Exit on error

# Konfiguration
BASE_URL="http://127.0.0.1:8000"
POSTAL_CODE="10115"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Utility-Funktionen
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_test() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Führe HTTP-Request aus und zeige Ergebnis
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    print_test "$description"
    echo -e "${PURPLE}$method $endpoint${NC}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
                       -H "Content-Type: application/json" \
                       -d "$data" \
                       "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    # Trenne Response Body und Status Code
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    # Formatiere JSON wenn möglich
    if echo "$response_body" | jq . >/dev/null 2>&1; then
        echo "$response_body" | jq .
    else
        echo "$response_body"
    fi
    
    # Status Code prüfen
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        print_success "Status: $http_code"
    elif [[ $http_code -ge 400 && $http_code -lt 500 ]]; then
        print_warning "Client Error: $http_code"
    else
        print_error "Server Error: $http_code"
    fi
    
    echo
}

# Test-Funktionen
test_health() {
    print_header "HEALTH & INFO TESTS"
    
    make_request "GET" "/" "" "API Root"
    make_request "GET" "/api/v1/health" "" "Health Check"
    make_request "GET" "/api/v1/stores" "" "Liste alle Stores"
}

test_search() {
    print_header "SEARCH TESTS"
    
    make_request "GET" "/api/v1/search/database?query=Milch&postal_code=$POSTAL_CODE" "" "Datenbanksuche: Milch"
    make_request "GET" "/api/v1/search/database?query=Bio%20Äpfel&postal_code=$POSTAL_CODE&store_name=Lidl" "" "Datenbanksuche mit Filtern"
    
    # POST-Request für vollständige Suche
    search_data='{
        "query": "Hafermilch",
        "postal_code": "'$POSTAL_CODE'",
        "store_preferences": ["Lidl", "Aldi"],
        "price_filter": {
            "min_price": 0.5,
            "max_price": 3.0
        }
    }'
    make_request "POST" "/api/v1/search" "$search_data" "Vollständige Produktsuche"
    
    # Suche mit Umlauten
    make_request "GET" "/api/v1/search/database?query=Käse&postal_code=$POSTAL_CODE" "" "Suche mit Umlauten"
}

test_admin() {
    print_header "ADMIN TESTS"
    
    make_request "POST" "/api/v1/admin/stores/initialize" "" "Stores initialisieren"
    make_request "GET" "/api/v1/admin/system/overview" "" "System-Übersicht"
    make_request "GET" "/api/v1/admin/crawl/status/overview" "" "Crawl-Status Übersicht"
    make_request "GET" "/api/v1/admin/crawl/status" "" "Legacy Crawl-Status"
}

test_crawl() {
    print_header "MANUAL CRAWLING TESTS"
    
    # Lidl Crawl starten
    print_test "Starte Lidl Crawl..."
    crawl_response=$(curl -s -X POST "$BASE_URL/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=$POSTAL_CODE")
    echo "$crawl_response" | jq .
    
    # Crawl-ID extrahieren falls vorhanden
    if echo "$crawl_response" | jq -e '.crawl_id' >/dev/null 2>&1; then
        crawl_id=$(echo "$crawl_response" | jq -r '.crawl_id')
        print_success "Crawl gestartet mit ID: $crawl_id"
        
        # Status verfolgen
        sleep 2
        make_request "GET" "/api/v1/admin/crawl/status/$crawl_id" "" "Crawl-Status abrufen"
        make_request "GET" "/api/v1/admin/crawl/store/Lidl/status" "" "Lidl Store Status"
        
    else
        print_warning "Crawl konnte nicht gestartet werden oder bereits aktiv"
    fi
    
    # Rate Limiting Test
    print_test "Rate Limiting Test - Zweiter Lidl Crawl..."
    make_request "POST" "/api/v1/admin/crawl/trigger?store_name=Lidl&postal_code=$POSTAL_CODE" "" "Rate Limiting Test"
}

test_error_cases() {
    print_header "ERROR HANDLING TESTS"
    
    make_request "POST" "/api/v1/admin/crawl/trigger?store_name=InvalidStore&postal_code=$POSTAL_CODE" "" "Ungültiger Store"
    make_request "POST" "/api/v1/admin/crawl/trigger" "" "Fehlende Parameter"
    make_request "GET" "/api/v1/search/database?query=Milch&postal_code=invalid" "" "Ungültige PLZ"
    make_request "GET" "/api/v1/search/database?query=&postal_code=$POSTAL_CODE" "" "Leere Suchanfrage"
    make_request "GET" "/api/v1/nonexistent-endpoint" "" "404 Test"
}

test_performance() {
    print_header "PERFORMANCE TESTS"
    
    # Komplexe Suchanfrage
    complex_search='{
        "query": "Bio Vollkorn Haferflocken glutenfrei",
        "postal_code": "'$POSTAL_CODE'",
        "store_preferences": ["Lidl", "Aldi"],
        "price_filter": {
            "min_price": 1.0,
            "max_price": 8.0
        },
        "include_unavailable": true
    }'
    make_request "POST" "/api/v1/search" "$complex_search" "Komplexe Suchanfrage"
    
    # Mehrere schnelle Requests
    print_test "Mehrere schnelle Datenbanksuchen..."
    for term in "Milch" "Brot" "Käse" "Joghurt"; do
        make_request "GET" "/api/v1/search/database?query=$term&postal_code=$POSTAL_CODE" "" "Suche: $term"
    done
}

# Hauptfunktion
main() {
    local test_type=${1:-"all"}
    
    echo -e "${GREEN}🚀 Preisvergleich Backend API Tests${NC}"
    echo -e "${BLUE}Base URL: $BASE_URL${NC}"
    echo -e "${BLUE}Test PLZ: $POSTAL_CODE${NC}"
    echo
    
    # Prüfe ob Backend läuft
    if ! curl -s "$BASE_URL/api/v1/health" >/dev/null; then
        print_error "Backend ist nicht erreichbar unter $BASE_URL"
        echo "Starte das Backend mit: arch -arm64 python3 start.py --env local --reload"
        exit 1
    fi
    
    case $test_type in
        "health")
            test_health
            ;;
        "search")
            test_search
            ;;
        "admin")
            test_admin
            ;;
        "crawl")
            test_crawl
            ;;
        "errors")
            test_error_cases
            ;;
        "performance")
            test_performance
            ;;
        "all")
            test_health
            test_search
            test_admin
            test_crawl
            test_error_cases
            test_performance
            ;;
        *)
            echo "Verwendung: $0 [health|search|admin|crawl|errors|performance|all]"
            exit 1
            ;;
    esac
    
    print_header "TESTS ABGESCHLOSSEN"
    print_success "Alle Tests durchgeführt!"
    echo
    echo "💡 Weitere Tests:"
    echo "   - Swagger UI: $BASE_URL/docs"
    echo "   - Redoc: $BASE_URL/redoc"
    echo "   - OpenAPI JSON: $BASE_URL/openapi.json"
    echo
    echo "📝 HTTP-Client-Datei für VS Code: api_test.http"
    echo "   (Installiere 'REST Client' Extension)"
}

# Skript ausführen
main "$@" 
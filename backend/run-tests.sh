#!/bin/bash

# Test Runner für Preisvergleich Split Backend Architecture
# Usage: ./run-tests.sh [category] [options]

CATEGORY=${1:-all}
shift # Remove first argument, rest are pytest options

echo "🧪 Running Preisvergleich Tests..."
echo "📂 Category: $CATEGORY"
echo ""

case $CATEGORY in
    unit)
        echo "🔹 Running Unit Tests..."
        arch -arm64 python3 -m pytest tests/ -m "unit" -v $@
        ;;
    integration)
        echo "🔗 Running Integration Tests..."
        arch -arm64 python3 -m pytest tests/integration/ -v $@
        ;;
    crawlers)
        echo "🕷️ Running Crawler Tests..."
        arch -arm64 python3 -m pytest tests/crawlers/ -v $@
        ;;
    slow)
        echo "🐌 Running Slow Tests..."
        arch -arm64 python3 -m pytest tests/ -m "slow" -v $@
        ;;
    fast)
        echo "⚡ Running Fast Tests (no integration/crawler)..."
        arch -arm64 python3 -m pytest tests/ -m "not integration and not crawler and not slow" -v $@
        ;;
    all)
        echo "🚀 Running All Tests..."
        arch -arm64 python3 -m pytest tests/ -v $@
        ;;
    help|--help|-h)
        echo "🧪 Test Runner Usage:"
        echo ""
        echo "Categories:"
        echo "  unit          Run unit tests only"
        echo "  integration   Run integration tests"
        echo "  crawlers      Run crawler tests"
        echo "  slow          Run slow tests"
        echo "  fast          Run fast tests (excluding integration/crawler/slow)"
        echo "  all           Run all tests (default)"
        echo ""
        echo "Examples:"
        echo "  ./run-tests.sh                    # All tests"
        echo "  ./run-tests.sh integration        # Integration tests only"
        echo "  ./run-tests.sh fast               # Fast tests only"
        echo "  ./run-tests.sh all --maxfail=1    # Stop on first failure"
        echo "  ./run-tests.sh crawlers -k lidl   # Only Lidl crawler tests"
        echo ""
        ;;
    *)
        echo "❌ Unknown category: $CATEGORY"
        echo "Use './run-tests.sh help' for usage information"
        exit 1
        ;;
esac 
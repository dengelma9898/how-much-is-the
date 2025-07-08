#!/bin/bash

# Preisvergleich App - Complete Project Starter
echo "🚀 Starting Preisvergleich App Development Environment..."
echo ""

# Color codes for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -d "backend" ] || [ ! -d "android" ] || [ ! -d "ios" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Show menu
echo "🛒 Preisvergleich App Development Setup"
echo "======================================"
echo ""
echo "Please choose what you want to start:"
echo ""
echo "1) 🐍 Backend only (Python FastAPI)"
echo "2) 🤖 Android only (Kotlin + Compose)"
echo "3) 🍎 iOS only (Swift + SwiftUI)"
echo "4) 🌐 Backend + Android"
echo "5) 🌐 Backend + iOS"
echo "6) 🚀 Everything (Backend + Android + iOS)"
echo "7) ❓ Show project info"
echo "8) 🛠️  Setup development environment"
echo "9) ❌ Exit"
echo ""

read -p "Enter your choice (1-9): " choice

case $choice in
    1)
        print_status "Starting Backend..."
        cd backend && ./start.sh
        ;;
    2)
        print_status "Starting Android development..."
        cd android && ./start.sh
        ;;
    3)
        print_status "Starting iOS development..."
        cd ios && ./start.sh
        ;;
    4)
        print_status "Starting Backend + Android..."
        echo "Starting backend in background..."
        cd backend && ./start.sh &
        BACKEND_PID=$!
        sleep 3
        cd ../android && ./start.sh
        kill $BACKEND_PID
        ;;
    5)
        print_status "Starting Backend + iOS..."
        echo "Starting backend in background..."
        cd backend && ./start.sh &
        BACKEND_PID=$!
        sleep 3
        cd ../ios && ./start.sh
        kill $BACKEND_PID
        ;;
    6)
        print_status "Starting complete development environment..."
        echo "Starting backend in background..."
        cd backend && ./start.sh &
        BACKEND_PID=$!
        sleep 3
        print_success "Backend started on http://localhost:8000"
        
        echo ""
        print_status "Building Android project..."
        cd ../android && ./gradlew build
        
        echo ""
        print_status "Building iOS project..."
        cd ../ios && xcodebuild -project PreisvergleichApp.xcodeproj -scheme PreisvergleichApp build
        
        echo ""
        print_success "All projects ready!"
        echo ""
        echo "📚 Available resources:"
        echo "   Backend API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo "   Android: Open android/ in Android Studio"
        echo "   iOS: Open ios/PreisvergleichApp.xcodeproj in Xcode"
        
        echo ""
        echo "Press Enter to stop backend..."
        read
        kill $BACKEND_PID
        ;;
    7)
        echo ""
        echo "📱 Preisvergleich App - Project Information"
        echo "========================================="
        echo ""
        echo "🛠️  Tech Stack:"
        echo "   Backend: Python FastAPI 0.115.0"
        echo "   Android: Kotlin 2.1.0 + Jetpack Compose"
        echo "   iOS: Swift + SwiftUI (iOS 17+)"
        echo ""
        echo "📁 Project Structure:"
        echo "   backend/ - Python FastAPI backend"
        echo "   android/ - Android Kotlin app"
        echo "   ios/ - iOS Swift app"
        echo ""
        echo "🚀 Quick Start:"
        echo "   ./start-all.sh - This script"
        echo "   backend/start.sh - Start backend only"
        echo "   android/start.sh - Setup Android"
        echo "   ios/start.sh - Setup iOS"
        echo ""
        echo "📚 Documentation:"
        echo "   README.md - Complete setup guide"
        echo "   backend/README.md - Backend documentation"
        echo "   android/README.md - Android documentation"
        echo "   ios/README.md - iOS documentation"
        ;;
    8)
        print_status "Setting up development environment..."
        echo ""
        
        # Check Python
        if command -v python3 &> /dev/null; then
            print_success "Python 3 is installed: $(python3 --version)"
        else
            print_error "Python 3 is not installed"
        fi
        
        # Check pip
        if command -v pip3 &> /dev/null; then
            print_success "pip3 is available"
        else
            print_warning "pip3 not found in PATH"
            echo "   Add to PATH: export PATH=\"/Users/\$USER/Library/Python/3.9/bin:\$PATH\""
        fi
        
        # Check Android Studio
        if [ -d "/Applications/Android Studio.app" ]; then
            print_success "Android Studio is installed"
        else
            print_warning "Android Studio not found in /Applications/"
        fi
        
        # Check Xcode
        if command -v xcodebuild &> /dev/null; then
            print_success "Xcode is installed: $(xcodebuild -version | head -n1)"
        else
            print_warning "Xcode is not installed"
        fi
        
        echo ""
        print_status "Installing backend dependencies..."
        cd backend && pip3 install -r requirements.txt
        cd ..
        
        print_success "Development environment setup complete!"
        ;;
    9)
        print_status "Goodbye! 👋"
        exit 0
        ;;
    *)
        print_error "Invalid choice. Please enter 1-9."
        exit 1
        ;;
esac 
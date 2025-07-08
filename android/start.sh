#!/bin/bash

# Preisvergleich Android Start Script
echo "🤖 Starting Preisvergleich Android Development..."

# Check if we're in the correct directory
if [ ! -f "build.gradle.kts" ]; then
    echo "❌ Error: Please run this script from the android directory"
    echo "   Usage: cd android && ./start.sh"
    exit 1
fi

# Check if Gradle wrapper is available
if [ ! -f "gradlew" ]; then
    echo "❌ Error: Gradle wrapper not found"
    exit 1
fi

# Make gradlew executable
chmod +x gradlew

echo "📦 Building Android project..."
./gradlew build

echo ""
echo "✅ Android project is ready!"
echo ""
echo "🔧 Next steps:"
echo "   1. Open Android Studio"
echo "   2. Open this directory: $(pwd)"
echo "   3. Wait for Gradle sync to complete"
echo "   4. Run the app on emulator or device"
echo ""
echo "📱 Or use command line:"
echo "   ./gradlew installDebug  # Install on connected device"
echo "   ./gradlew assembleDebug # Build APK" 
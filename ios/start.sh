#!/bin/bash

# Preisvergleich iOS Start Script
echo "🍎 Starting Preisvergleich iOS Development..."

# Check if we're in the correct directory
if [ ! -f "PreisvergleichApp.xcodeproj/project.pbxproj" ]; then
    echo "❌ Error: Please run this script from the ios directory"
    echo "   Usage: cd ios && ./start.sh"
    exit 1
fi

# Check if Xcode is available
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode is not installed or xcodebuild not found"
    exit 1
fi

echo "🔨 Building iOS project for simulator..."
xcodebuild -project PreisvergleichApp.xcodeproj -scheme PreisvergleichApp -destination 'platform=iOS Simulator,name=iPhone 16' -configuration Debug build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ iOS project built successfully!"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Open Xcode:"
    echo "      open PreisvergleichApp.xcodeproj"
    echo ""
    echo "   2. Or build and run from command line:"
    echo "      xcodebuild -project PreisvergleichApp.xcodeproj -scheme PreisvergleichApp -destination 'platform=iOS Simulator,name=iPhone 16' run"
    echo ""
    echo "📱 Available simulators:"
    xcrun simctl list devices | grep iPhone
else
    echo ""
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi 
#!/bin/bash
# Build script for Raspberry Pi
# This script builds the application for Raspberry Pi using PyInstaller

echo "🔨 Building Cable Marker Detection System for Raspberry Pi..."

# Check if we're on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "   Building anyway, but some features may not work correctly..."
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected. Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found. Please create one first:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        exit 1
    fi
fi

# Install/upgrade PyInstaller
echo "📦 Installing/upgrading PyInstaller..."
pip install --upgrade pyinstaller

            # Build using the spec file
            echo "🔨 Building executable..."
            pyinstaller build.spec --clean

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📁 Executable location: dist/cable_marker_detector"
    echo ""
    echo "To run the application:"
    echo "   ./dist/cable_marker_detector"
else
    echo "❌ Build failed!"
    exit 1
fi



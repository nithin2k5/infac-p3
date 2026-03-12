#!/bin/bash
# ============================================================
#  build_mac.sh — Build Cable Marker Detector for macOS
# ============================================================
set -e

echo "🍎 Building Cable Marker Detector for macOS..."
echo ""

# ── Check Python virtual environment ─────────────────────────────────────────
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "⚙️  Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ No virtual environment found. Create one first:"
        echo "   python3 -m venv venv && source venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# ── Check required files ──────────────────────────────────────────────────────
if [ ! -f "weights-5.pt" ]; then
    echo "❌ weights-5.pt not found! Place the YOLO weights file in this directory."
    exit 1
fi

if [ ! -f "mac.spec" ]; then
    echo "❌ mac.spec not found! Make sure it exists in this directory."
    exit 1
fi

# ── Install / upgrade PyInstaller ─────────────────────────────────────────────
echo "📦 Ensuring PyInstaller is up to date..."
pip install --quiet --upgrade pyinstaller

# ── Build ─────────────────────────────────────────────────────────────────────
echo "🔨 Running PyInstaller..."
echo ""
pyinstaller mac.spec --clean --noconfirm

echo ""
if [ -d "dist/CableMarkerDetector.app" ]; then
    echo "✅ Build successful!"
    echo "📁 App bundle: dist/CableMarkerDetector.app"
    echo ""
    echo "To run:"
    echo "   open dist/CableMarkerDetector.app"
    echo ""
    echo "Note: On first run macOS may warn about an untrusted developer."
    echo "      Go to System Settings → Privacy & Security and click 'Open Anyway'."
elif [ -f "dist/cable_marker" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable: dist/cable_marker"
    echo ""
    echo "To run:"
    echo "   ./dist/cable_marker"
else
    echo "❌ Build produced no output. Check the PyInstaller logs above."
    exit 1
fi

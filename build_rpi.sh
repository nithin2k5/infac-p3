#!/bin/bash
# ============================================================
#  build_rpi.sh — Build Cable Marker Detector for Raspberry Pi
# ============================================================
set -e

echo "🍓 Building Cable Marker Detector for Raspberry Pi..."
echo ""

# ── Check we are on Raspberry Pi (warn, do not block) ────────────────────────
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This script is intended for Raspberry Pi."
    echo "   Cross-compiling on other Linux won't produce a working ARM binary."
    echo "   Continuing anyway — press Ctrl+C within 5 seconds to abort."
    sleep 5
fi

# ── Check Python virtual environment ─────────────────────────────────────────
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "⚙️  Activating virtual environment..."
        source venv/bin/activate
    else
        echo "❌ No virtual environment found. Create one first:"
        echo "   python3 -m venv venv && source venv/bin/activate"
        echo "   pip install -r requirements_rpi.txt"
        exit 1
    fi
fi

# ── Check required files ──────────────────────────────────────────────────────
if [ ! -f "weights-5.pt" ]; then
    echo "❌ weights-5.pt not found! Place the YOLO weights file in this directory."
    exit 1
fi

if [ ! -f "rpi.spec" ]; then
    echo "❌ rpi.spec not found! Make sure it exists in this directory."
    exit 1
fi

# ── Install / upgrade PyInstaller ─────────────────────────────────────────────
echo "📦 Ensuring PyInstaller is up to date..."
pip install --quiet --upgrade pyinstaller

# ── Build ─────────────────────────────────────────────────────────────────────
echo "🔨 Running PyInstaller..."
echo ""
pyinstaller rpi.spec --clean --noconfirm

echo ""
if [ -f "dist/cable_marker/cable_marker" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable: dist/cable_marker/cable_marker"
    echo ""

    # ── Desktop shortcut (optional) ──────────────────────────────────────────
    DESKTOP="$HOME/Desktop"
    if [ -d "$DESKTOP" ] && [ -f "CableMarkerDetector.desktop" ]; then
        echo "🔗 Installing desktop shortcut..."
        cp CableMarkerDetector.desktop "$DESKTOP/"
        chmod +x "$DESKTOP/CableMarkerDetector.desktop"

        APPS_DIR="$HOME/.local/share/applications"
        mkdir -p "$APPS_DIR"
        cp CableMarkerDetector.desktop "$APPS_DIR/"
        echo "   Shortcut placed on Desktop and in application menu."
    fi

    echo ""
    echo "To run the application:"
    echo "   ./dist/cable_marker/cable_marker"
    echo ""
    echo "Or double-click the desktop shortcut (if installed)."
else
    echo "❌ Build produced no output. Check the PyInstaller logs above."
    exit 1
fi

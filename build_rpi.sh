#!/bin/bash
# ============================================================
#  build_rpi.sh — Build INFAC Cable Marker Vision for Raspberry Pi
# ============================================================
set -e

echo "🍓 Building INFAC Cable Marker Vision for Raspberry Pi..."
echo ""

# ── Resolve project root (the directory this script lives in) ────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# ── Clean previous build artifacts (fix permission-denied from sudo builds) ───
echo "🧹 Cleaning previous build artifacts..."
for DIR in dist build __pycache__; do
    if [ -d "$DIR" ]; then
        # If we don't own it (e.g. previous run used sudo), fix ownership first
        if [ ! -w "$DIR" ]; then
            echo "   ⚠️  '$DIR' is not writable — fixing ownership with sudo..."
            sudo chown -R "$USER":"$USER" "$DIR"
        fi
        rm -rf "$DIR"
        echo "   ✔ Removed $DIR"
    fi
done
echo ""

# ── Build ─────────────────────────────────────────────────────────────────────
echo "🔨 Running PyInstaller..."
echo ""
pyinstaller rpi.spec --clean --noconfirm

echo ""
if [ -f "dist/cable_marker/cable_marker" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable: $SCRIPT_DIR/dist/cable_marker/cable_marker"
    echo ""

    # ── Fix executable permissions ────────────────────────────────────────────
    chmod +x "$SCRIPT_DIR/dist/cable_marker/cable_marker"
    echo "   ✔ Executable permissions set."

    # ── Create launcher wrapper script ────────────────────────────────────────
    # This wrapper ensures DISPLAY and env vars are correct when launched
    # from a .desktop file, autostart, or double-click — not just from a terminal.
    LAUNCHER="$SCRIPT_DIR/launch_infac.sh"
    cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
# INFAC Cable Marker Vision — launcher wrapper
# Ensures correct environment when started from desktop / autostart.
export DISPLAY="\${DISPLAY:-:0}"
export XAUTHORITY="\${XAUTHORITY:-\$HOME/.Xauthority}"

EXEC="$SCRIPT_DIR/dist/cable_marker/cable_marker"
LOG="$SCRIPT_DIR/infac_launch.log"

echo "[\$(date)] Starting INFAC..." >> "\$LOG"
"\$EXEC" >> "\$LOG" 2>&1
echo "[\$(date)] Exited with code \$?" >> "\$LOG"
LAUNCHER_EOF
    chmod +x "$LAUNCHER"
    echo "   ✔ Launcher wrapper created: $LAUNCHER"

    # ── Write .desktop files dynamically (no hardcoded username) ─────────────
    DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=INFAC Cable Marker Vision
Comment=INFAC Industrial Cable Marker Detection System
Exec=$LAUNCHER
Icon=$SCRIPT_DIR/dist/cable_marker/app_icon.png
Path=$SCRIPT_DIR/dist/cable_marker/
Terminal=false
Hidden=false
Categories=Utility;Application;
StartupNotify=true
X-GNOME-Autostart-enabled=true"

    # ── Desktop shortcut ──────────────────────────────────────────────────────
    DESKTOP_DIR="$HOME/Desktop"
    if [ -d "$DESKTOP_DIR" ]; then
        echo "$DESKTOP_CONTENT" > "$DESKTOP_DIR/INFAC-CableMarker.desktop"
        chmod +x "$DESKTOP_DIR/INFAC-CableMarker.desktop"
        echo "   ✔ Desktop shortcut: $DESKTOP_DIR/INFAC-CableMarker.desktop"
    fi

    # ── Application menu entry ────────────────────────────────────────────────
    APPS_DIR="$HOME/.local/share/applications"
    mkdir -p "$APPS_DIR"
    echo "$DESKTOP_CONTENT" > "$APPS_DIR/INFAC-CableMarker.desktop"
    echo "   ✔ App menu entry: $APPS_DIR/INFAC-CableMarker.desktop"

    # ── Autostart on boot (LXDE / Raspberry Pi OS desktop) ───────────────────
    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"
    echo "$DESKTOP_CONTENT" > "$AUTOSTART_DIR/infac-cable-marker.desktop"
    chmod +x "$AUTOSTART_DIR/infac-cable-marker.desktop"

    echo ""
    echo "🚀 Autostart configured:"
    echo "   ✔ $AUTOSTART_DIR/infac-cable-marker.desktop"
    echo "   The INFAC app will launch automatically on every graphical login."
    echo ""
    echo "   To disable autostart later:"
    echo "   rm $AUTOSTART_DIR/infac-cable-marker.desktop"
    echo ""
    echo "To run the application now:"
    echo "   $LAUNCHER"
    echo ""
    echo "Or double-click 'INFAC-CableMarker' on the Desktop."
    echo ""
    echo "Launch log (for debugging): $SCRIPT_DIR/infac_launch.log"
else
    echo "❌ Build produced no output. Check the PyInstaller logs above."
    exit 1
fi

#!/bin/bash
# Startup script for Cable Marker Detection on Raspberry Pi
# This script ensures proper environment and runs the application

echo "🍓 Cable Marker Detection System - Raspberry Pi"
echo "=============================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Some features may not work correctly"
    echo ""
fi

# Check if script is run with sudo (needed for GPIO)
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Not running as root"
    echo "   GPIO access requires root privileges or gpio group membership"
    echo ""
    echo "Options:"
    echo "  1. Run with sudo: sudo ./run_rpi.sh"
    echo "  2. Add user to gpio group: sudo usermod -a -G gpio $USER"
    echo "     (then logout and login again)"
    echo ""
    read -p "Do you want to run with sudo? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo "$0" "$@"
        exit $?
    fi
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run the installation script first"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import customtkinter" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "   Please run: pip install -r requirements_rpi.txt"
    exit 1
fi

# Check for display
if [ -z "$DISPLAY" ]; then
    echo "⚠️  No DISPLAY environment variable set"
    echo "   Setting DISPLAY=:0"
    export DISPLAY=:0
fi

# Run the application
echo "🚀 Starting application..."
echo ""
python app.py

# Cleanup on exit
echo ""
echo "✅ Application closed"




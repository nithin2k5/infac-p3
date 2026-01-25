#!/bin/bash
# Installation script for Cable Marker Detection on Raspberry Pi
# Run this script on your Raspberry Pi to set up everything

echo "🍓 Cable Marker Detection System - Raspberry Pi Installation"
echo "============================================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Installation will continue, but GPIO features may not work"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
fi

# Navigate to script directory
cd "$(dirname "$0")"

echo "Step 1: Updating system packages..."
echo "-----------------------------------"
sudo apt-get update
sudo apt-get upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
echo "-----------------------------------------"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-rpi.gpio \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    v4l-utils

echo ""
echo "Step 3: Creating virtual environment..."
echo "---------------------------------------"
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists, removing old one..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo ""
echo "Step 4: Upgrading pip..."
echo "------------------------"
pip install --upgrade pip setuptools wheel

echo ""
echo "Step 5: Installing Python dependencies..."
echo "-----------------------------------------"
pip install -r requirements_rpi.txt

echo ""
echo "Step 6: Setting up GPIO permissions..."
echo "--------------------------------------"
# Add user to gpio and video groups
sudo usermod -a -G gpio $USER
sudo usermod -a -G video $USER
echo "✅ User $USER added to gpio and video groups"
echo "   (You'll need to logout and login again for this to take effect)"

echo ""
echo "Step 7: Configuring camera..."
echo "-----------------------------"
# Enable camera if not already enabled
if ! grep -q "start_x=1" /boot/config.txt; then
    echo "Enabling camera in /boot/config.txt..."
    sudo bash -c 'echo "start_x=1" >> /boot/config.txt'
    sudo bash -c 'echo "gpu_mem=128" >> /boot/config.txt'
    echo "⚠️  Camera enabled. Reboot required!"
    REBOOT_NEEDED=1
fi

# Set up v4l2 for USB cameras
if command -v v4l2-ctl &> /dev/null; then
    echo "✅ v4l2-utils installed for USB camera support"
fi

echo ""
echo "Step 8: Testing installation..."
echo "-------------------------------"
python -c "
import sys
try:
    import customtkinter
    print('✅ CustomTkinter: OK')
except:
    print('❌ CustomTkinter: FAILED')
    sys.exit(1)

try:
    import cv2
    print('✅ OpenCV: OK')
except:
    print('❌ OpenCV: FAILED')
    sys.exit(1)

try:
    import numpy
    print('✅ NumPy: OK')
except:
    print('❌ NumPy: FAILED')
    sys.exit(1)

try:
    import roboflow
    print('✅ Roboflow: OK')
except:
    print('❌ Roboflow: FAILED')
    sys.exit(1)

try:
    import RPi.GPIO as GPIO
    print('✅ RPi.GPIO: OK')
except:
    print('⚠️  RPi.GPIO: Not available (install with: sudo apt-get install python3-rpi.gpio)')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================="
    echo "✅ Installation completed successfully!"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo "1. Logout and login again (for GPIO permissions)"
    if [ -n "$REBOOT_NEEDED" ]; then
        echo "2. Reboot your Raspberry Pi (for camera to work)"
        echo "   Run: sudo reboot"
    fi
    echo ""
    echo "To run the application:"
    echo "  ./run_rpi.sh"
    echo ""
    echo "Or run with sudo for full GPIO access:"
    echo "  sudo ./run_rpi.sh"
    echo ""
else
    echo ""
    echo "❌ Installation completed with errors"
    echo "   Please check the error messages above"
    exit 1
fi




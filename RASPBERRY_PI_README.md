# Raspberry Pi 5 Integration Guide

This guide details the steps to deploy the **Cable Marker Detection System** on a **Raspberry Pi 5** running Raspberry Pi OS (Bookworm).

## 📋 Prerequisites

- **Hardware**:
  - Raspberry Pi 5 (4GB or 8GB recommended)
  - Active Cooler (Recommended for sustained inference)
  - USB Camera or Raspberry Pi Camera Module 3
  - MicroSD Card (32GB+) with Raspberry Pi OS (Bookworm) 64-bit

- **Software**:
  - Python 3.11+ (Pre-installed on Bookworm)
  - Wayland/X11 Desktop Environment

## 🚀 Installation Steps

### 1. System Preparation
First, update your system to ensure all drivers are current.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

### 2. Dependencies
Install system-level dependencies required for OpenCV, GUI, and Camera handling.

```bash
sudo apt install -y \
    python3-venv \
    python3-pip \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    python3-rpi-lgpio  # Critical for Pi 5 GPIO support
```

> **Note**: On Raspberry Pi 5, the traditional `RPi.GPIO` library does not work directly due to the new RP1 I/O chip. We use `python3-rpi-lgpio` as a drop-in replacement.

### 3. Project Setup
Clone or copy the project to your Pi.

```bash
cd ~/
# If using git:
# git clone <your-repo-url> infac-p3
cd infac-p3
```

### 4. Method A: Quick Install (Script)
We have provided a script to automate the setup.

```bash
chmod +x install_rpi.sh
./install_rpi.sh
```

### 5. Method B: Manual Setup (Recommended for Pi 5)
Due to PEP 668 (managed environments) on Bookworm, use a virtual environment.

```bash
# Create virtual environment
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate

# Install Python requirements
pip install -r requirements_rpi.txt

# Install Pi 5 compatible GPIO library (if not using system package)
pip install rpi-lgpio
```

## 📷 Camera Setup for Pi 5

Raspberry Pi 5 uses `libcamera` by default. 

**USB Cameras**:
Work out of the box. Ensure they are accessible:
```bash
ls /dev/video*
```
You should see `/dev/video0` etc.

**Pi Camera Module 3**:
Ensure it's enabled in `conifg.txt` (usually automatic on Pi 5). 
If using OpenCV, you might need to use the `libcamerasrc` backend or legacy camera support is less relevant on Pi 5.
For best results with this app, verify your camera works with:
```bash
rpicam-hello
```

## 🔧 GPIO Configuration (Pi 5 Specific)

The GPIO pinout remains the standard 40-pin header.
- **GPIO 18, 23, 24** are used for output signals.
- **GND** is common ground.

The application uses `RPi.GPIO` style calls. On Pi 5, ensure `rpi-lgpio` is installed so these calls translate correctly to the new hardware.

## ▶️ Running the Application

1. **Activate Environment** (if not already):
   ```bash
   source venv/bin/activate
   ```

2. **Run the App**:
   ```bash
   python app.py
   ```

   *Or use the runner script:*
   ```bash
   ./run_rpi.sh
   ```

## ⚡ Performance Tips for Pi 5

1. **Active Cooling**: Ensure the official active cooler is running.
2. **Overclocking** (Optional but safe with cooler):
   Add to `/boot/firmware/config.txt`:
   ```ini
   arm_freq=2600
   gpu_freq=900
   ```
3. **App Settings**:
   - Use **Resolution**: 1280x720 (High) or 640x480 (Fast)
   - Ensure "Simulate" is OFF.

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **GPIO Error** | Ensure `python3-rpi-lgpio` is installed. Remove standard `RPi.GPIO` if it conflicts. |
| **Camera not found** | Check connection. Try `libcamera-hello` to verify hardware. |
| **Slow FPS** | Reduce resolution in `app.py` or check thermal throttling (`vcgencmd measure_temp`). |
| **"Externally Managed Environment"** | Always use `source venv/bin/activate` before installing pip packages. |

---
*Generated for Infac-P3 Project*

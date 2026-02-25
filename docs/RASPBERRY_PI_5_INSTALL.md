# 🍓 Raspberry Pi 5 Installation Guide

This guide is specifically optimized for **Raspberry Pi 5** running **Raspberry Pi OS (Bookworm)**.

The Raspberry Pi 5 introduces significant changes (Active Cooler, new GPIO chip, Wayland desktop, managed Python environments) that require specific setup steps differently from older models.

## 📋 Prerequisites

- **Hardware**:
  - Raspberry Pi 5 (4GB or 8GB)
  - Official Active Cooler (Highly recommended for ML inference)
  - MicroSD Card (32GB+) with Raspberry Pi OS Bookworm (64-bit)
  - Camera (USB Webcam or Pi Camera Module 3)

- **Software**:
  - Raspberry Pi OS (Bookworm) 64-bit
  - Internet connection

## 🚀 Option 1: Automatic Installation (Recommended)

We have updated the installation script to fully support Raspberry Pi 5.

1. **Clone the repository**:
   ```bash
   cd ~/
   git clone <your-repo-url> infac-p3
   cd infac-p3
   ```

2. **Run the installer**:
   ```bash
   chmod +x install_rpi.sh
   ./install_rpi.sh
   ```

   **What this does:**
   - Updates system packages
   - Installs `python3-rpi-lgpio` (Critical for Pi 5 GPIO)
   - Creates a Python virtual environment (`venv`) that inherits system packages
   - Installs all dependencies
   - Configures permissions and camera

3. **Reboot**:
   ```bash
   sudo reboot
   ```

---

## 🛠️ Option 2: Manual Installation

If you prefer to set up everything manually or encounter issues with the script, follow these steps.

### 1. Install System Dependencies

Raspberry Pi 5 needs specific system libraries for GPIO and OpenCV.

```bash
sudo apt update && sudo apt full-upgrade -y

sudo apt install -y \
    python3-venv \
    python3-pip \
    libopencv-dev \
    python3-opencv \
    python3-rpi-lgpio \
    libatlas-base-dev
```

> **Note:** `python3-rpi-lgpio` is the modern replacement for `RPi.GPIO` on Pi 5.

### 2. Set Up Virtual Environment

On Bookworm, you **must** use a virtual environment to avoid "Externally Managed Environment" errors.

```bash
cd ~/infac-p3

# Create venv with access to system packages (like opencv and rpi-lgpio)
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate
```

### 3. Install Python Libraries

```bash
pip install --upgrade pip
pip install -r requirements_rpi.txt
```

### 4. Configure Permissions

Add your user to necessary groups to access GPIO and Video without `sudo`.

```bash
sudo usermod -a -G gpio,video $USER
```
*You must logout and login again for this to work.*

---

## 🛠️ Option 3: Standalone "App" Installation (Exe-like)

If you want to run the application like a standalone program without typing commands:

1. **Build the App**:
   Run the build script to create a standalone executable.
   ```bash
   ./build_rpi.sh
   ```
   *This will take a few minutes.*

2. **Launch from Desktop**:
   - A shortcut **"Infac Cable Marker Detector"** will appear on your desktop.
   - Double-click it to run.
   - If asked, choose "Execute".

3. **Launch from Menu**:
   - The app will also appear in your "Raspberry Pi" start menu under **Applications** or **Accessories**.

**Note:** This creates a standalone Linux executable in `dist/cable_marker_detector`.

---

## ⚡ Performance & Tips for Pi 5

### 1. Cooling is Critical
The Pi 5 runs hot. Ensure your Active Cooler is working. The script/app should not cause throttling if cooled properly.
Check temp: `vcgencmd measure_temp`

### 2. GPIO Differences
The Pi 5 uses the RP1 chip for I/O.
- Old `RPi.GPIO` library wrappers might fail if not updated.
- We use `rpi-lgpio` which provides a compatible interface.
- If you see GPIO errors, ensure `python3-rpi-lgpio` is installed via apt.

### 3. Camera
- **USB Cameras**: Just work (`/dev/video0`).
- **Pi Camera 3**: Uses `libcamera`. OpenCV should pick it up if `libcamerasrc` is used or via legacy compatibility layer (which corresponds to `/dev/video0` usually if no other cams are present).

### 4. Display (Wayland)
Pi 5 uses Wayland by default.
- If the app window is black or transparent, try running with:
  ```bash
  GDK_BACKEND=x11 python app.py
  ```
- Or switch to X11 in `sudo raspi-config` > Advanced Options > Wayland > X11.

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'RPi'` | Run `sudo apt install python3-rpi-lgpio` |
| `error: externally-managed-environment` | Use the virtual environment! `source venv/bin/activate` |
| Camera lag | Lower resolution in `app.py` or check lighting |
| Permission denied (GPIO/Video) | Run `sudo ./run_rpi.sh` or relogin after `usermod` |

22# 🍓 Cable Marker Detection System - Raspberry Pi Guide

A professional cable marker detection system optimized for Raspberry Pi with real-time camera detection, GPIO control, and automatic marker recognition.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [GPIO Pin Configuration](#gpio-pin-configuration)
- [Camera Setup](#camera-setup)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)

---

## 🎯 Overview

This system detects cable markers (colored stripes) in real-time using a camera connected to a Raspberry Pi. When markers are detected, the system automatically controls GPIO pins based on the detected colors, making it perfect for industrial automation and cable management systems.

### Key Capabilities

- **Real-time Detection**: Live camera feed with automatic marker detection
- **Smart Detection**: Lightweight checks followed by full detection (0.5s countdown)
- **3-Stripe Grouping**: Automatically groups 3 stripes into 1 marking
- **GPIO Control**: Hardware control via GPIO pins based on detected colors
- **Scene Locking**: Prevents redundant detections until scene changes
- **Professional UI**: Clean, responsive interface optimized for Raspberry Pi

---

## ✨ Features

### Detection Features
- ✅ Real-time camera feed (30 FPS)
- ✅ Automatic marker detection with 0.5s countdown
- ✅ Accurate 3-stripe grouping algorithm
- ✅ Color filtering (White, Yellow, Blue, Pink, Green)
- ✅ Confidence-based filtering (30% minimum)
- ✅ Scene change detection
- ✅ Auto-save detection images

### Hardware Features
- ✅ GPIO pin control (GPIO 18, 23, 24)
- ✅ Color-to-pin mapping
- ✅ GPIO test functionality
- ✅ Automatic error recovery
- ✅ Thread-safe operations

### Performance Features
- ✅ Optimized for Raspberry Pi 4
- ✅ Low-latency camera (buffer size: 1)
- ✅ Image compression before API calls
- ✅ Multithreaded detection
- ✅ Smart detection intervals

---

## 📦 Prerequisites

### Hardware Requirements
- **Raspberry Pi 3 or newer** (Raspberry Pi 4 recommended for best performance)
- **Raspberry Pi OS** (Bullseye or newer)
- **4GB+ SD card** with Raspberry Pi OS installed
- **USB Camera** or **Raspberry Pi Camera Module**
- **Internet connection** (for Roboflow API)
- **Monitor, keyboard, and mouse** (or SSH access)
- **Optional**: GPIO hardware for control (relays, LEDs, etc.)

### Software Requirements
- Python 3.8+
- pip and venv
- Roboflow API key (configured in `roboflow_detector.py`)

---

## 🚀 Installation

### Step 1: Transfer Files to Raspberry Pi

**Option A: Using SCP (from your computer)**
```bash
scp -r infac-p3 pi@raspberrypi.local:~/
```

**Option B: Using USB Drive**
1. Copy the project folder to a USB drive
2. Plug USB drive into Raspberry Pi
3. Copy files to home directory:
   ```bash
   cp -r /media/pi/USB_DRIVE/infac-p3 ~/
   ```

**Option C: Using Git (if repository is available)**
```bash
git clone <repository-url>
cd infac-p3
```

### Step 2: Run Installation Script

```bash
cd ~/infac-p3
chmod +x install_rpi.sh
./install_rpi.sh
```

The installation script will:
- ✅ Update system packages
- ✅ Install Python dependencies
- ✅ Install OpenCV and camera drivers
- ✅ Install RPi.GPIO library
- ✅ Configure GPIO permissions
- ✅ Enable camera support
- ✅ Create virtual environment
- ✅ Install all Python packages

**⏱️ Installation Time**: 20-30 minutes on Raspberry Pi

### Step 3: Logout and Login

After installation, **logout and login again** for GPIO permissions to take effect:

```bash
logout
```

Or reboot:
```bash
sudo reboot
```

---

## 🔧 GPIO Pin Configuration

### Physical Pin Layout

| GPIO Pin | Physical Pin | Colors Detected |
|----------|--------------|-----------------|
| GPIO 18  | Pin 12       | Yellow, Green, Pink, Grey |
| GPIO 23  | Pin 16       | Blue, Green, Red, Grey |
| GPIO 24  | Pin 18       | White, Pink, Red, Grey |
| GND      | Pins 6,9,14  | Ground (connect all devices) |

### Pin Combinations by Color

| Color | GPIO Pins Activated |
|-------|---------------------|
| **Yellow** | GPIO 18 HIGH |
| **Blue**   | GPIO 23 HIGH |
| **Green**  | GPIO 18 + 23 HIGH |
| **White**  | GPIO 24 HIGH |
| **Pink**   | GPIO 18 + 24 HIGH |
| **Red**    | GPIO 23 + 24 HIGH |
| **Grey**   | GPIO 18 + 23 + 24 HIGH |

### Wiring Example

```
Raspberry Pi          External Device (Relay/LED)
─────────────────     ────────────────────────────
GPIO 18 (Pin 12) ──── IN1
GPIO 23 (Pin 16) ──── IN2
GPIO 24 (Pin 18) ──── IN3
GND (Pin 6)      ──── GND
```

---

## 📷 Camera Setup

### USB Camera Setup

1. **Plug in USB camera** to Raspberry Pi
2. **Check if detected**:
   ```bash
   ls /dev/video*
   ```
   You should see `/dev/video0` (or similar)

3. **Test camera**:
   ```bash
   v4l2-ctl --list-devices
   ffplay /dev/video0
   ```

4. **In the application**: Select "Camera 0" from dropdown

### Raspberry Pi Camera Module Setup

1. **Connect camera** to CSI port on Raspberry Pi
2. **Enable camera**:
   ```bash
   sudo raspi-config
   ```
   Navigate to: `Interface Options` → `Camera` → `Enable`

3. **Reboot**:
   ```bash
   sudo reboot
   ```

4. **Test camera**:
   ```bash
   raspistill -o test.jpg
   ```

### Camera Troubleshooting

**Camera not detected:**
```bash
# Check available cameras
v4l2-ctl --list-devices

# Install v4l2 utilities
sudo apt-get install v4l-utils

# Load camera module (for Pi Camera)
sudo modprobe bcm2835-v4l2

# Check permissions
sudo usermod -a -G video $USER
# Then logout and login again
```

---

## 🎮 Running the Application

### Method 1: Using Run Script (Recommended)

**Standard Mode (No GPIO):**
```bash
./run_rpi.sh
```

**With GPIO Control:**
```bash
sudo ./run_rpi.sh
```

The script will:
- Check if running on Raspberry Pi
- Activate virtual environment
- Set up display environment
- Run the application

### Method 2: Manual Run

```bash
# Activate virtual environment
source venv/bin/activate

# Set display (if needed)
export DISPLAY=:0

# Run application
python app.py
```

### Method 3: Run as Service (Production)

Create a systemd service file `/etc/systemd/system/cable-detector.service`:

```ini
[Unit]
Description=Cable Marker Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/infac-p3
Environment="DISPLAY=:0"
ExecStart=/home/pi/infac-p3/venv/bin/python /home/pi/infac-p3/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cable-detector.service
sudo systemctl start cable-detector.service
```

---

## 🔄 How It Works

### Detection Workflow

1. **Lightweight Check** (every 0.5s)
   - Low-resolution image check (480x360)
   - Fast stripe detection
   - No API call

2. **Countdown** (0.5 seconds)
   - When stripes detected
   - Visual countdown in UI
   - Prepares for capture

3. **Full Detection**
   - Captures frame at 1280x720
   - Sends to Roboflow API
   - Groups stripes into markings (3 stripes = 1 marking)
   - Draws detections on image

4. **Scene Lock**
   - Displays detected image
   - Locks scene until stripes disappear
   - Prevents redundant detections

5. **GPIO Control**
   - Sets GPIO pins based on detected color
   - Maintains pin state until next detection

### Detection Algorithm

```
Raw Detections → Filter by Confidence → Group by Proximity → Markings
     (API)           (30% min)          (250px vertical)    (3 stripes)
```

**Grouping Logic:**
- Vertical distance: ≤ 250px
- Horizontal distance: ≤ 500px
- Same color required
- Iterative clustering approach

### Time Intervals

| Stage | Duration | Description |
|-------|----------|-------------|
| Lightweight Check | 0.5s | Fast stripe detection |
| Countdown | 0.5s | Visual countdown |
| Full Detection | 1-3s | API call + processing |
| Scene Lock | Until change | Display results |

---

## ⚙️ Performance Optimization

### Hardware Optimization

**Raspberry Pi 4 Overclocking** (with active cooling):
Edit `/boot/config.txt`:
```ini
arm_freq=2000
gpu_freq=750
over_voltage=2
```

**Check CPU Temperature:**
```bash
vcgencmd measure_temp
```

**Monitor Performance:**
```bash
# CPU usage
top

# Memory usage
free -h

# Disk space
df -h
```

### Software Optimization

**Current Optimizations:**
- ✅ Camera buffer size: 1 (low latency)
- ✅ Frame resolution: 1280x720
- ✅ Detection interval: 0.5s smart detection
- ✅ Image compression (75% JPEG quality)
- ✅ Image resizing (max 1280px) before API call
- ✅ Multithreaded detection
- ✅ Scene locking (no redundant detection)

**For Better Performance:**
1. Use Raspberry Pi OS Lite (headless)
2. Close unnecessary applications
3. Use 720p camera resolution
4. Ensure adequate power supply (5V 3A)
5. Use active cooling for overclocking

---

## 🐛 Troubleshooting

### GPIO Issues

**GPIO not working:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again
logout

# Or run with sudo
sudo ./run_rpi.sh
```

**GPIO permission denied:**
```bash
# Check group membership
groups

# Verify GPIO access
ls -l /dev/gpiomem
```

### Camera Issues

**Camera not detected:**
```bash
# List available cameras
ls /dev/video*

# Check camera devices
v4l2-ctl --list-devices

# Install v4l2 utilities
sudo apt-get install v4l-utils

# Test camera
ffplay /dev/video0
```

**Camera permission denied:**
```bash
sudo usermod -a -G video $USER
logout  # Then login again
```

### Performance Issues

**Slow detection:**
- Check internet connection (Roboflow API)
- Reduce camera resolution
- Close other applications
- Check CPU temperature
- Ensure adequate power supply

**High CPU usage:**
```bash
# Check running processes
top

# Kill unnecessary processes
killall <process-name>

# Check memory
free -h
```

**Out of memory:**
- Increase swap size
- Close browser and other apps
- Use lighter detection model

### Import Errors

**Module not found:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements_rpi.txt
```

**Display errors:**
```bash
# Set display
export DISPLAY=:0

# Allow X11 forwarding
xhost +local:
```

---

## 🧪 Testing

### Test GPIO

**In Python:**
```python
from gpio_controller import GPIOController

gpio = GPIOController()
gpio.test_gpio()  # Blinks all pins 3 times
```

**In Application:**
- Click "Test GPIO" button in UI
- Watch status indicator

### Test Camera

```bash
# Test USB camera
ffplay /dev/video0

# Test Pi Camera
raspistill -o test.jpg

# Check camera info
v4l2-ctl --device=/dev/video0 --all
```

### Test Detection

1. Start application
2. Select camera from dropdown
3. Click "Start Camera"
4. Enable "Auto-Detect"
5. Point camera at cable markers
6. Watch for detection results

### System Status

```bash
# CPU temperature
vcgencmd measure_temp

# Memory usage
free -h

# Disk space
df -h

# Camera status
vcgencmd get_camera

# GPU memory
vcgencmd get_mem gpu
```

---

## 📊 Application Usage

### UI Components

1. **Camera Section**
   - Camera dropdown (select camera)
   - Start/Stop buttons
   - Capture Frame button
   - Auto-Detect toggle

2. **Display Area**
   - Live camera feed
   - Detected image display
   - Detection annotations

3. **Results Panel**
   - Marker count
   - Color filter dropdown
   - Detection details
   - Save button

4. **GPIO Section** (Raspberry Pi)
   - GPIO status indicator
   - Test GPIO button

### Workflow

1. **Start Camera**
   - Select camera from dropdown
   - Click "Start Camera"
   - Verify live feed appears

2. **Enable Auto-Detect**
   - Toggle "Auto-Detect" switch ON
   - System will automatically detect markers

3. **Monitor Detection**
   - Watch status messages
   - View detected markers in results panel
   - Check GPIO status (if using hardware)

4. **Filter Results**
   - Select color from filter dropdown
   - View filtered results

5. **Save Results**
   - Click "Save" button
   - Detection image saved to `detections/` folder

---

## ✅ Quick Start Checklist

- [ ] Raspberry Pi OS installed
- [ ] Internet connection working
- [ ] Camera connected and tested
- [ ] Project files transferred to Raspberry Pi
- [ ] `install_rpi.sh` script executed successfully
- [ ] Logged out and back in (for GPIO permissions)
- [ ] Virtual environment activated
- [ ] Application runs without errors
- [ ] Camera detected in application
- [ ] GPIO test passes (if using hardware)
- [ ] Auto-detect working
- [ ] Markers detected correctly

---

## 📝 Configuration

### GPIO Pin Configuration

Edit `app.py` line 54:
```python
self.gpio_controller = GPIOController(pin1=18, pin2=23, pin3=24)
```

### Detection Parameters

Edit `app.py` lines 47-51:
```python
self.detector = RoboflowDetector(
    min_confidence=0.3,              # Minimum confidence (30%)
    grouping_distance=250,            # Vertical grouping distance (px)
    grouping_horizontal_distance=500  # Horizontal grouping distance (px)
)
```

### Camera Settings

Edit `app.py` lines 723-730:
```python
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
self.camera.set(cv2.CAP_PROP_FPS, 30)
self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

---

## 🔐 Security Notes

- **GPIO Access**: Requires root or gpio group membership
- **API Key**: Keep Roboflow API key secure
- **Network**: Ensure secure network connection for API calls
- **Permissions**: Review file permissions in production

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review installation logs
3. Test components individually (camera, GPIO, detection)
4. Check system resources (CPU, memory, temperature)

---

## 🔄 Updates

**Update Application:**
```bash
cd ~/infac-p3
git pull origin main  # If using git
pip install -r requirements_rpi.txt --upgrade
```

**Update System:**
```bash
sudo apt-get update
sudo apt-get upgrade
```

---

## 📄 License

[Add your license information here]

---

## 🙏 Acknowledgments

- Roboflow for detection API
- OpenCV for image processing
- CustomTkinter for modern UI
- Raspberry Pi Foundation for hardware platform

---

**Made with ❤️ for Raspberry Pi**

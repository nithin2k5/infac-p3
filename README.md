# 📡 cable marker

A real-time cable marker detection system using **local YOLO inference** — no cloud API, no credits required. Built with Python, OpenCV, CustomTkinter, and Ultralytics YOLO.

---

## ✨ Features

- ✅ **Credit-Free** — Runs 100% locally using `weights-5.pt`
- ✅ Real-time detection from camera or video file
- ✅ Color filtering (White, Yellow, Blue, Pink, Green)
- ✅ Region of Interest (ROI) selection
- ✅ 3-stripe grouping algorithm (3 stripes = 1 marking)
- ✅ GPIO hardware control (Raspberry Pi)
- ✅ Classic dark professional UI

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation — Desktop (macOS/Linux)](#installation--desktop-macoslinux)
- [Installation — Raspberry Pi](#installation--raspberry-pi)
- [Running the Application](#running-the-application)
- [GPIO Pin Configuration](#gpio-pin-configuration)
- [Detection Parameters](#detection-parameters)
- [Troubleshooting](#troubleshooting)

---

## 📦 Prerequisites

### Hardware
- Any PC / Mac **or** Raspberry Pi 3/4/5
- USB camera or Raspberry Pi Camera Module

### Software
- Python 3.9+
- `pip` and `venv`

---

## 💻 Installation — Desktop (macOS/Linux)

```bash
git clone https://github.com/nithin2k5/infac-p3.git
cd infac-p3

python3 -m venv venv
source venv/bin/activate

pip install ultralytics customtkinter pillow opencv-python
python app.py
```

---

## 🍓 Installation — Raspberry Pi

### Step 1 — Clone the repo

```bash
git clone https://github.com/nithin2k5/infac-p3.git
cd infac-p3
```

### Step 2 — Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-tk libopencv-dev
```

### Step 3 — Create virtual environment and install packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install ultralytics customtkinter pillow opencv-python RPi.GPIO
```

> **Note:** If OpenCV fails to install, use the headless build:
> ```bash
> pip install opencv-python-headless
> ```

### Step 4 — Run the app

```bash
source venv/bin/activate
python app.py
```

### Auto-start on Boot (optional)

```bash
# Create launcher script
cat > ~/start_cable_marker.sh << 'EOF'
#!/bin/bash
cd ~/infac-p3
source venv/bin/activate
python app.py
EOF

chmod +x ~/start_cable_marker.sh
```

Add to your Pi's desktop autostart or crontab as needed.

---

## 🎮 Running the Application

| Platform | Command |
|----------|---------|
| macOS/Linux | `python app.py` |
| Raspberry Pi | `source venv/bin/activate && python app.py` |
| Raspberry Pi (with GPIO) | `sudo python app.py` |

---

## 🔧 GPIO Pin Configuration

| GPIO Pin | Physical Pin | Colors |
|----------|-------------|--------|
| GPIO 18  | Pin 12      | Yellow, Green, Pink, Grey |
| GPIO 23  | Pin 16      | Blue, Green, Red, Grey |
| GPIO 24  | Pin 18      | White, Pink, Red, Grey |
| GND      | Pins 6/9/14 | Ground |

### Color → Pin Mapping

| Color | Pins Activated |
|-------|---------------|
| Yellow | GPIO 18 |
| Blue   | GPIO 23 |
| Green  | GPIO 18 + 23 |
| White  | GPIO 24 |
| Pink   | GPIO 18 + 24 |
| Red    | GPIO 23 + 24 |
| Grey   | GPIO 18 + 23 + 24 |

---

## ⚙️ Detection Parameters

Adjust in `app.py`:

```python
self.detector = RoboflowDetector(
    min_confidence=0.70,              # Minimum confidence (70%)
    grouping_distance=250,            # Vertical grouping distance (px)
    grouping_horizontal_distance=500  # Horizontal grouping distance (px)
)
```

Adjust in `roboflow_detector.py`:

```python
results = self.model(frame, conf=self.min_confidence, iou=0.45, verbose=False)
```

---

## 🔄 Updating

```bash
cd ~/infac-p3
git pull origin main
source venv/bin/activate
pip install --upgrade ultralytics
```

---

## 🐛 Troubleshooting

### Camera not detected
```bash
ls /dev/video*
v4l2-ctl --list-devices
sudo usermod -a -G video $USER
# Then logout and log back in
```

### GPIO permission denied
```bash
sudo usermod -a -G gpio $USER
# Then logout and log back in
# Or run: sudo python app.py
```

### Module not found
```bash
source venv/bin/activate
pip install ultralytics customtkinter pillow opencv-python RPi.GPIO
```

### Display issues (headless Pi)
```bash
export DISPLAY=:0
xhost +local:
python app.py
```

---

## 📁 Project Structure

```
infac-p3/
├── app.py                  # Main application & UI
├── roboflow_detector.py    # Local YOLO inference engine
├── gpio_controller.py      # Raspberry Pi GPIO control
├── weights-5.pt            # YOLO model weights
└── detections/             # Auto-saved detection images
```

---

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) for local inference
- [OpenCV](https://opencv.org) for image processing
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern UI
- Raspberry Pi Foundation

---

**Made with ❤️ — runs fully offline, no API credits needed**

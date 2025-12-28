# Cable Marker Detection System - Usage Guide

## 🚀 Quick Start

### Launch Application
```bash
cd /Users/nithinkumark/Developer/python/infac-p3
source venv/bin/activate
python app.py
```

## 🎯 Features

### **Roboflow-Powered Detection**
The system uses Roboflow workflow API for accurate detection of:
- **Yellow** markers
- **Blue** markers
- **Green** markers
- **Pink** markers
- **White** markers

### **Cloud-Based Detection**
- Uses Roboflow's trained workflow model
- No local model training required
- Fast and accurate detection via API

## 📖 How to Use

### 1. Load Image
- Click **"📁 Load Image"**
- Select an image with cable markers

### 2. Detect Markers
- Click **"🔍 Detect Markers"**
- Wait for Roboflow API to process the image
- View results in real-time

### 3. View Results
Each detected marker shows:
- **Cable Number** (1, 2, 3, etc.)
- **Marker Color** (Yellow, Blue, Green, Pink, White)
- **Stripe Count** (typically 3 bars: `|||`)
- **Confidence Score** (percentage)
- **Position & Size** (bounding box)

### 4. Export Results
- **"💾 Save Results"**: Save annotated image with markers highlighted
- **"📊 Export Data"**: Export detection data as JSON or TXT

## 🎨 Visual Output

The app displays:
- **Colored Bounding Boxes** around each marker (matching the marker color)
- **Labels** showing "Cable 1: Yellow", "Cable 2: Blue", etc.
- **Confidence Scores** below each box
- **Bar Patterns** (|||) indicating stripe count

## 📊 Example Output

```
Cable #1
═════════════════════════
Marker Color: Yellow
Stripe Count: 3
Bar Pattern: |||
Confidence: 95.2%
Marker Position: (120, 45)
Marker Size: 68x89px

Cable #2
═════════════════════════
Marker Color: Blue
Stripe Count: 3
Bar Pattern: |||
Confidence: 93.8%
Marker Position: (245, 180)
Marker Size: 62x94px

... (and so on for each cable)
```

## 🔧 Detection Engine

### **Roboflow Workflow API**
- Uses cloud-based Roboflow workflow for detection
- High accuracy detection
- Fast inference via API
- No local model training required

## 💡 Tips for Best Results

1. **Good Lighting**: Ensure markers are well-lit
2. **Clear Images**: Use high-resolution images
3. **Focused View**: Markers should be visible and in focus
4. **Multiple Angles**: Test with different camera angles
5. **Internet Connection**: Requires internet for API calls

## 🐛 Troubleshooting

### Roboflow API Not Working
- Check internet connection
- Verify API key is valid in `roboflow_detector.py`
- Check if `requests` library is installed: `pip list | grep requests`

### Low Confidence Scores
- Ensure image quality is good
- Check if markers are clearly visible
- Try with different lighting conditions

## 📈 Performance

- **Detection Speed**: Depends on API response time
- **Accuracy**: High accuracy via trained workflow
- **Confidence**: Typically 80-99%
- **Requires**: Internet connection for API calls

## 🎯 Color Classes

The system detects:
- Yellow striped markers (|||)
- Blue striped markers (|||)
- Green striped markers (|||)
- Pink striped markers (|||)
- White striped markers (|||)

Each marker typically has 3 stripes and is wrapped around cables.

---
**Built with Roboflow API, CustomTkinter, and OpenCV**

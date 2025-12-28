# Cable Marker Detection System - Professional Edition

An advanced Python application for automatically detecting and identifying striped cable markers using computer vision and machine learning techniques.

## 🎯 Features

### **Automatic Detection**
- **No Manual Annotation Required**: Automatically detects striped markers without circles or annotations
- **Stripe Pattern Recognition**: Identifies multi-colored stripe patterns on cables
- **Intelligent Filtering**: Distinguishes markers from cables, backgrounds, and artifacts
- **High Precision**: Optimized for accuracy with minimal false positives

### **Professional UI**
- **Modern Design**: Built with CustomTkinter for a professional appearance
- **Dark Mode Interface**: Easy on the eyes with clean, modern aesthetics
- **Real-time Feedback**: Live status updates and progress indicators
- **Responsive Layout**: Adaptive design for different screen sizes

### **Advanced Analysis**
- **Component ID Tracking**: Each marker gets a unique identifier
- **Color Pattern Detection**: Identifies stripe sequences (e.g., Green→Black→Purple)
- **Confidence Scoring**: Reports detection confidence percentage
- **Bounding Box Visualization**: Precise localization of each marker
- **Bar Pattern Output**: Visual representation as `|||` patterns

### **Export Capabilities**
- **Save Annotated Images**: Export results with visual annotations
- **JSON Data Export**: Machine-readable detection data
- **Text Reports**: Human-readable detection reports
- **Timestamp Tracking**: Automatic timestamp on all exports

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd infac-p3
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage

1. **Launch the application:**
```bash
python app.py
```

2. **Load your image:**
   - Click **"📁 Load Image"**
   - Select an image containing cable markers

3. **Detect markers:**
   - Click **"🔍 Detect Markers"**
   - Wait for automatic detection to complete

4. **View results:**
   - See detected markers highlighted with green boxes
   - Review detailed information in the sidebar
   - Check color patterns and confidence scores

5. **Export results:**
   - **"💾 Save Results"**: Save annotated image
   - **"📊 Export Data"**: Export detection data (JSON/TXT)

## 🔬 How It Works

### Detection Pipeline

1. **Preprocessing**
   - Convert to HSV color space
   - Apply edge detection (Canny)
   - Enhance structural features

2. **Region Identification**
   - Find potential marker regions using morphology
   - Filter by size, aspect ratio, and shape
   - Eliminate false positives (cables, background)

3. **Color Analysis**
   - Divide regions into vertical strips
   - Detect dominant color in each strip
   - Build color sequence pattern

4. **Validation**
   - Calculate detection confidence
   - Verify stripe patterns
   - Remove low-confidence detections

5. **Results**
   - Generate unique component IDs
   - Create bounding boxes
   - Output bar patterns (|||)

### Detection Rules

- **Precision First**: Avoids false positives on cable insulation
- **Stripe-Level Detection**: Analyzes texture and color patterns
- **Independent Components**: Each marker is separate, even if similar
- **Multi-Cable Support**: Handles multiple cables in one image
- **Robust Filtering**: Ignores lighting artifacts and reflections

## 📊 Output Format

Each detected marker includes:

```
Component ID: 1
Type: Cable Marker
Color Pattern: Green → Black → Purple
Stripe Count: 3
Confidence: 87.5%
Position: (245, 180)
Size: 35x78px
Bar: |||
```

## 🎨 Supported Color Patterns

- Red, Orange, Yellow
- Green, Blue, Purple
- Brown, Black, White, Gray
- Multi-stripe combinations

## 📋 Requirements

- Python 3.10+
- OpenCV >= 4.10.0
- NumPy >= 2.0.0
- Pillow >= 10.4.0
- CustomTkinter >= 5.2.0
- scikit-image >= 0.22.0

## 🏗️ Architecture

```
app.py          - Main application with professional UI
detector.py     - Core detection algorithms
requirements.txt - Python dependencies
```

## 🔧 Configuration

Detection parameters can be adjusted in `detector.py`:
- Minimum marker area: `300-15000 px²`
- Aspect ratio range: `0.8-6.0`
- Confidence threshold: `15%+`
- Color coverage: `15%+ per strip`

## 📝 License

See LICENSE file for details.

## 🙏 Credits

Built with modern computer vision techniques and professional UI design principles.
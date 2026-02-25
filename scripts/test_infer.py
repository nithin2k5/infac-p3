import cv2
from roboflow_detector import RoboflowDetector
detector = RoboflowDetector()
try:
    img = cv2.imread('detections/20260122_145330_WhatsAppImage2026-01-21at20420_0markers.jpg')
    if img is not None:
        print("Testing single frame inference...")
        res = detector.detect_single_frame(img)
        print("Result single frame:", res)
        print("Testing standard batch predict...")
        res2 = detector.detect_markers(img)
        print("Result detect_markers:", res2)
except Exception as e:
    print("Error:", e)

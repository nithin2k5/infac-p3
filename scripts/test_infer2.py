import cv2
from roboflow_detector import RoboflowDetector
detector = RoboflowDetector()
try:
    img = cv2.imread('detections/20260122_145330_WhatsAppImage2026-01-21at20420_0markers.jpg')
    res = detector.model.predict("detections/20260122_145330_WhatsAppImage2026-01-21at20420_0markers.jpg", confidence=50)
    print("OBJECT:", res)
    print("JSON:", res.json())
except Exception as e:
    print("Error:", e)

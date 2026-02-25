import cv2
from roboflow_detector import RoboflowDetector

# Read an image for a single detection test instead of live webcam
img = cv2.imread('detections/20260122_145330_WhatsAppImage2026-01-21at20420_0markers.jpg')
detector = RoboflowDetector()
res = detector.detect_single_frame(img)
print("Single frame (client.infer) result:", res)

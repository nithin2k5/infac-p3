import cv2
from roboflow_detector import RoboflowDetector
detector = RoboflowDetector()
print('Model type:', type(detector.model))

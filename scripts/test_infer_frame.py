import cv2
import time
from roboflow_detector import RoboflowDetector

detector = RoboflowDetector()

def start():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not open.")
        return
        
    print("Capturing 5 frames...")
    for _ in range(5):
        ret, frame = cap.read()
        if not ret: break
        
        start_t = time.time()
        dets = detector.detect_single_frame(frame)
        print(f"Elapsed: {time.time() - start_t:.2f}s | Dets: {len(dets)}")
        print(dets)
        
    cap.release()
    
start()

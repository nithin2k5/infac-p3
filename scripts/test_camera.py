import cv2
import time
from roboflow_detector import RoboflowDetector

def cb(detections, metadata):
    print("DETECTIONS RECVD:", detections)
def frame_cb(frame, metadata):
    pass

detector = RoboflowDetector()
detector.start_webrtc_stream(frame_callback=frame_cb, detection_callback=cb)
time.sleep(10)
detector.stop_webrtc_stream()

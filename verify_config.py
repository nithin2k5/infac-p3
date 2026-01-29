
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from roboflow_detector import RoboflowDetector

try:
    detector = RoboflowDetector()
    print(f"Model Version: {detector.roboflow_model_version}")
    print(f"Min Confidence: {detector.min_confidence}")
    
    if detector.roboflow_model_version == "13" and detector.min_confidence == 0.60:
        print("SUCCESS: Configuration verified.")
    else:
        print("FAILURE: Configuration mismatch.")
        print(f"Expected Version: 13, Got: {detector.roboflow_model_version}")
        print(f"Expected Confidence: 0.60, Got: {detector.min_confidence}")

except Exception as e:
    print(f"Error during verification: {e}")

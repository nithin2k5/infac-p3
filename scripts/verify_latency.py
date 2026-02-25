
import cv2
import numpy as np
import time
from unittest.mock import MagicMock
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from roboflow_detector import RoboflowDetector

def test_resize_logic():
    print("🧪 Starting Resizing Logic Verification...")
    
    # Initialize detector
    detector = RoboflowDetector()
    
    # Mock the internal initialized flags and clients to avoid real API calls
    detector._roboflow_initialized = True
    detector._inference_initialized = True
    
    # Mock model
    mock_model = MagicMock()
    # Mock return value for predict
    mock_prediction = MagicMock()
    mock_prediction.json.return_value = {'predictions': []}
    mock_model.predict.return_value = mock_prediction
    detector.model = mock_model
    
    # Mock client
    mock_client = MagicMock()
    mock_client.infer.return_value = {'predictions': []}
    detector.client = mock_client
    
    # creates large 4k image
    large_image = np.zeros((2160, 3840, 3), dtype=np.uint8)
    print(f"🖼️  Created large test image: {large_image.shape}")
    
    # Test detect_markers (Static)
    print("\n--- Testing detect_markers (Static) ---")
    detector.detect_markers(large_image)
    
    # Verify predict was called
    if mock_model.predict.called:
        # Check arguments
        args, kwargs = mock_model.predict.call_args
        # The first arg is the temp file path
        temp_path = args[0]
        print(f"✅ Predict called with file: {temp_path}")
        
        # Read the file to check dimensions
        processed_img = cv2.imread(temp_path)
        if processed_img is not None:
            h, w = processed_img.shape[:2]
            print(f"📏 Processed Image Dimensions: {w}x{h}")
            if w <= 640 and h <= 640:
                print("✅ PASSED: Image was resized to <= 640px")
            else:
                print(f"❌ FAILED: Image was not resized properly ({w}x{h})")
        else:
             print("❌ FAILED: Could not read temp file")
    else:
        print("❌ FAILED: Predict was not called")

    # Test detect_single_frame (Streaming)
    print("\n--- Testing detect_single_frame (Streaming) ---")
    detector.detect_single_frame(large_image)
    
    if mock_client.infer.called:
        args, kwargs = mock_client.infer.call_args
        # The first arg is the frame
        passed_frame = args[0]
        h, w = passed_frame.shape[:2]
        print(f"📏 Inferred Frame Dimensions: {w}x{h}")
        
        if w <= 640 and h <= 640:
            print("✅ PASSED: Frame was resized to <= 640px")
        else:
            print(f"❌ FAILED: Frame was not resized properly ({w}x{h})")
    else:
        print("❌ FAILED: Client.infer was not called")

if __name__ == "__main__":
    test_resize_logic()

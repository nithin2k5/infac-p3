"""
Local Cable Marker Detector using YOLO
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Callable, Tuple
import threading
import os

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("WARNING: ultralytics is not installed. Please install it with `pip install ultralytics`.")

class RoboflowDetector:
    """
    Cable marker detector using local YOLO model (weights-5.pt).
    Replaces the old Roboflow API.
    """
    
    def __init__(self, min_confidence=0.70, grouping_distance=250, grouping_horizontal_distance=500, max_area_ratio=0.15):
        self.min_confidence = min_confidence
        self.grouping_distance = grouping_distance
        self.grouping_horizontal_distance = grouping_horizontal_distance
        self.max_area_ratio = max_area_ratio
        
        self.model = None
        self._inference_initialized = False
        self._initialized = False
        
        # Load local YOLO model
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights-5.pt')
        if YOLO_AVAILABLE:
            if os.path.exists(model_path):
                print(f"🔄 Initializing local YOLO model from {model_path}...")
                try:
                    self.model = YOLO(model_path)
                    self._inference_initialized = True
                    self._initialized = True
                    print("✅ Local YOLO model initialized successfully.")
                except Exception as e:
                    print(f"❌ Failed to load YOLO model: {e}")
            else:
                print(f"❌ Local model weights not found at {model_path}!")
        
        print("\n🔧 Initialization Summary:")
        print(f"   Local YOLO Inference: {'✅ ENABLED' if self._inference_initialized else '❌ DISABLED'}")
        if self._inference_initialized:
            print(f"   Confidence threshold: {min_confidence * 100}%")

    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """Detect markers in a static image using local YOLO model."""
        return self.detect_single_frame(image)

    def detect_single_frame(self, frame: np.ndarray) -> List[Dict]:
        """Detect markers in a single frame using local YOLO model."""
        if not self._inference_initialized or self.model is None:
            print("⚠️ Local model not initialized")
            return []

        if frame is None or frame.size == 0:
            return []

        try:
            # We can run inference directly with strict NMS (iou) and higher confidence
            results = self.model(frame, conf=self.min_confidence, iou=0.45, verbose=False)
            
            markers = []
            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                names = result.names
                
                orig_h, orig_w = frame.shape[:2]
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    
                    if conf < self.min_confidence:
                        continue
                        
                    xyxy = box.xyxy[0].cpu().numpy() # x_min, y_min, x_max, y_max
                    x_min, y_min, x_max, y_max = xyxy
                    w = x_max - x_min
                    h = y_max - y_min
                    
                    # Filter by size
                    area_ratio = (w * h) / (orig_w * orig_h)
                    if area_ratio > self.max_area_ratio:
                        continue
                        
                    color = str(names[cls_id])
                    
                    markers.append({
                        "component_id": len(markers) + 1,
                        "component_type": "Cable Marker",
                        "primary_color": color,
                        "color_pattern": [color],
                        "bounding_box": {"x": int(x_min), "y": int(y_min), "width": int(w), "height": int(h)},
                        "confidence": round(conf * 100, 2),
                        "center": (int(x_min + w / 2), int(y_min + h / 2)),
                        "stripe_count": 3
                    })
                    
            return markers

        except Exception as e:
            print(f"⚠️ Inference failed: {e}")
            return []

    def _group_stripes_into_markings(self, stripes: List[Dict]) -> List[Dict]:
        """Group stripes into markings: 3 stripes = 1 marking"""
        if not stripes:
            return []
        
        grouped = []
        used_indices = set()
        
        # Sort stripes by position
        sorted_stripes = sorted(stripes, key=lambda s: (s["center"][1], s["center"][0]))
        
        for i, stripe in enumerate(sorted_stripes):
            if i in used_indices:
                continue
            
            # Start a new group
            group = [stripe]
            group_indices = {i}
            used_indices.add(i)
            color = stripe.get("primary_color", "Unknown")
            
            # Find nearby stripes of same color
            added_new = True
            iterations = 0
            max_iterations = 20
            
            while added_new and iterations < max_iterations:
                added_new = False
                iterations += 1
                
                for j, other_stripe in enumerate(sorted_stripes):
                    if j in used_indices:
                        continue
                    
                    other_color = other_stripe.get("primary_color", "Unknown")
                    if color.lower() != other_color.lower():
                        continue
                    
                    other_center = other_stripe["center"]
                    
                    # Check if close to any stripe in group
                    is_close = False
                    for group_stripe in group:
                        group_center = group_stripe["center"]
                        vertical_dist = abs(other_center[1] - group_center[1])
                        horizontal_dist = abs(other_center[0] - group_center[0])
                        
                        if (vertical_dist < self.grouping_distance and 
                            horizontal_dist < self.grouping_horizontal_distance):
                            is_close = True
                            break
                    
                    if is_close:
                        group.append(other_stripe)
                        group_indices.add(j)
                        used_indices.add(j)
                        added_new = True
            
            # Create marking from group
            if group:
                min_x = min(s["bounding_box"]["x"] for s in group)
                min_y = min(s["bounding_box"]["y"] for s in group)
                max_x = max(s["bounding_box"]["x"] + s["bounding_box"]["width"] for s in group)
                max_y = max(s["bounding_box"]["y"] + s["bounding_box"]["height"] for s in group)
                
                avg_confidence = sum(s["confidence"] for s in group) / len(group)
                
                marking = {
                    "component_id": len(grouped) + 1,
                    "component_type": "Cable Marker",
                    "primary_color": color,
                    "color_pattern": [color],
                    "bounding_box": {
                        "x": min_x,
                        "y": min_y,
                        "width": max_x - min_x,
                        "height": max_y - min_y
                    },
                    "confidence": round(avg_confidence, 2),
                    "center": ((min_x + max_x) // 2, (min_y + max_y) // 2),
                    "stripe_count": len(group),
                    "stripes_in_group": len(group)
                }
                
                grouped.append(marking)
        
        # Sort by position
        grouped.sort(key=lambda m: (m["center"][1], m["center"][0]))
        for idx, marking in enumerate(grouped):
            marking["component_id"] = idx + 1
        
        return grouped
    
    def draw_detections(self, image: np.ndarray, markers: List[Dict]) -> np.ndarray:
        """Draw detection results on image"""
        result = image.copy()
        
        # Generate dynamic color from class name
        def get_color_from_name(name: str):
            """Generate a consistent color from a string using hash"""
            import hashlib
            hash_val = int(hashlib.md5(name.encode()).hexdigest(), 16)
            # Generate BGR color
            b = (hash_val & 0xFF)
            g = ((hash_val >> 8) & 0xFF)
            r = ((hash_val >> 16) & 0xFF)
            # Ensure color is bright enough
            return (max(b, 100), max(g, 100), max(r, 100))
        
        for marker in markers:
            bbox = marker["bounding_box"]
            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            
            color_name = marker.get("primary_color", "Unknown")
            box_color = get_color_from_name(color_name)  # Dynamic color generation
            
            # Draw bounding box
            cv2.rectangle(result, (x, y), (x + w, y + h), box_color, 3)
            
            # Draw label with class name from model
            label = f"{color_name}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            cv2.rectangle(result, (x, y - 35), (x + label_size[0] + 10, y - 5), (0, 0, 0), -1)
            cv2.putText(result, label, (x + 5, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw confidence
            conf_text = f"{marker['confidence']:.1f}%"
            cv2.putText(result, conf_text, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return result

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get the current capabilities of the detector
        """
        return {
            "static_images": self._inference_initialized,
            "real_time_streaming": self._inference_initialized,
            "batch_video_processing": False,
            "webrtc_available": False,
            "inference_sdk": False,
            "roboflow_sdk": False,
            "local_yolo": self._inference_initialized
        }

    def start_webrtc_stream(self, *args, **kwargs):
        pass

    def stop_webrtc_stream(self):
        pass

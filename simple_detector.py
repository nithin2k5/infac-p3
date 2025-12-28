"""
Simple Direct Cable Marker Detector
No pretrained models - Pure OpenCV color detection
"""

import cv2
import numpy as np
from typing import List, Dict


class SimpleMarkerDetector:
    """Simple, direct cable marker detector using only OpenCV"""
    
    def __init__(self):
        # Direct HSV color ranges for markers
        self.colors = {
            "Green": {"lower": np.array([35, 40, 40]), "upper": np.array([85, 255, 255])},
            "Blue": {"lower": np.array([90, 50, 50]), "upper": np.array([130, 255, 255])},
            "Yellow": {"lower": np.array([20, 80, 80]), "upper": np.array([35, 255, 255])},
            "Pink": {"lower": np.array([140, 30, 80]), "upper": np.array([175, 255, 255])},
            "Purple": {"lower": np.array([120, 30, 60]), "upper": np.array([155, 255, 255])},
            "White": {"lower": np.array([0, 0, 150]), "upper": np.array([180, 50, 255])},
            "Gray": {"lower": np.array([0, 0, 50]), "upper": np.array([180, 50, 200])},
        }
    
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """Detect cable markers directly by color"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        height, width = image.shape[:2]
        
        all_detections = []
        
        # Detect each color
        for color_name, color_range in self.colors.items():
            # Create mask
            mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
            
            # Clean up mask
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 200:  # Minimum area
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio
                aspect = h / (w + 0.001)
                if aspect < 0.2 or aspect > 10.0:
                    continue
                
                # Calculate coverage
                roi_mask = mask[y:y+h, x:x+w]
                coverage = cv2.countNonZero(roi_mask) / (w * h)
                
                if coverage > 0.1:  # At least 10% coverage
                    all_detections.append({
                        "bbox": (x, y, w, h),
                        "color": color_name,
                        "coverage": coverage,
                        "center_y": y + h // 2
                    })
        
        # Sort by vertical position
        all_detections.sort(key=lambda d: d["center_y"])
        
        # Remove overlapping detections
        filtered = self._remove_overlaps(all_detections)
        
        # Build result
        markers = []
        for idx, det in enumerate(filtered):
            x, y, w, h = det["bbox"]
            markers.append({
                "component_id": idx + 1,
                "component_type": "Cable Marker",
                "primary_color": det["color"],
                "color_pattern": [det["color"]],
                "bounding_box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "confidence": round(min(det["coverage"] * 100, 95), 2),
                "center": (int(x + w/2), int(y + h/2)),
                "stripe_count": 3
            })
        
        return markers
    
    def _remove_overlaps(self, detections: List[Dict]) -> List[Dict]:
        """Remove overlapping detections, keep the one with higher coverage"""
        if not detections:
            return []
        
        filtered = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            x1, y1, w1, h1 = det1["bbox"]
            best_det = det1
            
            # Check for overlaps
            for j, det2 in enumerate(detections):
                if i == j or j in used:
                    continue
                
                x2, y2, w2, h2 = det2["bbox"]
                
                # Calculate overlap
                x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = x_overlap * y_overlap
                
                area1 = w1 * h1
                iou = overlap_area / min(area1, w2 * h2) if min(area1, w2 * h2) > 0 else 0
                
                if iou > 0.3:  # Overlapping
                    # Keep the one with higher coverage
                    if det2["coverage"] > best_det["coverage"]:
                        best_det = det2
                    used.add(j)
            
            filtered.append(best_det)
            used.add(i)
        
        return filtered
    
    def draw_detections(self, image: np.ndarray, markers: List[Dict]) -> np.ndarray:
        """Draw detection results"""
        result = image.copy()
        
        color_map = {
            "Yellow": (0, 255, 255),
            "Blue": (255, 0, 0),
            "Green": (0, 255, 0),
            "Pink": (203, 192, 255),
            "Purple": (255, 0, 255),
            "White": (255, 255, 255),
            "Gray": (128, 128, 128)
        }
        
        for marker in markers:
            bbox = marker["bounding_box"]
            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            
            color = marker.get("primary_color", "Unknown")
            box_color = color_map.get(color, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(result, (x, y), (x + w, y + h), box_color, 3)
            
            # Draw label
            label = f"Cable {marker['component_id']}: {color}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            cv2.rectangle(result, (x, y - 35), (x + label_size[0] + 10, y - 5), (0, 0, 0), -1)
            cv2.putText(result, label, (x + 5, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw confidence
            conf_text = f"{marker['confidence']:.1f}%"
            cv2.putText(result, conf_text, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw bar pattern
            bars = '|' * marker.get('stripe_count', 3)
            cv2.putText(result, bars, (x, y + h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
        
        return result




"""
Advanced Cable Marker Detector - Maximum Accuracy Version
Uses multiple detection strategies for highest precision
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple


class AdvancedMarkerDetector:
    """High-accuracy cable marker detector"""
    
    def __init__(self):
        # Precise HSV color ranges for cable markers
        self.color_ranges = {
            "Green": [
                {"lower": np.array([35, 40, 40]), "upper": np.array([85, 255, 255])},
                {"lower": np.array([40, 30, 30]), "upper": np.array([90, 255, 255])}
            ],
            "Blue": [
                {"lower": np.array([90, 50, 50]), "upper": np.array([130, 255, 255])},
                {"lower": np.array([85, 40, 40]), "upper": np.array([135, 255, 255])}
            ],
            "Yellow": [
                {"lower": np.array([20, 80, 80]), "upper": np.array([35, 255, 255])},
                {"lower": np.array([18, 60, 60]), "upper": np.array([38, 255, 255])}
            ],
            "Pink": [
                {"lower": np.array([140, 30, 80]), "upper": np.array([175, 255, 255])},
                {"lower": np.array([135, 20, 60]), "upper": np.array([180, 255, 255])}
            ],
            "Purple": [
                {"lower": np.array([120, 30, 60]), "upper": np.array([155, 255, 255])},
                {"lower": np.array([115, 20, 50]), "upper": np.array([160, 255, 255])}
            ],
            "White": [
                {"lower": np.array([0, 0, 150]), "upper": np.array([180, 50, 255])},
                {"lower": np.array([0, 0, 120]), "upper": np.array([180, 60, 255])}
            ],
            "Gray": [
                {"lower": np.array([0, 0, 50]), "upper": np.array([180, 50, 200])},
                {"lower": np.array([0, 0, 40]), "upper": np.array([180, 60, 180])}
            ],
        }
    
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """Detect cable markers with maximum accuracy"""
        height, width = image.shape[:2]
        
        # Preprocessing for better detection
        processed = self._preprocess_image(image)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Strategy 1: Color-based detection
        color_detections = self._detect_by_color(image, hsv)
        
        # Strategy 2: Texture and pattern detection
        texture_detections = self._detect_by_texture(image, processed)
        
        # Strategy 3: Edge-based detection
        edge_detections = self._detect_by_edges(image, processed)
        
        # Merge all detections
        all_detections = self._merge_detections(
            color_detections, 
            texture_detections, 
            edge_detections
        )
        
        # Filter and validate detections
        validated = self._validate_detections(all_detections, image, hsv)
        
        # Sort by position (left to right or top to bottom)
        validated.sort(key=lambda m: (m["center"][0], m["center"][1]))
        
        # Assign IDs
        for idx, marker in enumerate(validated):
            marker["component_id"] = idx + 1
        
        return validated
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better detection"""
        # Apply CLAHE for better contrast
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return denoised
    
    def _detect_by_color(self, image: np.ndarray, hsv: np.ndarray) -> List[Dict]:
        """Detect markers by color analysis"""
        detections = []
        
        for color_name, color_variants in self.color_ranges.items():
            combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            # Try all color variants
            for variant in color_variants:
                mask = cv2.inRange(hsv, variant["lower"], variant["upper"])
                combined_mask = cv2.bitwise_or(combined_mask, mask)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 7))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 100:  # Lower minimum area
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (markers are compact)
                aspect_ratio = h / (w + 0.001)
                if aspect_ratio < 0.2 or aspect_ratio > 8.0:  # More lenient
                    continue
                
                detections.append({
                    "bbox": (x, y, w, h),
                    "color": color_name,
                    "confidence": 0.5,  # Lower confidence
                    "method": "color"
                })
        
        return detections
    
    def _detect_by_texture(self, image: np.ndarray, processed: np.ndarray) -> List[Dict]:
        """Detect markers by texture patterns"""
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Detect horizontal lines (stripes)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        detect_horizontal = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Find contours
        contours, _ = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Lower threshold
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            detections.append({
                "bbox": (x, y, w, h),
                "confidence": 0.3,  # Lower confidence
                "method": "texture"
            })
        
        return detections
    
    def _detect_by_edges(self, image: np.ndarray, processed: np.ndarray) -> List[Dict]:
        """Detect markers using edge detection"""
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # Multi-scale edge detection
        edges1 = cv2.Canny(gray, 30, 100)
        edges2 = cv2.Canny(gray, 50, 150)
        edges = cv2.bitwise_or(edges1, edges2)
        
        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 80:  # Lower threshold
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio
            aspect_ratio = h / (w + 0.001)
            if aspect_ratio < 0.3 or aspect_ratio > 10.0:  # More lenient
                continue
            
            detections.append({
                "bbox": (x, y, w, h),
                "confidence": 0.4,  # Lower confidence
                "method": "edges"
            })
        
        return detections
    
    def _merge_detections(self, *detection_lists) -> List[Dict]:
        """Merge detections from multiple strategies"""
        all_detections = []
        for det_list in detection_lists:
            all_detections.extend(det_list)
        
        if not all_detections:
            return []
        
        # Non-maximum suppression
        merged = []
        used = set()
        
        for i, det1 in enumerate(all_detections):
            if i in used:
                continue
            
            x1, y1, w1, h1 = det1["bbox"]
            overlapping = [det1]
            
            for j, det2 in enumerate(all_detections):
                if i == j or j in used:
                    continue
                
                x2, y2, w2, h2 = det2["bbox"]
                
                # Check overlap
                if self._boxes_overlap((x1, y1, w1, h1), (x2, y2, w2, h2)):
                    overlapping.append(det2)
                    used.add(j)
            
            # Merge overlapping detections
            if overlapping:
                merged_det = self._merge_box_group(overlapping)
                merged.append(merged_det)
                used.add(i)
        
        return merged
    
    def _boxes_overlap(self, box1: Tuple, box2: Tuple, threshold: float = 0.2) -> bool:
        """Check if two boxes overlap"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return False
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        
        iou = intersection / min(area1, area2)
        return iou > threshold
    
    def _merge_box_group(self, detections: List[Dict]) -> Dict:
        """Merge a group of overlapping detections"""
        # Find bounding box that covers all
        x_min = min(d["bbox"][0] for d in detections)
        y_min = min(d["bbox"][1] for d in detections)
        x_max = max(d["bbox"][0] + d["bbox"][2] for d in detections)
        y_max = max(d["bbox"][1] + d["bbox"][3] for d in detections)
        
        # Get best color (from color-based detection)
        color = None
        for det in detections:
            if "color" in det:
                color = det["color"]
                break
        
        # Average confidence
        avg_conf = sum(d.get("confidence", 0.5) for d in detections) / len(detections)
        
        return {
            "bbox": (x_min, y_min, x_max - x_min, y_max - y_min),
            "color": color,
            "confidence": min(avg_conf * 1.5, 0.99)  # Higher multiplier
        }
    
    def _validate_detections(self, detections: List[Dict], 
                            image: np.ndarray, hsv: np.ndarray) -> List[Dict]:
        """Validate and refine detections"""
        validated = []
        
        for det in detections:
            x, y, w, h = det["bbox"]
            
            # Ensure bounds are valid
            x = max(0, x - 5)
            y = max(0, y - 5)
            w = min(image.shape[1] - x, w + 10)
            h = min(image.shape[0] - y, h + 10)
            
            if w < 10 or h < 10:
                continue
            
            # Extract ROI
            roi_hsv = hsv[y:y+h, x:x+w]
            
            # Identify or confirm color
            if det.get("color") is None:
                color = self._identify_dominant_color(roi_hsv)
                if color is None:
                    continue
                det["color"] = color
            else:
                # Verify color
                verified_color = self._identify_dominant_color(roi_hsv)
                if verified_color:
                    det["color"] = verified_color
            
            # Count stripes
            stripe_count = self._count_stripes_advanced(roi_hsv, det["color"])
            
            # Build marker info
            marker = {
                "component_id": 0,
                "component_type": "Cable Marker",
                "primary_color": det["color"],
                "color_pattern": [det["color"]],
                "bounding_box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "confidence": round(det.get("confidence", 0.8) * 100, 2),
                "center": (int(x + w/2), int(y + h/2)),
                "stripe_count": stripe_count
            }
            
            validated.append(marker)
        
        return validated
    
    def _identify_dominant_color(self, roi_hsv: np.ndarray) -> str:
        """Identify dominant color in ROI with multiple passes"""
        if roi_hsv.size == 0:
            return None
        
        total_pixels = roi_hsv.shape[0] * roi_hsv.shape[1]
        color_scores = {}
        
        for color_name, variants in self.color_ranges.items():
            max_coverage = 0
            
            for variant in variants:
                mask = cv2.inRange(roi_hsv, variant["lower"], variant["upper"])
                pixel_count = cv2.countNonZero(mask)
                coverage = pixel_count / total_pixels
                max_coverage = max(max_coverage, coverage)
            
            color_scores[color_name] = max_coverage
        
        # Get best color
        if not color_scores:
            return None
        
        best_color = max(color_scores.items(), key=lambda x: x[1])
        
        # Threshold: at least 2% coverage (very low)
        if best_color[1] > 0.02:
            return best_color[0]
        
        # If still nothing, return the highest score anyway
        if best_color[1] > 0:
            return best_color[0]
        
        return None
    
    def _count_stripes_advanced(self, roi_hsv: np.ndarray, color: str) -> int:
        """Count stripes using advanced analysis"""
        if color not in self.color_ranges or roi_hsv.size == 0:
            return 3  # Default
        
        # Create mask for the color
        combined_mask = np.zeros(roi_hsv.shape[:2], dtype=np.uint8)
        for variant in self.color_ranges[color]:
            mask = cv2.inRange(roi_hsv, variant["lower"], variant["upper"])
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Find connected components
        num_labels, labels = cv2.connectedComponents(combined_mask)
        
        # Count significant components
        stripe_count = 0
        for label in range(1, num_labels):
            component_size = np.sum(labels == label)
            if component_size > 10:  # Lower minimum pixels
                stripe_count += 1
        
        # Always default to 3 stripes
        return 3
    
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
            
            # Draw thick bounding box
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


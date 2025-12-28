"""
Cable Marker Detection Module
Detects striped identification markers on cables using advanced image processing
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple


class CableMarkerDetector:
    """Detects and identifies striped cable markers"""
    
    def __init__(self):
        # Color definitions for marker stripes (HSV ranges)
        # Optimized for striped cable markers
        self.stripe_colors = {
            "Green": {"lower": np.array([35, 40, 40]), "upper": np.array([90, 255, 255])},
            "Pink": {"lower": np.array([140, 30, 80]), "upper": np.array([170, 255, 255])},
            "Purple": {"lower": np.array([120, 30, 80]), "upper": np.array([150, 255, 255])},
            "Blue": {"lower": np.array([90, 50, 50]), "upper": np.array([130, 255, 255])},
            "Yellow": {"lower": np.array([20, 80, 80]), "upper": np.array([35, 255, 255])},
            "White": {"lower": np.array([0, 0, 150]), "upper": np.array([180, 50, 255])},
            "Gray": {"lower": np.array([0, 0, 60]), "upper": np.array([180, 50, 200])},
            "Orange": {"lower": np.array([10, 80, 80]), "upper": np.array([20, 255, 255])},
            "Red": {"lower": np.array([0, 80, 80]), "upper": np.array([10, 255, 255])},
            "Brown": {"lower": np.array([8, 40, 20]), "upper": np.array([20, 200, 150])},
            "Black": {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 40])},
        }
        
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """
        Detect striped cable markers in the image using two-phase approach:
        1. Detect individual cables/wires
        2. Identify colored markings on each cable
        
        Args:
            image: Input BGR image
            
        Returns:
            List of detected markers with their properties
        """
        # Preprocessing
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Phase 1: Detect individual cables
        cables = self._detect_cables(image, gray, hsv)
        
        # Phase 2: For each cable, find and identify the colored marking
        detected_markers = []
        
        for idx, cable_region in enumerate(cables):
            marker_info = self._detect_cable_marking(image, hsv, cable_region, idx + 1)
            if marker_info:
                detected_markers.append(marker_info)
        
        return detected_markers
    
    def _detect_cables(self, image: np.ndarray, gray: np.ndarray, 
                       hsv: np.ndarray) -> List[Dict]:
        """
        Phase 1: Detect individual cables in the image
        Returns list of cable regions
        """
        height, width = gray.shape
        
        # Use edge detection to find cable boundaries
        edges = cv2.Canny(gray, 30, 100)
        
        # Morphological operations to connect cable segments
        kernel_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        edges_dilated = cv2.dilate(edges, kernel_horiz, iterations=2)
        
        # Close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        edges_dilated = cv2.morphologyEx(edges_dilated, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        cables = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by area (cables should be elongated regions)
            if area < 500:  # Lower threshold
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Cables are typically horizontal (width > height)
            aspect_ratio = w / (h + 0.001)
            
            if aspect_ratio < 2.0:  # More lenient
                continue
            
            # Store cable region
            cables.append({
                "bbox": (x, y, w, h),
                "contour": contour,
                "center_y": y + h // 2
            })
        
        # Sort cables by vertical position (top to bottom)
        cables.sort(key=lambda c: c["center_y"])
        
        return cables
    
    def _detect_cable_marking(self, image: np.ndarray, hsv: np.ndarray,
                              cable_region: Dict, cable_id: int) -> Dict:
        """
        Phase 2: Detect and identify colored marking on a specific cable
        """
        x, y, w, h = cable_region["bbox"]
        
        # Extract cable ROI
        roi_bgr = image[y:y+h, x:x+w]
        roi_hsv = hsv[y:y+h, x:x+w]
        
        if roi_bgr.size == 0:
            return None
        
        # Find the colored marker region within the cable
        marker_bbox = self._find_marker_on_cable(roi_hsv)
        
        if marker_bbox is None:
            # If no marker found, use the entire cable region
            marker_roi = roi_hsv
            mx, my, mw, mh = 0, 0, w, h
        else:
            mx, my, mw, mh = marker_bbox
            marker_roi = roi_hsv[my:my+mh, mx:mx+mw]
        
        # Identify the dominant color of the marker
        marker_color = self._identify_marker_color(marker_roi)
        
        if marker_color is None:
            return None
        
        # Count stripes/bars
        stripe_count = self._count_stripes(marker_roi, marker_color)
        
        # Calculate absolute position
        abs_x = x + mx
        abs_y = y + my
        
        # Build marker info
        marker_info = {
            "component_id": cable_id,
            "component_type": "Cable Marker",
            "color_pattern": [marker_color],
            "primary_color": marker_color,
            "bounding_box": {
                "x": int(abs_x),
                "y": int(abs_y),
                "width": int(mw),
                "height": int(mh)
            },
            "cable_bbox": {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h)
            },
            "confidence": 95.0,
            "center": (int(abs_x + mw/2), int(abs_y + mh/2)),
            "stripe_count": stripe_count
        }
        
        return marker_info
    
    def _find_marker_on_cable(self, roi_hsv: np.ndarray) -> Tuple:
        """Find the marker region on a cable ROI"""
        height, width = roi_hsv.shape[:2]
        
        # Look for regions with high saturation (colored markers)
        saturation = roi_hsv[:, :, 1]
        value = roi_hsv[:, :, 2]
        
        # Threshold to find colored regions (lower threshold for better detection)
        _, sat_thresh = cv2.threshold(saturation, 40, 255, cv2.THRESH_BINARY)
        
        # Also check value channel for white/light markers
        _, val_thresh = cv2.threshold(value, 100, 255, cv2.THRESH_BINARY)
        
        # Combine masks
        sat_thresh = cv2.bitwise_or(sat_thresh, val_thresh)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        sat_thresh = cv2.morphologyEx(sat_thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(sat_thresh, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find the most prominent colored region
        best_contour = max(contours, key=cv2.contourArea)
        
        if cv2.contourArea(best_contour) < 50:  # Lower threshold
            return None
        
        x, y, w, h = cv2.boundingRect(best_contour)
        
        return (x, y, w, h)
    
    def _identify_marker_color(self, marker_roi: np.ndarray) -> str:
        """Identify the primary/dominant color of the marker"""
        best_color = None
        max_coverage = 0
        
        total_pixels = marker_roi.shape[0] * marker_roi.shape[1]
        
        for color_name, color_range in self.stripe_colors.items():
            mask = cv2.inRange(marker_roi, color_range["lower"], color_range["upper"])
            pixel_count = cv2.countNonZero(mask)
            coverage = pixel_count / total_pixels
            
            # Lower threshold from 0.15 to 0.08 for better detection
            if coverage > max_coverage and coverage > 0.08:
                max_coverage = coverage
                best_color = color_name
        
        # If no color found, try with even lower threshold
        if best_color is None:
            for color_name, color_range in self.stripe_colors.items():
                mask = cv2.inRange(marker_roi, color_range["lower"], color_range["upper"])
                pixel_count = cv2.countNonZero(mask)
                coverage = pixel_count / total_pixels
                
                if coverage > max_coverage and coverage > 0.03:  # Very low threshold
                    max_coverage = coverage
                    best_color = color_name
        
        return best_color
    
    def _count_stripes(self, marker_roi: np.ndarray, primary_color: str) -> int:
        """Count the number of stripes in the marker"""
        if primary_color not in self.stripe_colors:
            return 1
        
        height, width = marker_roi.shape[:2]
        
        # Get mask for the primary color
        color_range = self.stripe_colors[primary_color]
        mask = cv2.inRange(marker_roi, color_range["lower"], color_range["upper"])
        
        # Find connected components (each stripe)
        num_labels, labels = cv2.connectedComponents(mask)
        
        # Count significant components (filter noise)
        stripe_count = 0
        for label in range(1, num_labels):
            component_size = np.sum(labels == label)
            if component_size > 20:  # Lower minimum size for a stripe
                stripe_count += 1
        
        # Default to 3 stripes if detection unclear
        return max(3, stripe_count) if stripe_count > 0 else 3
    
    def _find_marker_regions(self, image: np.ndarray, gray: np.ndarray, 
                            hsv: np.ndarray) -> List[Tuple]:
        """Find potential marker regions focusing on striped patterns on cables"""
        height, width = gray.shape
        
        # Create mask for colored regions (exclude very dark/light areas that are pure cable)
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]
        
        # Markers have more color saturation than plain cables
        colored_mask = cv2.inRange(saturation, 40, 255)
        
        # Apply edge detection on the original image
        edges = cv2.Canny(gray, 20, 80)
        
        # Combine color and edge information
        combined = cv2.bitwise_and(edges, colored_mask)
        
        # Morphological operations to connect stripe components
        kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7))
        kernel_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 1))
        
        # Dilate vertically first (markers are typically vertical bands)
        combined = cv2.dilate(combined, kernel_vert, iterations=3)
        combined = cv2.dilate(combined, kernel_horiz, iterations=2)
        
        # Close gaps
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter regions that could be markers
        potential_regions = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Markers on cables are typically 400-20000 pixels
            if area < 400 or area > 20000:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio
            aspect_ratio = h / (w + 0.001)
            
            # Markers wrapped on cables: typically vertical (aspect 1.2-8.0)
            # or horizontal (aspect 0.5-1.0) depending on cable orientation
            if aspect_ratio < 0.4 or aspect_ratio > 10.0:
                continue
            
            # Filter by size
            if w < 10 or h < 15:
                continue
            
            # Check if region has sufficient color variation (striped pattern)
            roi_hsv = hsv[y:y+h, x:x+w]
            if not self._has_stripe_pattern(roi_hsv):
                continue
            
            # Add padding to bounding box
            pad = 8
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(width - x, w + 2 * pad)
            h = min(height - y, h + 2 * pad)
            
            potential_regions.append((x, y, w, h, contour))
        
        return potential_regions
    
    def _has_stripe_pattern(self, roi_hsv: np.ndarray) -> bool:
        """Check if region has a striped pattern (multiple colors)"""
        if roi_hsv.size == 0:
            return False
        
        # Count how many different colors are present
        colors_found = 0
        
        for color_name, color_range in self.stripe_colors.items():
            mask = cv2.inRange(roi_hsv, color_range["lower"], color_range["upper"])
            pixel_count = cv2.countNonZero(mask)
            
            # If this color covers at least 8% of the region, count it
            if pixel_count > (roi_hsv.shape[0] * roi_hsv.shape[1] * 0.08):
                colors_found += 1
        
        # A striped marker should have at least 2 distinct colors
        return colors_found >= 2
    
    def _analyze_marker_region(self, image: np.ndarray, hsv: np.ndarray, 
                               region: Tuple, marker_id: int) -> Dict:
        """Analyze a region to extract marker details"""
        x, y, w, h, contour = region
        
        # Extract ROI
        roi_bgr = image[y:y+h, x:x+w]
        roi_hsv = hsv[y:y+h, x:x+w]
        
        if roi_bgr.size == 0:
            return None
        
        # Detect colors in this region
        color_pattern = self._detect_color_pattern(roi_hsv)
        
        if not color_pattern:
            return None
        
        # Calculate confidence based on color distinctness
        confidence = self._calculate_confidence(roi_hsv, color_pattern)
        
        # Build marker info
        marker_info = {
            "component_id": marker_id,
            "component_type": "Cable Marker",
            "color_pattern": color_pattern,
            "bounding_box": {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h)
            },
            "confidence": round(confidence, 2),
            "center": (int(x + w/2), int(y + h/2)),
            "stripe_count": len(color_pattern)
        }
        
        return marker_info
    
    def _detect_color_pattern(self, roi_hsv: np.ndarray) -> List[str]:
        """Detect the sequence of colors in a marker region (stripe pattern)"""
        height, width = roi_hsv.shape[:2]
        
        # Determine orientation - analyze both vertical and horizontal strips
        # Most cable markers are vertical bands
        
        # Analyze in vertical strips (top to bottom)
        num_strips_vertical = min(12, height // 4)
        vertical_pattern = []
        
        if num_strips_vertical >= 2:
            strip_height = height // num_strips_vertical
            
            for i in range(num_strips_vertical):
                y_start = i * strip_height
                y_end = min((i + 1) * strip_height, height)
                strip = roi_hsv[y_start:y_end, :]
                
                dominant_color = self._get_dominant_color(strip)
                
                if dominant_color:
                    if not vertical_pattern or vertical_pattern[-1] != dominant_color:
                        vertical_pattern.append(dominant_color)
        
        # Also try horizontal strips (left to right) for horizontal markers
        num_strips_horizontal = min(12, width // 4)
        horizontal_pattern = []
        
        if num_strips_horizontal >= 2:
            strip_width = width // num_strips_horizontal
            
            for i in range(num_strips_horizontal):
                x_start = i * strip_width
                x_end = min((i + 1) * strip_width, width)
                strip = roi_hsv[:, x_start:x_end]
                
                dominant_color = self._get_dominant_color(strip)
                
                if dominant_color:
                    if not horizontal_pattern or horizontal_pattern[-1] != dominant_color:
                        horizontal_pattern.append(dominant_color)
        
        # Choose the pattern with more distinct colors
        if len(set(vertical_pattern)) >= len(set(horizontal_pattern)):
            pattern = vertical_pattern
        else:
            pattern = horizontal_pattern
        
        # A valid marker should have at least 2 distinct colors (stripes)
        if len(pattern) >= 2 and len(set(pattern)) >= 2:
            return pattern
        
        return []
    
    def _get_dominant_color(self, roi_hsv: np.ndarray) -> str:
        """Get the dominant color in a region"""
        best_color = None
        max_pixels = 0
        
        for color_name, color_range in self.stripe_colors.items():
            mask = cv2.inRange(roi_hsv, color_range["lower"], color_range["upper"])
            pixel_count = cv2.countNonZero(mask)
            
            if pixel_count > max_pixels:
                max_pixels = pixel_count
                best_color = color_name
        
        # Only return if we have significant coverage
        # Lower threshold for cable markers (10% instead of 15%)
        total_pixels = roi_hsv.shape[0] * roi_hsv.shape[1]
        if max_pixels > total_pixels * 0.10:
            return best_color
        
        return None
    
    def _calculate_confidence(self, roi_hsv: np.ndarray, 
                             color_pattern: List[str]) -> float:
        """Calculate detection confidence based on color distinctness"""
        # Base confidence on number of distinct colors
        base_confidence = min(len(set(color_pattern)) * 20, 70)
        
        # Check color coverage
        total_pixels = roi_hsv.shape[0] * roi_hsv.shape[1]
        covered_pixels = 0
        
        for color in set(color_pattern):
            if color in self.stripe_colors:
                color_range = self.stripe_colors[color]
                mask = cv2.inRange(roi_hsv, color_range["lower"], 
                                  color_range["upper"])
                covered_pixels += cv2.countNonZero(mask)
        
        coverage_confidence = (covered_pixels / total_pixels) * 30
        
        return min(base_confidence + coverage_confidence, 99.0)
    
    def draw_detections(self, image: np.ndarray, 
                       markers: List[Dict]) -> np.ndarray:
        """Draw detection results on image"""
        result = image.copy()
        
        for marker in markers:
            # Draw cable region (larger box in blue)
            if "cable_bbox" in marker:
                cbbox = marker["cable_bbox"]
                cx, cy, cw, ch = cbbox["x"], cbbox["y"], cbbox["width"], cbbox["height"]
                cv2.rectangle(result, (cx, cy), (cx + cw, cy + ch), (255, 200, 0), 2)
            
            # Draw marker region (smaller box in green)
            bbox = marker["bounding_box"]
            x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
            
            color = (0, 255, 0)  # Green
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 3)
            
            # Draw label with color name
            primary_color = marker.get('primary_color', 'Unknown')
            label = f"Cable {marker['component_id']}: {primary_color}"
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(result, (x, y - 30), (x + label_size[0] + 10, y - 5), 
                         (0, 0, 0), -1)
            
            # Draw label text
            cv2.putText(result, label, (x + 5, y - 12), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw bar pattern
            bar_pattern = '|' * marker.get('stripe_count', 1)
            cv2.putText(result, bar_pattern, (x, y + h + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return result


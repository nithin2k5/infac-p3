"""
Roboflow Inference Detector
Uses Roboflow workflow API for cable marker detection
"""

import cv2
import numpy as np
from typing import List, Dict
import base64
import io
import tempfile
import os
from PIL import Image


class RoboflowDetector:
    """Detector using Roboflow Inference API"""
    
    def __init__(self, min_confidence=0.3, grouping_distance=250, grouping_horizontal_distance=500):
        self.use_http = False
        self.workspace_name = "cable-evfad"
        self.workflow_id = "find-white-stripes-yellow-stripes-blue-stripes-pink-stripes-and-green-stripes"
        self.api_key = "os34K4b17ImpAhsyrIiz"
        self.api_url = "https://serverless.roboflow.com"
        
        # Detection parameters (increased for better grouping)
        self.min_confidence = min_confidence  # Minimum confidence threshold (0.0 to 1.0)
        self.grouping_distance = grouping_distance  # Max vertical distance for grouping stripes (increased to 250)
        self.grouping_horizontal_distance = grouping_horizontal_distance  # Max horizontal distance (increased to 500)
        
        # Always use direct HTTP requests to match website API format exactly
        try:
            import requests
            self.requests = requests
            self.use_http = True
            print("✅ Using direct HTTP requests to Roboflow API (matches website format)")
            print(f"⚙️  Detection settings: min_confidence={min_confidence}, grouping_distance={grouping_distance}px")
        except ImportError:
            print("❌ requests library not available")
            self.use_http = False
    
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """Detect markers using Roboflow workflow"""
        if not self.use_http:
            print("❌ Roboflow HTTP client not initialized")
            return []
        
        # Optimize image for faster processing
        original_height, original_width = image.shape[:2]
        processed_image = image.copy()
        
        # Resize large images to speed up detection (max 1920px on longest side)
        max_dimension = 1920
        if max(original_height, original_width) > max_dimension:
            scale = max_dimension / max(original_height, original_width)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            processed_image = cv2.resize(processed_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"⚡ Resized image from {original_width}x{original_height} to {new_width}x{new_height} for faster detection")
        
        # Save image to temporary file
        temp_file = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_path = temp_file.name
            temp_file.close()
            
            # Save with optimized JPEG quality (85% for good quality but smaller file)
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
            success = cv2.imwrite(temp_path, processed_image, encode_params)
            if not success:
                print(f"Error: Failed to save image to {temp_path}")
                return []
            
            # Read image bytes for HTTP API
            with open(temp_path, 'rb') as f:
                image_bytes = f.read()
            
            print(f"📦 Image size: {len(image_bytes) / 1024:.1f} KB")
            
            # Always use HTTP requests directly (matches website format exactly)
            result = self._run_workflow_http(image_bytes)
            
            # Get processed image dimensions for coordinate conversion
            proc_height, proc_width = processed_image.shape[:2]
            
            # Parse results (using processed image dimensions)
            raw_markers = self._parse_roboflow_results(result, image_width=proc_width, image_height=proc_height)
            
            # Scale coordinates back to original image size if resized
            if max(original_height, original_width) > max_dimension:
                scale_x = original_width / proc_width
                scale_y = original_height / proc_height
                for marker in raw_markers:
                    bbox = marker["bounding_box"]
                    marker["bounding_box"] = {
                        "x": int(bbox["x"] * scale_x),
                        "y": int(bbox["y"] * scale_y),
                        "width": int(bbox["width"] * scale_x),
                        "height": int(bbox["height"] * scale_y)
                    }
                    # Update center
                    marker["center"] = (marker["bounding_box"]["x"] + marker["bounding_box"]["width"] // 2,
                                       marker["bounding_box"]["y"] + marker["bounding_box"]["height"] // 2)
            
            # Group stripes into markings: 3 stripes = 1 marking
            grouped_markers = self._group_stripes_into_markings(raw_markers)
            
            return grouped_markers
            
        except Exception as e:
            print(f"Error running Roboflow workflow: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def _run_workflow_http(self, image_bytes: bytes) -> dict:
        """Run workflow using HTTP requests - matches website API format"""
        import base64
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # API endpoint - CORRECT format: /workflows/ (plural)
        # Matches: https://serverless.roboflow.com/cable-evfad/workflows/find-cables-and-stripes-on-the-cables
        url = f"{self.api_url}/{self.workspace_name}/workflows/{self.workflow_id}"
        
        print(f"📡 Calling Roboflow API: {url}")
        
        # Headers - CORRECT format: only Content-Type, no Authorization header
        headers = {
            "Content-Type": "application/json"
        }
        
        # Payload - CORRECT format: api_key in body, inputs with type and value
        payload = {
            "api_key": self.api_key,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": image_b64
                }
            }
        }
        
        try:
            # Make request with reduced timeout for faster failure detection
            print("⏳ Sending request to Roboflow...")
            response = self.requests.post(url, json=payload, headers=headers, timeout=15)
            
            # Check status
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                response.raise_for_status()
            
            result = response.json()
            print(f"✅ Received response from Roboflow")
            return result
            
        except self.requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text[:500]}")
            raise
    
    def _parse_roboflow_results(self, result: dict, image_width: int = None, image_height: int = None) -> List[Dict]:
        """Parse Roboflow workflow results"""
        markers = []
        
        try:
            # Debug: Print full result structure for troubleshooting
            print(f"\n{'='*60}")
            print("📦 ROBOFLOW RESPONSE STRUCTURE:")
            print(f"{'='*60}")
            if isinstance(result, dict):
                print(f"Type: dict")
                print(f"Keys: {list(result.keys())}")
                # Print first level values (truncated)
                for key, value in result.items():
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                    else:
                        print(f"  {key}: {str(value)[:100]}")
            elif isinstance(result, list):
                print(f"Type: list (length: {len(result)})")
                if result:
                    print(f"First item type: {type(result[0])}")
                    if isinstance(result[0], dict):
                        print(f"First item keys: {list(result[0].keys())}")
            else:
                print(f"Type: {type(result)}")
                print(f"Value: {str(result)[:500]}")
            print(f"{'='*60}\n")
            
            # Handle different response structures
            # Workflows can return detections in various formats
            predictions = []
            
            if isinstance(result, list):
                # Direct list of predictions
                predictions = result
            elif isinstance(result, dict):
                # Check for workflow output structure - common formats:
                
                # Format 1: Workflow outputs array
                if 'outputs' in result:
                    outputs = result['outputs']
                    if isinstance(outputs, list):
                        # Each output might be a detection step
                        for output in outputs:
                            if isinstance(output, dict):
                                # Look for predictions in this output
                                for key in ['predictions', 'results', 'output', 'detections', 'objects', 'data']:
                                    if key in output:
                                        preds = output[key]
                                        if isinstance(preds, list):
                                            predictions.extend(preds)
                                        elif isinstance(preds, dict):
                                            # Single prediction or nested
                                            if 'predictions' in preds:
                                                if isinstance(preds['predictions'], list):
                                                    predictions.extend(preds['predictions'])
                                            else:
                                                predictions.append(preds)
                
                # Format 2: Direct predictions key
                if not predictions:
                    for key in ['predictions', 'results', 'output', 'detections', 'objects', 'data']:
                        if key in result:
                            preds = result[key]
                            if isinstance(preds, list):
                                predictions = preds
                                break
                            elif isinstance(preds, dict):
                                # Might be nested
                                if 'predictions' in preds and isinstance(preds['predictions'], list):
                                    predictions = preds['predictions']
                                else:
                                    predictions = [preds]
                                break
                
                # Format 3: Workflow step results (nested)
                if not predictions and 'steps' in result:
                    steps = result['steps']
                    if isinstance(steps, list):
                        for step in steps:
                            if isinstance(step, dict) and 'output' in step:
                                step_output = step['output']
                                if isinstance(step_output, list):
                                    predictions.extend(step_output)
                                elif isinstance(step_output, dict):
                                    if 'predictions' in step_output:
                                        preds = step_output['predictions']
                                        if isinstance(preds, list):
                                            predictions.extend(preds)
                
                # Format 4: Result itself is a prediction
                if not predictions and ('x' in result or 'bbox' in result or 'x_min' in result or 'class' in result):
                    predictions = [result]
                
                # Format 5: Check all top-level keys for arrays of predictions
                if not predictions:
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) > 0:
                            # Check if first item looks like a prediction
                            if isinstance(value[0], dict) and ('x' in value[0] or 'bbox' in value[0] or 'class' in value[0]):
                                predictions = value
                                break
            
            # Ensure predictions is a list
            if not isinstance(predictions, list):
                predictions = [predictions] if predictions else []
            
            print(f"Found {len(predictions)} raw predictions to parse\n")
            
            # Parse each prediction - focus on "stripes on the cable" detections
            for idx, pred in enumerate(predictions):
                if not isinstance(pred, dict):
                    continue
                
                # Skip "cable" detections, only process "stripes on the cable"
                pred_class = pred.get('class', pred.get('label', pred.get('name', ''))).lower()
                if 'cable' in pred_class and 'stripe' not in pred_class:
                    print(f"Skipping 'cable' detection (not a stripe marker)")
                    continue
                
                # Extract bounding box - try multiple formats
                x, y, w, h = 0, 0, 0, 0
                found_bbox = False
                
                # Format 1: bbox object
                if 'bbox' in pred:
                    bbox = pred['bbox']
                    if isinstance(bbox, dict):
                        x = int(bbox.get('x', bbox.get('x_min', 0)))
                        y = int(bbox.get('y', bbox.get('y_min', 0)))
                        w = int(bbox.get('width', bbox.get('x_max', 0) - x))
                        h = int(bbox.get('height', bbox.get('y_max', 0) - y))
                        found_bbox = True
                
                # Format 2: Direct x, y, width, height (normalized or absolute)
                if not found_bbox and all(k in pred for k in ['x', 'y', 'width', 'height']):
                    x_val = float(pred['x'])
                    y_val = float(pred['y'])
                    w_val = float(pred['width'])
                    h_val = float(pred['height'])
                    
                    # Check if normalized (0-1 range) or absolute pixels
                    if image_width and image_height and 0 <= x_val <= 1 and 0 <= y_val <= 1:
                        # Normalized coordinates - convert to pixels
                        x = int(x_val * image_width)
                        y = int(y_val * image_height)
                        w = int(w_val * image_width)
                        h = int(h_val * image_height)
                    else:
                        # Absolute pixel coordinates
                        x = int(x_val)
                        y = int(y_val)
                        w = int(w_val)
                        h = int(h_val)
                    found_bbox = True
                
                # Format 3: x_min, y_min, x_max, y_max
                if not found_bbox and all(k in pred for k in ['x_min', 'y_min', 'x_max', 'y_max']):
                    x = int(pred['x_min'])
                    y = int(pred['y_min'])
                    w = int(pred['x_max'] - pred['x_min'])
                    h = int(pred['y_max'] - pred['y_min'])
                    found_bbox = True
                
                if not found_bbox or w <= 0 or h <= 0:
                    print(f"Skipping prediction {idx}: No valid bbox found")
                    continue
                
                # Extract class/color
                color = pred.get('class', pred.get('label', pred.get('color', pred.get('name', pred.get('class_name', 'Unknown')))))
                
                # If color is still Unknown, skip only if it's really unknown
                # Some detections might have class_id instead of class name
                if not color or (color == 'Unknown' and 'class_id' not in pred):
                    # Try to get class_id and map it if possible
                    class_id = pred.get('class_id')
                    if class_id is not None:
                        # Common class ID mappings (adjust based on your dataset)
                        class_map = {0: 'yellow', 1: 'blue', 2: 'green', 3: 'pink', 4: 'white'}
                        color = class_map.get(class_id, 'Unknown')
                    else:
                        continue
                
                # Extract confidence
                confidence = pred.get('confidence', pred.get('score', pred.get('probability', 0.8)))
                if isinstance(confidence, (int, float)):
                    confidence_raw = float(confidence) if confidence <= 1.0 else float(confidence) / 100.0
                    confidence_percent = confidence_raw * 100
                else:
                    confidence_raw = 0.8
                    confidence_percent = 80.0
                
                # Filter by minimum confidence
                if confidence_raw < self.min_confidence:
                    print(f"Skipping low confidence detection: {confidence_percent:.1f}% < {self.min_confidence * 100}%")
                    continue
                
                markers.append({
                    "component_id": idx + 1,
                    "component_type": "Cable Marker",
                    "primary_color": str(color).capitalize(),
                    "color_pattern": [str(color).capitalize()],
                    "bounding_box": {
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h
                    },
                    "confidence": round(float(confidence_percent), 2),
                    "center": (x + w // 2, y + h // 2),
                    "stripe_count": 3
                })
            
            # Sort by position
            markers.sort(key=lambda m: (m["center"][1], m["center"][0]))
            for idx, marker in enumerate(markers):
                marker["component_id"] = idx + 1
            
        except Exception as e:
            print(f"Error parsing results: {e}")
            import traceback
            traceback.print_exc()
            print(f"Result structure: {result}")
        
        return markers
    
    def _group_stripes_into_markings(self, stripes: List[Dict]) -> List[Dict]:
        """
        Group stripes into markings: 3 stripes = 1 marking
        Uses clustering approach - any stripe close to ANY stripe in the group gets added
        """
        if not stripes:
            return []
        
        print(f"\n🔍 GROUPING {len(stripes)} stripes into markings...")
        print(f"   Max vertical distance: {self.grouping_distance}px")
        print(f"   Max horizontal distance: {self.grouping_horizontal_distance}px")
        
        # Group stripes by color and proximity using clustering
        grouped = []
        used_indices = set()
        
        # Sort stripes by Y position (top to bottom) then X (left to right)
        sorted_stripes = sorted(stripes, key=lambda s: (s["center"][1], s["center"][0]))
        
        # Print all stripes for debugging
        print(f"\n   Raw stripes detected:")
        for i, stripe in enumerate(sorted_stripes):
            color = stripe.get("primary_color", "Unknown")
            center = stripe["center"]
            conf = stripe.get("confidence", 0)
            print(f"   [{i}] {color} at ({center[0]}, {center[1]}) - {conf:.1f}%")
        
        for i, stripe in enumerate(sorted_stripes):
            if i in used_indices:
                continue
            
            # Start a new group with this stripe
            group = [stripe]
            group_indices = {i}
            used_indices.add(i)
            color = stripe.get("primary_color", "Unknown")
            
            print(f"\n   Starting new group with stripe [{i}] ({color})")
            
            # Keep looking for nearby stripes until no more can be added
            # Use iterative expansion: check if any remaining stripe is close to ANY stripe in the group
            added_new = True
            iterations = 0
            max_iterations = 20  # Prevent infinite loops
            
            while added_new and iterations < max_iterations:
                added_new = False
                iterations += 1
                
                for j, other_stripe in enumerate(sorted_stripes):
                    if j in used_indices:
                        continue
                    
                    other_color = other_stripe.get("primary_color", "Unknown")
                    
                    # Must be same color
                    if color.lower() != other_color.lower():
                        continue
                    
                    other_center = other_stripe["center"]
                    
                    # Check if this stripe is close to ANY stripe already in the group
                    is_close = False
                    for group_stripe in group:
                        group_center = group_stripe["center"]
                        
                        vertical_dist = abs(other_center[1] - group_center[1])
                        horizontal_dist = abs(other_center[0] - group_center[0])
                        
                        if (vertical_dist < self.grouping_distance and 
                            horizontal_dist < self.grouping_horizontal_distance):
                            is_close = True
                            print(f"      Found nearby stripe [{j}]: v_dist={vertical_dist}px, h_dist={horizontal_dist}px")
                            break
                    
                    if is_close:
                        group.append(other_stripe)
                        group_indices.add(j)
                        used_indices.add(j)
                        added_new = True
            
            # Create a marking from the group (regardless of stripe count)
            if group:
                # Calculate combined bounding box
                min_x = min(s["bounding_box"]["x"] for s in group)
                min_y = min(s["bounding_box"]["y"] for s in group)
                max_x = max(s["bounding_box"]["x"] + s["bounding_box"]["width"] for s in group)
                max_y = max(s["bounding_box"]["y"] + s["bounding_box"]["height"] for s in group)
                
                # Calculate average confidence
                avg_confidence = sum(s["confidence"] for s in group) / len(group)
                
                # Create marking
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
                print(f"   ✓ Created marking with {len(group)} stripe(s) from indices {sorted(group_indices)}")
        
        # Sort grouped markings by position
        grouped.sort(key=lambda m: (m["center"][1], m["center"][0]))
        for idx, marking in enumerate(grouped):
            marking["component_id"] = idx + 1
        
        # Log grouping summary
        single_stripe_count = sum(1 for m in grouped if m.get('stripes_in_group', 1) == 1)
        two_stripe_count = sum(1 for m in grouped if m.get('stripes_in_group', 1) == 2)
        three_plus_count = sum(1 for m in grouped if m.get('stripes_in_group', 1) >= 3)
        
        print(f"\n📊 GROUPING SUMMARY:")
        print(f"   Input: {len(stripes)} raw stripes")
        print(f"   Output: {len(grouped)} markings")
        print(f"   - 1 stripe: {single_stripe_count} marking(s)")
        print(f"   - 2 stripes: {two_stripe_count} marking(s)")
        print(f"   - 3+ stripes: {three_plus_count} marking(s)")
        
        # Warning if we have groups with less than 3 stripes
        if single_stripe_count > 0 or two_stripe_count > 0:
            print(f"   ⚠️  Warning: Some markings have < 3 stripes. Consider adjusting grouping distances.")
        
        return grouped
    
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
            "Gray": (128, 128, 128),
            "Red": (0, 0, 255),
            "Orange": (0, 165, 255)
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


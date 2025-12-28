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
    
    def __init__(self):
        self.use_http = False
        self.workspace_name = "cable-evfad"
        self.workflow_id = "find-cables-and-stripes-on-the-cables"
        self.api_key = "os34K4b17ImpAhsyrIiz"
        self.api_url = "https://serverless.roboflow.com"
        
        # Always use direct HTTP requests to match website API format exactly
        try:
            import requests
            self.requests = requests
            self.use_http = True
            print("✅ Using direct HTTP requests to Roboflow API (matches website format)")
        except ImportError:
            print("❌ requests library not available")
            self.use_http = False
    
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """Detect markers using Roboflow workflow"""
        if not self.use_http:
            print("❌ Roboflow HTTP client not initialized")
            return []
        
        # Save image to temporary file
        temp_file = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_path = temp_file.name
            temp_file.close()
            
            # Save image to file (convert BGR to RGB if needed, but OpenCV saves BGR correctly)
            success = cv2.imwrite(temp_path, image)
            if not success:
                print(f"Error: Failed to save image to {temp_path}")
                return []
            
            # Read image bytes for HTTP API
            with open(temp_path, 'rb') as f:
                image_bytes = f.read()
            
            # Always use HTTP requests directly (matches website format exactly)
            result = self._run_workflow_http(image_bytes)
            
            # Get image dimensions for coordinate conversion if needed
            height, width = image.shape[:2]
            
            # Parse results
            markers = self._parse_roboflow_results(result, image_width=width, image_height=height)
            
            return markers
            
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
            # Make request
            print("⏳ Sending request to Roboflow...")
            response = self.requests.post(url, json=payload, headers=headers, timeout=30)
            
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
                    confidence = float(confidence) * 100 if confidence <= 1.0 else float(confidence)
                else:
                    confidence = 80.0
                
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
                    "confidence": round(float(confidence), 2),
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


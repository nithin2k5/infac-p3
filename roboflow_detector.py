"""
Roboflow Cable Marker Detector

Features:
- Static image detection via Roboflow model (infacp3/v2)
- Batch video processing via Roboflow Python SDK

Usage:
    detector = RoboflowDetector()

    # Static image detection
    markers = detector.detect_markers(image)

    # Batch video processing
    results = detector.process_video_batch("video.mp4")
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Callable, Tuple
import threading
import time
import os


class RoboflowDetector:
    """
    Cable marker detector using Roboflow model (infacp3/v2)

    Capabilities:
    - Static image detection via Roboflow Python SDK (detect_markers method)
    - Batch video processing via Roboflow Python SDK (predict_video, process_video_batch methods)

    Uses direct model inference for consistent results with Roboflow website.
    """
    
    def __init__(self, min_confidence=0.25, grouping_distance=250, grouping_horizontal_distance=500):
        self.client = None
        self.workspace_name = "cable-evfad"
        # self.workflow_id = "small-object-detection-sahi" # Removed legacy workflow
        self.api_key = "os34K4b17ImpAhsyrIiz"
        self.api_url = "https://serverless.roboflow.com"

        # Roboflow Python SDK components
        self.rf = None
        self.project = None
        self.model = None
        self.roboflow_project_name = "infacp3"  # Project name from Roboflow workspace
        self.roboflow_model_version = "2"  # Model version
        
        # Detection parameters
        self.min_confidence = min_confidence
        self.grouping_distance = grouping_distance
        self.grouping_horizontal_distance = grouping_horizontal_distance
        
        # WebRTC session
        self.session = None
        self.session_active = False
        self.session_lock = threading.Lock()
        
        # Frame and detection callbacks
        self.frame_callback: Optional[Callable] = None
        self.detection_callback: Optional[Callable] = None
        
        # Latest detections
        self.latest_detections: List[Dict] = []
        self.latest_frame: Optional[np.ndarray] = None
        self.detections_lock = threading.Lock()
        
        # Initialization tracking
        self._initialization_failed = False
        self._initialization_error = None
        
        # Initialize both SDKs
        inference_initialized = False
        roboflow_initialized = False

        # Initialize Inference SDK client (for real-time/WebRTC)
        try:
            print("🔄 Initializing Inference SDK...")
            from inference_sdk import InferenceHTTPClient
            from inference_sdk.webrtc import WebcamSource, StreamConfig, VideoMetadata

            print(f"   API URL: {self.api_url}")
            print(f"   API Key: {self.api_key[:8]}...{self.api_key[-4:]}")

            self.client = InferenceHTTPClient.init(
                api_url=self.api_url,
                api_key=self.api_key
            )
            self.WebcamSource = WebcamSource
            self.StreamConfig = StreamConfig
            self.VideoMetadata = VideoMetadata
            inference_initialized = True

            print("✅ Inference SDK initialized for real-time/WebRTC processing")
        except ImportError as e:
            print(f"⚠️  Inference SDK not available: {e}")
            print("   Real-time/WebRTC features will be disabled")
            self.client = None
            self.WebcamSource = None
            self.StreamConfig = None
            self.VideoMetadata = None
        except Exception as e:
            print(f"⚠️  Failed to initialize Inference SDK: {e}")
            print(f"   Error type: {type(e).__name__}")
            print("   Real-time/WebRTC features will be disabled")
            self.client = None
            self.WebcamSource = None
            self.StreamConfig = None
            self.VideoMetadata = None

        # Initialize Roboflow Python SDK (for batch video processing)
        try:
            print("🔄 Initializing Roboflow Python SDK...")
            from roboflow import Roboflow

            print(f"   Project: {self.roboflow_project_name}")
            print(f"   Version: {self.roboflow_model_version}")

            self.rf = Roboflow(api_key=self.api_key)
            self.project = self.rf.workspace(self.workspace_name).project(self.roboflow_project_name)
            self.model = self.project.version(self.roboflow_model_version).model
            roboflow_initialized = True
            print("✅ Roboflow Python SDK initialized for batch video processing")
        except ImportError as e:
            print(f"⚠️  Roboflow SDK not available: {e}")
            print("   Batch video processing features will be disabled")
            self.rf = None
            self.project = None
            self.model = None
        except Exception as e:
            print(f"⚠️  Failed to initialize Roboflow SDK: {e}")
            print(f"   Error type: {type(e).__name__}")
            print("   Batch video processing features will be disabled")
            self.rf = None
            self.project = None
            self.model = None

        # Set initialization flags
        self._inference_initialized = inference_initialized
        self._roboflow_initialized = roboflow_initialized

        # Debug output
        print(f"\n🔧 Initialization Summary:")
        print(f"   Roboflow Model: {'✅ ENABLED' if roboflow_initialized else '❌ DISABLED'}")
        print(f"   Inference SDK: {'✅ ENABLED (WebRTC)' if inference_initialized else '❌ DISABLED'}")

        if not self._roboflow_initialized:
            print(f"\n{'='*60}")
            print("❌ CRITICAL: Roboflow model could not be initialized!")
            print(f"{'='*60}")
            print("Detection requires the Roboflow Python SDK.")
            print("To fix this, install the required package:")
            print("  pip install roboflow")
            print("  Or: pip install -r requirements.txt")
            print(f"{'='*60}\n")
            self._initialization_failed = True
        else:
            print(f"\n⚙️  Detection settings:")
            print(f"   Model: {self.roboflow_project_name}/v{self.roboflow_model_version}")
            print(f"   Confidence threshold: {min_confidence * 100}%")
            print(f"   Grouping distance: {grouping_distance}px")
            print(f"📦 Workspace: {self.workspace_name}")
            print(f"🔑 API Key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else '***'}")
            if self._inference_initialized:
                print(f"📡 WebRTC streaming: Available")

    
    def detect_markers(self, image: np.ndarray) -> List[Dict]:
        """
        Detect markers in a static image using direct Roboflow model inference
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
            
        Returns:
            List of detected marker dictionaries
        """
        if not self._roboflow_initialized or not self.model:
            print("\n" + "="*60)
            print("❌ ERROR: Roboflow model not initialized!")
            print("="*60)
            print("Detection requires the Roboflow Python SDK.")
            print("\nTo fix this:")
            print("  1. Install the package: pip install roboflow")
            print("  2. Or install all requirements: pip install -r requirements.txt")
            print("  3. Restart the application")
            print("="*60 + "\n")
            return []
        
        if image is None or image.size == 0:
            print("❌ Invalid image provided")
            return []
        
        try:
            print(f"📸 Detecting markers using Roboflow model {self.roboflow_project_name}/v{self.roboflow_model_version}...")
            print(f"   Image size: {image.shape[1]}x{image.shape[0]}")
            print(f"   Confidence threshold: {self.min_confidence * 100}%")
            
            # Save image to temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                # Save with good quality for accurate detection
                cv2.imwrite(tmp_path, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            try:
                print(f"⏳ Running inference on image...")
                
                # Use direct Roboflow model inference
                result = self.model.predict(
                    tmp_path,
                    confidence=int(self.min_confidence * 100),  # Convert to percentage
                    overlap=30
                )
                
                print(f"✅ Received model predictions")
                
                # Parse results from Roboflow model
                raw_markers = self._parse_roboflow_predictions(result, image.shape[1], image.shape[0])
                
                print(f"✅ Detection complete: {len(raw_markers)} raw result(s) returned")
                
                return raw_markers
                
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except Exception as e:
                    print(f"⚠️ Warning: Could not delete temp file: {e}")
                    
        except Exception as e:
            print(f"❌ Error with Roboflow model inference: {e}")
            import traceback
            traceback.print_exc()
            return []
    def detect_single_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect markers in a single frame using InferenceHTTPClient (faster than model.predict for streams)
        
        Args:
            frame: Input frame as numpy array (BGR)
            
        Returns:
            List of detected marker dictionaries
        """
        if not self._inference_initialized or not self.client:
            # Fallback to slower method if SDK not ready
            return self.detect_markers(frame)
            
        try:
            # Use InferenceHTTPClient for direct in-memory inference
            # This avoids writing to disk
            result = self.client.infer(
                frame,
                model_id=f"{self.roboflow_project_name}/{self.roboflow_model_version}"
            )
            
            # Result format from client.infer is usually a dict
            # We can reuse the parsing logic if we wrap it or handle the dict
            
            # Adapt result for parsing logic
            # _parse_roboflow_predictions expects something it can access .json() or dict
            # client.infer typically returns a dict directly
            
            return self._parse_roboflow_predictions(result, frame.shape[1], frame.shape[0])
            
        except Exception as e:
            print(f"⚠️ Single frame inference failed: {e}")
            return []

    def start_webrtc_stream(self, camera_index: int = 0, 
                           frame_callback: Optional[Callable] = None,
                           detection_callback: Optional[Callable] = None,
                           resolution: tuple = (1280, 720)):
        """
        Start WebRTC streaming session for real-time detection
        
        Args:
            camera_index: Camera device index
            frame_callback: Callback function(frame, metadata) for processed frames
            detection_callback: Callback function(detections, metadata) for detection data
            resolution: Camera resolution (width, height)
        """
        if not self._inference_initialized:
            print("\n" + "="*60)
            print("❌ ERROR: Roboflow Inference SDK not initialized!")
            print("="*60)
            print("WebRTC streaming requires the inference-sdk package.")
            print("\nTo fix this:")
            print("  1. Install the packages: pip install inference-sdk aiortc")
            print("  2. Or install all requirements: pip install -r requirements.txt")
            print("  3. Restart the application")
            print("   Note: aiortc is required for WebRTC functionality")
            print("="*60 + "\n")
            return False
        
        if not self.WebcamSource or not self.StreamConfig:
            print("❌ WebRTC components not available")
            print("   This usually means inference-sdk was not installed correctly")
            print("   Install with: pip install inference-sdk")
            return False
        
        if self.session_active:
            print("⚠️ WebRTC session already active")
            return False
        
        try:
            # Configure video source (webcam)
            # Note: WebcamSource may use the default camera (index 0)
            # Camera index selection might not be directly supported
            # If you need specific camera selection, you may need to set it as the default
            # or use environment variables/OS settings
            source = self.WebcamSource(resolution=resolution)
            
            # Configure streaming options
            config = self.StreamConfig(
                stream_output=["output_image"],  # Get video back with annotations
                data_output=["predictions"],      # Get prediction data via datachannel
                requested_plan="webrtc-gpu-medium",  # Options: webrtc-gpu-small, webrtc-gpu-medium, webrtc-gpu-large
                requested_region="us",               # Options: us, eu, ap
            )
            
            # Store callbacks
            self.frame_callback = frame_callback
            self.detection_callback = detection_callback
            
            # Create streaming session
            # using model ID as workflow ID for direct inference
            model_id = f"{self.roboflow_project_name}/{self.roboflow_model_version}"
            print(f"📡 Starting WebRTC stream with: {model_id}")
            
            self.session = self.client.webrtc.stream(
                source=source,
                workflow=model_id,
                workspace=self.workspace_name,  # Required for model ID
                image_input="image",
                config=config
            )
            
            # Register frame handler
            @self.session.on_frame
            def show_frame(frame, metadata):
                """Handle incoming video frames"""
                # Convert frame to numpy array if needed
                if isinstance(frame, np.ndarray):
                    frame_np = frame
                else:
                    # Convert PIL or other formats to numpy
                    frame_np = np.array(frame)
                    if len(frame_np.shape) == 3 and frame_np.shape[2] == 3:
                        # Convert RGB to BGR for OpenCV
                        frame_np = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                
                # Store latest frame
                with self.detections_lock:
                    self.latest_frame = frame_np.copy()
                
                # Call user callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(frame_np, metadata)
                    except Exception as e:
                        print(f"⚠️ Error in frame callback: {e}")
            
            # Register data handler for predictions
            @self.session.on_data()
            def on_data(data: dict, metadata):
                """Handle prediction data via datachannel"""
                try:
                    # Parse detections from data
                    detections = self._parse_stream_data(data, metadata)
                    
                    # Store latest detections
                    with self.detections_lock:
                        self.latest_detections = detections
                    
                    # Call user callback if provided
                    if self.detection_callback:
                        try:
                            self.detection_callback(detections, metadata)
                        except Exception as e:
                            print(f"⚠️ Error in detection callback: {e}")
                    else:
                        # Default: print detection info
                        print(f"Frame {metadata.frame_id}: {len(detections)} marker(s) detected")
                        
                except Exception as e:
                    print(f"⚠️ Error processing detection data: {e}")
            
            self.session_active = True
            print("✅ WebRTC streaming session started")
            
            # Run session in background thread
            def run_session():
                try:
                    self.session.run()
                except Exception as e:
                    print(f"❌ WebRTC session error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    with self.session_lock:
                        self.session_active = False
                    print("🛑 WebRTC session stopped")
            
            session_thread = threading.Thread(target=run_session, daemon=True)
            session_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start WebRTC stream: {e}")
            import traceback
            traceback.print_exc()
            self.session_active = False
            return False
    
    def stop_webrtc_stream(self):
        """Stop WebRTC streaming session"""
        if not self.session_active or not self.session:
            return
        
        try:
            self.session.close()
            with self.session_lock:
                self.session_active = False
            print("✅ WebRTC stream stopped")
        except Exception as e:
            print(f"⚠️ Error stopping WebRTC stream: {e}")
    
    def get_latest_detections(self) -> List[Dict]:
        """Get latest detections from WebRTC stream"""
        with self.detections_lock:
            return self.latest_detections.copy()
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get latest frame from WebRTC stream"""
        with self.detections_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def _parse_stream_data(self, data: dict, metadata) -> List[Dict]:
        """Parse detection data from WebRTC stream"""
        detections = []
        
        try:
            # Extract predictions from data
            predictions = []
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            if isinstance(data, dict):
                # Check common keys for predictions
                for key in ['predictions', 'results', 'output', 'detections', 'objects', 'data']:
                    if key in data:
                        preds = data[key]
                        if isinstance(preds, list):
                            predictions = preds
                            break
                        elif isinstance(preds, dict):
                            # Handle nested predictions: data['predictions']['predictions']
                            if 'predictions' in preds and isinstance(preds['predictions'], list):
                                predictions = preds['predictions']
                                break
                            # Handle case where output name is unknown but contains 'predictions'
                            for subkey in preds.keys():
                                if isinstance(preds[subkey], dict) and 'predictions' in preds[subkey]:
                                    if isinstance(preds[subkey]['predictions'], list):
                                        predictions = preds[subkey]['predictions']
                                        break
                            if predictions:
                                break
            
            # Parse each prediction
            for idx, pred in enumerate(predictions):
                if not isinstance(pred, dict):
                    continue
                
                # Extract class/color
                color = pred.get('class', pred.get('label', pred.get('name', 'Unknown')))
                
                # Extract bounding box
                # Roboflow standard: x, y are centers
                w = float(pred.get('width', pred.get('w', 0)))
                h = float(pred.get('height', pred.get('h', 0)))
                
                if 'bbox' in pred and isinstance(pred['bbox'], dict):
                    bbox = pred['bbox']
                    w = float(bbox.get('width', w))
                    h = float(bbox.get('height', h))
                    
                    if 'x_min' in bbox:
                        x_min = float(bbox['x_min'])
                        y_min = float(bbox['y_min'])
                    else:
                        # Assume x, y are centers
                        x_center = float(bbox.get('x', 0))
                        y_center = float(bbox.get('y', 0))
                        x_min = x_center - w / 2
                        y_min = y_center - h / 2
                else:
                    # Direct keys
                    if 'x_min' in pred:
                        x_min = float(pred['x_min'])
                        y_min = float(pred['y_min'])
                    else:
                        x_center = float(pred.get('x', 0))
                        y_center = float(pred.get('y', 0))
                        x_min = x_center - w / 2
                        y_min = y_center - h / 2

                if w <= 0 or h <= 0:
                    continue
                
                # Extract class/color
                color_raw = str(pred.get('class', pred.get('label', pred.get('name', 'Unknown'))))
                color = color_raw # Keep raw name
                
                # Extract confidence
                confidence = pred.get('confidence', pred.get('score', 0.8))
                confidence_raw = float(confidence) if confidence <= 1.0 else float(confidence) / 100.0
                confidence_percent = confidence_raw * 100
                
                # Log what we found
                print(f"      - Stream Found '{color_raw}' with {confidence_percent:.1f}% confidence")
                
                # Note: Local filtering and 'cable' skipping removed as requested
                # confidence_raw < self.min_confidence check removed
                
                
                detections.append({
                    "component_id": idx + 1,
                    "component_type": "Cable Marker",
                    "primary_color": color,
                    "color_pattern": [color],
                    "bounding_box": {"x": int(x_min), "y": int(y_min), "width": int(w), "height": int(h)},
                    "confidence": round(confidence_percent, 2),
                    "center": (int(x_min + w / 2), int(y_min + h / 2)),
                    "stripe_count": 3
                })
            
        except Exception as e:
            print(f"⚠️ Error parsing stream data: {e}")
        
        return detections
    
    def _parse_roboflow_predictions(self, result, image_width: int, image_height: int) -> List[Dict]:
        """Parse predictions from Roboflow Python SDK model.predict()"""
        markers = []
        
        try:
            # Roboflow model returns a prediction object with a 'predictions' attribute
            predictions = []
            
            # Check for various result formats
            if hasattr(result, 'json') and callable(result.json):
                # Get JSON representation
                result_dict = result.json()
                if 'predictions' in result_dict:
                    predictions = result_dict['predictions']
            elif hasattr(result, 'predictions'):
                predictions = result.predictions
            elif isinstance(result, dict):
                if 'predictions' in result:
                    predictions = result['predictions']
            
            # Parse each prediction
            for idx, pred in enumerate(predictions):
                # Convert prediction object to dict if needed
                if hasattr(pred, '__dict__'):
                    pred_dict = pred.__dict__
                elif isinstance(pred, dict):
                    pred_dict = pred
                else:
                    continue
                
                # Check for nested json_prediction (common in Roboflow SDK responses)
                if 'json_prediction' in pred_dict and isinstance(pred_dict['json_prediction'], dict):
                    # Use the nested prediction data
                    pred_data = pred_dict['json_prediction']
                    # Merge specific fields from parent if missing in nested
                    if 'class' not in pred_data and 'class' in pred_dict:
                        pred_data['class'] = pred_dict['class']
                    if 'confidence' not in pred_data and 'confidence' in pred_dict:
                        pred_data['confidence'] = pred_dict['confidence']
                    pred_dict = pred_data
                
                # Extract class/color
                color_raw = str(pred_dict.get('class', pred_dict.get('class_name', 'Unknown')))
                color = color_raw # Keep raw name
                
                # Extract confidence
                confidence = pred_dict.get('confidence', 0.8)
                confidence_raw = float(confidence) if confidence <= 1.0 else float(confidence) / 100.0
                confidence_percent = confidence_raw * 100
                
                # Extract bounding box (Roboflow format: x, y are centers, width, height)
                x_center = float(pred_dict.get('x', 0))
                y_center = float(pred_dict.get('y', 0))
                w = float(pred_dict.get('width', 0))
                h = float(pred_dict.get('height', 0))
                
                if w <= 0 or h <= 0:
                    continue
                
                # Calculate top-left corner
                x_min = x_center - w / 2
                y_min = y_center - h / 2
                
                markers.append({
                    "component_id": len(markers) + 1,
                    "component_type": "Cable Marker",
                    "primary_color": color,
                    "color_pattern": [color],
                    "bounding_box": {"x": int(x_min), "y": int(y_min), "width": int(w), "height": int(h)},
                    "confidence": round(confidence_percent, 2),
                    "center": (int(x_center), int(y_center)),
                    "stripe_count": 3
                })
            
        except Exception as e:
            print(f"⚠️ Error parsing Roboflow predictions: {e}")
            import traceback
            traceback.print_exc()
        
        return markers
    

    
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
        
        # Generate dynamic color from class name (no hardcoded color map)
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

        Returns:
            Dictionary indicating which features are available
        """
        return {
            "static_images": self._inference_initialized,
            "real_time_streaming": self._inference_initialized,
            "batch_video_processing": self._roboflow_initialized,
            "webrtc_available": self.WebcamSource is not None,
            "inference_sdk": self._inference_initialized,
            "roboflow_sdk": self._roboflow_initialized
        }

    def predict_video(self, video_path: str, fps: int = 5,
                     prediction_type: str = "batch-video") -> Tuple[str, str, int]:
        """
        Submit a video for batch processing using Roboflow Python SDK

        Args:
            video_path: Path to the video file
            fps: Frames per second to process (default: 5)
            prediction_type: Type of prediction ("batch-video")

        Returns:
            Tuple of (job_id, signed_url, expire_time)

        Raises:
            RuntimeError: If Roboflow SDK is not initialized or video processing fails
        """
        if not self._roboflow_initialized or not self.model:
            raise RuntimeError("Roboflow Python SDK not initialized. Batch video processing is not available.")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            print(f"🎥 Submitting video for batch processing: {os.path.basename(video_path)}")
            print(f"   FPS: {fps}, Type: {prediction_type}")

            # Submit video for processing
            job_id, signed_url, expire_time = self.model.predict_video(
                video_path,
                fps=fps,
                prediction_type=prediction_type,
            )

            print(f"✅ Video processing job submitted successfully")
            print(f"   Job ID: {job_id}")
            print(f"   Results URL: {signed_url}")
            print(f"   Expires: {expire_time}")

            return job_id, signed_url, expire_time

        except Exception as e:
            print(f"❌ Failed to submit video for processing: {e}")
            raise RuntimeError(f"Video processing submission failed: {e}")

    def poll_until_video_results(self, job_id: str, timeout: int = 300,
                                poll_interval: int = 10) -> Dict:
        """
        Poll for video processing results until completion

        Args:
            job_id: Job ID returned from predict_video
            timeout: Maximum time to wait in seconds (default: 300 = 5 minutes)
            poll_interval: Time between polls in seconds (default: 10)

        Returns:
            Dictionary containing the processing results

        Raises:
            TimeoutError: If processing doesn't complete within timeout
            RuntimeError: If Roboflow SDK is not initialized or polling fails
        """
        if not self._roboflow_initialized or not self.model:
            raise RuntimeError("Roboflow Python SDK not initialized. Batch video processing is not available.")

        try:
            print(f"⏳ Polling for video results (Job ID: {job_id})")
            print(f"   Timeout: {timeout}s, Poll interval: {poll_interval}s")

            start_time = time.time()

            while time.time() - start_time < timeout:
                results = self.model.poll_until_video_results(job_id)

                if results and 'status' in results:
                    status = results.get('status', '').lower()

                    if status == 'complete' or status == 'completed':
                        print(f"✅ Video processing completed!")
                        print(f"   Found {len(results.get('predictions', []))} frames with detections")
                        return results
                    elif status in ['failed', 'error']:
                        raise RuntimeError(f"Video processing failed: {results}")
                    else:
                        print(f"   Status: {status} - waiting...")

                time.sleep(poll_interval)

            # Timeout reached
            raise TimeoutError(f"Video processing did not complete within {timeout} seconds")

        except Exception as e:
            print(f"❌ Failed to poll video results: {e}")
            raise RuntimeError(f"Video result polling failed: {e}")

    def process_video_batch(self, video_path: str, fps: int = 5,
                           timeout: int = 300) -> Dict:
        """
        Complete workflow for batch video processing: submit video and wait for results

        Args:
            video_path: Path to the video file
            fps: Frames per second to process
            timeout: Maximum time to wait for results in seconds

        Returns:
            Dictionary containing the processing results

        Raises:
            RuntimeError: If video processing fails
            TimeoutError: If processing times out
        """
        try:
            # Submit video for processing
            job_id, signed_url, expire_time = self.predict_video(video_path, fps=fps)

            # Wait for results
            results = self.poll_until_video_results(job_id, timeout=timeout)

            return results

        except Exception as e:
            print(f"❌ Batch video processing failed: {e}")
            raise

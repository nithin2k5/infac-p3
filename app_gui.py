"""
Professional Cable Marker Detection Application
Modern UI with advanced detection capabilities
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from roboflow_detector import RoboflowDetector
from gpio_controller import GPIOController
import os
from datetime import datetime
import threading
import time


class CableMarkerApp:
    """Professional cable marker detection application"""
    
    def __init__(self):
        # Set appearance with professional theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Professional color palette
        self.colors = {
            "primary": "#2563EB",  # Professional blue
            "primary_dark": "#1E40AF",  # Darker blue for hover
            "button": "#2D2D2D",  # Unified button color
            "button_hover": "#3D3D3D",  # Unified button hover
            "background": "#121212",
            "surface": "#1E1E1E",
            "surface_light": "#2D2D2D",
            "text_primary": "#FFFFFF",
            "text_secondary": "#B0B0B0",
            "border": "#404040",  # Subtle borders
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "info": "#2196F3"
        }
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Cable Marker Detection System")
        self.root.geometry("1700x950")
        self.root.configure(fg_color=self.colors["background"])
        
        # Initialize Roboflow detector with accuracy settings
        # min_confidence: 0.3 = 30% (lower = more detections, higher = fewer false positives)
        # grouping_distance: 150px vertical, 300px horizontal for grouping stripes
        self.detector = RoboflowDetector(min_confidence=0.3, grouping_distance=150, grouping_horizontal_distance=300)
        
        # Initialize GPIO controller
        self.gpio_controller = GPIOController(pin1=18, pin2=23, pin3=24)
        
        # Setup detection storage directory
        self.detections_dir = "detections"
        os.makedirs(self.detections_dir, exist_ok=True)
        if self.detector.use_http:
            self.detector_type = "Roboflow Workflow"
            print("✅ Using Roboflow Workflow Detector")
        else:
            print("❌ Roboflow detector not available - requests library missing")
            self.detector_type = "Not Available"
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.current_display = None
        self.image_path = None
        self.detected_markers = []
        self.all_detected_markers = []  # Store all detections before filtering
        
        # Camera variables
        self.camera = None
        self.camera_active = False
        self.camera_index = 0
        self.capture_thread = None
        self.show_detection_pause = False  # Flag to pause camera feed to show detection
        self.auto_detect_enabled = True  # Enable automatic detection on live feed
        self.detection_interval = 2.0  # Run detection every 2 seconds
        self.last_detection_time = 0  # Track last detection time
        self.live_detected_markers = []  # Store markers detected from live feed
        self.auto_detect_var = None  # Will be set in UI setup
        self.detection_running = False  # Flag to prevent multiple simultaneous detections
        self.detection_thread = None  # Thread for running detection
        self.latest_frame = None  # Store latest frame for detection
        self.detections_drawn_frame = None  # Cache the frame with detections drawn
        self.frame_lock = threading.Lock()  # Lock for thread-safe frame access
        
        # Color filter
        self.selected_color_filter = "All"  # Default: detect all colors
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Left sidebar
        self.create_sidebar()
        
        # Main content area
        self.create_main_area()
        
        # Bottom status bar
        self.create_status_bar()
        
    def create_sidebar(self):
        """Create left sidebar with controls"""
        sidebar = ctk.CTkFrame(
            self.root, 
            width=380, 
            corner_radius=0,
            fg_color=self.colors["surface"]
        )
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Header section with gradient effect
        header_frame = ctk.CTkFrame(
            sidebar,
            fg_color=self.colors["primary"],
            corner_radius=0,
            height=120
        )
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        # Title with better styling
        title = ctk.CTkLabel(
            header_frame,
            text="Cable Marker",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title.pack(pady=(20, 5), padx=20)
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Detection System",
            font=ctk.CTkFont(size=14),
            text_color="#E0E0E0"
        )
        subtitle.pack(pady=(0, 15), padx=20)
        
        # Status badge
        status_badge = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_badge.pack(fill="x", padx=20, pady=(20, 10))
        
        badge = ctk.CTkFrame(
            status_badge,
            fg_color=self.colors["success"],
            corner_radius=15,
            height=30
        )
        badge.pack(fill="x")
        badge.pack_propagate(False)
        
        self.detector_label = ctk.CTkLabel(
            badge,
            text=f"● {getattr(self, 'detector_type', 'Unknown')}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white"
        )
        self.detector_label.pack(pady=6)
        
        # Section label
        actions_label = ctk.CTkLabel(
            sidebar,
            text="INPUT SOURCE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        actions_label.pack(pady=(10, 15), padx=20, anchor="w")
        
        # Input source selection
        source_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        source_frame.pack(fill="x", padx=20, pady=5)
        
        self.load_btn = ctk.CTkButton(
            source_frame,
            text="📁 Load from File",
            command=self.load_image,
            height=48,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_spacing=10,
            border_width=1,
            border_color=self.colors["border"]
        )
        self.load_btn.pack(fill="x", pady=(0, 8))
        
        # Camera selection dropdown
        camera_select_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
        camera_select_frame.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            camera_select_frame,
            text="Camera:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(side="left", padx=(0, 10))
        
        self.camera_var = ctk.StringVar(value="Select Camera")
        self.camera_dropdown = ctk.CTkComboBox(
            camera_select_frame,
            values=self.get_available_cameras(),
            variable=self.camera_var,
            command=self.on_camera_selected,
            width=180,
            height=35,
            corner_radius=6
        )
        self.camera_dropdown.pack(side="left", fill="x", expand=True)
        
        # Camera control buttons
        self.camera_start_btn = ctk.CTkButton(
            source_frame,
            text="📷 Start Camera",
            command=self.start_camera,
            height=48,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.camera_start_btn.pack(fill="x", pady=(0, 8))
        
        self.camera_stop_btn = ctk.CTkButton(
            source_frame,
            text="⏹ Stop Camera",
            command=self.stop_camera,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.camera_stop_btn.pack(fill="x", pady=(0, 8))
        
        self.capture_btn = ctk.CTkButton(
            source_frame,
            text="📸 Capture Frame",
            command=self.capture_frame,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.capture_btn.pack(fill="x", pady=(0, 8))
        
        # Auto-detection toggle
        auto_detect_frame = ctk.CTkFrame(source_frame, fg_color="transparent")
        auto_detect_frame.pack(fill="x", pady=(0, 15))
        
        self.auto_detect_var = ctk.BooleanVar(value=True)
        self.auto_detect_switch = ctk.CTkSwitch(
            auto_detect_frame,
            text="Auto-detect on Live Feed",
            variable=self.auto_detect_var,
            command=self.toggle_auto_detect,
            font=ctk.CTkFont(size=12)
        )
        self.auto_detect_switch.pack(side="left", padx=(0, 10))
        
        self.auto_detect_status = ctk.CTkLabel(
            auto_detect_frame,
            text="● ON",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["success"]
        )
        self.auto_detect_status.pack(side="left")
        
        # Separator
        separator1 = ctk.CTkFrame(sidebar, height=1, fg_color=self.colors["surface_light"])
        separator1.pack(fill="x", padx=20, pady=(0, 15))
        
        # Detection section
        detection_label = ctk.CTkLabel(
            sidebar,
            text="DETECTION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        detection_label.pack(pady=(0, 15), padx=20, anchor="w")
        
        # Color filter selection
        filter_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["surface_light"], corner_radius=8)
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            filter_frame,
            text="Filter by Color:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"]
        ).pack(anchor="w", padx=12, pady=(10, 5))
        
        self.color_filter_var = ctk.StringVar(value="All")
        color_options = ["All", "White", "Yellow", "Blue", "Pink", "Green"]
        
        self.color_filter_dropdown = ctk.CTkComboBox(
            filter_frame,
            values=color_options,
            variable=self.color_filter_var,
            command=self.on_color_filter_changed,
            width=300,
            height=35,
            corner_radius=6,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            state="readonly"
        )
        self.color_filter_dropdown.pack(padx=12, pady=(0, 10), fill="x")
        
        # Info label showing filter status
        self.filter_info_label = ctk.CTkLabel(
            filter_frame,
            text="Showing: All colors",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_secondary"]
        )
        self.filter_info_label.pack(padx=12, pady=(0, 10))
        
        # Secondary actions
        secondary_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        secondary_frame.pack(fill="x", padx=20, pady=5)
        
        self.reset_btn = ctk.CTkButton(
            secondary_frame,
            text="Reset View",
            command=self.reset_view,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.reset_btn.pack(fill="x", pady=(0, 6))
        
        self.save_btn = ctk.CTkButton(
            secondary_frame,
            text="Save Results",
            command=self.save_results,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.save_btn.pack(fill="x", pady=(0, 6))
        
        self.export_btn = ctk.CTkButton(
            secondary_frame,
            text="Export Data",
            command=self.export_data,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.export_btn.pack(fill="x", pady=(0, 6))
        
        # Separator with modern styling
        separator = ctk.CTkFrame(sidebar, height=1, fg_color=self.colors["surface_light"])
        separator.pack(fill="x", padx=20, pady=(20, 15))
        
        # Results section header
        results_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        results_header.pack(fill="x", padx=20, pady=(0, 10))
        
        results_label = ctk.CTkLabel(
            results_header,
            text="RESULTS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        results_label.pack(side="left")
        
        # Stats card with modern design
        self.stats_frame = ctk.CTkFrame(
            sidebar,
            fg_color=self.colors["surface_light"],
            corner_radius=10
        )
        self.stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        stats_inner = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=15, pady=12)
        
        self.markers_count = ctk.CTkLabel(
            stats_inner,
            text="0",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.markers_count.pack(anchor="w")
        
        ctk.CTkLabel(
            stats_inner,
            text="Markers Detected",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))
        
        # Results text with better styling
        results_container = ctk.CTkFrame(
            sidebar,
            fg_color=self.colors["surface_light"],
            corner_radius=10
        )
        results_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.results_text = ctk.CTkTextbox(
            results_container,
            font=ctk.CTkFont(family="SF Mono", size=11),
            wrap="word",
            fg_color="transparent",
            text_color=self.colors["text_primary"],
            corner_radius=0
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def create_main_area(self):
        """Create main display area"""
        main_frame = ctk.CTkFrame(
            self.root, 
            corner_radius=0,
            fg_color=self.colors["background"]
        )
        main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header bar
        header_bar = ctk.CTkFrame(
            main_frame,
            height=60,
            corner_radius=0,
            fg_color=self.colors["surface"]
        )
        header_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_bar.grid_propagate(False)
        
        header_title = ctk.CTkLabel(
            header_bar,
            text="Image Preview",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        header_title.pack(side="left", padx=25, pady=18)
        
        # Canvas for image display with modern card design
        self.canvas_frame = ctk.CTkFrame(
            main_frame,
            fg_color=self.colors["surface"],
            corner_radius=12
        )
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=(15, 25))
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Placeholder with better design
        placeholder_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        placeholder_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.placeholder_icon = ctk.CTkLabel(
            placeholder_frame,
            text="📷",
            font=ctk.CTkFont(size=64)
        )
        self.placeholder_icon.pack(pady=(0, 15))
        
        self.placeholder = ctk.CTkLabel(
            placeholder_frame,
            text="Load an image to begin detection",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        self.placeholder.pack()
        
        ctk.CTkLabel(
            placeholder_frame,
            text="Supported formats: JPG, PNG, BMP, TIFF",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(5, 0))
        
        # Image label (will be created when image is loaded)
        self.image_label = None
        
    def create_status_bar(self):
        """Create bottom status bar"""
        status_frame = ctk.CTkFrame(
            self.root, 
            height=40, 
            corner_radius=0,
            fg_color=self.colors["surface"]
        )
        status_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        status_frame.grid_propagate(False)
        
        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["success"]
        )
        self.status_indicator.pack(side="left", padx=(20, 10), pady=0)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready - Load an image to start",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="left", padx=0, pady=0)
        
        # Version/Info
        version_label = ctk.CTkLabel(
            status_frame,
            text="v1.0.0",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_secondary"]
        )
        version_label.pack(side="right", padx=20, pady=0)
        
    def load_image(self):
        """Load image from file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.image_path = file_path
            self.original_image = cv2.imread(file_path)
            
            if self.original_image is None:
                messagebox.showerror("Error", "Failed to load image!")
                return
            
            self.current_display = self.original_image.copy()
            self.display_image(self.current_display)
            
            # Enable reset button
            self.reset_btn.configure(state="normal")
            
            # Clear previous results
            self.detected_markers = []
            self.all_detected_markers = []
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", "✓ Image loaded. Detecting markers automatically...")
            self.markers_count.configure(text="0")
            # Reset color filter to "All"
            self.color_filter_var.set("All")
            self.selected_color_filter = "All"
            
            filename = os.path.basename(file_path)
            self.status_label.configure(text=f"Loading: {filename}...")
            self.status_indicator.configure(text_color=self.colors["info"])
            self.root.update()
            
            # Automatically detect markers
            self.detect_markers()
            
    def display_image(self, image):
        """Display image on canvas - optimized for speed"""
        if image is None:
            return
        
        try:
            # Convert BGR to RGB (required for display)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get canvas dimensions
            canvas_width = self.canvas_frame.winfo_width()
            canvas_height = self.canvas_frame.winfo_height()
            
            # Skip if canvas is too small
            if canvas_width < 100 or canvas_height < 100:
                return
            
            # Scale image to fit (use faster INTER_LINEAR)
            height, width = image_rgb.shape[:2]
            scale = min(canvas_width / width, canvas_height / height) * 0.95
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Fast resize with INTER_LINEAR (faster than default INTER_CUBIC)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Convert to PhotoImage
            pil_image = Image.fromarray(image_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Display
            if self.image_label is None:
                self.image_label = ctk.CTkLabel(self.canvas_frame, text="")
                self.image_label.place(relx=0.5, rely=0.5, anchor="center")
            
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep reference
        except Exception as e:
            # Silently handle errors to avoid blocking
            pass
        
    def detect_markers(self):
        """Run marker detection (automatically triggered)"""
        if self.original_image is None:
            return
        
        self.status_label.configure(text="Processing... Detecting markers")
        self.status_indicator.configure(text_color=self.colors["info"])
        self.root.update()
        
        # Run detection - get all markers
        self.all_detected_markers = self.detector.detect_markers(self.original_image)
        
        # Debug: Print all detected colors
        if self.all_detected_markers:
            all_colors = [m.get('primary_color', 'Unknown') for m in self.all_detected_markers]
            print(f"📊 Detected {len(self.all_detected_markers)} markers with colors: {set(all_colors)}")
        
        # Apply color filter
        self.apply_color_filter()
        
        # Draw results (only filtered markers)
        self.processed_image = self.detector.draw_detections(
            self.original_image, 
            self.detected_markers
        )
        
        # Display
        self.display_image(self.processed_image)
        
        # Update results
        self.update_results()
        
        # Automatically save detection image
        saved_path = self.auto_save_detection()
        if saved_path:
            print(f"💾 Detection image saved to: {saved_path}")
        
        # Control GPIO pins based on detected colors
        self.gpio_controller.process_detected_colors(self.detected_markers)
        
        # Enable export buttons
        self.save_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        
        marker_count = len(self.detected_markers)
        total_count = len(self.all_detected_markers)
        filter_text = f" ({total_count} total)" if self.selected_color_filter != "All" else ""
        save_text = f" | Saved to detections/" if saved_path else ""
        self.status_label.configure(
            text=f"Detection complete - Found {marker_count} marker(s){filter_text}{save_text}"
        )
        self.status_indicator.configure(text_color=self.colors["success"])
        
        # If camera is active, pause feed to show detection for 5 seconds
        if self.camera_active:
            self.show_detection_pause = True
            self.status_label.configure(
                text=f"Showing detection for 5 seconds... Found {marker_count} marker(s){filter_text}{save_text}"
            )
            # Resume camera feed after 5 seconds
            self.root.after(5000, self.resume_camera_feed)
    
    def on_color_filter_changed(self, choice):
        """Handle color filter selection change"""
        if not choice:
            return
            
        self.selected_color_filter = choice
        print(f"🎨 Color filter changed to: '{choice}'")
        
        # Update filter info label
        if hasattr(self, 'filter_info_label'):
            if choice == "All":
                self.filter_info_label.configure(text="Showing: All colors")
            else:
                self.filter_info_label.configure(text=f"Showing: {choice} only")
        
        if self.all_detected_markers:
            # Re-apply filter to existing detections
            self.apply_color_filter()
            
            # Redraw with filtered results
            if self.original_image is not None:
                self.processed_image = self.detector.draw_detections(
                    self.original_image, 
                    self.detected_markers
                )
                self.display_image(self.processed_image)
                self.update_results()
                
                # Update GPIO pins based on filtered results
                self.gpio_controller.process_detected_colors(self.detected_markers)
                
                # Update status
                marker_count = len(self.detected_markers)
                total_count = len(self.all_detected_markers)
                if choice != "All":
                    self.status_label.configure(
                        text=f"Filtered: {marker_count} {choice.lower()} marker(s) (of {total_count} total)"
                    )
                else:
                    self.status_label.configure(
                        text=f"Showing all {total_count} marker(s)"
                    )
        else:
            print("⚠️ No markers detected yet. Run detection first.")
            if hasattr(self, 'filter_info_label'):
                self.filter_info_label.configure(text="No detections yet")
    
    def apply_color_filter(self):
        """Filter markers based on selected color"""
        if self.selected_color_filter == "All":
            self.detected_markers = self.all_detected_markers.copy()
        else:
            # Filter by selected color (case-insensitive, handle various formats)
            filter_color = self.selected_color_filter.lower().strip()
            
            # Normalize color names for matching
            color_normalizations = {
                "white": ["white", "whites", "white-stripe", "white-stripes"],
                "yellow": ["yellow", "yellows", "yellow-stripe", "yellow-stripes"],
                "blue": ["blue", "blues", "blue-stripe", "blue-stripes"],
                "pink": ["pink", "pinks", "pink-stripe", "pink-stripes"],
                "green": ["green", "greens", "green-stripe", "green-stripes"]
            }
            
            # Get all possible variations for the selected color
            color_variations = color_normalizations.get(filter_color, [filter_color])
            
            # Filter markers - check if color matches any variation
            self.detected_markers = []
            for marker in self.all_detected_markers:
                marker_color = marker.get('primary_color', '').lower().strip()
                
                # Check exact match or if marker color contains filter color
                if marker_color in color_variations or any(var in marker_color for var in color_variations):
                    self.detected_markers.append(marker)
                # Also check if filter color is in marker color (for compound names)
                elif filter_color in marker_color:
                    self.detected_markers.append(marker)
        
        # Re-number the filtered markers
        for idx, marker in enumerate(self.detected_markers, 1):
            marker["component_id"] = idx
        
        # Debug output
        print(f"🔍 Filter: '{self.selected_color_filter}' -> Found {len(self.detected_markers)}/{len(self.all_detected_markers)} markers")
        if self.detected_markers:
            colors_found = [m.get('primary_color', 'Unknown') for m in self.detected_markers]
            print(f"   Colors found: {set(colors_found)}")
        
    def update_results(self):
        """Update results display"""
        self.results_text.delete("1.0", "end")
        
        if not self.detected_markers:
            self.results_text.insert("1.0", 
                "No markers detected in this image."
            )
            self.markers_count.configure(text="Markers: 0")
            return
        
        # Summary
        self.markers_count.configure(text=f"{len(self.detected_markers)}")
        
        # Detailed results with professional formatting
        results_text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        results_text += "  DETECTION RESULTS\n"
        results_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, marker in enumerate(self.detected_markers, 1):
            cable_id = marker['component_id']
            primary_color = marker.get('primary_color', 'Unknown')
            confidence = marker['confidence']
            
            results_text += f"┌─ Cable #{cable_id}\n"
            results_text += f"│  Color: {primary_color}\n"
            results_text += f"│  Confidence: {confidence:.1f}%\n"
            stripe_count = marker.get('stripe_count', 3)
            stripes_in_group = marker.get('stripes_in_group', stripe_count)
            results_text += f"│  Pattern: {'|' * stripe_count} ({stripes_in_group} stripes = 1 marking)\n"
            
            bbox = marker['bounding_box']
            results_text += f"│  Position: ({bbox['x']}, {bbox['y']})\n"
            results_text += f"│  Size: {bbox['width']} × {bbox['height']} px\n"
            
            if idx < len(self.detected_markers):
                results_text += "│\n"
            else:
                results_text += "└\n"
        
        results_text += "\n" + "─" * 40 + "\n"
        total_stripes = sum(m.get('stripes_in_group', m.get('stripe_count', 3)) for m in self.detected_markers)
        results_text += f"Total: {len(self.detected_markers)} marking(s) detected ({total_stripes} stripes total)\n"
        
        self.results_text.insert("1.0", results_text)
        
    def reset_view(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_display = self.original_image.copy()
            self.display_image(self.current_display)
            self.status_label.configure(text="Reset to original image")
            self.status_indicator.configure(text_color=self.colors["info"])
            
    def auto_save_detection(self):
        """Automatically save detection image with timestamp"""
        if self.processed_image is None:
            return None
        
        try:
            # Generate filename with timestamp and detection count
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            marker_count = len(self.detected_markers)
            total_count = len(self.all_detected_markers)
            
            # Include source filename if available
            if hasattr(self, 'image_path') and self.image_path:
                source_name = os.path.splitext(os.path.basename(self.image_path))[0]
                # Sanitize filename (remove invalid characters)
                source_name = "".join(c for c in source_name if c.isalnum() or c in ('-', '_'))[:30]
                filename = f"{timestamp}_{source_name}_{marker_count}markers.jpg"
            else:
                filename = f"{timestamp}_detection_{marker_count}markers.jpg"
            
            file_path = os.path.join(self.detections_dir, filename)
            
            # Save image
            success = cv2.imwrite(file_path, self.processed_image)
            if success:
                return file_path
            else:
                print(f"⚠️ Failed to save detection image to {file_path}")
                return None
        except Exception as e:
            print(f"⚠️ Error auto-saving detection image: {e}")
            return None
    
    def save_results(self):
        """Save annotated image (manual save with dialog)"""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No results to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ],
            initialdir=self.detections_dir  # Start in detections directory
        )
        
        if file_path:
            cv2.imwrite(file_path, self.processed_image)
            messagebox.showinfo("Success", f"Results saved to:\n{file_path}")
            self.status_label.configure(text=f"Saved: {os.path.basename(file_path)}")
            
    def export_data(self):
        """Export detection data to JSON"""
        if not self.detected_markers:
            messagebox.showwarning("Warning", "No data to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            import json
            
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "source_image": os.path.basename(self.image_path) if self.image_path else "unknown",
                "total_markers": len(self.detected_markers),
                "markers": self.detected_markers
            }
            
            with open(file_path, 'w') as f:
                if file_path.endswith('.json'):
                    json.dump(export_data, f, indent=2)
                else:
                    # Text format
                    f.write(f"Cable Marker Detection Report\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(f"Date: {export_data['timestamp']}\n")
                    f.write(f"Source: {export_data['source_image']}\n")
                    f.write(f"Total Markers: {export_data['total_markers']}\n\n")
                    
                    for marker in self.detected_markers:
                        f.write(f"\nMarker ID: {marker['component_id']}\n")
                        f.write(f"  Type: {marker['component_type']}\n")
                        f.write(f"  Pattern: {' → '.join(marker['color_pattern'])}\n")
                        f.write(f"  Confidence: {marker['confidence']}%\n")
                        f.write(f"  Bar: {'|' * marker['stripe_count']}\n")
            
            messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
            self.status_label.configure(text=f"Exported: {os.path.basename(file_path)}")
    
    def get_available_cameras(self):
        """Get list of available cameras"""
        cameras = ["Select Camera"]
        for i in range(10):  # Check first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(f"Camera {i}")
                cap.release()
        return cameras if len(cameras) > 1 else ["No Camera Found"]
    
    def on_camera_selected(self, choice):
        """Handle camera selection"""
        if choice and choice != "Select Camera" and "Camera" in choice:
            try:
                self.camera_index = int(choice.split()[-1])
                self.camera_start_btn.configure(state="normal")
            except:
                self.camera_index = 0
        else:
            self.camera_start_btn.configure(state="disabled")
    
    def start_camera(self):
        """Start camera feed"""
        if self.camera_active:
            return
        
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                messagebox.showerror("Error", f"Failed to open camera {self.camera_index}")
                return
            
            self.camera_active = True
            self.last_detection_time = 0  # Reset detection timer
            self.live_detected_markers = []  # Clear previous detections
            self.detections_drawn_frame = None  # Clear cached detection frame
            self.camera_start_btn.configure(state="disabled")
            self.camera_stop_btn.configure(state="normal")
            self.capture_btn.configure(state="normal")
            self.camera_dropdown.configure(state="disabled")
            
            # Start camera feed thread
            self.capture_thread = threading.Thread(target=self.update_camera_feed, daemon=True)
            self.capture_thread.start()
            
            auto_status = "enabled" if self.auto_detect_enabled else "disabled"
            self.status_label.configure(text=f"Camera {self.camera_index} active - Auto-detect {auto_status}")
            self.status_indicator.configure(text_color=self.colors["info"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
    
    def stop_camera(self):
        """Stop camera feed"""
        self.camera_active = False
        self.show_detection_pause = False  # Reset pause flag
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_start_btn.configure(state="normal")
        self.camera_stop_btn.configure(state="disabled")
        self.capture_btn.configure(state="disabled")
        self.camera_dropdown.configure(state="normal")
        
        # Clear camera view
        if self.placeholder:
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place(relx=0.5, rely=0.4, anchor="center")
        
        self.status_label.configure(text="Camera stopped")
        self.status_indicator.configure(text_color=self.colors["warning"])
    
    def run_detection_async(self, frame):
        """Run detection in a separate thread to avoid blocking camera feed"""
        if self.detection_running:
            return  # Skip if detection is already running
        
        self.detection_running = True
        def detect():
            try:
                # Get all markers (this may take time with API call)
                all_markers = self.detector.detect_markers(frame)
                
                # Apply color filter
                temp_all = self.all_detected_markers
                self.all_detected_markers = all_markers
                self.apply_color_filter()
                detected = self.detected_markers.copy()
                self.all_detected_markers = temp_all
                
                # Draw detections once (cache the result)
                if detected:
                    display_frame = self.detector.draw_detections(frame, detected)
                else:
                    display_frame = frame.copy()  # No detections, cache clean frame
                
                # Thread-safe update of shared data
                with self.frame_lock:
                    self.live_detected_markers = detected
                    self.detections_drawn_frame = display_frame
                
                print(f"✅ Detection complete: {len(detected)} marker(s) found")
                
                # Update UI in main thread (non-blocking)
                self.root.after(0, self.update_results)
                self.root.after(0, lambda: self.markers_count.configure(text=f"{len(detected)}"))
                
                # Control GPIO pins
                self.gpio_controller.process_detected_colors(detected)
                
                # Update status
                marker_count = len(detected)
                if marker_count > 0:
                    status_text = f"Live detection: {marker_count} marker(s) found"
                    self.root.after(0, lambda t=status_text: self.status_label.configure(text=t))
                    self.root.after(0, lambda: self.status_indicator.configure(text_color=self.colors["success"]))
                else:
                    self.root.after(0, lambda: self.status_label.configure(
                        text="Live detection: No markers found"
                    ))
                    self.root.after(0, lambda: self.status_indicator.configure(text_color=self.colors["info"]))
                
            except Exception as e:
                print(f"⚠️ Detection error in live feed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.detection_running = False
        
        # Start detection in background thread (non-blocking)
        self.detection_thread = threading.Thread(target=detect, daemon=True)
        self.detection_thread.start()
    
    def update_camera_feed(self):
        """Update camera feed in a separate thread with automatic detection (non-blocking)"""
        # Hide placeholder once
        if self.placeholder:
            self.root.after(0, lambda: self.placeholder.place_forget())
        if hasattr(self, 'placeholder_icon'):
            self.root.after(0, lambda: self.placeholder_icon.place_forget())
        
        frame_count = 0
        while self.camera_active and self.camera:
            # Skip updating if showing detection pause
            if self.show_detection_pause:
                time.sleep(0.1)  # Check less frequently when paused
                continue
                
            ret, frame = self.camera.read()
            if ret:
                frame_count += 1
                
                # Store reference (no copy for speed)
                self.original_image = frame
                
                # Check if it's time to run detection (non-blocking)
                current_time = time.time()
                should_detect = (self.auto_detect_enabled and 
                               not self.detection_running and
                               (current_time - self.last_detection_time) >= self.detection_interval)
                
                if should_detect:
                    # Start detection in background thread (non-blocking)
                    self.last_detection_time = current_time
                    print(f"🔍 Starting detection at frame {frame_count}...")
                    self.run_detection_async(frame.copy())
                
                # Display frame immediately (don't wait for detection)
                # Use cached detection frame if available (thread-safe)
                try:
                    with self.frame_lock:
                        if self.detections_drawn_frame is not None:
                            # Use the pre-drawn detection frame (fast)
                            display_frame = self.detections_drawn_frame
                        else:
                            # No detections yet, show raw frame
                            display_frame = frame
                except:
                    # Fallback if lock fails
                    display_frame = frame
                
                # Display frame (non-blocking, always smooth)
                self.display_image(display_frame)
                
                # Enable reset button (only once)
                if frame_count == 1:
                    self.root.after(0, lambda: self.reset_btn.configure(state="normal"))
            else:
                break
            
            # Sleep for smooth 30 FPS
            time.sleep(0.033)
    
    def capture_frame(self):
        """Capture current frame from camera"""
        if not self.camera_active or self.original_image is None:
            messagebox.showwarning("Warning", "No camera frame available")
            return
        
        # Use current frame
        self.current_display = self.original_image.copy()
        self.display_image(self.current_display)
        
        # Clear previous results
        self.detected_markers = []
        self.all_detected_markers = []
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "✓ Frame captured. Detecting markers automatically...")
        self.markers_count.configure(text="0")
        # Reset color filter to "All"
        self.color_filter_var.set("All")
        self.selected_color_filter = "All"
        
        # Set image_path to None for camera captures (for filename generation)
        self.image_path = None
        
        self.status_label.configure(text="Frame captured. Detecting...")
        self.status_indicator.configure(text_color=self.colors["info"])
        self.root.update()
        
        # Automatically detect markers
        self.detect_markers()
    
    def toggle_auto_detect(self):
        """Toggle automatic detection on live feed"""
        self.auto_detect_enabled = self.auto_detect_var.get()
        if self.auto_detect_enabled:
            self.auto_detect_status.configure(text="● ON", text_color=self.colors["success"])
            self.status_label.configure(text="Auto-detection enabled - Detecting every 2 seconds")
        else:
            self.auto_detect_status.configure(text="● OFF", text_color=self.colors["text_secondary"])
            self.status_label.configure(text="Auto-detection disabled")
        print(f"🔄 Auto-detection: {'ON' if self.auto_detect_enabled else 'OFF'}")
    
    def resume_camera_feed(self):
        """Resume camera feed after showing detection"""
        if self.camera_active:
            self.show_detection_pause = False
            self.status_label.configure(text="Camera feed resumed")
            self.status_indicator.configure(text_color=self.colors["info"])
            
    def run(self):
        """Start the application"""
        # Cleanup on close
        def on_closing():
            if self.camera_active:
                self.stop_camera()
            # Cleanup GPIO
            self.gpio_controller.cleanup()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = CableMarkerApp()
    app.run()


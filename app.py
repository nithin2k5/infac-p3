"""
Cable Marker Detection System
Simple, Professional Interface
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


# Check if running on Raspberry Pi
IS_RASPBERRY_PI = os.path.exists('/proc/device-tree/model') and \
                  'Raspberry Pi' in open('/proc/device-tree/model', 'r').read()

if IS_RASPBERRY_PI:
    print("🍓 Running on Raspberry Pi - Optimized mode enabled")
else:
    print("💻 Running on desktop - Standard mode")


class CableMarkerApp:
    """Simple and professional cable marker detection application"""
    
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")  # Updated theme
        
        # Classic Professional Dark Palette
        self.colors = {
            "bg": "#1e2228",             # Classic dark IDE background
            "surface": "#252b35",        # Slightly elevated surface
            "surface2": "#2e3440",       # Card / input background (Nord-inspired)
            "primary": "#5b8dd9",        # Muted steel blue
            "primary_hover": "#4a76c0",  # Slightly darker steel blue
            "success": "#5cb85c",        # Classic bootstrap green
            "warning": "#d9a64a",        # Muted amber
            "error": "#c0392b",          # Classic dark red
            "text": "#d8dee9",           # Soft off-white (easy on the eyes)
            "text_secondary": "#636d7e", # Classic muted grey
            "border": "#3b4252"          # Subtle slate border
        }
        
        # Main window configuration
        self.root = ctk.CTk()
        self.root.title("cable marker")
        self.root.geometry("480x320" if IS_RASPBERRY_PI else "800x480")
        self.root.minsize(480, 320)
        self.root.configure(fg_color=self.colors["bg"])
        
        # Initialize detector
        self.detector = RoboflowDetector(
            min_confidence=0.40,
            grouping_distance=250,
            grouping_horizontal_distance=500
        )
        
        # Initialize GPIO
        self.gpio_controller = GPIOController(pin1=18, pin2=23, pin3=24)
        
        # Setup directories
        self.detections_dir = "detections"
        os.makedirs(self.detections_dir, exist_ok=True)
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.current_display = None
        self.image_path = None
        self.detected_markers = []
        self.detected_markers = []
        self.all_detected_markers = []
        
        # ROI Variables
        self.roi = None  # (x, y, w, h) or None
        self.roi_selecting = False
        self.roi_start_point = None
        self.roi_current_point = None
        
        # Camera variables
        self.camera = None
        self.camera_active = False
        self.camera_index = 0
        self.capture_thread = None
        
        # Parallel Inference Performance (Optimized for Cloud Latency)
        import concurrent.futures
        # We store executor so we can cleanly shut it down when stopping streams
        self.inference_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.inference_counter = 0      # IDs for outgoing requests
        self.completed_inference_id = -1 # ID of the latest processed result
        self.active_inference_count = 0  # Track current threads in flight
        self.inference_lock = threading.Lock() # Lock for counters
        
        self.live_detected_markers = []
        

        
        # Filter
        self.selected_color_filter = "All"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the modern Dashboard UI"""
        # Configure grid layout (3 columns: Sidebar, Main, Right Panel)
        self.root.grid_columnconfigure(0, weight=0, minsize=140)  # Left Sidebar (Controls)
        self.root.grid_columnconfigure(1, weight=1)               # Center (Video)
        self.root.grid_columnconfigure(2, weight=0, minsize=140)  # Right Panel (Insights)
        
        self.root.grid_rowconfigure(0, weight=0, minsize=30)      # Header
        self.root.grid_rowconfigure(1, weight=1)                  # Main Content
        self.root.grid_rowconfigure(2, weight=0, minsize=10)      # Footer
        
        self.create_header()
        self.create_sidebar()        # Left: Controls
        self.create_main_display()   # Center: Video
        self.create_right_panel()    # Right: Insights
        # self.create_footer()       # Removed footer for cleaner look, status moved to sidebar/header

        
    def create_header(self):
        """Create sleek, premium header bar"""
        header = ctk.CTkFrame(
            self.root,
            height=30,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        # Accent line at the very bottom
        ctk.CTkFrame(
            header, height=1, fg_color=self.colors["primary"], corner_radius=0
        ).place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        # Left: Icon + App Name
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(
            left,
            text="▨ cable marker",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"]
        ).pack(side="left")

        # Right: Status pill
        self.header_status = ctk.CTkLabel(
            header,
            text="● System Ready",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors["success"]
        )
        self.header_status.grid(row=0, column=2, sticky="e", padx=8)
        
    def create_sidebar(self):
        """Create controls sidebar (Left Panel) — Premium Redesign"""
        sidebar = ctk.CTkFrame(
            self.root,
            width=260,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)

        # Subtle right border
        ctk.CTkFrame(
            sidebar, width=1, fg_color=self.colors["border"], corner_radius=0
        ).place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["primary"]
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        def section_label(text):
            lf = ctk.CTkFrame(scroll, fg_color="transparent")
            lf.pack(fill="x", padx=4, pady=(6, 2))
            ctk.CTkFrame(lf, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(
                lf,
                text=text,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=self.colors["text_secondary"],
                anchor="w"
            ).pack(fill="x")

        def icon_btn(parent, icon, label, command, color=None, hover=None, state="normal"):
            c = color or self.colors["surface2"]
            h = hover or self.colors["primary"]
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=4, pady=2)
            btn = ctk.CTkButton(
                f,
                text=f"{icon}  {label}",
                fg_color=c,
                hover_color=h,
                text_color=self.colors["text"],
                font=ctk.CTkFont(size=10),
                command=command,
                height=24,
                corner_radius=4,
                anchor="w",
                state=state
            )
            btn.pack(fill="x")
            return btn

        # ── INPUT SOURCE ──────────────────────────
        section_label("INPUT SOURCE")

        cam_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cam_frame.pack(fill="x", padx=4, pady=2)
        self.camera_var = ctk.StringVar(value="Select Camera")
        self.camera_dropdown = ctk.CTkComboBox(
            cam_frame,
            values=self.get_available_cameras(),
            variable=self.camera_var,
            command=self.on_camera_selected,
            height=24,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            fg_color=self.colors["surface2"],
            dropdown_fg_color=self.colors["surface2"],
            border_color=self.colors["border"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["primary_hover"],
            corner_radius=4
        )
        self.camera_dropdown.pack(fill="x")

        self.camera_start_btn = icon_btn(
            scroll, "▶", "Start Stream", self.start_camera,
            color=self.colors["success"], hover="#00b856", state="disabled"
        )
        self.camera_stop_btn = icon_btn(
            scroll, "⏹", "Stop Stream", self.stop_camera,
            color=self.colors["error"], hover="#cc0033", state="disabled"
        )
        icon_btn(scroll, "📂", "Load File", self.load_image)

        # ── FILTERS ───────────────────────────────
        section_label("COLOR FILTER")

        filter_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        filter_frame.pack(fill="x", padx=4, pady=2)
        self.color_filter_var = ctk.StringVar(value="All Colors")
        self.color_filter_dropdown = ctk.CTkComboBox(
            filter_frame,
            values=["All Colors", "White", "Yellow", "Blue", "Pink", "Green"],
            variable=self.color_filter_var,
            command=self.on_color_filter_changed,
            height=24,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            fg_color=self.colors["surface2"],
            dropdown_fg_color=self.colors["surface2"],
            border_color=self.colors["border"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["primary_hover"],
            corner_radius=4
        )
        self.color_filter_dropdown.pack(fill="x")

        # ── REGION OF INTEREST ────────────────────
        section_label("REGION OF INTEREST")

        roi_row = ctk.CTkFrame(scroll, fg_color="transparent")
        roi_row.pack(fill="x", padx=4, pady=2)
        roi_row.grid_columnconfigure(0, weight=1)
        roi_row.grid_columnconfigure(1, weight=1)

        self.select_roi_btn = ctk.CTkButton(
            roi_row, text="⛶ Select",
            fg_color=self.colors["surface2"],
            hover_color=self.colors["primary"],
            text_color=self.colors["text"],
            height=24, corner_radius=4, font=ctk.CTkFont(size=10),
            command=self.toggle_roi_selection
        )
        self.select_roi_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self.reset_roi_btn = ctk.CTkButton(
            roi_row, text="↺ Reset",
            fg_color=self.colors["surface2"],
            hover_color=self.colors["warning"],
            text_color=self.colors["text"],
            height=24, corner_radius=4, font=ctk.CTkFont(size=10),
            command=self.reset_roi, state="disabled"
        )
        self.reset_roi_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # ── ACTIONS ───────────────────────────────
        section_label("ACTIONS")
        self.reset_btn = icon_btn(
            scroll, "↺", "Reset View", self.reset_view, state="disabled"
        )

        # ── GPIO ──────────────────────────────────
        if IS_RASPBERRY_PI or self.gpio_controller.gpio_available:
            section_label("HARDWARE")
            gpio_status = self.gpio_controller.get_status()
            status_text = "GPIO Ready" if gpio_status["initialized"] else "GPIO Simulated"
            sc = self.colors["success"] if gpio_status["initialized"] else self.colors["warning"]

            self.gpio_status_label = ctk.CTkLabel(
                scroll, text=f"● {status_text}",
                font=ctk.CTkFont(size=9),
                text_color=sc, anchor="w"
            )
            self.gpio_status_label.pack(fill="x", padx=4, pady=(0, 2))

            self.gpio_test_btn = icon_btn(
                scroll, "⚡", "Test Output Signals",
                self.test_gpio,
                color=self.colors["primary"],
                hover=self.colors["primary_hover"]
            )
        
    def create_main_display(self):
        """Create premium main image display area"""
        main = ctk.CTkFrame(
            self.root,
            fg_color=self.colors["bg"],
            corner_radius=0
        )
        main.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Canvas container with subtle inner border
        self.canvas_frame = ctk.CTkFrame(
            main,
            fg_color=self.colors["bg"],
            corner_radius=0,
            border_width=0
        )
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # Placeholder group — centred
        ph_container = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        ph_container.place(relx=0.5, rely=0.5, anchor="center")

        self.placeholder_icon = ctk.CTkLabel(
            ph_container,
            text="📷",
            font=ctk.CTkFont(size=72),
            text_color=self.colors["border"]
        )
        self.placeholder_icon.pack(pady=(0, 16))

        self.placeholder = ctk.CTkLabel(
            ph_container,
            text="No Source Active",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        self.placeholder.pack(pady=(0, 6))

        ctk.CTkLabel(
            ph_container,
            text="Load a file or start a camera stream to begin detection",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["border"]
        ).pack()

        self.image_label = None
        
    def create_right_panel(self):
        """Create the Right Insights Panel — Premium Redesign"""
        right_panel = ctk.CTkFrame(
            self.root,
            width=120,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        right_panel.grid(row=1, column=2, sticky="nsew", padx=0, pady=0)
        right_panel.grid_propagate(False)

        # Left border accent
        ctk.CTkFrame(
            right_panel, width=1, fg_color=self.colors["border"]
        ).place(relx=0, rely=0, relheight=1.0, anchor="nw")

        # ── Big counter card
        counter_card = ctk.CTkFrame(
            right_panel,
            fg_color=self.colors["surface2"],
            corner_radius=8
        )
        counter_card.pack(fill="x", padx=4, pady=(10, 6))

        ctk.CTkLabel(
            counter_card,
            text="DETECTED",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(6, 0))

        self.markers_count = ctk.CTkLabel(
            counter_card,
            text="0",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.markers_count.pack(pady=(0, 2))

        ctk.CTkLabel(
            counter_card,
            text="cable markers",
            font=ctk.CTkFont(size=9),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 6))

        # ── Section label
        lf = ctk.CTkFrame(right_panel, fg_color="transparent")
        lf.pack(fill="x", padx=4, pady=(2, 4))
        ctk.CTkFrame(lf, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(
            lf, text="DETECTIONS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.colors["text_secondary"], anchor="w"
        ).pack(fill="x")

        # ── Scrollable card list
        self.results_scroll = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["primary"]
        )
        self.results_scroll.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # Export button removed per user request
        self.save_btn = None  # kept as stub to avoid AttributeErrors

    # Footer removed

        
    def load_image(self):
        """Load image or video from file"""
        VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".m4v"}

        file_path = filedialog.askopenfilename(
            title="Select Image or Video",
            filetypes=[
                ("Image & Video files",
                 "*.jpg *.jpeg *.png *.bmp *.tiff "
                 "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("All files", "*.*"),
            ]
        )

        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()

        # --- Video path ---
        if ext in VIDEO_EXTENSIONS:
            self.start_video_file_mode(file_path)
            return

        # --- Image path ---
        self.image_path = file_path
        self.original_image = cv2.imread(file_path)

        if self.original_image is None:
            messagebox.showerror("Error", "Failed to load image!")
            return

        self.current_display = self.original_image.copy()
        self.display_image(self.current_display)

        self.reset_btn.configure(state="normal")
        self.detected_markers = []
        self.all_detected_markers = []
        self.markers_count.configure(text="0")
        self.color_filter_var.set("All Colors")
        self.selected_color_filter = "All"

        self.header_status.configure(
            text=f"● Loading: {os.path.basename(file_path)}",
            text_color=self.colors["warning"]
        )
        self.root.update()
        self.detect_markers()
            
    def display_image(self, image):
        """Display image on canvas"""
        if image is None:
            # print("DEBUG: display_image called with None")
            return
        
        try:
            # print(f"DEBUG: display_image called with shape {image.shape}")
            if self.placeholder:
                self.placeholder.place_forget()
            if hasattr(self, 'placeholder_icon'):
                self.placeholder_icon.place_forget()
        
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            canvas_width = self.canvas_frame.winfo_width()
            canvas_height = self.canvas_frame.winfo_height()
            
            # print(f"DEBUG: Canvas size: {canvas_width}x{canvas_height}")

            # Force updates if canvas is too small (e.g. initialization)
            if canvas_width < 10 or canvas_height < 10:
                canvas_width = 640
                canvas_height = 480
                # print("DEBUG: Canvas too small, using default 640x480 for scaling")
        
            height, width = image_rgb.shape[:2]
            scale = min(canvas_width / width, canvas_height / height) * 0.95
            new_width = int(width * scale)
            new_height = int(height * scale)
        
            image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

            pil_image = Image.fromarray(image_rgb)
            photo = ImageTk.PhotoImage(pil_image)

            if self.image_label is None:
                self.image_label = ctk.CTkLabel(self.canvas_frame, text="")
                self.image_label.place(relx=0.5, rely=0.5, anchor="center")
                # Bind mouse events for ROI selection
                self.image_label.bind("<Button-1>", self.on_roi_start)
                self.image_label.bind("<B1-Motion>", self.on_roi_drag)
                self.image_label.bind("<ButtonRelease-1>", self.on_roi_end)
                self.image_label.bind("<Enter>", lambda e: self.on_mouse_enter())
                self.image_label.bind("<Leave>", lambda e: self.on_mouse_leave())

            self.image_label.configure(image=photo)
            self.image_label.image = photo
            
            # Store scaling info for coordinate mapping
            self.display_scale = scale
            self.display_offset_x = (canvas_width - new_width) // 2
            self.display_offset_y = (canvas_height - new_height) // 2
            # print("DEBUG: Image updated on label")
            
        except Exception as e:
            print(f"Error displaying image: {e}")
        
    def detect_markers(self):
        """Run marker detection"""
        if self.original_image is None:
            return
        
        self.header_status.configure(text="● Detecting...", text_color=self.colors["warning"])
        self.root.update()
        
        # Handle ROI
        detect_image = self.original_image
        offset_x, offset_y = 0, 0
        
        if self.roi:
            x, y, w, h = self.roi
            # Ensure ROI is valid within image bounds
            img_h, img_w = self.original_image.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)
            
            if w > 0 and h > 0:
                detect_image = self.original_image[y:y+h, x:x+w]
                offset_x, offset_y = x, y
        
        # Run detection
        self.all_detected_markers = self.detector.detect_markers(detect_image)
        
        # Adjust coordinates if ROI was used
        if offset_x > 0 or offset_y > 0:
            for marker in self.all_detected_markers:
                # Adjust bounding box if present
                if 'bounding_box' in marker:
                    marker['bounding_box']['x'] += offset_x
                    marker['bounding_box']['y'] += offset_y
                
                # Adjust center tuple
                if 'center' in marker:
                    cx, cy = marker['center']
                    marker['center'] = (cx + offset_x, cy + offset_y)
        
        self.apply_color_filter()
        
        self.processed_image = self.detector.draw_detections(
            self.original_image, 
            self.detected_markers
        )
        
        # Draw ROI rectangle
        if self.roi:
            x, y, w, h = self.roi
            cv2.rectangle(self.processed_image, (x, y), (x+w, y+h), (0, 255, 255), 2)
            cv2.putText(self.processed_image, "ROI", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        self.display_image(self.processed_image)
        self.update_results()
        
        # saved_path = self.auto_save_detection() # Removed
        
        self.gpio_controller.process_detected_colors(self.detected_markers)
        
        if self.save_btn:  # Export button may be disabled
            self.save_btn.configure(state="normal")
        
        marker_count = len(self.detected_markers)
        marker_count = len(self.detected_markers)
        self.header_status.configure(text=f"● Found {marker_count} Marker(s)", text_color=self.colors["success"])
    
    def apply_color_filter(self):
        """Show all markers (no filtering - removed local logic)"""
        # Just show everything the model detected - no filtering
        self.detected_markers = self.all_detected_markers.copy()
        
        # Renumber for display
        for idx, marker in enumerate(self.detected_markers, 1):
            marker["component_id"] = idx
        
    def update_results(self):
        """Update results display with cards"""
        # Clear existing cards
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
            
        if not self.detected_markers:
            # Show empty state
            ctk.CTkLabel(
                self.results_scroll,
                text="No markers detected\nWaiting for input...",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color=self.colors["text_secondary"]
            ).pack(pady=40)
            self.markers_count.configure(text="0")
            return
            
        self.markers_count.configure(text=f"{len(self.detected_markers)}")
        
        # Create cards for each marker
        for i, marker in enumerate(self.detected_markers):
            color = marker.get('primary_color', 'Unknown')
            confidence = marker['confidence']
            stripes = marker.get('stripes_in_group', marker.get('stripe_count', 3))
            
            # Card Container
            card = ctk.CTkFrame(self.results_scroll, fg_color=self.colors["bg"], corner_radius=8)
            card.pack(fill="x", pady=(0, 10))
            
            # Card Content
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="x", padx=10, pady=10)
            
            # Left: Color Indicator
            indicator_color = self._get_color_hex(color)
            indicator = ctk.CTkLabel(content, text="●", text_color=indicator_color, font=ctk.CTkFont(size=18))
            indicator.pack(side="left", padx=(0, 10))
            
            # Middle: Info
            info_frame = ctk.CTkFrame(content, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True)
            
            ctk.CTkLabel(
                info_frame, 
                text=f"{color} Marker", 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["text"],
                anchor="w"
            ).pack(fill="x")
            
            ctk.CTkLabel(
                info_frame, 
                text=f"{stripes} Stripes | ID #{i+1}", 
                font=ctk.CTkFont(size=11),
                text_color=self.colors["text_secondary"],
                anchor="w"
            ).pack(fill="x")
            
            # Right: Confidence
            badge = ctk.CTkFrame(content, fg_color=self.colors["surface"], corner_radius=12)
            badge.pack(side="right")
            
            ctk.CTkLabel(
                badge,
                text=f"{int(confidence)}%",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["success"] if confidence > 80 else self.colors["warning"]
            ).pack(padx=8, pady=2)
            
    def _get_color_hex(self, color_name):
        """Helper to get hex code for UI indicators"""
        colors = {
            "yellow": "#facc15",
            "blue": "#3b82f6", 
            "green": "#22c55e",
            "red": "#ef4444",
            "white": "#f8fafc",
            "pink": "#ec4899",
            "grey": "#9ca3af"
        }
        return colors.get(str(color_name).lower(), "#94a3b8")
        
    def reset_view(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_display = self.original_image.copy()
            self.display_image(self.current_display)
            self.header_status.configure(text="● Reset View", text_color=self.colors["text_secondary"])
            
    
    # def auto_save_detection(self): <-- Removed method
    #    ...

    
    def save_results(self):
        """Save annotated image"""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No results to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All files", "*.*")],
            initialdir=self.detections_dir
        )
        
        if file_path:
            cv2.imwrite(file_path, self.processed_image)
            messagebox.showinfo("Success", f"Saved to:\n{file_path}")
            self.header_status.configure(text="● Saved Successfully", text_color=self.colors["success"])
            
    def on_color_filter_changed(self, choice):
        """Handle color filter change"""
        if not choice:
            return
        
        self.selected_color_filter = choice
        
        if self.all_detected_markers:
            self.apply_color_filter()
            
            if self.original_image is not None:
                self.processed_image = self.detector.draw_detections(
                    self.original_image,
                    self.detected_markers
                )
                self.display_image(self.processed_image)
                self.update_results()
                
                self.gpio_controller.process_detected_colors(self.detected_markers)
                
                marker_count = len(self.detected_markers)
                total_count = len(self.all_detected_markers)
                if choice != "All":
                    self.header_status.configure(
                        text=f"● Filter: {marker_count}/{total_count} {choice}",
                        text_color=self.colors["warning"]
                    )
                else:
                    self.header_status.configure(text=f"● Showing All {total_count}", text_color=self.colors["success"])
    
    def get_available_cameras(self):
        """Get available cameras including simulation and video file modes"""
        cameras = ["Select Camera"]

        # Add Video File option
        cameras.append("📹 Load Video File")

        # Add Simulation Mode option
        cameras.append("📷 Simulate Loaded Image")
        cameras.append("---")

        # Check specifically for macOS
        import platform
        system = platform.system()
        backend = cv2.CAP_ANY
        if system == 'Darwin':
            backend = cv2.CAP_AVFOUNDATION

        for i in range(5):  # Reduced range to speed up startup
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                cameras.append(f"Camera {i}")
                cap.release()

        return cameras
    
    def on_camera_selected(self, choice):
        """Handle camera selection"""
        if not choice or choice == "Select Camera" or choice == "---":
            self.camera_start_btn.configure(state="disabled")
            return

        self.camera_start_btn.configure(state="normal")

        if "Load Video File" in choice:
            self.camera_index = -2  # Special index for video file
        elif "Simulate Loaded Image" in choice:
            self.camera_index = -1  # Special index for simulation
        elif "Camera" in choice:
            try:
                self.camera_index = int(choice.split()[-1])
            except:
                self.camera_index = 0
    
    def start_camera(self):
        """Start Local Camera Loop for real-time detection"""
        if self.camera_active:
            return

        # Check for Video File Mode
        if self.camera_index == -2:
            self.start_video_file_mode()
            return

        # Check for Simulation Mode
        if self.camera_index == -1:
            self.start_simulation_mode()
            return
            
        # Local Camera Loop (replacing WebRTC)
        try:
            print(f"📷 Starting local camera loop on device {self.camera_index}...")
            
            # Initialize camera capture locally
            import platform
            system = platform.system()
            if system == 'Darwin':
                self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_AVFOUNDATION)
            else:
                self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                messagebox.showerror("Error", f"Failed to open Camera {self.camera_index}")
                return
                
            # Set resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            self.camera_active = True
            self.simulation_running = False # Reuse this flag or ensure clean state
            
            self.camera_start_btn.configure(state="disabled")
            self.camera_stop_btn.configure(state="normal")
            self.camera_dropdown.configure(state="disabled")
            
            # Hide placeholder
            if self.placeholder:
                self.placeholder.place_forget()
            if hasattr(self, 'placeholder_icon'):
                self.placeholder_icon.place_forget()

            self.header_status.configure(text="● Starting Camera...", text_color=self.colors["warning"])
            
            def camera_loop():
                """Background thread: Read Camera -> Display Smooth Video -> Async Inference"""
                print("🔹 Camera thread started (Performance Mode)")
                
                # Inference state
                self.latest_detections_lock = threading.Lock()
                self.is_inferencing = False
                last_inference_time = 0.0
                MIN_INFERENCE_INTERVAL = 0.05  # 20 FPS target (assuming sufficient threads)
                
                while self.camera_active and self.camera.isOpened():
                    try:
                        ret, frame = self.camera.read()
                        if not ret:
                            print("❌ Warning: Failed to read frame from camera")
                            time.sleep(0.1)
                            continue
                        
                        # Resize for consistent processing speed if needed (optional)
                        # frame = cv2.resize(frame, (640, 480))
                        
                        self.original_image = frame.copy()
                        
                        # --- ASYNC INFERENCE ---
                        # Start new inference if we have capacity AND interval elapsed
                        now = time.time()
                        can_start = False
                        with self.inference_lock:
                            # Allow up to 10 concurrent requests for continuous feel
                            if self.active_inference_count < 10 and (now - last_inference_time) >= MIN_INFERENCE_INTERVAL:
                                can_start = True
                                self.active_inference_count += 1
                                self.inference_counter += 1
                                current_job_id = self.inference_counter
                                last_inference_time = now
                        
                        if can_start:
                            def run_inference_job(input_frame, job_id):
                                try:
                                    # Prepare input frame (crop if ROI set)
                                    detect_frame = input_frame
                                    offset_x, offset_y = 0, 0
                                    
                                    if self.roi:
                                        x, y, w, h = self.roi
                                        img_h, img_w = input_frame.shape[:2]
                                        x = max(0, min(x, img_w))
                                        y = max(0, min(y, img_h))
                                        w = min(w, img_w - x)
                                        h = min(h, img_h - y)
                                        
                                        if w > 0 and h > 0:
                                            detect_frame = input_frame[y:y+h, x:x+w]
                                            offset_x, offset_y = x, y
                                    
                                    # Run inference (network bound)
                                    detections = self.detector.detect_single_frame(detect_frame)
                                    
                                    # Adjust coordinates if ROI used
                                    if offset_x > 0 or (offset_y > 0 and detections):
                                        for marker in detections:
                                            if 'bounding_box' in marker:
                                                marker['bounding_box']['x'] += offset_x
                                                marker['bounding_box']['y'] += offset_y
                                            
                                            if 'center' in marker:
                                                cx, cy = marker['center']
                                                marker['center'] = (cx + offset_x, cy + offset_y)
                                    
                                    # Group stripes
                                    if detections:
                                        detections = self.detector._group_stripes_into_markings(detections)
                                    
                                    # Update detections safely, only if it's the latest result
                                    with self.latest_detections_lock:
                                        if job_id > self.completed_inference_id:
                                            self.all_detected_markers = detections
                                            self.completed_inference_id = job_id
                                        
                                except Exception as e:
                                    print(f"⚠️ Inference error: {e}")
                                finally:
                                    with self.inference_lock:
                                        self.active_inference_count -= 1
                            
                            # Start parallel inference job
                            self.inference_executor.submit(run_inference_job, frame.copy(), current_job_id)
                        
                        # --- RENDER Loop (Runs at full camera FPS) ---
                        
                        # Get latest available detections
                        with self.latest_detections_lock:
                            current_all_markers = self.all_detected_markers.copy() if hasattr(self, 'all_detected_markers') else []
                        
                        # Apply local filters (fast)
                        self.all_detected_markers = current_all_markers # Ensure filter uses latest
                        self.apply_color_filter()
                        filtered_detections = self.detected_markers.copy()
                        
                        # Draw results overlay
                        # Draw results overlay
                        if filtered_detections:
                            display_frame = self.detector.draw_detections(frame, filtered_detections)
                            self.processed_image = display_frame # Keep reference
                        else:
                            display_frame = frame.copy()
                            self.processed_image = display_frame
                            
                        # Draw ROI rectangle on live feed
                        if self.roi:
                            x, y, w, h = self.roi
                            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                            cv2.putText(display_frame, "ROI ACTIVE", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        
                        # Update UI (thread-safe calls)
                        def update_ui_components():
                            # 1. Display Image (Video Feedback)
                            self.display_image(display_frame)
                            
                            # 2. Update Counts
                            self.markers_count.configure(text=f"{len(filtered_detections)}")
                            
                            # 3. Update Results Text (Throttle this if needed)
                            # self.update_results() 
                            
                            # 4. Update GPIO
                            self.gpio_controller.process_detected_colors(filtered_detections)
                            
                            # 5. Update Status
                            if filtered_detections:
                                self.header_status.configure(
                                    text=f"● Live: {len(filtered_detections)} Detected", 
                                    text_color=self.colors["success"]
                                )
                            else:
                                self.header_status.configure(
                                    text="● Live: Scanning...", 
                                    text_color=self.colors["primary"]
                                )
                                
                        self.root.after(0, update_ui_components)
                        
                        # Run at ~30 FPS or max speed
                        time.sleep(0.01) 
                        
                    except Exception as e:
                        print(f"⚠️ Error in camera loop: {e}")
                        time.sleep(0.5)
                
                # Cleanup when loop ends
                if self.camera:
                    self.camera.release()
                print("🛑 Camera thread stopped")

            # Start the thread
            self.capture_thread = threading.Thread(target=camera_loop, daemon=True)
            self.capture_thread.start()
            
            print("✅ Local camera loop started")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
            import traceback
            traceback.print_exc()


    def start_simulation_mode(self):
        """Start Simulation Mode using loaded image"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first to simulate!")
            return
            
        self.camera_active = True
        self.simulation_running = True
        
        self.camera_start_btn.configure(state="disabled")
        self.camera_stop_btn.configure(state="normal")
        self.camera_dropdown.configure(state="disabled")
        
        # Hide placeholder
        if self.placeholder:
            self.placeholder.place_forget()
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place_forget()
            
        self.header_status.configure(text="● Simulation Active", text_color=self.colors["warning"])
        self.header_status.configure(text="● Simulating", text_color=self.colors["warning"])
        
        print("✅ Simulation Mode started")
        
        def simulate_loop():
            """Background thread to simulate camera feed"""
            while self.camera_active and self.simulation_running:
                try:
                    if self.original_image is None:
                        break
                        
                    # Simulate frame (copy original)
                    frame = self.original_image.copy()
                    
                    # Prepare input frame (crop if ROI set)
                    detect_frame = frame
                    offset_x, offset_y = 0, 0
                    
                    if self.roi:
                        x, y, w, h = self.roi
                        img_h, img_w = frame.shape[:2]
                        x = max(0, min(x, img_w))
                        y = max(0, min(y, img_h))
                        w = min(w, img_w - x)
                        h = min(h, img_h - y)
                        
                        if w > 0 and h > 0:
                            detect_frame = frame[y:y+h, x:x+w]
                            offset_x, offset_y = x, y
                    
                    # Run static detection
                    self.all_detected_markers = self.detector.detect_markers(detect_frame)
                    
                    # Adjust coordinates if ROI used
                    if offset_x > 0 or offset_y > 0 and self.all_detected_markers:
                        for marker in self.all_detected_markers:
                            if 'bounding_box' in marker:
                                marker['bounding_box']['x'] += offset_x
                                marker['bounding_box']['y'] += offset_y
                            
                            if 'center' in marker:
                                cx, cy = marker['center']
                                marker['center'] = (cx + offset_x, cy + offset_y)
                    
                        # Update UI in main thread
                    def update_ui():
                        self.apply_color_filter()
                        
                        # Draw results
                        self.processed_image = self.detector.draw_detections(
                            frame, 
                            self.detected_markers
                        )
                        
                        # Draw ROI rectangle
                        if self.roi:
                            x, y, w, h = self.roi
                            cv2.rectangle(self.processed_image, (x, y), (x+w, y+h), (0, 255, 255), 2)
                        
                        self.display_image(self.processed_image)
                        self.update_results()
                        self.gpio_controller.process_detected_colors(self.detected_markers)
                        
                        marker_count = len(self.detected_markers)
                        self.markers_count.configure(text=f"{marker_count}")
                        
                    self.root.after(0, update_ui)
                    
                    # 10 FPS simulation
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Simulation error: {e}")
                    break
            
            print("🛑 Simulation loop ended")
            
        self.capture_thread = threading.Thread(target=simulate_loop, daemon=True)
        self.capture_thread.start()
    
    def start_video_file_mode(self, file_path: str = None):
        """Open a video file and run detection frame-by-frame"""
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select Video File",
                filetypes=[
                    ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                    ("All files", "*.*")
                ]
            )
        if not file_path:
            return  # User cancelled

        if self.camera_active:
            self.stop_camera()
                
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            messagebox.showerror("Error", f"Failed to open video:\n{file_path}")
            return

        self.camera = cap  # Reuse camera slot for cleanup
        self.camera_active = True
        self.simulation_running = False

        self.camera_start_btn.configure(state="disabled")
        self.camera_stop_btn.configure(state="normal")
        self.camera_dropdown.configure(state="disabled")

        if self.placeholder:
            self.placeholder.place_forget()
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place_forget()

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_delay = 1.0 / fps  # Sleep to maintain original video speed
        video_name = os.path.basename(file_path)
        self.header_status.configure(text=f"● Video: {video_name}", text_color=self.colors["warning"])
        print(f"🎬 Playing video: {video_name}  ({fps:.1f} FPS)")

        self.latest_detections_lock = threading.Lock()
        self.is_inferencing = False
        
        # Ensure we have a fresh thread pool
        import concurrent.futures
        if not hasattr(self, 'inference_executor'):
            self.inference_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

        def video_loop():
            nonlocal cap
            while self.camera_active:
                try:
                    ret, frame = cap.read()
                    if not ret:
                        # End of video — loop back to start
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break

                    self.original_image = frame.copy()

                    # --- ASYNC INFERENCE ---
                    can_start = False
                    with self.inference_lock:
                        if self.active_inference_count < 10:
                            can_start = True
                            self.active_inference_count += 1
                            self.inference_counter += 1
                            current_job_id = self.inference_counter
                    
                    if can_start:
                        def run_inference_job(input_frame, job_id):
                            try:
                                detect_frame = input_frame
                                offset_x, offset_y = 0, 0

                                if self.roi:
                                    x, y, w, h = self.roi
                                    img_h, img_w = input_frame.shape[:2]
                                    x = max(0, min(x, img_w))
                                    y = max(0, min(y, img_h))
                                    w = min(w, img_w - x)
                                    h = min(h, img_h - y)
                                    if w > 0 and h > 0:
                                        detect_frame = input_frame[y:y+h, x:x+w]
                                        offset_x, offset_y = x, y

                                detections = self.detector.detect_single_frame(detect_frame)

                                if (offset_x > 0 or offset_y > 0) and detections:
                                    for marker in detections:
                                        if 'bounding_box' in marker:
                                            marker['bounding_box']['x'] += offset_x
                                            marker['bounding_box']['y'] += offset_y
                                        if 'center' in marker:
                                            cx, cy = marker['center']
                                            marker['center'] = (cx + offset_x, cy + offset_y)

                                if detections:
                                    detections = self.detector._group_stripes_into_markings(detections)

                                with self.latest_detections_lock:
                                    if job_id > self.completed_inference_id:
                                        self.all_detected_markers = detections
                                        self.completed_inference_id = job_id
                            except Exception as e:
                                print(f"⚠️ Video inference error: {e}")
                            finally:
                                with self.inference_lock:
                                    self.active_inference_count -= 1

                        self.inference_executor.submit(run_inference_job, frame.copy(), current_job_id)

                    # --- RENDER ---
                    with self.latest_detections_lock:
                        current_all = self.all_detected_markers.copy() if hasattr(self, 'all_detected_markers') else []

                    self.all_detected_markers = current_all
                    self.apply_color_filter()
                    filtered = self.detected_markers.copy()

                    if filtered:
                        display_frame = self.detector.draw_detections(frame, filtered)
                    else:
                        display_frame = frame.copy()
                    self.processed_image = display_frame

                    if self.roi:
                        rx, ry, rw, rh = self.roi
                        cv2.rectangle(display_frame, (rx, ry), (rx+rw, ry+rh), (0, 255, 255), 2)
                        cv2.putText(display_frame, "ROI ACTIVE", (rx, ry-10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                    def update_ui(df=display_frame, fd=filtered):
                        self.display_image(df)
                        self.markers_count.configure(text=f"{len(fd)}")
                        self.gpio_controller.process_detected_colors(fd)
                        if fd:
                            self.header_status.configure(
                                text=f"● Video: {len(fd)} Detected",
                                text_color=self.colors["success"]
                            )
                        else:
                            self.header_status.configure(
                                text=f"● Video: {video_name}",
                                text_color=self.colors["primary"]
                            )

                    self.root.after(0, update_ui)
                    time.sleep(frame_delay)

                except Exception as e:
                    print(f"⚠️ Video loop error: {e}")
                    time.sleep(0.5)

            cap.release()
            self.camera = None
            self.camera_active = False # Ensure flag is off when thread exits
            print("🛑 Video file playback stopped")

        self.capture_thread = threading.Thread(target=video_loop, daemon=True)
        self.capture_thread.start()
        print("✅ Video file mode started")

    def stop_camera(self):
        """Stop Camera or Simulation"""
        print("Stopping camera/simulation...")
        self.camera_active = False
        self.simulation_running = False

        # Properly wait for the capture thread to terminate
        if getattr(self, 'capture_thread', None) and self.capture_thread.is_alive():
            print("⏳ Waiting for previous video loop to cleanly terminate...")
            self.capture_thread.join(timeout=2.0)
            print("✅ Thread terminated.")
            self.capture_thread = None

        # Properly shutdown old pool to prevent pending inferences of the old video from bleeding into the new one
        if hasattr(self, 'inference_executor'):
            print("⏳ Shutting down inference pool...")
            # False -> don't wait for completion of pending threads, cancel them immediately
            self.inference_executor.shutdown(wait=False, cancel_futures=True)
            import concurrent.futures
            # Recreate a fresh thread pool executor
            self.inference_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

        # Reset counters so old thread IDs don't overrule new thread IDs
        with self.inference_lock:
            self.inference_counter = 0
            self.completed_inference_id = -1
            self.active_inference_count = 0

        # Stop WebRTC stream (legacy cleanup if needed)
        # self.detector.stop_webrtc_stream()
        
        # Camera release is handled in the thread loop when self.camera_active becomes False
        # But we can force release here if we want to be safe, though usually safer to let thread exit
        if hasattr(self, 'camera') and self.camera is not None and getattr(self.camera, 'isOpened', lambda: False)():
             self.camera.release()
             self.camera = None
        
        self.camera_start_btn.configure(state="normal")
        self.camera_stop_btn.configure(state="disabled")
        self.camera_dropdown.configure(state="normal")
        
        if self.placeholder:
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place(relx=0.5, rely=0.4, anchor="center")
        
        self.header_status.configure(text="● Stopped", text_color=self.colors["text_secondary"])
        self.header_status.configure(text="● Ready", text_color=self.colors["success"])
        print("✅ Stopped")
    

    

    
    
    # def resume_camera_feed(self): <-- Removed
    #    ...

    
    def test_gpio(self):
        """Test GPIO functionality"""
        def run_test():
            self.header_status.configure(text="● Testing GPIO...", text_color=self.colors["warning"])
            # self.root.update() # Avoid calling update in thread
            
            # Run test
            success = self.gpio_controller.test_gpio()
            if success:
                self.header_status.configure(text="● GPIO Test Passed", text_color=self.colors["success"])
                self.gpio_status_label.configure(text="Get Status: Active", text_color=self.colors["success"])
                messagebox.showinfo("Success", "GPIO Test Sequence Completed")
            else:
                self.header_status.configure(text="● GPIO Test Failed", text_color=self.colors["error"])
                self.gpio_status_label.configure(text="Status: Error", text_color=self.colors["error"])
                messagebox.showerror("Error", "GPIO Test Failed")
                
            self.gpio_test_btn.configure(state="normal")
            # Reset status after delay
            self.root.after(3000, lambda: self.header_status.configure(text="● Ready", text_color=self.colors["success"]))
        
            # Run test in background thread
            thread = threading.Thread(target=run_test, daemon=True)
            thread.start()
            
    def run(self):
        """Run application"""
        def on_closing():
            if self.camera_active:
                self.stop_camera()
            # Clean up GPIO
            self.gpio_controller.cleanup()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

    # --- ROI Selection Methods ---
    
    def toggle_roi_selection(self):
        """Toggle ROI selection mode"""
        self.roi_selecting = not self.roi_selecting
        
        if self.roi_selecting:
            self.select_roi_btn.configure(
                text="Click & Drag to Select", 
                fg_color=self.colors["primary"],
                state="disabled" # Keep it active/pressed look or use state
            )
            # Change cursor if possible, or just rely on text
            if self.image_label:
                self.image_label.configure(cursor="crosshair")
        else:
            self.select_roi_btn.configure(
                text="⛝ Select Area", 
                fg_color=self.colors["surface"],
                state="normal"
            )
            if self.image_label:
                self.image_label.configure(cursor="")

    def reset_roi(self):
        """Reset ROI to full image"""
        self.roi = None
        self.reset_roi_btn.configure(state="disabled")
        self.header_status.configure(text="● ROI Cleared", text_color=self.colors["success"])
        
        # Trigger re-detection/update
        if not self.camera_active and self.original_image is not None:
             self.detect_markers()
        else:
             # Camera loop picks up None roi automatically
             pass

    def on_mouse_enter(self):
        if self.roi_selecting:
            self.image_label.configure(cursor="crosshair")

    def on_mouse_leave(self):
        self.image_label.configure(cursor="")

    def on_roi_start(self, event):
        """Start ROI selection"""
        if not self.roi_selecting:
            return
            
        self.roi_start_point = (event.x, event.y)
        self.roi_current_point = (event.x, event.y)

    def on_roi_drag(self, event):
        """Update ROI selection visualization"""
        if not self.roi_selecting or not self.roi_start_point:
            return
            
        self.roi_current_point = (event.x, event.y)
        
        # Visual feedback (draw rectangle on current display copy)
        if self.current_display is not None:
            # We can't easily draw on the PhotoImage directly efficiently here without canvas logic
            # or converting back and forth. 
            # Ideally, we'd use a Canvas widget instead of Label for better drawing.
            # But for now, let's just use the final selection.
            # OR prevent complex drawing during drag for simplicity in Tkinter Label.
            pass

    def on_roi_end(self, event):
        """Finalize ROI selection"""
        if not self.roi_selecting or not self.roi_start_point:
            return
            
        end_point = (event.x, event.y)
        start_point = self.roi_start_point
        
        # Calculate coordinates in ORIGINAL image space
        # event.x/y are relative to the label image (which is resized)
        
        if not hasattr(self, 'display_scale') or self.display_scale == 0:
            return
            
        # Get bounds
        x1 = min(start_point[0], end_point[0])
        y1 = min(start_point[1], end_point[1])
        x2 = max(start_point[0], end_point[0])
        y2 = max(start_point[1], end_point[1])
        
        # Minimum size check (e.g., 10px)
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.roi_selecting = False
            self.toggle_roi_selection() # Reset button
            return

        # Map to original image coordinates
        scale = self.display_scale
        orig_x = int(x1 / scale)
        orig_y = int(y1 / scale)
        orig_w = int((x2 - x1) / scale)
        orig_h = int((y2 - y1) / scale)
        
        # Bounds check
        if self.original_image is not None:
            h, w = self.original_image.shape[:2]
            orig_x = max(0, min(orig_x, w))
            orig_y = max(0, min(orig_y, h))
            orig_w = min(orig_w, w - orig_x)
            orig_h = min(orig_h, h - orig_y)
            
            self.roi = (orig_x, orig_y, orig_w, orig_h)
            
            print(f"ROI Selected: {self.roi}")
            self.header_status.configure(text=f"● ROI Active: {orig_w}x{orig_h}", text_color=self.colors["warning"])
            self.reset_roi_btn.configure(state="normal")
            
            # Reset selection mode
            self.roi_selecting = False
            self.toggle_roi_selection() # Reset UI state
            
            # Trigger update
            if not self.camera_active:
                self.detect_markers()
            # If camera active, next frame will use ROI


if __name__ == "__main__":
    app = CableMarkerApp()
    app.run()

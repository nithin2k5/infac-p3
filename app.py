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
        
        # Modern, Professional Color Scheme
        self.colors = {
            "bg": "#0f172a",          # Slate 900
            "surface": "#1e293b",     # Slate 800
            "primary": "#3b82f6",     # Blue 500
            "primary_hover": "#2563eb", # Blue 600
            "success": "#10b981",     # Emerald 500
            "warning": "#f59e0b",     # Amber 500
            "error": "#ef4444",       # Red 500
            "text": "#f8fafc",        # Slate 50
            "text_secondary": "#94a3b8", # Slate 400
            "border": "#334155"       # Slate 700
        }
        
        # Main window configuration
        self.root = ctk.CTk()
        self.root.title("Cable Marker AI Detection")
        self.root.geometry("1400x850")
        self.root.minsize(1280, 720)
        self.root.configure(fg_color=self.colors["bg"])
        
        # Initialize detector
        self.detector = RoboflowDetector(
            min_confidence=0.25,
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
        # self.show_detection_pause = False  <-- Removed
        self.live_detected_markers = []
        

        
        # Filter
        self.selected_color_filter = "All"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the modern Dashboard UI"""
        # Configure grid layout (3 columns: Sidebar, Main, Right Panel)
        self.root.grid_columnconfigure(0, weight=0, minsize=280)  # Left Sidebar (Controls)
        self.root.grid_columnconfigure(1, weight=1)               # Center (Video)
        self.root.grid_columnconfigure(2, weight=0, minsize=320)  # Right Panel (Insights)
        
        self.root.grid_rowconfigure(0, weight=0, minsize=70)      # Header
        self.root.grid_rowconfigure(1, weight=1)                  # Main Content
        self.root.grid_rowconfigure(2, weight=0, minsize=35)      # Footer
        
        self.create_header()
        self.create_sidebar()        # Left: Controls
        self.create_main_display()   # Center: Video
        self.create_right_panel()    # Right: Insights
        self.create_footer()
        
    def create_header(self):
        """Create simple header"""
        header = ctk.CTkFrame(self.root, height=70, fg_color=self.colors["surface"], corner_radius=0)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_propagate(False)
        
        # Title with icon
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=30)
        
        title_icon = ctk.CTkLabel(
            title_frame,
            text="⚡",
            font=ctk.CTkFont(size=24),
            text_color=self.colors["primary"]
        )
        title_icon.pack(side="left", padx=(0, 10))
        
        title = ctk.CTkLabel(
            title_frame,
            text="Cable Marker AI",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors["text"]
        )
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="| Professional Detection System",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        subtitle.pack(side="left", padx=(10, 0), pady=(4, 0))
        
        # Status
        self.header_status = ctk.CTkLabel(
            header,
            text="● System Ready",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["success"]
        )
        self.header_status.pack(side="right", padx=40)
        
    def create_sidebar(self):
        """Create controls sidebar (Left Panel)"""
        sidebar = ctk.CTkFrame(
            self.root,
            width=280,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent"
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- Section: Input Source ---
        ctk.CTkLabel(
            scroll,
            text="INPUT SOURCE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.camera_var = ctk.StringVar(value="Select Camera Device")
        self.camera_dropdown = ctk.CTkComboBox(
            scroll,
            values=self.get_available_cameras(),
            variable=self.camera_var,
            command=self.on_camera_selected,
            height=40,
            fg_color=self.colors["bg"],
            button_color=self.colors["primary"],
            border_color=self.colors["border"]
        )
        self.camera_dropdown.pack(fill="x", pady=(0, 10))
        
        self.camera_start_btn = ctk.CTkButton(
            scroll,
            text="▶ START STREAM",
            command=self.start_camera,
            height=40,
            fg_color=self.colors["success"],
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            state="disabled"
        )
        self.camera_start_btn.pack(fill="x", pady=(0, 10))
        
        self.camera_stop_btn = ctk.CTkButton(
            scroll,
            text="⏹ STOP",
            command=self.stop_camera,
            height=40,
            fg_color=self.colors["error"],
            hover_color="#b91c1c",
            font=ctk.CTkFont(weight="bold"),
            state="disabled"
        )
        self.camera_stop_btn.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(
            scroll,
            text="📁 Load Image File",
            command=self.load_image,
            height=40,
            fg_color=self.colors["border"],
            hover_color=self.colors["primary"],
            text_color=self.colors["text"],
        ).pack(fill="x", pady=(0, 25))
        
        # --- Section: Filters ---
        ctk.CTkLabel(
            scroll,
            text="FILTERS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.color_filter_var = ctk.StringVar(value="All Colors")
        self.color_filter_dropdown = ctk.CTkComboBox(
            scroll,
            values=["All Colors", "White", "Yellow", "Blue", "Pink", "Green"],
            variable=self.color_filter_var,
            command=self.on_color_filter_changed,
            height=36,
            fg_color=self.colors["bg"],
            button_color=self.colors["primary"],
            border_color=self.colors["border"]
        )
        self.color_filter_dropdown.pack(fill="x", pady=(0, 25))
        
        # --- Section: ROI ---
        ctk.CTkLabel(
            scroll,
            text="DETECTION AREA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        roi_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        roi_frame.pack(fill="x", pady=(0, 25))
        
        self.select_roi_btn = ctk.CTkButton(
            roi_frame,
            text="⛝ Select Area",
            command=self.toggle_roi_selection,
            height=32,
            fg_color=self.colors["surface"],
            border_width=1,
            border_color=self.colors["primary"]
        )
        self.select_roi_btn.pack(fill="x", pady=(0, 5))
        
        self.reset_roi_btn = ctk.CTkButton(
            roi_frame,
            text="↺ Reset Full View",
            command=self.reset_roi,
            height=32,
            fg_color=self.colors["surface"],
            border_width=1,
            border_color=self.colors["border"],
            state="disabled"
        )
        self.reset_roi_btn.pack(fill="x")
        
        # --- Section: Actions ---
        ctk.CTkLabel(
            scroll,
            text="ACTIONS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.reset_btn = ctk.CTkButton(
            scroll,
            text="🔄 Reset View",
            command=self.reset_view,
            height=36,
            fg_color=self.colors["border"],
            hover_color=self.colors["primary"],
            state="disabled"
        )
        self.reset_btn.pack(fill="x", pady=(0, 25))
        
        # --- Section: GPIO ---
        if IS_RASPBERRY_PI or self.gpio_controller.gpio_available:
            ctk.CTkLabel(
                scroll,
                text="HARDWARE",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["primary"],
                anchor="w"
            ).pack(fill="x", pady=(0, 10))
            
            # GPIO Status
            gpio_status = self.gpio_controller.get_status()
            status_text = "✅ Active" if gpio_status["initialized"] else "Simulation"
            status_color = self.colors["success"] if gpio_status["initialized"] else self.colors["warning"]
            
            self.gpio_status_label = ctk.CTkLabel(
                scroll,
                text=f"GPIO: {status_text}",
                font=ctk.CTkFont(size=12),
                text_color=status_color,
                anchor="w"
            )
            self.gpio_status_label.pack(fill="x", pady=(0, 10))
            
            self.gpio_test_btn = ctk.CTkButton(
                scroll,
                text="Test Signals",
                command=self.test_gpio,
                height=32,
                fg_color="#6366f1",
                hover_color="#4f46e5"
            )
            self.gpio_test_btn.pack(fill="x", pady=(0, 15))
        
    def create_main_display(self):
        """Create enhanced main image display area"""
        main = ctk.CTkFrame(
            self.root, 
            fg_color=self.colors["bg"],
            corner_radius=0
        )
        main.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)
        
        # Canvas frame with border
        self.canvas_frame = ctk.CTkFrame(
            main,
            fg_color=self.colors["surface"],
            corner_radius=0,
            border_width=0
        )
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Placeholder
        placeholder_frame = ctk.CTkFrame(self.canvas_frame, fg_color="transparent")
        placeholder_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.placeholder_icon = ctk.CTkLabel(
            placeholder_frame,
            text="📷",
            font=ctk.CTkFont(size=80),
            text_color=self.colors["border"]
        )
        self.placeholder_icon.pack(pady=(0, 20))
        
        self.placeholder = ctk.CTkLabel(
            placeholder_frame,
            text="Ready to Scan",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        self.placeholder.pack(pady=(0, 10))
        
        sub_placeholder = ctk.CTkLabel(
            placeholder_frame,
            text="Load an image or start the camera feed to begin",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        sub_placeholder.pack()
        
        self.image_label = None
        
    def create_right_panel(self):
        """Create Right Insights Panel"""
        right_panel = ctk.CTkFrame(
            self.root,
            width=320,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        right_panel.grid(row=1, column=2, sticky="nsew", padx=0, pady=0)
        right_panel.grid_propagate(False)
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent"
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- Total Count Card ---
        ctk.CTkLabel(
            scroll,
            text="TOTAL DETECTED",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        count_card = ctk.CTkFrame(scroll, fg_color=self.colors["bg"], corner_radius=12)
        count_card.pack(fill="x", pady=(0, 25))
        
        self.markers_count = ctk.CTkLabel(
            count_card,
            text="0",
            font=ctk.CTkFont(size=64, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.markers_count.pack(pady=(20, 5))
        
        ctk.CTkLabel(
            count_card,
            text="Markers Visible",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 20))

        # --- Detection Log ---
        ctk.CTkLabel(
            scroll,
            text="LIVE FEED",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.results_text = ctk.CTkTextbox(
            scroll,
            height=300,
            font=ctk.CTkFont(family="Courier", size=11),
            fg_color=self.colors["bg"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
            corner_radius=8
        )
        self.results_text.pack(fill="x", pady=(0, 20))
        
        # --- Export Options ---
        ctk.CTkLabel(
            scroll,
            text="EXPORT",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.save_btn = ctk.CTkButton(
            scroll,
            text="💾 Save Analysis",
            command=self.save_results,
            height=40,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            font=ctk.CTkFont(weight="bold"),
            state="disabled"
        )
        self.save_btn.pack(fill="x", pady=(0, 10))

    def create_footer(self):
        """Create simple footer"""
        footer = ctk.CTkFrame(
            self.root, 
            height=35,
            fg_color=self.colors["bg"],
            corner_radius=0
        )
        footer.grid(row=2, column=0, columnspan=3, sticky="ew")
        footer.grid_propagate(False)
        
        # Border top
        border = ctk.CTkFrame(footer, height=1, fg_color=self.colors["border"])
        border.pack(fill="x", side="top")
        
        self.status_label = ctk.CTkLabel(
            footer,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="left", padx=20)
        
        version = ctk.CTkLabel(
            footer,
            text="v2.1",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_secondary"]
        )
        version.pack(side="right", padx=20)
        
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
            
            self.reset_btn.configure(state="normal")
            self.detected_markers = []
            self.all_detected_markers = []
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", "Image loaded. Running detection...\n")
            self.markers_count.configure(text="0")
            self.color_filter_var.set("All")
            self.selected_color_filter = "All"
            
            self.status_label.configure(text=f"Loading: {os.path.basename(file_path)}")
            self.header_status.configure(text="● Processing", text_color=self.colors["warning"])
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
        
        self.status_label.configure(text="Detecting markers...")
        self.header_status.configure(text="● Detecting", text_color=self.colors["warning"])
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
        
        self.save_btn.configure(state="normal")
        
        marker_count = len(self.detected_markers)
        self.status_label.configure(text=f"Found {marker_count} marker(s)")
        self.header_status.configure(text="● Complete", text_color=self.colors["success"])
    
    def apply_color_filter(self):
        """Show all markers (no filtering - removed local logic)"""
        # Just show everything the model detected - no filtering
        self.detected_markers = self.all_detected_markers.copy()
        
        # Renumber for display
        for idx, marker in enumerate(self.detected_markers, 1):
            marker["component_id"] = idx
        
    def update_results(self):
        """Update results display"""
        self.results_text.delete("1.0", "end")
        
        if not self.detected_markers:
            self.results_text.insert("1.0", "No markers detected.")
            self.markers_count.configure(text="0")
            return
        
        self.markers_count.configure(text=f"{len(self.detected_markers)}")
        
        results_text = "DETECTION RESULTS\n"
        results_text += "=" * 35 + "\n\n"
        
        for marker in self.detected_markers:
            cable_id = marker['component_id']
            color = marker.get('primary_color', 'Unknown')
            confidence = marker['confidence']
            stripe_count = marker.get('stripe_count', 3)
            stripes_in_group = marker.get('stripes_in_group', stripe_count)
            
            results_text += f"Cable #{cable_id}\n"
            results_text += f"  Color: {color}\n"
            results_text += f"  Confidence: {confidence:.1f}%\n"
            results_text += f"  Stripes: {stripes_in_group}\n\n"
        
        total_stripes = sum(m.get('stripes_in_group', m.get('stripe_count', 3)) for m in self.detected_markers)
        results_text += "=" * 35 + "\n"
        results_text += f"Total: {len(self.detected_markers)} marking(s)\n"
        results_text += f"Stripes: {total_stripes}\n"
        
        self.results_text.insert("1.0", results_text)
        
    def reset_view(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_display = self.original_image.copy()
            self.display_image(self.current_display)
            self.status_label.configure(text="Reset to original image")
            
    
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
            self.status_label.configure(text=f"Saved: {os.path.basename(file_path)}")
            
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
                    self.status_label.configure(
                        text=f"Filtered: {marker_count} {choice.lower()} of {total_count} total"
                    )
                else:
                    self.status_label.configure(text=f"Showing all {total_count} marker(s)")
    
    def get_available_cameras(self):
        """Get available cameras including simulation mode"""
        cameras = ["Select Camera"]
        
        # Add Simulation Mode option
        cameras.append("📷 Simulate Loaded Image")
        cameras.append("---")
        
        for i in range(10):
            cap = cv2.VideoCapture(i)
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
        
        if "Simulate Loaded Image" in choice:
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
        
        # Check for Simulation Mode
        if self.camera_index == -1:
            self.start_simulation_mode()
            return
            
        # Local Camera Loop (replacing WebRTC)
        try:
            print(f"📷 Starting local camera loop on device {self.camera_index}...")
            
            # Initialize camera capture locally
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

            self.status_label.configure(text=f"Camera active - starting inference...")
            self.header_status.configure(text="● Starting", text_color=self.colors["warning"])
            
            def camera_loop():
                """Background thread: Read Camera -> Display Smooth Video -> Async Inference"""
                print("🔹 Camera thread started (Performance Mode)")
                
                # Inference state
                self.latest_detections_lock = threading.Lock()
                self.is_inferencing = False
                
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
                        # Only start new inference if previous one finished
                        if not self.is_inferencing:
                            
                            def run_inference_job(input_frame):
                                try:
                                    self.is_inferencing = True
                                    
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
                                    if offset_x > 0 or offset_y > 0 and detections:
                                        for marker in detections:
                                            if 'bounding_box' in marker:
                                                marker['bounding_box']['x'] += offset_x
                                                marker['bounding_box']['y'] += offset_y
                                            
                                            if 'center' in marker:
                                                cx, cy = marker['center']
                                                marker['center'] = (cx + offset_x, cy + offset_y)
                                    
                                    # Group stripes
                                    if detections:
                                        grouped = self.detector._group_stripes_into_markings(detections)
                                        detections = grouped
                                    
                                    # Update detections safely
                                    with self.latest_detections_lock:
                                        self.all_detected_markers = detections
                                        
                                except Exception as e:
                                    print(f"⚠️ Inference error: {e}")
                                finally:
                                    self.is_inferencing = False
                            
                            # Start inference in background
                            inf_thread = threading.Thread(target=run_inference_job, args=(frame.copy(),), daemon=True)
                            inf_thread.start()
                        
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
                                self.status_label.configure(text=f"Live: {len(filtered_detections)} marker(s)")
                                self.header_status.configure(text="● Detected", text_color=self.colors["success"])
                            else:
                                self.status_label.configure(text="Live: Scanning...")
                                self.header_status.configure(text="● Scanning", text_color=self.colors["primary"])
                                
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
            
        self.status_label.configure(text="Simulation Mode Active")
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
    
    def stop_camera(self):
        """Stop Camera or Simulation"""
        print("Stopping camera/simulation...")
        self.camera_active = False
        self.simulation_running = False
        # self.show_detection_pause = False <-- Removed

        # Stop WebRTC stream (legacy cleanup if needed)
        # self.detector.stop_webrtc_stream()
        
        # Camera release is handled in the thread loop when self.camera_active becomes False
        # But we can force release here if we want to be safe, though usually safer to let thread exit
        
        self.camera_start_btn.configure(state="normal")
        self.camera_stop_btn.configure(state="disabled")
        self.camera_dropdown.configure(state="normal")
        
        if self.placeholder:
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place(relx=0.5, rely=0.4, anchor="center")
        
        self.status_label.configure(text="Stopped")
        self.header_status.configure(text="● Ready", text_color=self.colors["success"])
        print("✅ Stopped")
    

    

    
    
    # def resume_camera_feed(self): <-- Removed
    #    ...

    
    def test_gpio(self):
        """Test GPIO functionality"""
        def run_test():
            self.status_label.configure(text="Testing GPIO...")
            self.gpio_test_btn.configure(state="disabled")
            
            # Run test
            success = self.gpio_controller.test_gpio()
            
            # Update status
            if success:
                self.status_label.configure(text="GPIO test passed!")
                self.gpio_status_label.configure(
                    text="Status: ✅ Ready",
                    text_color=self.colors["success"]
                )
            else:
                self.status_label.configure(text="GPIO test failed!")
                self.gpio_status_label.configure(
                    text="Status: ❌ Failed",
                    text_color=self.colors["error"]
                )
            
            # Re-enable button
            self.root.after(3000, lambda: self.gpio_test_btn.configure(state="normal"))
            self.root.after(3000, lambda: self.status_label.configure(text="Ready"))
        
            # Run test in background thread
            thread = threading.Thread(target=run_test, daemon=True)
            thread.start()
            
    def run(self):
        """Run application"""
        def on_closing():
            if self.camera_active:
                self.stop_camera()
            # Stop WebRTC stream if active
            if self.detector.session_active:
                self.detector.stop_webrtc_stream()
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
        self.status_label.configure(text="ROI cleared - Detecting full frame")
        
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
            self.status_label.configure(text=f"ROI Active: {orig_w}x{orig_h}")
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

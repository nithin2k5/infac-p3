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


class CableMarkerApp:
    """Simple and professional cable marker detection application"""
    
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Simple color scheme
        self.colors = {
            "bg": "#1a1a1a",
            "surface": "#2d2d2d",
            "primary": "#0ea5e9",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "text": "#ffffff",
            "text_secondary": "#9ca3af",
            "border": "#404040"
        }
        
        # Main window
        self.root = ctk.CTk()
        self.root.title("Cable Marker Detection")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        self.root.configure(fg_color=self.colors["bg"])
        
        # Initialize detector with improved grouping distances
        self.detector = RoboflowDetector(
            min_confidence=0.3,
            grouping_distance=250,        # Increased for better stripe grouping
            grouping_horizontal_distance=500  # Increased for better stripe grouping
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
        self.all_detected_markers = []
        
        # Camera variables
        self.camera = None
        self.camera_active = False
        self.camera_index = 0
        self.capture_thread = None
        self.show_detection_pause = False
        self.auto_detect_enabled = True
        self.detection_interval = 2.0
        self.last_detection_time = 0
        self.live_detected_markers = []
        self.detection_running = False
        self.detection_thread = None
        self.detections_drawn_frame = None
        self.frame_lock = threading.Lock()
        
        # Smart detection variables
        self.stripes_detected = False
        self.waiting_for_capture = False
        self.capture_countdown = 0
        self.last_check_time = 0
        self.check_interval = 0.5  # Check for stripes every 0.5 seconds
        self.countdown_duration = 0.5  # Fast 0.5 second countdown before capture
        self.scene_locked = False  # Lock until scene changes
        
        # Filter
        self.selected_color_filter = "All"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup simple UI layout"""
        
        # Configure responsive grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Header
        self.create_header()
        
        # Sidebar
        self.create_sidebar()
        
        # Main display
        self.create_main_display()
        
        # Footer
        self.create_footer()
        
    def create_header(self):
        """Create simple header"""
        header = ctk.CTkFrame(self.root, height=60, fg_color=self.colors["surface"], corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="Cable Marker Detection System",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text"]
        )
        title.pack(side="left", padx=30, pady=15)
        
        # Status
        self.header_status = ctk.CTkLabel(
            header,
            text="● Ready",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["success"]
        )
        self.header_status.pack(side="right", padx=30)
        
    def create_sidebar(self):
        """Create simple sidebar"""
        sidebar = ctk.CTkFrame(
            self.root,
            width=320,
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
        scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Load Image
        ctk.CTkLabel(
            scroll,
            text="Load Image",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        ctk.CTkButton(
            scroll,
            text="Choose File",
            command=self.load_image,
            height=40,
            fg_color=self.colors["primary"],
            hover_color="#0284c7"
        ).pack(fill="x", pady=(0, 20))
        
        # Camera
        ctk.CTkLabel(
            scroll,
            text="Camera",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.camera_var = ctk.StringVar(value="Select Camera")
        self.camera_dropdown = ctk.CTkComboBox(
            scroll,
            values=self.get_available_cameras(),
            variable=self.camera_var,
            command=self.on_camera_selected,
            height=40
        )
        self.camera_dropdown.pack(fill="x", pady=(0, 8))
        
        camera_buttons = ctk.CTkFrame(scroll, fg_color="transparent")
        camera_buttons.pack(fill="x", pady=(0, 8))
        
        self.camera_start_btn = ctk.CTkButton(
            camera_buttons,
            text="Start",
            command=self.start_camera,
            height=40,
            width=145,
            fg_color=self.colors["success"],
            hover_color="#16a34a",
            state="disabled"
        )
        self.camera_start_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        self.camera_stop_btn = ctk.CTkButton(
            camera_buttons,
            text="Stop",
            command=self.stop_camera,
            height=40,
            width=145,
            fg_color=self.colors["error"],
            hover_color="#dc2626",
            state="disabled"
        )
        self.camera_stop_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        
        self.capture_btn = ctk.CTkButton(
            scroll,
            text="Capture Frame",
            command=self.capture_frame,
            height=40,
            state="disabled"
        )
        self.capture_btn.pack(fill="x", pady=(0, 8))
        
        # Auto-detect
        self.auto_detect_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            scroll,
            text="Auto-Detect",
            variable=self.auto_detect_var,
            command=self.toggle_auto_detect,
            font=ctk.CTkFont(size=12)
        ).pack(fill="x", pady=(0, 20))
        
        # Color Filter
        ctk.CTkLabel(
            scroll,
            text="Color Filter",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.color_filter_var = ctk.StringVar(value="All")
        self.color_filter_dropdown = ctk.CTkComboBox(
            scroll,
            values=["All", "White", "Yellow", "Blue", "Pink", "Green"],
            variable=self.color_filter_var,
            command=self.on_color_filter_changed,
            height=40
        )
        self.color_filter_dropdown.pack(fill="x", pady=(0, 20))
        
        # Actions
        ctk.CTkLabel(
            scroll,
            text="Actions",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        action_buttons = ctk.CTkFrame(scroll, fg_color="transparent")
        action_buttons.pack(fill="x", pady=(0, 20))
        
        self.reset_btn = ctk.CTkButton(
            action_buttons,
            text="Reset",
            command=self.reset_view,
            height=38,
            width=145,
            state="disabled"
        )
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        
        self.save_btn = ctk.CTkButton(
            action_buttons,
            text="Save",
            command=self.save_results,
            height=38,
            width=145,
            state="disabled"
        )
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        
        # Results
        ctk.CTkLabel(
            scroll,
            text="Results",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_secondary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        # Marker count
        count_frame = ctk.CTkFrame(scroll, fg_color=self.colors["bg"], corner_radius=8)
        count_frame.pack(fill="x", pady=(0, 8))
        
        self.markers_count = ctk.CTkLabel(
            count_frame,
            text="0",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.markers_count.pack(pady=15)
        
        ctk.CTkLabel(
            count_frame,
            text="Markers Detected",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        ).pack(pady=(0, 15))
        
        # Results text
        self.results_text = ctk.CTkTextbox(
            scroll,
            height=200,
            font=ctk.CTkFont(family="Courier", size=10),
            fg_color=self.colors["bg"]
        )
        self.results_text.pack(fill="both", expand=True, pady=(0, 0))
        
    def create_main_display(self):
        """Create main image display area"""
        main = ctk.CTkFrame(
            self.root, 
            fg_color=self.colors["bg"],
            corner_radius=0
        )
        main.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)
        
        # Canvas frame
        self.canvas_frame = ctk.CTkFrame(
            main,
            fg_color=self.colors["surface"],
            corner_radius=8,
            border_width=1,
            border_color=self.colors["border"]
        )
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Placeholder
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
            text="Load Image or Start Camera",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        self.placeholder.pack()
        
        self.image_label = None
        
    def create_footer(self):
        """Create simple footer"""
        footer = ctk.CTkFrame(
            self.root, 
            height=35,
            fg_color=self.colors["surface"],
            corner_radius=0
        )
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            footer,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="left", padx=20)
        
        version = ctk.CTkLabel(
            footer,
            text="v2.0",
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
            return
        
        try:
            if self.placeholder:
                self.placeholder.place_forget()
            if hasattr(self, 'placeholder_icon'):
                self.placeholder_icon.place_forget()
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            canvas_width = self.canvas_frame.winfo_width()
            canvas_height = self.canvas_frame.winfo_height()
            
            if canvas_width < 100 or canvas_height < 100:
                return
            
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
            
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        except Exception as e:
            pass
        
    def detect_markers(self):
        """Run marker detection"""
        if self.original_image is None:
            return
        
        self.status_label.configure(text="Detecting markers...")
        self.header_status.configure(text="● Detecting", text_color=self.colors["warning"])
        self.root.update()
        
        self.all_detected_markers = self.detector.detect_markers(self.original_image)
        
        self.apply_color_filter()
        
        self.processed_image = self.detector.draw_detections(
            self.original_image, 
            self.detected_markers
        )
        
        self.display_image(self.processed_image)
        self.update_results()
        
        saved_path = self.auto_save_detection()
        
        self.gpio_controller.process_detected_colors(self.detected_markers)
        
        self.save_btn.configure(state="normal")
        
        marker_count = len(self.detected_markers)
        self.status_label.configure(text=f"Found {marker_count} marker(s)")
        self.header_status.configure(text="● Complete", text_color=self.colors["success"])
    
    def apply_color_filter(self):
        """Filter markers by color"""
        if self.selected_color_filter == "All":
            self.detected_markers = self.all_detected_markers.copy()
        else:
            filter_color = self.selected_color_filter.lower().strip()
            
            color_normalizations = {
                "white": ["white", "whites", "white-stripe", "white-stripes"],
                "yellow": ["yellow", "yellows", "yellow-stripe", "yellow-stripes"],
                "blue": ["blue", "blues", "blue-stripe", "blue-stripes"],
                "pink": ["pink", "pinks", "pink-stripe", "pink-stripes"],
                "green": ["green", "greens", "green-stripe", "green-stripes"]
            }
            
            color_variations = color_normalizations.get(filter_color, [filter_color])
            
            self.detected_markers = []
            for marker in self.all_detected_markers:
                marker_color = marker.get('primary_color', '').lower().strip()
                
                if marker_color in color_variations or any(var in marker_color for var in color_variations):
                    self.detected_markers.append(marker)
                elif filter_color in marker_color:
                    self.detected_markers.append(marker)
        
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
            
    def auto_save_detection(self):
        """Auto-save detection image"""
        if self.processed_image is None:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            marker_count = len(self.detected_markers)
            
            if hasattr(self, 'image_path') and self.image_path:
                source_name = os.path.splitext(os.path.basename(self.image_path))[0]
                source_name = "".join(c for c in source_name if c.isalnum() or c in ('-', '_'))[:30]
                filename = f"{timestamp}_{source_name}_{marker_count}markers.jpg"
            else:
                filename = f"{timestamp}_detection_{marker_count}markers.jpg"
            
            file_path = os.path.join(self.detections_dir, filename)
            cv2.imwrite(file_path, self.processed_image)
            return file_path
        except Exception as e:
            return None
    
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
        """Get available cameras"""
        cameras = ["Select Camera"]
        for i in range(10):
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
        """Start camera"""
        if self.camera_active:
            return
        
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                messagebox.showerror("Error", f"Failed to open camera {self.camera_index}")
                return
            
            self.camera_active = True
            self.last_detection_time = 0
            self.live_detected_markers = []
            self.detections_drawn_frame = None
            
            # Reset smart detection variables
            self.stripes_detected = False
            self.waiting_for_capture = False
            self.capture_countdown = 0
            self.last_check_time = 0
            self.scene_locked = False
            
            self.camera_start_btn.configure(state="disabled")
            self.camera_stop_btn.configure(state="normal")
            self.capture_btn.configure(state="normal")
            self.camera_dropdown.configure(state="disabled")
            
            self.capture_thread = threading.Thread(target=self.update_camera_feed, daemon=True)
            self.capture_thread.start()
            
            self.status_label.configure(text=f"Camera {self.camera_index} active - scanning for cables")
            self.header_status.configure(text="● Scanning", text_color=self.colors["primary"])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
    
    def stop_camera(self):
        """Stop camera"""
        self.camera_active = False
        self.show_detection_pause = False
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_start_btn.configure(state="normal")
        self.camera_stop_btn.configure(state="disabled")
        self.capture_btn.configure(state="disabled")
        self.camera_dropdown.configure(state="normal")
        
        if self.placeholder:
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        if hasattr(self, 'placeholder_icon'):
            self.placeholder_icon.place(relx=0.5, rely=0.4, anchor="center")
        
        self.status_label.configure(text="Camera stopped")
        self.header_status.configure(text="● Ready", text_color=self.colors["success"])
    
    def check_for_stripes_lightweight(self, frame):
        """Lightweight check to see if any stripes are visible"""
        if self.detection_running:
            return False
        
        self.detection_running = True
        
        def check():
            try:
                # Quick check with very low resolution for maximum speed
                small_frame = cv2.resize(frame, (480, 360))
                predictions = self.detector.detect_markers(small_frame)
                
                has_stripes = len(predictions) > 0
                
                with self.frame_lock:
                    self.stripes_detected = has_stripes
                
                print(f"Stripe check: {'Found stripes' if has_stripes else 'No stripes'}")
                
            except Exception as e:
                print(f"Check error: {e}")
                with self.frame_lock:
                    self.stripes_detected = False
            finally:
                self.detection_running = False
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def process_frame_full(self, frame):
        """Full detection and processing of frame"""
        def detect():
            try:
                self.root.after(0, lambda: self.status_label.configure(text="Processing captured frame..."))
                self.root.after(0, lambda: self.header_status.configure(text="● Processing", text_color=self.colors["warning"]))
                
                all_markers = self.detector.detect_markers(frame)
                
                temp_all = self.all_detected_markers
                self.all_detected_markers = all_markers
                self.apply_color_filter()
                detected = self.detected_markers.copy()
                self.all_detected_markers = temp_all
                
                if detected:
                    display_frame = self.detector.draw_detections(frame, detected)
                    self.original_image = frame.copy()
                    self.processed_image = display_frame
                else:
                    display_frame = frame.copy()
                
                with self.frame_lock:
                    self.live_detected_markers = detected
                    self.detections_drawn_frame = display_frame
                
                self.root.after(0, self.update_results)
                self.root.after(0, lambda: self.markers_count.configure(text=f"{len(detected)}"))
                
                self.gpio_controller.process_detected_colors(detected)
                
                marker_count = len(detected)
                if marker_count > 0:
                    status_text = f"Captured: {marker_count} marker(s) detected"
                    self.root.after(0, lambda t=status_text: self.status_label.configure(text=t))
                    self.root.after(0, lambda: self.header_status.configure(text="● Detected", text_color=self.colors["success"]))
                    self.root.after(0, lambda: self.save_btn.configure(state="normal"))
                    
                    # Lock scene until stripes disappear
                    with self.frame_lock:
                        self.scene_locked = True
                else:
                    self.root.after(0, lambda: self.status_label.configure(text="Captured: No markers found"))
                    self.root.after(0, lambda: self.header_status.configure(text="● Scanning", text_color=self.colors["primary"]))
                
            except Exception as e:
                print(f"Detection error: {e}")
        
        thread = threading.Thread(target=detect, daemon=True)
        thread.start()
    
    def update_camera_feed(self):
        """Update camera feed with smart detection"""
        if self.placeholder:
            self.root.after(0, lambda: self.placeholder.place_forget())
        if hasattr(self, 'placeholder_icon'):
            self.root.after(0, lambda: self.placeholder_icon.place_forget())
        
        frame_count = 0
        countdown_start_time = None
        
        while self.camera_active and self.camera:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Display frame immediately (smooth feed)
            try:
                with self.frame_lock:
                    if self.detections_drawn_frame is not None and self.scene_locked:
                        # Show detected frame while locked
                        display_frame = self.detections_drawn_frame
                    else:
                        display_frame = frame
            except:
                display_frame = frame
            
            self.display_image(display_frame)
            
            # Smart detection logic
            if self.auto_detect_enabled and not self.detection_running:
                # Check if we need to reset scene lock
                if self.scene_locked:
                    # Periodically check if stripes are gone
                    if current_time - self.last_check_time >= self.check_interval:
                        self.last_check_time = current_time
                        self.check_for_stripes_lightweight(frame.copy())
                        
                        # If no stripes detected anymore, unlock scene
                        time.sleep(0.1)  # Wait for check to complete
                        with self.frame_lock:
                            if not self.stripes_detected:
                                self.scene_locked = False
                                self.detections_drawn_frame = None
                                print("Scene changed - ready for next detection")
                                self.root.after(0, lambda: self.status_label.configure(text="Ready for next detection"))
                                self.root.after(0, lambda: self.header_status.configure(text="● Scanning", text_color=self.colors["primary"]))
                
                # If not locked and not in countdown, check for stripes
                elif not self.waiting_for_capture:
                    if current_time - self.last_check_time >= self.check_interval:
                        self.last_check_time = current_time
                        self.check_for_stripes_lightweight(frame.copy())
                        
                        # Wait a bit for check to complete
                        time.sleep(0.1)
                        
                        # If stripes detected, start countdown
                        with self.frame_lock:
                            if self.stripes_detected:
                                self.waiting_for_capture = True
                                countdown_start_time = current_time
                                print(f"Stripes detected! Starting {self.countdown_duration}s countdown...")
                                self.root.after(0, lambda: self.status_label.configure(text=f"Stripes detected! Capturing in {self.countdown_duration}s..."))
                                self.root.after(0, lambda: self.header_status.configure(text="● Countdown", text_color=self.colors["warning"]))
                
                # Handle countdown
                elif self.waiting_for_capture and countdown_start_time:
                    elapsed = current_time - countdown_start_time
                    remaining = max(0, self.countdown_duration - elapsed)
                    
                    if remaining > 0:
                        # Update countdown display
                        self.root.after(0, lambda r=remaining: self.status_label.configure(text=f"Capturing in {r:.1f}s..."))
                    else:
                        # Countdown finished, capture and process
                        print("Capturing frame now!")
                        self.root.after(0, lambda: self.status_label.configure(text="Capturing frame..."))
                        self.process_frame_full(frame.copy())
                        
                        # Reset countdown state
                        self.waiting_for_capture = False
                        countdown_start_time = None
            
            if frame_count == 1:
                self.root.after(0, lambda: self.reset_btn.configure(state="normal"))
            
            # Smooth 30 FPS
            time.sleep(0.033)
    
    def capture_frame(self):
        """Capture frame from camera"""
        if not self.camera_active or self.original_image is None:
            messagebox.showwarning("Warning", "No camera frame available")
            return
        
        self.current_display = self.original_image.copy()
        self.display_image(self.current_display)
        
        self.detected_markers = []
        self.all_detected_markers = []
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Frame captured. Detecting...\n")
        self.markers_count.configure(text="0")
        self.color_filter_var.set("All")
        self.selected_color_filter = "All"
        
        self.image_path = None
        
        self.status_label.configure(text="Frame captured. Detecting...")
        self.header_status.configure(text="● Processing", text_color=self.colors["warning"])
        self.root.update()
        
        self.detect_markers()
            
    def toggle_auto_detect(self):
        """Toggle auto-detection"""
        self.auto_detect_enabled = self.auto_detect_var.get()
        status = "enabled" if self.auto_detect_enabled else "disabled"
        self.status_label.configure(text=f"Auto-detection {status}")
    
    def resume_camera_feed(self):
        """Resume camera feed"""
        if self.camera_active:
            self.show_detection_pause = False
            self.status_label.configure(text="Camera feed resumed")
            
    def run(self):
        """Run application"""
        def on_closing():
            if self.camera_active:
                self.stop_camera()
            self.gpio_controller.cleanup()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = CableMarkerApp()
    app.run()

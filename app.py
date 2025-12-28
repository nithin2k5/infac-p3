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
import os
from datetime import datetime


class CableMarkerApp:
    """Professional cable marker detection application"""
    
    def __init__(self):
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Cable Marker Detection System - Professional Edition")
        self.root.geometry("1600x900")
        
        # Initialize Roboflow detector only
        self.detector = RoboflowDetector()
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
        sidebar = ctk.CTkFrame(self.root, width=350, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Title
        title = ctk.CTkLabel(
            sidebar,
            text="Cable Marker Detector",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 10), padx=20)
        
        subtitle = ctk.CTkLabel(
            sidebar,
            text="Roboflow-Powered Detection",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 10), padx=20)
        
        # Detector type indicator
        self.detector_label = ctk.CTkLabel(
            sidebar,
            text=f"Engine: {getattr(self, 'detector_type', 'Unknown')}",
            font=ctk.CTkFont(size=10),
            text_color="lightgreen"
        )
        self.detector_label.pack(pady=(0, 20), padx=20)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        self.load_btn = ctk.CTkButton(
            btn_frame,
            text="📁 Load Image",
            command=self.load_image,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.load_btn.pack(fill="x", pady=5)
        
        self.detect_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 Detect Markers",
            command=self.detect_markers,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#388E3C",
            state="disabled"
        )
        self.detect_btn.pack(fill="x", pady=5)
        
        self.reset_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Reset View",
            command=self.reset_view,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#FF9800",
            hover_color="#F57C00",
            state="disabled"
        )
        self.reset_btn.pack(fill="x", pady=5)
        
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save Results",
            command=self.save_results,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            state="disabled"
        )
        self.save_btn.pack(fill="x", pady=5)
        
        self.export_btn = ctk.CTkButton(
            btn_frame,
            text="📊 Export Data",
            command=self.export_data,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#00BCD4",
            hover_color="#0097A7",
            state="disabled"
        )
        self.export_btn.pack(fill="x", pady=5)
        
        # Separator
        separator = ctk.CTkFrame(sidebar, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=20)
        
        # Results section
        results_label = ctk.CTkLabel(
            sidebar,
            text="Detection Results",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        results_label.pack(pady=(10, 15), padx=20)
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(sidebar)
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.markers_count = ctk.CTkLabel(
            self.stats_frame,
            text="Markers: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.markers_count.pack(pady=5)
        
        # Results text
        self.results_text = ctk.CTkTextbox(
            sidebar,
            font=ctk.CTkFont(family="Courier", size=11),
            wrap="word"
        )
        self.results_text.pack(fill="both", expand=True, padx=20, pady=10)
        
    def create_main_area(self):
        """Create main display area"""
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas for image display
        self.canvas_frame = ctk.CTkFrame(main_frame)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.canvas_frame,
            text="Load an image to begin detection",
            font=ctk.CTkFont(size=20),
            text_color="gray50"
        )
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        
        # Image label (will be created when image is loaded)
        self.image_label = None
        
    def create_status_bar(self):
        """Create bottom status bar"""
        status_frame = ctk.CTkFrame(self.root, height=35, corner_radius=0)
        status_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        status_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready - Load an image to start",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=15, pady=5)
        
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
            
            # Enable buttons
            self.detect_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            
            # Clear previous results
            self.detected_markers = []
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", "Image loaded successfully.\nClick 'Detect Markers' to begin analysis.")
            self.markers_count.configure(text="Markers: 0")
            
            filename = os.path.basename(file_path)
            self.status_label.configure(text=f"Loaded: {filename}")
            
    def display_image(self, image):
        """Display image on canvas"""
        if image is None:
            return
        
        # Hide placeholder
        if self.placeholder:
            self.placeholder.place_forget()
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get canvas dimensions
        canvas_width = self.canvas_frame.winfo_width()
        canvas_height = self.canvas_frame.winfo_height()
        
        # Scale image to fit
        height, width = image_rgb.shape[:2]
        
        if canvas_width > 100 and canvas_height > 100:
            scale = min(canvas_width / width, canvas_height / height) * 0.95
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        pil_image = Image.fromarray(image_rgb)
        photo = ImageTk.PhotoImage(pil_image)
        
        # Display
        if self.image_label is None:
            self.image_label = ctk.CTkLabel(self.canvas_frame, text="")
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.image_label.configure(image=photo)
        self.image_label.image = photo  # Keep reference
        
    def detect_markers(self):
        """Run marker detection"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return
        
        self.status_label.configure(text="Processing... Detecting markers")
        self.root.update()
        
        # Run detection
        self.detected_markers = self.detector.detect_markers(self.original_image)
        
        # Draw results
        self.processed_image = self.detector.draw_detections(
            self.original_image, 
            self.detected_markers
        )
        
        # Display
        self.display_image(self.processed_image)
        
        # Update results
        self.update_results()
        
        # Enable export buttons
        self.save_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        
        marker_count = len(self.detected_markers)
        self.status_label.configure(
            text=f"Detection complete - Found {marker_count} marker(s)"
        )
        
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
        self.markers_count.configure(text=f"Markers: {len(self.detected_markers)}")
        
        # Detailed results
        results_text = "=== DETECTION RESULTS ===\n\n"
        
        for marker in self.detected_markers:
            cable_id = marker['component_id']
            primary_color = marker.get('primary_color', 'Unknown')
            
            results_text += f"Cable #{cable_id}\n"
            results_text += f"═════════════════════════\n"
            results_text += f"Marker Color: {primary_color}\n"
            results_text += f"Stripe Count: {marker['stripe_count']}\n"
            results_text += f"Bar Pattern: {'|' * marker['stripe_count']}\n"
            results_text += f"Confidence: {marker['confidence']}%\n"
            
            bbox = marker['bounding_box']
            results_text += f"Marker Position: ({bbox['x']}, {bbox['y']})\n"
            results_text += f"Marker Size: {bbox['width']}x{bbox['height']}px\n"
            results_text += "\n"
        
        results_text += "─" * 35 + "\n"
        results_text += f"Total Cables Detected: {len(self.detected_markers)}\n"
        
        self.results_text.insert("1.0", results_text)
        
    def reset_view(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_display = self.original_image.copy()
            self.display_image(self.current_display)
            self.status_label.configure(text="Reset to original image")
            
    def save_results(self):
        """Save annotated image"""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No results to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ]
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
            
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CableMarkerApp()
    app.run()


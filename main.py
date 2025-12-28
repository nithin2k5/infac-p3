import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os


class ColorPartDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color-Based Part Detection System")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")
        
        # Variables
        self.current_image = None
        self.original_image = None
        self.processed_image = None
        self.image_path = None
        
        # Color ranges for detection (HSV format)
        self.color_ranges = {
            "Red": {"lower": np.array([0, 100, 100]), "upper": np.array([10, 255, 255]), "color": (0, 0, 255)},
            "Orange": {"lower": np.array([10, 100, 100]), "upper": np.array([25, 255, 255]), "color": (0, 165, 255)},
            "Yellow": {"lower": np.array([25, 100, 100]), "upper": np.array([35, 255, 255]), "color": (0, 255, 255)},
            "Green": {"lower": np.array([35, 100, 100]), "upper": np.array([85, 255, 255]), "color": (0, 255, 0)},
            "Blue": {"lower": np.array([85, 100, 100]), "upper": np.array([130, 255, 255]), "color": (255, 0, 0)},
            "Purple": {"lower": np.array([130, 100, 100]), "upper": np.array([160, 255, 255]), "color": (255, 0, 255)},
            "Brown": {"lower": np.array([10, 50, 50]), "upper": np.array([20, 150, 150]), "color": (42, 42, 165)},
            "Black": {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 50]), "color": (0, 0, 0)},
            "White": {"lower": np.array([0, 0, 200]), "upper": np.array([180, 30, 255]), "color": (255, 255, 255)},
        }
        
        self.detection_results = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title bar
        title_frame = tk.Frame(self.root, bg="#2d2d2d", height=60)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="Color-Based Part Detection System", 
            font=("Arial", 20, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        title_label.pack(pady=15)
        
        # Main container
        main_container = tk.Frame(self.root, bg="#1e1e1e")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg="#2d2d2d", width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Control buttons
        controls_label = tk.Label(
            left_panel,
            text="Controls",
            font=("Arial", 14, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        controls_label.pack(pady=20)
        
        self.load_btn = tk.Button(
            left_panel,
            text="📁 Load Image",
            command=self.load_image,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.load_btn.pack(pady=10, padx=20, fill=tk.X)
        
        self.detect_btn = tk.Button(
            left_panel,
            text="🔍 Detect Colors",
            command=self.detect_colors,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.detect_btn.pack(pady=10, padx=20, fill=tk.X)
        
        self.reset_btn = tk.Button(
            left_panel,
            text="🔄 Reset",
            command=self.reset_view,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.reset_btn.pack(pady=10, padx=20, fill=tk.X)
        
        self.save_btn = tk.Button(
            left_panel,
            text="💾 Save Result",
            command=self.save_result,
            font=("Arial", 12),
            bg="#9C27B0",
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.save_btn.pack(pady=10, padx=20, fill=tk.X)
        
        # Separator
        separator = tk.Frame(left_panel, bg="#444444", height=2)
        separator.pack(fill=tk.X, padx=20, pady=20)
        
        # Detection results
        results_label = tk.Label(
            left_panel,
            text="Detection Results",
            font=("Arial", 14, "bold"),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        results_label.pack(pady=10)
        
        # Results text widget with scrollbar
        results_frame = tk.Frame(left_panel, bg="#2d2d2d")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(
            results_frame,
            font=("Courier", 10),
            bg="#1a1a1a",
            fg="#00ff00",
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Right panel - Image display
        right_panel = tk.Frame(main_container, bg="#2d2d2d")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Image canvas
        self.canvas = tk.Canvas(right_panel, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#2d2d2d", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready - Load an image to begin",
            font=("Arial", 10),
            bg="#2d2d2d",
            fg="#ffffff",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=5)
        
    def load_image(self):
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
            
            self.current_image = self.original_image.copy()
            self.display_image(self.current_image)
            
            self.detect_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Image loaded successfully!\nClick 'Detect Colors' to begin analysis.")
    
    def display_image(self, image):
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate scaling to fit canvas
        height, width = image_rgb.shape[:2]
        
        if canvas_width > 1 and canvas_height > 1:
            scale = min(canvas_width / width, canvas_height / height) * 0.95
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            image_rgb = cv2.resize(image_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        image_pil = Image.fromarray(image_rgb)
        self.photo = ImageTk.PhotoImage(image_pil)
        
        # Display on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo,
            anchor=tk.CENTER
        )
    
    def detect_colors(self):
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first!")
            return
        
        self.status_label.config(text="Processing... Detecting green circles")
        self.root.update()
        
        # Create a copy for processing
        result_image = self.original_image.copy()
        hsv_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV)
        
        self.detection_results = []
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== CIRCLED MARKS DETECTION ===\n\n")
        
        # Step 1: Detect green circles (the markers)
        # Green color range for the circles
        green_lower = np.array([40, 100, 100])
        green_upper = np.array([80, 255, 255])
        
        green_mask = cv2.inRange(hsv_image, green_lower, green_upper)
        
        # Apply morphological operations
        kernel = np.ones((5, 5), np.uint8)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours of green circles
        contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter for circular/elliptical shapes
        circles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Minimum area for a circle
                # Fit ellipse to check if it's circular
                if len(contour) >= 5:
                    ellipse = cv2.fitEllipse(contour)
                    (center_x, center_y), (width, height), angle = ellipse
                    
                    # Check if it's reasonably circular (aspect ratio close to 1)
                    aspect_ratio = max(width, height) / (min(width, height) + 0.001)
                    
                    if aspect_ratio < 2.0:  # Reasonably circular
                        circles.append({
                            "center": (int(center_x), int(center_y)),
                            "size": (int(width), int(height)),
                            "angle": angle
                        })
        
        if not circles:
            self.results_text.insert(tk.END, "No green circles detected!\n")
            self.results_text.insert(tk.END, "Please mark the areas you want to detect with green circles.")
            self.status_label.config(text="No circles found")
            return
        
        # Sort circles from left to right
        circles.sort(key=lambda c: c["center"][0])
        
        # Step 2: Analyze the color inside each circle
        detected_marks = []
        for i, circle in enumerate(circles):
            center_x, center_y = circle["center"]
            radius = int(max(circle["size"]) / 2)
            
            # Create a mask for the circle interior
            mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
            cv2.circle(mask, (center_x, center_y), int(radius * 0.6), 255, -1)
            
            # Extract the region inside the circle
            roi_hsv = cv2.bitwise_and(hsv_image, hsv_image, mask=mask)
            
            # Detect the dominant color in this region
            detected_color = self._detect_color_in_region(roi_hsv, mask)
            
            if detected_color:
                detected_marks.append({
                    "mark_id": i + 1,
                    "color": detected_color["name"],
                    "center": (center_x, center_y),
                    "confidence": detected_color["confidence"]
                })
                
                # Draw on result image
                cv2.circle(result_image, (center_x, center_y), radius, (0, 255, 0), 3)
                cv2.putText(
                    result_image,
                    f"{i+1}: {detected_color['name']}",
                    (center_x - 40, center_y - radius - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )
                
                # Add to results
                self.results_text.insert(
                    tk.END,
                    f"Mark #{i+1}: {detected_color['name']}\n"
                    f"  Position: ({center_x}, {center_y})\n"
                    f"  Confidence: {detected_color['confidence']:.1f}%\n\n"
                )
        
        # Generate bar pattern
        if detected_marks:
            pattern = "".join(["|" for _ in detected_marks])
            color_sequence = " > ".join([m["color"] for m in detected_marks])
            
            self.results_text.insert(tk.END, f"\n{'='*30}\n")
            self.results_text.insert(tk.END, f"Pattern: {pattern}\n")
            self.results_text.insert(tk.END, f"Sequence: {color_sequence}\n")
            self.results_text.insert(tk.END, f"Total Marks: {len(detected_marks)}\n")
            
            self.detection_results = detected_marks
            self.status_label.config(text=f"Detected {len(detected_marks)} circled marks")
        else:
            self.results_text.insert(tk.END, "Could not detect colors inside circles.\n")
            self.status_label.config(text="No colors detected")
        
        self.processed_image = result_image
        self.display_image(result_image)
        self.save_btn.config(state=tk.NORMAL)
    
    def _detect_color_in_region(self, roi_hsv, mask):
        """Detect the dominant color in a masked region"""
        best_match = None
        max_pixel_count = 0
        
        for color_name, color_data in self.color_ranges.items():
            # Skip green (that's our circle color)
            if color_name == "Green":
                continue
            
            # Create mask for this color in the ROI
            color_mask = cv2.inRange(roi_hsv, color_data["lower"], color_data["upper"])
            
            # Combine with the circle mask
            combined_mask = cv2.bitwise_and(color_mask, mask)
            
            # Count non-zero pixels
            pixel_count = cv2.countNonZero(combined_mask)
            
            if pixel_count > max_pixel_count:
                max_pixel_count = pixel_count
                best_match = color_name
        
        if best_match and max_pixel_count > 50:  # Minimum pixel threshold
            # Calculate confidence based on pixel count
            total_pixels = cv2.countNonZero(mask)
            confidence = (max_pixel_count / total_pixels) * 100 if total_pixels > 0 else 0
            
            return {
                "name": best_match,
                "confidence": confidence,
                "pixel_count": max_pixel_count
            }
        
        return None
    
    def reset_view(self):
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.display_image(self.current_image)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "View reset to original image.\nClick 'Detect Colors' to analyze.")
            self.status_label.config(text="Reset to original image")
            self.save_btn.config(state=tk.DISABLED)
    
    def save_result(self):
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No processed image to save!")
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
            messagebox.showinfo("Success", f"Image saved successfully!\n{file_path}")
            self.status_label.config(text=f"Saved: {os.path.basename(file_path)}")


def main():
    root = tk.Tk()
    app = ColorPartDetectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


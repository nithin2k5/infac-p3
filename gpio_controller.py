"""
GPIO Controller for Color Detection
Controls GPIO pins based on detected colors
"""

import sys
import platform

# Try to import RPi.GPIO for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO not available. GPIO functionality will be simulated.")
    print("   Install with: pip install RPi.GPIO (on Raspberry Pi)")


class GPIOController:
    """Controls GPIO pins based on detected colors"""
    
    def __init__(self, pin1=18, pin2=23, pin3=24):
        """
        Initialize GPIO controller
        
        Args:
            pin1: GPIO pin number for Pin1 (default: 18)
            pin2: GPIO pin number for Pin2 (default: 23)
            pin3: GPIO pin number for Pin3 (default: 24)
        """
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        
        self.gpio_available = GPIO_AVAILABLE
        self.initialized = False
        
        # Color to pin mapping
        self.color_pin_map = {
            "Yellow": [pin1],
            "Blue": [pin2],
            "Green": [pin1, pin2],
            "White": [pin3],
            "Pink": [pin1, pin3],
            "Red": [pin2, pin3],
            "Grey": [pin1, pin2, pin3],
            "Gray": [pin1, pin2, pin3]  # Alternative spelling
        }
        
        if self.gpio_available:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Setup pins as outputs
                GPIO.setup(self.pin1, GPIO.OUT)
                GPIO.setup(self.pin2, GPIO.OUT)
                GPIO.setup(self.pin3, GPIO.OUT)
                
                # Initialize all pins to LOW
                GPIO.output(self.pin1, GPIO.LOW)
                GPIO.output(self.pin2, GPIO.LOW)
                GPIO.output(self.pin3, GPIO.LOW)
                
                self.initialized = True
                print(f"✅ GPIO initialized - Pin1: {pin1}, Pin2: {pin2}, Pin3: {pin3}")
            except Exception as e:
                print(f"⚠️ GPIO initialization error: {e}")
                self.gpio_available = False
        else:
            print("⚠️ Running in simulation mode (no GPIO hardware)")
    
    def set_pins_for_color(self, color):
        """
        Set GPIO pins HIGH based on detected color
        
        Args:
            color: Detected color name (Yellow, Blue, Green, White, Pink, Red, Grey/Gray)
        """
        if not self.initialized and not self.gpio_available:
            # Simulation mode
            pins = self.color_pin_map.get(color, [])
            if pins:
                print(f"🔌 [SIM] Setting pins {pins} HIGH for color: {color}")
            else:
                print(f"⚠️ [SIM] Unknown color: {color}")
            return
        
        # Get pins for this color
        pins_to_set = self.color_pin_map.get(color, [])
        
        if not pins_to_set:
            print(f"⚠️ Unknown color: {color} - No GPIO pins configured")
            return
        
        try:
            # First, set all pins to LOW
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.LOW)
            GPIO.output(self.pin3, GPIO.LOW)
            
            # Then set the required pins to HIGH
            for pin in pins_to_set:
                GPIO.output(pin, GPIO.HIGH)
            
            pin_names = [f"Pin{self.pin1}" if pin == self.pin1 else 
                        f"Pin{self.pin2}" if pin == self.pin2 else 
                        f"Pin{self.pin3}" for pin in pins_to_set]
            
            print(f"🔌 GPIO: Set {', '.join(pin_names)} HIGH for color: {color}")
            
        except Exception as e:
            print(f"❌ Error setting GPIO pins: {e}")
    
    def set_all_pins_low(self):
        """Set all pins to LOW"""
        if not self.initialized and not self.gpio_available:
            print("🔌 [SIM] Setting all pins LOW")
            return
        
        try:
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.LOW)
            GPIO.output(self.pin3, GPIO.LOW)
            print("🔌 GPIO: All pins set to LOW")
        except Exception as e:
            print(f"❌ Error setting pins LOW: {e}")
    
    def process_detected_colors(self, detected_markers):
        """
        Process detected markers and set GPIO pins based on colors
        
        Args:
            detected_markers: List of detected marker dictionaries with 'primary_color' field
        """
        if not detected_markers:
            self.set_all_pins_low()
            return
        
        # Get unique colors from detected markers
        detected_colors = set()
        for marker in detected_markers:
            color = marker.get('primary_color', '').strip()
            if color:
                detected_colors.add(color)
        
        # If multiple colors detected, we need to decide which one to use
        # For now, use the first detected color
        # You can modify this logic based on your requirements
        if detected_colors:
            primary_color = list(detected_colors)[0]
            self.set_pins_for_color(primary_color)
            
            if len(detected_colors) > 1:
                print(f"⚠️ Multiple colors detected: {detected_colors}")
                print(f"   Using primary color: {primary_color}")
        else:
            self.set_all_pins_low()
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.initialized and self.gpio_available:
            try:
                GPIO.cleanup()
                print("✅ GPIO cleaned up")
            except Exception as e:
                print(f"⚠️ Error cleaning up GPIO: {e}")
    
    def __del__(self):
        """Destructor - cleanup on deletion"""
        self.cleanup()


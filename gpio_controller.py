"""
GPIO Controller for Color Detection
Controls GPIO pins based on detected colors
Optimized for Raspberry Pi with robust error handling
"""

import sys
import platform
import os
import time

# Check if running on Raspberry Pi
IS_RASPBERRY_PI = os.path.exists('/proc/device-tree/model')
if IS_RASPBERRY_PI:
    try:
        with open('/proc/device-tree/model', 'r') as f:
            IS_RASPBERRY_PI = 'Raspberry Pi' in f.read()
    except:
        IS_RASPBERRY_PI = False

# Try to import RPi.GPIO for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    if IS_RASPBERRY_PI:
        print("✅ RPi.GPIO loaded - Running on Raspberry Pi")
    else:
        print("✅ RPi.GPIO available (but not on Raspberry Pi hardware)")
except ImportError:
    GPIO_AVAILABLE = False
    if IS_RASPBERRY_PI:
        print("❌ ERROR: RPi.GPIO not installed on Raspberry Pi!")
        print("   Install with: sudo apt-get install python3-rpi.gpio")
        print("   Or: pip install RPi.GPIO")
    else:
        print("⚠️ RPi.GPIO not available. GPIO functionality will be simulated.")
        print("   (This is normal on non-Raspberry Pi systems)")


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
            "yellow": [pin1],
            "blue": [pin2],
            "green": [pin1, pin2],
            "white": [pin3],
            "pink": [pin1, pin3],
            "red": [pin2, pin3],
            "grey": [pin1, pin2, pin3],
            "gray": [pin1, pin2, pin3]  # Alternative spelling
        }
        
        if self.gpio_available:
            try:
                # Check if GPIO is already initialized and cleanup if needed
                try:
                    GPIO.cleanup()
                    time.sleep(0.1)  # Brief pause for cleanup
                except:
                    pass  # Ignore cleanup errors if GPIO wasn't initialized
                
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Setup pins as outputs with explicit configuration
                GPIO.setup(self.pin1, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.pin2, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.pin3, GPIO.OUT, initial=GPIO.LOW)
                
                # Verify pins are LOW
                GPIO.output(self.pin1, GPIO.LOW)
                GPIO.output(self.pin2, GPIO.LOW)
                GPIO.output(self.pin3, GPIO.LOW)
                
                self.initialized = True
                print(f"✅ GPIO initialized successfully")
                print(f"   Pin1 (GPIO {pin1}) - Yellow, Green, Pink, Grey")
                print(f"   Pin2 (GPIO {pin2}) - Blue, Green, Red, Grey")
                print(f"   Pin3 (GPIO {pin3}) - White, Pink, Red, Grey")
                print(f"   All pins set to LOW (safe state)")
                
            except PermissionError:
                print(f"❌ GPIO Permission Error!")
                print(f"   Run with sudo or add user to gpio group:")
                print(f"   sudo usermod -a -G gpio $USER")
                print(f"   Then logout and login again")
                self.gpio_available = False
            except Exception as e:
                print(f"❌ GPIO initialization error: {e}")
                print(f"   This might be a hardware or permission issue")
                self.gpio_available = False
        else:
            print("⚠️ Running in simulation mode (no GPIO hardware)")
            if IS_RASPBERRY_PI:
                print("   GPIO hardware should be available. Check RPi.GPIO installation.")
    
    def set_pins_for_color(self, color):
        """
        Set GPIO pins HIGH based on detected color
        Thread-safe with error recovery
        
        Args:
            color: Detected color name (Yellow, Blue, Green, White, Pink, Red, Grey/Gray)
        """
        if not self.initialized and not self.gpio_available:
            # Simulation mode
            pins = self.color_pin_map.get(color, [])
            if pins:
                pin_str = ', '.join([f"GPIO{p}" for p in pins])
                print(f"🔌 [SIM] Setting {pin_str} HIGH for color: {color}")
            else:
                print(f"⚠️ [SIM] Unknown color: {color}")
            return
        
        # Get pins for this color
        pins_to_set = self.color_pin_map.get(color, [])
        
        if not pins_to_set:
            print(f"⚠️ Unknown color: {color} - No GPIO pins configured")
            return
        
        try:
            # First, set all pins to LOW (clean state)
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.LOW)
            GPIO.output(self.pin3, GPIO.LOW)
            
            # Small delay for GPIO stability (important on Raspberry Pi)
            if IS_RASPBERRY_PI:
                time.sleep(0.001)  # 1ms delay
            
            # Then set the required pins to HIGH
            for pin in pins_to_set:
                GPIO.output(pin, GPIO.HIGH)
                if IS_RASPBERRY_PI:
                    time.sleep(0.001)  # 1ms delay between pin changes
            
            # Create readable pin names
            pin_names = []
            for pin in pins_to_set:
                if pin == self.pin1:
                    pin_names.append(f"GPIO{self.pin1}")
                elif pin == self.pin2:
                    pin_names.append(f"GPIO{self.pin2}")
                elif pin == self.pin3:
                    pin_names.append(f"GPIO{self.pin3}")
            
            print(f"🔌 GPIO: {', '.join(pin_names)} → HIGH for {color}")
            
        except RuntimeError as e:
            print(f"❌ GPIO Runtime Error: {e}")
            print(f"   Attempting to reinitialize GPIO...")
            self.reinitialize_gpio()
        except Exception as e:
            print(f"❌ Error setting GPIO pins: {e}")
            print(f"   Pin states may be inconsistent")
    
    def set_all_pins_low(self):
        """Set all pins to LOW (safe state)"""
        if not self.initialized and not self.gpio_available:
            print("🔌 [SIM] Setting all pins LOW")
            return
        
        try:
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.LOW)
            GPIO.output(self.pin3, GPIO.LOW)
            print("🔌 GPIO: All pins → LOW (safe state)")
        except RuntimeError as e:
            print(f"❌ GPIO Runtime Error: {e}")
            self.reinitialize_gpio()
        except Exception as e:
            print(f"❌ Error setting pins LOW: {e}")
    
    def reinitialize_gpio(self):
        """Reinitialize GPIO after error (emergency recovery)"""
        if not self.gpio_available:
            return
        
        print("🔄 Attempting GPIO reinitialization...")
        try:
            GPIO.cleanup()
            time.sleep(0.2)
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            GPIO.setup(self.pin1, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin2, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin3, GPIO.OUT, initial=GPIO.LOW)
            
            self.initialized = True
            print("✅ GPIO reinitialized successfully")
        except Exception as e:
            print(f"❌ GPIO reinitialization failed: {e}")
            self.initialized = False
            self.gpio_available = False
    
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
        """Cleanup GPIO resources safely"""
        if self.initialized and self.gpio_available:
            try:
                # Set all pins to LOW before cleanup
                GPIO.output(self.pin1, GPIO.LOW)
                GPIO.output(self.pin2, GPIO.LOW)
                GPIO.output(self.pin3, GPIO.LOW)
                time.sleep(0.1)
                
                GPIO.cleanup()
                self.initialized = False
                print("✅ GPIO cleaned up successfully")
            except Exception as e:
                print(f"⚠️ Error cleaning up GPIO: {e}")
                # Try forced cleanup
                try:
                    GPIO.cleanup()
                except:
                    pass
    
    def get_status(self):
        """Get GPIO status information"""
        status = {
            "available": self.gpio_available,
            "initialized": self.initialized,
            "is_raspberry_pi": IS_RASPBERRY_PI,
            "pins": {
                "pin1": self.pin1,
                "pin2": self.pin2,
                "pin3": self.pin3
            }
        }
        return status
    
    def test_gpio(self):
        """Test GPIO functionality (blink all pins)"""
        if not self.initialized:
            print("❌ Cannot test GPIO - not initialized")
            return False
        
        print("🧪 Testing GPIO pins...")
        try:
            for i in range(3):
                # Set all HIGH
                GPIO.output(self.pin1, GPIO.HIGH)
                GPIO.output(self.pin2, GPIO.HIGH)
                GPIO.output(self.pin3, GPIO.HIGH)
                print(f"   Test {i+1}/3: All pins HIGH")
                time.sleep(0.2)
                
                # Set all LOW
                GPIO.output(self.pin1, GPIO.LOW)
                GPIO.output(self.pin2, GPIO.LOW)
                GPIO.output(self.pin3, GPIO.LOW)
                print(f"   Test {i+1}/3: All pins LOW")
                time.sleep(0.2)
            
            print("✅ GPIO test passed!")
            return True
        except Exception as e:
            print(f"❌ GPIO test failed: {e}")
            return False
    
    def __del__(self):
        """Destructor - cleanup on deletion"""
        self.cleanup()



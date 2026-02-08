#!/usr/bin/env python3
"""
Galvo Motor Tuning & Calibration
Compensates for motor dynamics to improve line straightness, especially diagonals

Galvo mirrors have inertia and response times. When drawing diagonals,
both X and Y motors must move simultaneously. If they have different
response characteristics or lag, diagonal lines appear curved or jagged.

This script helps you:
1. Test current motor behavior with calibration patterns
2. Tune lag compensation values
3. Apply corrections when drawing custom shapes
"""
import sys
import time
import os
import math
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS


# Default calibration parameters
DEFAULT_CALIBRATION = {
    "x_lag": 0,      # X-axis lag compensation (-50 to 50)
    "y_lag": 0,      # Y-axis lag compensation (-50 to 50)
    "x_scale": 1.0,  # X-axis geometric scaling (0.8 to 1.2)
    "y_scale": 1.0,  # Y-axis geometric scaling (0.8 to 1.2)
    "x_offset": 0,   # X-axis center offset (-20 to 20)
    "y_offset": 0,   # Y-axis center offset (-20 to 20)
}

CALIBRATION_FILE = "laser_calibration.json"


def load_calibration():
    """Load calibration from file or return defaults"""
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                cal = json.load(f)
                print(f"✓ Loaded calibration from {CALIBRATION_FILE}")
                return cal
        except Exception as e:
            print(f"⚠️  Error loading calibration: {e}")
            print("   Using defaults")
    return DEFAULT_CALIBRATION.copy()


def save_calibration(cal):
    """Save calibration to file"""
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(cal, f, indent=2)
        print(f"✓ Calibration saved to {CALIBRATION_FILE}")
    except Exception as e:
        print(f"❌ Error saving calibration: {e}")


def apply_calibration(x, y, cal):
    """
    Apply calibration corrections to raw X/Y positions.
    
    The lag compensation shifts positions slightly to account for
    motor response delays. The scale adjusts for geometric distortion.
    
    Args:
        x, y: Raw position values (11-255 for positioning, 1-10 for center)
        cal: Calibration dictionary
    
    Returns:
        (x_corrected, y_corrected) tuple
    """
    # Handle center positions (1-10) - no lag compensation needed
    if x <= 10 and y <= 10:
        return (x, y)
    
    # Convert to centered coordinate system (-122 to 122, where 128 is center)
    center = 128
    x_centered = x - center
    y_centered = y - center
    
    # Apply scaling (geometric distortion correction)
    x_scaled = x_centered * cal["x_scale"]
    y_scaled = y_centered * cal["y_scale"]
    
    # Apply offsets
    x_scaled += cal["x_offset"]
    y_scaled += cal["y_offset"]
    
    # Apply lag compensation based on movement direction
    # For diagonals, we compensate the lagging axis
    x_compensated = x_scaled + cal["x_lag"]
    y_compensated = y_scaled + cal["y_lag"]
    
    # Convert back to DMX range and clamp
    x_final = int(center + x_compensated)
    y_final = int(center + y_compensated)
    
    x_final = max(11, min(255, x_final))
    y_final = max(11, min(255, y_final))
    
    return (x_final, y_final)


def draw_calibration_pattern(laser, pattern_type, cal, duration=3.0):
    """
    Draw test patterns for visual calibration.
    
    Patterns:
    - horizontal: Left-to-right scan
    - vertical: Bottom-to-top scan
    - diagonal1: Bottom-left to top-right
    - diagonal2: Top-left to bottom-right
    - box: Square outline
    - cross: X and Y axes
    - circle: Circle (multiple points)
    """
    steps = 30
    delay = duration / steps
    
    if pattern_type == "horizontal":
        print("Drawing horizontal line (left → right)")
        y_pos = 128  # Center
        for i in range(steps + 1):
            progress = i / steps
            x_pos = int(11 + (255 - 11) * progress)
            x_cal, y_cal = apply_calibration(x_pos, y_pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    elif pattern_type == "vertical":
        print("Drawing vertical line (bottom → top)")
        x_pos = 128  # Center
        for i in range(steps + 1):
            progress = i / steps
            y_pos = int(11 + (255 - 11) * progress)
            x_cal, y_cal = apply_calibration(x_pos, y_pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    elif pattern_type == "diagonal1":
        print("Drawing diagonal (↗ bottom-left → top-right)")
        for i in range(steps + 1):
            progress = i / steps
            pos = int(11 + (255 - 11) * progress)
            x_cal, y_cal = apply_calibration(pos, pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    elif pattern_type == "diagonal2":
        print("Drawing diagonal (↘ top-left → bottom-right)")
        for i in range(steps + 1):
            progress = i / steps
            x_pos = int(11 + (255 - 11) * progress)
            y_pos = int(255 - (255 - 11) * progress)
            x_cal, y_cal = apply_calibration(x_pos, y_pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    elif pattern_type == "box":
        print("Drawing box")
        corners = [(50, 50), (200, 50), (200, 200), (50, 200), (50, 50)]
        for i in range(len(corners)):
            x, y = corners[i]
            x_cal, y_cal = apply_calibration(x, y, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(duration / len(corners))
    
    elif pattern_type == "cross":
        print("Drawing cross (+ axes)")
        # Horizontal line
        for i in range(steps // 2 + 1):
            progress = i / (steps // 2)
            x_pos = int(50 + 150 * progress)
            x_cal, y_cal = apply_calibration(x_pos, 128, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
        time.sleep(0.2)
        # Vertical line
        for i in range(steps // 2 + 1):
            progress = i / (steps // 2)
            y_pos = int(50 + 150 * progress)
            x_cal, y_cal = apply_calibration(128, y_pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    elif pattern_type == "circle":
        print("Drawing circle")
        center_x, center_y = 128, 128
        radius = 80
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            x_pos = int(center_x + radius * math.cos(angle))
            y_pos = int(center_y + radius * math.sin(angle))
            x_cal, y_cal = apply_calibration(x_pos, y_pos, cal)
            laser.set_position(x_cal, y_cal)
            time.sleep(delay)
    
    # Return to center
    laser.center()


def print_menu():
    print("\n" + "=" * 60)
    print("Galvo Motor Calibration Menu")
    print("=" * 60)
    print("\nTest Patterns:")
    print("  1 - Horizontal line")
    print("  2 - Vertical line")
    print("  3 - Diagonal (↗)")
    print("  4 - Diagonal (↘)")
    print("  5 - Box/Square")
    print("  6 - Cross")
    print("  7 - Circle")
    print("\nCalibration:")
    print("  x-lag [value]   - Adjust X-axis lag (-50 to 50)")
    print("  y-lag [value]   - Adjust Y-axis lag (-50 to 50)")
    print("  x-scale [value] - Adjust X-axis scale (0.8 to 1.2)")
    print("  y-scale [value] - Adjust Y-axis scale (0.8 to 1.2)")
    print("  x-offset [value] - Adjust X-axis offset (-20 to 20)")
    print("  y-offset [value] - Adjust Y-axis offset (-20 to 20)")
    print("  status          - Show current calibration")
    print("  reset           - Reset to defaults")
    print("  save            - Save calibration")
    print("  q               - Quit")
    print()


def main():
    print("=" * 60)
    print("LaserPi - Galvo Motor Calibration Tool")
    print("=" * 60)
    print()
    print("This tool helps compensate for galvo motor dynamics.")
    print()
    print("Diagonal lines often appear curved because X and Y motors")
    print("have different response times. Use this tool to:")
    print("  1. Draw test patterns to see the current behavior")
    print("  2. Adjust lag compensation values")
    print("  3. Save calibration for use in custom scripts")
    print()
    print("⚠️  Note: Built-in MK2 patterns can't use calibration,")
    print("   but custom scripts drawing with set_position() can.")
    print()
    
    # Load calibration
    cal = load_calibration()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Use laser 1 for calibration
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    
    try:
        # Start DMX
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure laser - use a static pattern that shows position clearly
        print("Setting up laser with horizontal line pattern...")
        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(60)  # Horizontal line (~40% length) - shows position clearly
        laser.center()
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_zoom(128)
        laser.set_scanning_speed(200)  # Fast for smooth movement
        time.sleep(0.5)
        
        print("✓ Laser ready!")
        print_menu()
        
        # Interactive calibration loop
        while True:
            try:
                user_input = input("> ").strip().lower()
                
                if user_input == 'q':
                    break
                
                elif user_input == '1':
                    draw_calibration_pattern(laser, "horizontal", cal)
                elif user_input == '2':
                    draw_calibration_pattern(laser, "vertical", cal)
                elif user_input == '3':
                    draw_calibration_pattern(laser, "diagonal1", cal)
                elif user_input == '4':
                    draw_calibration_pattern(laser, "diagonal2", cal)
                elif user_input == '5':
                    draw_calibration_pattern(laser, "box", cal)
                elif user_input == '6':
                    draw_calibration_pattern(laser, "cross", cal)
                elif user_input == '7':
                    draw_calibration_pattern(laser, "circle", cal)
                
                elif user_input.startswith('x-lag '):
                    val = float(user_input.split()[1])
                    if -50 <= val <= 50:
                        cal["x_lag"] = val
                        print(f"✓ X-axis lag set to {val}")
                    else:
                        print("❌ Value must be between -50 and 50")
                
                elif user_input.startswith('y-lag '):
                    val = float(user_input.split()[1])
                    if -50 <= val <= 50:
                        cal["y_lag"] = val
                        print(f"✓ Y-axis lag set to {val}")
                    else:
                        print("❌ Value must be between -50 and 50")
                
                elif user_input.startswith('x-scale '):
                    val = float(user_input.split()[1])
                    if 0.8 <= val <= 1.2:
                        cal["x_scale"] = val
                        print(f"✓ X-axis scale set to {val}")
                    else:
                        print("❌ Value must be between 0.8 and 1.2")
                
                elif user_input.startswith('y-scale '):
                    val = float(user_input.split()[1])
                    if 0.8 <= val <= 1.2:
                        cal["y_scale"] = val
                        print(f"✓ Y-axis scale set to {val}")
                    else:
                        print("❌ Value must be between 0.8 and 1.2")
                
                elif user_input.startswith('x-offset '):
                    val = float(user_input.split()[1])
                    if -20 <= val <= 20:
                        cal["x_offset"] = val
                        print(f"✓ X-axis offset set to {val}")
                    else:
                        print("❌ Value must be between -20 and 20")
                
                elif user_input.startswith('y-offset '):
                    val = float(user_input.split()[1])
                    if -20 <= val <= 20:
                        cal["y_offset"] = val
                        print(f"✓ Y-axis offset set to {val}")
                    else:
                        print("❌ Value must be between -20 and 20")
                
                elif user_input == 'status':
                    print("\nCurrent calibration:")
                    for key, value in cal.items():
                        print(f"  {key}: {value}")
                    print()
                
                elif user_input == 'reset':
                    cal = DEFAULT_CALIBRATION.copy()
                    print("✓ Calibration reset to defaults")
                
                elif user_input == 'save':
                    save_calibration(cal)
                
                elif user_input:
                    print("❌ Unknown command. Type 'q' to quit.")
            
            except (ValueError, IndexError):
                print("❌ Invalid input format")
            except KeyboardInterrupt:
                print("\n")
                continue
        
        # Turn off laser
        print("\nTurning laser off...")
        laser.off()
        time.sleep(0.5)
        
        # Prompt to save if changes were made
        if cal != load_calibration():
            save_input = input("Save calibration before exiting? (y/N): ").strip().lower()
            if save_input == 'y':
                save_calibration(cal)
        
        print("✓ Done!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.stop()
        print("\nDMX driver stopped")


if __name__ == "__main__":
    main()

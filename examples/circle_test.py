#!/usr/bin/env python3
"""
Circle Test
Control a circular pattern on both MK2 lasers with interactive adjustments
"""
import sys
import time
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS


def print_controls():
    print("\nControls:")
    print("  p [0-255]   - Set pattern number")
    print("  c [0-255]   - Set color")
    print("  z [0-255]   - Set zoom/size")
    print("  s [0-255]   - Set scanning speed")
    print("  d [0-255]   - Set dynamic speed")
    print("  x [1-255]   - Set X position")
    print("  y [1-255]   - Set Y position")
    print("  center      - Center both lasers")
    print("  status      - Show current settings")
    print("  q           - Quit")
    print()


def main():
    print("=" * 60)
    print("LaserPi - Circle Pattern Control")
    print("=" * 60)
    print()
    print("This script lets you control circle patterns interactively.")
    print()
    print("First, use pattern_scan.py to find a good circle pattern,")
    print("then come back here and set it with 'p [number]'")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Create laser controllers
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")
    
    # Default settings
    settings = {
        "pattern": 0,
        "color": 255,
        "zoom": 128,
        "scanning_speed": 128,
        "dynamic_speed": 128,
        "x": 5,
        "y": 5
    }
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure both lasers in static pattern mode
        print("Initializing lasers...")
        for laser in [laser1, laser2]:
            laser.set_mode(MK2Mode.STATIC_PATTERN)
            laser.set_pattern(settings["pattern"])
            laser.set_position(settings["x"], settings["y"])
            laser.set_color(settings["color"])
            laser.set_color_segment(0)
            laser.set_zoom(settings["zoom"])
            laser.set_scanning_speed(settings["scanning_speed"])
            laser.set_dynamic_speed(settings["dynamic_speed"])
        
        print("✓ Lasers ready!")
        print_controls()
        
        # Interactive control loop
        while True:
            try:
                user_input = input("> ").strip().lower()
                
                if user_input == 'q':
                    break
                elif user_input == 'center':
                    settings["x"] = 5
                    settings["y"] = 5
                    laser1.center()
                    laser2.center()
                    print("✓ Centered both lasers")
                elif user_input == 'status':
                    print("\nCurrent settings:")
                    for key, value in settings.items():
                        print(f"  {key}: {value}")
                    print()
                    print(f"Laser 1: {laser1.get_all_values()}")
                    print(f"Laser 2: {laser2.get_all_values()}")
                    print()
                elif user_input.startswith('p '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["pattern"] = val
                        laser1.set_pattern(val)
                        laser2.set_pattern(val)
                        print(f"✓ Pattern set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                elif user_input.startswith('c '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["color"] = val
                        laser1.set_color(val)
                        laser2.set_color(val)
                        print(f"✓ Color set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                elif user_input.startswith('z '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["zoom"] = val
                        laser1.set_zoom(val)
                        laser2.set_zoom(val)
                        print(f"✓ Zoom set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                elif user_input.startswith('s '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["scanning_speed"] = val
                        laser1.set_scanning_speed(val)
                        laser2.set_scanning_speed(val)
                        print(f"✓ Scanning speed set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                elif user_input.startswith('d '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["dynamic_speed"] = val
                        laser1.set_dynamic_speed(val)
                        laser2.set_dynamic_speed(val)
                        print(f"✓ Dynamic speed set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                elif user_input.startswith('x '):
                    val = int(user_input.split()[1])
                    if 1 <= val <= 255:
                        settings["x"] = val
                        laser1.set_x_position(val)
                        laser2.set_x_position(val)
                        print(f"✓ X position set to {val}")
                    else:
                        print("❌ Value must be 1-255")
                elif user_input.startswith('y '):
                    val = int(user_input.split()[1])
                    if 1 <= val <= 255:
                        settings["y"] = val
                        laser1.set_y_position(val)
                        laser2.set_y_position(val)
                        print(f"✓ Y position set to {val}")
                    else:
                        print("❌ Value must be 1-255")
                elif user_input:
                    print("❌ Unknown command. Type 'q' to quit.")
            
            except (ValueError, IndexError):
                print("❌ Invalid input format")
            except KeyboardInterrupt:
                print()
                break
        
        # Turn off lasers
        print("\nTurning lasers off...")
        laser1.off()
        laser2.off()
        time.sleep(0.5)
        
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

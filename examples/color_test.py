#!/usr/bin/env python3
"""
Color and Color Segment Tester
Experiment with Channel 8 (Color) and Channel 9 (Color Segment) to understand their effects
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
    print("  c [0-255]   - Set color (Channel 8)")
    print("  s [0-255]   - Set color segment (Channel 9)")
    print("  scan-c      - Auto-scan through all colors (0-255)")
    print("  scan-s      - Auto-scan through all color segments (0-255)")
    print("  scan-both   - Scan both simultaneously")
    print("  p [0-255]   - Set pattern number")
    print("  status      - Show current settings")
    print("  q           - Quit")
    print()


def main():
    print("=" * 60)
    print("LaserPi - Color & Color Segment Tester")
    print("=" * 60)
    print()
    print("This script helps you understand what Channel 8 (Color)")
    print("and Channel 9 (Color Segment) do.")
    print()
    print("Typical behaviors:")
    print("  • Color (Ch8): Selects color from palette or color wheel")
    print("                 (Red→Green→Blue→White cycle)")
    print("  • Color Segment (Ch9): May control which parts of the")
    print("                         pattern show color vs blank")
    print()
    print("Experiment to discover the exact behavior!")
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
        "color": 128,
        "color_segment": 0,
        "zoom": 128,
        "scanning_speed": 128
    }
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure both lasers
        print("Initializing lasers...")
        for laser in [laser1, laser2]:
            laser.set_mode(MK2Mode.STATIC_PATTERN)
            laser.set_pattern(settings["pattern"])
            laser.center()
            laser.set_color(settings["color"])
            laser.set_color_segment(settings["color_segment"])
            laser.set_zoom(settings["zoom"])
            laser.set_scanning_speed(settings["scanning_speed"])
        
        print("✓ Lasers ready!")
        print()
        print(f"Starting with Color={settings['color']}, Color Segment={settings['color_segment']}")
        print_controls()
        
        # Interactive control loop
        while True:
            try:
                user_input = input("> ").strip().lower()
                
                if user_input == 'q':
                    break
                    
                elif user_input == 'status':
                    print("\nCurrent settings:")
                    for key, value in settings.items():
                        print(f"  {key}: {value}")
                    print()
                    
                elif user_input == 'scan-c':
                    print("\nScanning Color (Channel 8) from 0 to 255...")
                    print("Watch how the colors change. Press Ctrl+C to stop.")
                    print()
                    try:
                        for color in range(256):
                            laser1.set_color(color)
                            laser2.set_color(color)
                            print(f"\rColor: {color:3d}/255", end='', flush=True)
                            time.sleep(0.1)  # 100ms per step = ~25 seconds total
                        print("\n✓ Scan complete!")
                        settings["color"] = 255
                    except KeyboardInterrupt:
                        print("\n✓ Scan stopped")
                        
                elif user_input == 'scan-s':
                    print("\nScanning Color Segment (Channel 9) from 0 to 255...")
                    print("Watch how the pattern changes. Press Ctrl+C to stop.")
                    print()
                    try:
                        for segment in range(256):
                            laser1.set_color_segment(segment)
                            laser2.set_color_segment(segment)
                            print(f"\rColor Segment: {segment:3d}/255", end='', flush=True)
                            time.sleep(0.1)
                        print("\n✓ Scan complete!")
                        settings["color_segment"] = 255
                    except KeyboardInterrupt:
                        print("\n✓ Scan stopped")
                        
                elif user_input == 'scan-both':
                    print("\nScanning both Color and Color Segment simultaneously...")
                    print("Press Ctrl+C to stop.")
                    print()
                    try:
                        for value in range(256):
                            laser1.set_color(value)
                            laser2.set_color(value)
                            laser1.set_color_segment(value)
                            laser2.set_color_segment(value)
                            print(f"\rColor: {value:3d}/255 | Color Segment: {value:3d}/255", end='', flush=True)
                            time.sleep(0.1)
                        print("\n✓ Scan complete!")
                        settings["color"] = 255
                        settings["color_segment"] = 255
                    except KeyboardInterrupt:
                        print("\n✓ Scan stopped")
                        
                elif user_input.startswith('c '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["color"] = val
                        laser1.set_color(val)
                        laser2.set_color(val)
                        print(f"✓ Color set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                        
                elif user_input.startswith('s '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["color_segment"] = val
                        laser1.set_color_segment(val)
                        laser2.set_color_segment(val)
                        print(f"✓ Color segment set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                        
                elif user_input.startswith('p '):
                    val = int(user_input.split()[1])
                    if 0 <= val <= 255:
                        settings["pattern"] = val
                        laser1.set_pattern(val)
                        laser2.set_pattern(val)
                        print(f"✓ Pattern set to {val}")
                    else:
                        print("❌ Value must be 0-255")
                        
                elif user_input:
                    print("❌ Unknown command. Type 'q' to quit.")
                    
            except (ValueError, IndexError):
                print("❌ Invalid input format")
            except KeyboardInterrupt:
                print("\n")
                continue
        
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

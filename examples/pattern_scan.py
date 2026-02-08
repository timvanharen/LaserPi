#!/usr/bin/env python3
"""
Pattern Scanner
Interactively cycle through all MK2 pattern values to discover patterns
"""
import sys
import time
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS


def main():
    print("=" * 60)
    print("LaserPi - Pattern Scanner")
    print("=" * 60)
    print()
    print("This script helps you discover MK2 patterns by cycling")
    print("through all 256 pattern values on Channel 2.")
    print()
    print("Both lasers will be set to STATIC_PATTERN mode.")
    print()
    print("Controls:")
    print("  [Enter]     - Next pattern")
    print("  [Number]    - Jump to specific pattern")
    print("  [q]         - Quit")
    print()
    print("Note down pattern numbers that create circles or")
    print("other shapes you want to use!")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Create laser controllers
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")
    
    current_pattern = 0
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure both lasers in static pattern mode
        for laser in [laser1, laser2]:
            laser.set_mode(MK2Mode.STATIC_PATTERN)
            laser.center()
            laser.set_color(255)  # White
            laser.set_color_segment(0)
            laser.set_zoom(128)
            laser.set_scanning_speed(128)
        
        print("✓ Lasers ready! Starting pattern scan...")
        print()
        
        # Pattern scan loop
        while True:
            # Set current pattern on both lasers
            laser1.set_pattern(current_pattern)
            laser2.set_pattern(current_pattern)
            
            print(f"\r{'=' * 60}", end='')
            print(f"\rPattern {current_pattern:3d}/255 | ", end='')
            print(f"Next: [Enter] | Jump: [0-255] | Quit: [q] ", end='', flush=True)
            
            # Wait for user input
            user_input = input("\n> ").strip().lower()
            
            if user_input == 'q':
                print("\nQuitting...")
                break
            elif user_input == '':
                # Next pattern
                current_pattern = (current_pattern + 1) % 256
            elif user_input.isdigit():
                # Jump to specific pattern
                new_pattern = int(user_input)
                if 0 <= new_pattern <= 255:
                    current_pattern = new_pattern
                    print(f"Jumped to pattern {current_pattern}")
                else:
                    print("Invalid pattern number (must be 0-255)")
            else:
                print("Invalid input. Use [Enter], [0-255], or [q]")
        
        # Turn off lasers
        print("\nTurning lasers off...")
        laser1.off()
        laser2.off()
        time.sleep(0.5)
        
        print("✓ Done!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        laser1.off()
        laser2.off()
        time.sleep(0.5)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.stop()
        print("\nDMX driver stopped")


if __name__ == "__main__":
    main()

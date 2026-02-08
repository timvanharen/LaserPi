#!/usr/bin/env python3
"""
Basic MK2 Control Example
Turn on both lasers in static pattern mode with a test pattern
"""
import sys
import time
import os

# Add src directory to path so we can import laserpi
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS


def main():
    print("=" * 60)
    print("LaserPi - Basic Control Example")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Initialize DMX communication")
    print("  2. Turn on both MK2 lasers in static pattern mode")
    print("  3. Set pattern 0, centered, white color")
    print("  4. Run for 10 seconds")
    print()
    print("Press Ctrl+C to stop early")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Create laser controllers
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)  # Let driver stabilize
        
        print("Configuring Laser 1...")
        laser1.set_mode(MK2Mode.STATIC_PATTERN)
        laser1.set_pattern(0)  # Pattern 0 (you'll discover better patterns later)
        laser1.center()  # Center position
        laser1.set_color(255)  # White/full color
        laser1.set_color_segment(0)
        laser1.set_zoom(128)  # Medium zoom
        laser1.set_scanning_speed(128)  # Medium speed
        
        print("Configuring Laser 2...")
        laser2.set_mode(MK2Mode.STATIC_PATTERN)
        laser2.set_pattern(0)
        laser2.center()
        laser2.set_color(255)
        laser2.set_color_segment(0)
        laser2.set_zoom(128)
        laser2.set_scanning_speed(128)
        
        print()
        print("✓ Both lasers configured!")
        print()
        print(f"Laser 1 (address {LASER1_ADDRESS}): {laser1.get_all_values()}")
        print(f"Laser 2 (address {LASER2_ADDRESS}): {laser2.get_all_values()}")
        print()
        print("Lasers should now be active. Running for 10 seconds...")
        print()
        
        # Run for 10 seconds
        time.sleep(10)
        
        print("Turning lasers off...")
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

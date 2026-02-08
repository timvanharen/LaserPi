#!/usr/bin/env python3
"""
Complete Show Example
Synchronized control of lasers and hazer for a coordinated light show
"""
import sys
import time
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode, Hazer
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS, HAZER_ADDRESS


def main():
    print("=" * 60)
    print("LaserPi - Complete Show Example")
    print("=" * 60)
    print()
    print("This demo coordinates lasers and hazer for a simple show")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Create controllers
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")
    hazer = Hazer(universe, HAZER_ADDRESS, name="Main Hazer")
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)
        
        print("✓ All devices ready!")
        print()
        print("Starting show in 3 seconds...")
        time.sleep(3)
        print()
        
        # Scene 1: Hazer warm-up with static patterns
        print("Scene 1: Warming up hazer...")
        hazer.fade(30, duration=5.0)
        
        laser1.set_mode(MK2Mode.STATIC_PATTERN)
        laser1.set_pattern(20)  # Two circles horizontal
        laser1.center()
        laser1.set_color(255)
        laser1.set_zoom(128)
        laser1.set_scanning_speed(128)
        
        laser2.set_mode(MK2Mode.STATIC_PATTERN)
        laser2.set_pattern(150)  # Square
        laser2.center()
        laser2.set_color(128)  # Blue-ish
        laser2.set_zoom(128)
        laser2.set_scanning_speed(128)
        
        time.sleep(5)
        
        # Scene 2: Increase haze, switch to dynamic patterns
        print("Scene 2: Dynamic patterns with medium haze...")
        hazer.fade(50, duration=3.0)
        
        laser1.set_mode(MK2Mode.DYNAMIC_PATTERN)
        laser1.set_pattern(15)  # Small circles in orbit
        laser1.set_dynamic_speed(100)
        
        laser2.set_mode(MK2Mode.DYNAMIC_PATTERN)
        laser2.set_pattern(225)  # Rotating 5-point star
        laser2.set_dynamic_speed(80)
        laser2.set_scanning_speed(100)
        
        time.sleep(10)
        
        # Scene 3: Full haze with rotating stars
        print("Scene 3: Full intensity...")
        hazer.fade(70, duration=2.0)
        
        laser1.set_pattern(225)  # Both lasers with stars
        laser1.set_color(192)  # White-ish
        
        laser2.set_pattern(220)  # 4-point star
        laser2.set_color(64)  # Green-ish
        
        time.sleep(10)
        
        # Scene 4: Finale with circles
        print("Scene 4: Finale...")
        laser1.set_pattern(0)  # Expanding circle
        laser1.set_dynamic_speed(120)
        
        laser2.set_pattern(65)  # Two circles colliding
        laser2.set_dynamic_speed(120)
        
        time.sleep(8)
        
        # Fade out
        print("Fading out...")
        hazer.fade(20, duration=4.0)
        time.sleep(2)
        
        laser1.off()
        laser2.off()
        time.sleep(2)
        
        hazer.fade(0, duration=3.0)
        time.sleep(3)
        
        print()
        print("✓ Show complete!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        laser1.off()
        laser2.off()
        hazer.off()
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

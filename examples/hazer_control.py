#!/usr/bin/env python3
"""
Hazer Control Example
Demonstrates controlling a smoke/haze generator via DMX
"""
import sys
import time
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import Hazer
from laserpi.config import HAZER_ADDRESS


def print_controls():
    print("\nControls:")
    print("  [0-100]     - Set output percentage (e.g., '50' for 50%)")
    print("  on          - Turn on at 100%")
    print("  off         - Turn off")
    print("  fade [0-100] - Fade to target percentage over 3 seconds")
    print("  status      - Show current output level")
    print("  demo        - Run demo sequence")
    print("  q           - Quit")
    print()


def demo_sequence(hazer):
    """Run a demonstration sequence"""
    print("\n=== Running Demo Sequence ===\n")
    
    print("1. Starting at 0%...")
    hazer.off()
    time.sleep(2)
    
    print("2. Fading to 30% over 3 seconds...")
    hazer.fade(30, duration=3.0)
    time.sleep(2)
    
    print("3. Increasing to 60%...")
    hazer.set_output(60)
    time.sleep(3)
    
    print("4. Full output (100%)...")
    hazer.set_output(100)
    time.sleep(3)
    
    print("5. Fading to 50% over 2 seconds...")
    hazer.fade(50, duration=2.0)
    time.sleep(2)
    
    print("6. Fading out to 0% over 4 seconds...")
    hazer.fade(0, duration=4.0)
    time.sleep(1)
    
    print("\n=== Demo Complete ===\n")


def main():
    print("=" * 60)
    print("LaserPi - Hazer/Smoke Generator Control")
    print("=" * 60)
    print()
    print(f"Controlling hazer at DMX address {HAZER_ADDRESS}")
    print("Channel 1: Smoke output (0-100%)")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Create hazer controller
    hazer = Hazer(universe, HAZER_ADDRESS, name="Main Hazer")
    
    try:
        # Start DMX transmission
        driver.start(universe)
        time.sleep(0.5)
        
        print("✓ DMX communication started")
        print(f"✓ Hazer controller ready: {hazer}")
        print()
        print("Starting with hazer off (0%)")
        hazer.off()
        
        print_controls()
        
        # Interactive control loop
        while True:
            try:
                user_input = input("> ").strip().lower()
                
                if user_input == 'q':
                    break
                
                elif user_input == 'on':
                    hazer.on()
                    print(f"✓ Hazer ON at 100%")
                
                elif user_input == 'off':
                    hazer.off()
                    print(f"✓ Hazer OFF")
                
                elif user_input == 'status':
                    output = hazer.get_output()
                    print(f"\nCurrent output: {output:.1f}%")
                    print(f"DMX value: {universe.get_channel(HAZER_ADDRESS)}/255\n")
                
                elif user_input == 'demo':
                    demo_sequence(hazer)
                
                elif user_input.startswith('fade '):
                    try:
                        target = float(user_input.split()[1])
                        if 0 <= target <= 100:
                            current = hazer.get_output()
                            print(f"Fading from {current:.1f}% to {target:.1f}% over 3 seconds...")
                            hazer.fade(target, duration=3.0)
                            print(f"✓ Fade complete - now at {target:.1f}%")
                        else:
                            print("❌ Value must be between 0 and 100")
                    except (ValueError, IndexError):
                        print("❌ Usage: fade [0-100]")
                
                elif user_input.replace('.', '').isdigit():
                    # Direct percentage input
                    percent = float(user_input)
                    if 0 <= percent <= 100:
                        hazer.set_output(percent)
                        print(f"✓ Output set to {percent}%")
                    else:
                        print("❌ Value must be between 0 and 100")
                
                elif user_input:
                    print("❌ Unknown command. Type 'q' to quit.")
            
            except (ValueError, IndexError) as e:
                print(f"❌ Invalid input: {e}")
            except KeyboardInterrupt:
                print("\n")
                continue
        
        # Turn off hazer
        print("\nTurning hazer off...")
        hazer.off()
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

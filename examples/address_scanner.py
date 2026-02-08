#!/usr/bin/env python3
"""
DMX Address Scanner
Scans all DMX addresses to help identify devices and their responses

This tool helps you:
1. Find what DMX address your devices are actually set to
2. Test if devices respond to DMX commands
3. Discover address conflicts
"""
import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver


def scan_address(universe, address, test_value=255, duration=0.5):
    """
    Test a single DMX address by sending a value and showing result
    
    Args:
        universe: DMXUniverse instance
        address: DMX address to test (1-512)
        test_value: Value to send (0-255)
        duration: How long to hold the value (seconds)
    """
    # Set the address
    universe.set_channel(address, test_value)
    time.sleep(duration)
    # Clear it
    universe.set_channel(address, 0)


def scan_range(universe, start_addr, end_addr, test_value=255, duration=0.3):
    """
    Scan a range of addresses
    
    Args:
        universe: DMXUniverse instance
        start_addr: First address to scan
        end_addr: Last address to scan
        test_value: Value to send to each address
        duration: How long to hold each address
    """
    print(f"\nScanning addresses {start_addr} to {end_addr}...")
    print(f"Sending value {test_value} to each address for {duration}s")
    print("Watch for device responses (lights turning on, smoke output, etc.)")
    print()
    input("Press Enter to start scan...")
    print()
    
    for addr in range(start_addr, end_addr + 1):
        print(f"\rTesting address: {addr:3d}/{end_addr}  ", end='', flush=True)
        scan_address(universe, addr, test_value, duration)
    
    print("\n\n✓ Scan complete!")


def pulse_address(universe, address, cycles=5):
    """
    Pulse a specific address on and off to verify response
    
    Args:
        universe: DMXUniverse instance
        address: Address to pulse
        cycles: Number of on/off cycles
    """
    print(f"\nPulsing address {address} ({cycles} cycles)...")
    print("Watch for device response")
    print()
    
    for i in range(cycles):
        print(f"Cycle {i+1}/{cycles}: ON", end='', flush=True)
        universe.set_channel(address, 255)
        time.sleep(0.5)
        
        print(" → OFF")
        universe.set_channel(address, 0)
        time.sleep(0.5)
    
    print("\n✓ Pulse complete!")


def ramp_address(universe, address, duration=5.0):
    """
    Ramp an address from 0 to 255 and back to help identify gradual responses
    
    Args:
        universe: DMXUniverse instance
        address: Address to ramp
        duration: Total duration for ramp up and down
    """
    print(f"\nRamping address {address} (0→255→0 over {duration}s)...")
    print("Watch for gradual device response")
    print()
    
    steps = 50
    step_delay = duration / (steps * 2)
    
    # Ramp up
    for i in range(steps + 1):
        value = int((i / steps) * 255)
        universe.set_channel(address, value)
        print(f"\rValue: {value:3d}/255", end='', flush=True)
        time.sleep(step_delay)
    
    # Ramp down
    for i in range(steps, -1, -1):
        value = int((i / steps) * 255)
        universe.set_channel(address, value)
        print(f"\rValue: {value:3d}/255", end='', flush=True)
        time.sleep(step_delay)
    
    universe.set_channel(address, 0)
    print("\n\n✓ Ramp complete!")


def print_menu():
    print("\n" + "=" * 60)
    print("DMX Address Scanner Menu")
    print("=" * 60)
    print("\nScanning Options:")
    print("  1 - Quick scan (addresses 1-30)")
    print("  2 - Full scan (addresses 1-100)")
    print("  3 - Custom range scan")
    print("  4 - Pulse specific address (on/off cycles)")
    print("  5 - Ramp specific address (0-255 gradual)")
    print("  6 - Set address to specific value")
    print("  7 - Clear all channels (set all to 0)")
    print("  q - Quit")
    print()


def main():
    print("=" * 60)
    print("LaserPi - DMX Address Scanner")
    print("=" * 60)
    print()
    print("This tool helps you discover DMX device addresses by:")
    print("  • Scanning ranges of addresses")
    print("  • Pulsing specific addresses")
    print("  • Ramping values to see gradual responses")
    print()
    print("⚠️  Note: Some devices (like hazers) need warm-up time!")
    print("   Wait 3-5 minutes after powering on before testing.")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    try:
        # Start DMX
        driver.start(universe)
        time.sleep(0.5)
        
        print("✓ DMX driver started")
        print()
        print("All channels currently at 0")
        
        while True:
            print_menu()
            user_input = input("> ").strip().lower()
            
            if user_input == 'q':
                break
            
            elif user_input == '1':
                scan_range(universe, 1, 30, test_value=255, duration=0.3)
            
            elif user_input == '2':
                scan_range(universe, 1, 100, test_value=255, duration=0.3)
            
            elif user_input == '3':
                try:
                    start = int(input("Start address (1-512): "))
                    end = int(input("End address (1-512): "))
                    if 1 <= start <= 512 and 1 <= end <= 512 and start <= end:
                        scan_range(universe, start, end, test_value=255, duration=0.3)
                    else:
                        print("❌ Invalid range")
                except ValueError:
                    print("❌ Invalid input")
            
            elif user_input == '4':
                try:
                    addr = int(input("Address to pulse (1-512): "))
                    if 1 <= addr <= 512:
                        cycles = int(input("Number of cycles (default 5): ") or "5")
                        pulse_address(universe, addr, cycles)
                    else:
                        print("❌ Invalid address")
                except ValueError:
                    print("❌ Invalid input")
            
            elif user_input == '5':
                try:
                    addr = int(input("Address to ramp (1-512): "))
                    if 1 <= addr <= 512:
                        duration = float(input("Duration in seconds (default 5): ") or "5")
                        ramp_address(universe, addr, duration)
                    else:
                        print("❌ Invalid address")
                except ValueError:
                    print("❌ Invalid input")
            
            elif user_input == '6':
                try:
                    addr = int(input("Address (1-512): "))
                    value = int(input("Value (0-255): "))
                    if 1 <= addr <= 512 and 0 <= value <= 255:
                        universe.set_channel(addr, value)
                        print(f"✓ Address {addr} set to {value}")
                        print("  (will remain at this value until changed)")
                    else:
                        print("❌ Invalid address or value")
                except ValueError:
                    print("❌ Invalid input")
            
            elif user_input == '7':
                print("Clearing all channels...")
                universe.clear()
                print("✓ All channels set to 0")
            
            elif user_input:
                print("❌ Unknown command")
        
        # Clear all on exit
        print("\nClearing all channels...")
        universe.clear()
        time.sleep(0.5)
        
        print("✓ Done!")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        universe.clear()
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

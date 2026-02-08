#!/usr/bin/env python3
"""
RS485 Communication Test
Simple script to verify USB-RS485 adapter is working
Sends "hej bro" every second
"""
import serial
import time
import sys

# Configuration
SERIAL_PORT = "/dev/ttyUSB0"  # Change to your port (or /dev/dmx0)
BAUD_RATE = 9600  # Standard baud rate for testing (not DMX rate)

def main():
    print("=" * 60)
    print("RS485 Communication Test")
    print("=" * 60)
    print()
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print()
    print("This script sends 'hej bro' every second to test RS485.")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Open serial port
        print(f"Opening {SERIAL_PORT}...")
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"✓ Serial port opened successfully")
        print(f"  Device: {ser.name}")
        print(f"  Settings: {BAUD_RATE} 8N1")
        print()
        print("Starting transmission...")
        print("-" * 60)
        
        counter = 0
        
        while True:
            counter += 1
            message = "hej bro"
            
            # Send the message
            ser.write(message.encode('utf-8'))
            ser.flush()
            
            # Display what we sent
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] Packet {counter:4d}: '{message}' ({len(message)} bytes)")
            
            # Wait 1 second
            time.sleep(1)
    
    except serial.SerialException as e:
        print(f"\n❌ Serial port error: {e}")
        print()
        print("Troubleshooting:")
        print(f"  1. Check if {SERIAL_PORT} exists: ls -l {SERIAL_PORT}")
        print("  2. Check permissions: groups (should include 'dialout')")
        print("  3. Check USB connection: dmesg | grep tty")
        print("  4. Try a different port: ls /dev/ttyUSB*")
        return 1
    
    except KeyboardInterrupt:
        print("\n")
        print("-" * 60)
        print(f"✓ Stopped after {counter} packets")
        print()
        print("If you saw no errors, your RS485 adapter is working!")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

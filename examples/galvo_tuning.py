#!/usr/bin/env python3
"""
Galvo Motor Tuning & Calibration
Compensates for motor dynamics to improve line straightness, especially diagonals

Galvo mirrors have inertia and response times. When drawing diagonals,
both X and Y motors must move simultaneously. If they have different
response characteristics or lag, diagonal lines appear curved or jagged.

This script continuously traces test patterns at high speed so you can
see the shape in real-time while adjusting calibration values.

Controls:
  1-7    Select test pattern (continuous tracing)
  x-lag / y-lag / x-scale / y-scale / x-offset / y-offset  - Adjust cal
  status - Show current calibration
  save   - Save calibration
  reset  - Reset to defaults
  q      - Quit
"""
import sys
import time
import os
import math
import json
import threading

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


# ---------- Test pattern point generators ----------

def gen_horizontal(n=20):
    """Horizontal line (left → right)"""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((int(40 + 175 * t), 128))
    return pts

def gen_vertical(n=20):
    """Vertical line (top → bottom)"""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((128, int(40 + 175 * t)))
    return pts

def gen_diagonal1(n=20):
    """Diagonal ↗ (bottom-left → top-right)"""
    pts = []
    for i in range(n + 1):
        t = i / n
        pos = int(40 + 175 * t)
        pts.append((pos, pos))
    return pts

def gen_diagonal2(n=20):
    """Diagonal ↘ (top-left → bottom-right)"""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((int(40 + 175 * t), int(215 - 175 * t)))
    return pts

def gen_box(n=10):
    """Square outline"""
    pts = []
    corners = [(50, 50), (200, 50), (200, 200), (50, 200), (50, 50)]
    for i in range(len(corners) - 1):
        x1, y1 = corners[i]
        x2, y2 = corners[i + 1]
        for j in range(n):
            t = j / n
            pts.append((int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t)))
    return pts

def gen_cross(n=10):
    """Cross (+ axes)"""
    pts = []
    # Horizontal
    for i in range(n + 1):
        t = i / n
        pts.append((int(50 + 150 * t), 128))
    # Vertical
    for i in range(n + 1):
        t = i / n
        pts.append((128, int(50 + 150 * t)))
    return pts

def gen_circle(n=40):
    """Circle"""
    pts = []
    cx, cy, r = 128, 128, 80
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        pts.append((int(cx + r * math.cos(angle)),
                     int(cy + r * math.sin(angle))))
    return pts


PATTERNS = {
    '1': ("Horizontal line", gen_horizontal),
    '2': ("Vertical line", gen_vertical),
    '3': ("Diagonal ↗", gen_diagonal1),
    '4': ("Diagonal ↘", gen_diagonal2),
    '5': ("Box / Square", gen_box),
    '6': ("Cross +", gen_cross),
    '7': ("Circle", gen_circle),
}


# ---------- Calibration functions ----------

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
    """Apply calibration corrections to raw X/Y positions."""
    if x <= 10 and y <= 10:
        return (x, y)
    
    center = 128
    x_c = (x - center) * cal["x_scale"] + cal["x_offset"] + cal["x_lag"]
    y_c = (y - center) * cal["y_scale"] + cal["y_offset"] + cal["y_lag"]
    
    return (max(11, min(255, int(center + x_c))),
            max(11, min(255, int(center + y_c))))


# ---------- Continuous drawing thread ----------

def draw_loop(laser, state):
    """Continuously trace the current pattern at high speed."""
    while state['running']:
        pattern_key = state['pattern']
        if pattern_key is None:
            time.sleep(0.05)
            continue
        
        # Generate points for current pattern
        _, gen_fn = PATTERNS[pattern_key]
        raw_points = gen_fn()
        
        # Apply calibration to all points
        cal = state['cal']
        dmx_points = [apply_calibration(x, y, cal) for x, y in raw_points]
        
        # Trace all points
        for x, y in dmx_points:
            if not state['running'] or state['pattern'] != pattern_key:
                break
            laser.set_position(x, y)
            time.sleep(state['speed'])


# ---------- Main ----------

def print_menu():
    print("\n" + "=" * 60)
    print("Galvo Motor Calibration Menu")
    print("=" * 60)
    print("\nTest Patterns (continuously traced):")
    print("  1 - Horizontal line       5 - Box / Square")
    print("  2 - Vertical line         6 - Cross +")
    print("  3 - Diagonal ↗            7 - Circle")
    print("  4 - Diagonal ↘            0 - Stop tracing")
    print("\nCalibration:")
    print("  x-lag [val]    X-axis lag (-50 to 50)")
    print("  y-lag [val]    Y-axis lag (-50 to 50)")
    print("  x-scale [val]  X-axis scale (0.8 to 1.2)")
    print("  y-scale [val]  Y-axis scale (0.8 to 1.2)")
    print("  x-offset [val] X-axis offset (-20 to 20)")
    print("  y-offset [val] Y-axis offset (-20 to 20)")
    print("\nOther:")
    print("  status  - Show current calibration")
    print("  reset   - Reset to defaults")
    print("  save    - Save calibration")
    print("  faster  - Decrease trace delay (faster)")
    print("  slower  - Increase trace delay (slower)")
    print("  q       - Quit")
    print()


def main():
    print("=" * 60)
    print("LaserPi - Galvo Motor Calibration Tool")
    print("=" * 60)
    print()
    print("Patterns are continuously traced at high speed so you can")
    print("see the full shape while adjusting calibration values.")
    print()
    print("Diagonal lines appear curved when X/Y motors have different")
    print("response times. Adjust x-lag / y-lag to compensate.")
    print()
    
    cal = load_calibration()
    cal_on_load = cal.copy()
    
    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    
    state = {
        'running': True,
        'pattern': None,
        'cal': cal,
        'speed': 0.002,  # 2ms between points
    }
    
    try:
        driver.start(universe)
        time.sleep(0.5)
        
        # Use a dot pattern at smallest zoom as the "pen"
        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(0)    # Dot
        laser.set_zoom(0)       # Smallest possible
        laser.set_color(255)    # White
        laser.set_color_segment(0)
        laser.set_scanning_speed(255)  # Max scan speed
        laser.center()
        time.sleep(0.3)
        
        print("✓ Laser ready!")
        print_menu()
        
        # Start continuous drawing thread
        draw_thread = threading.Thread(target=draw_loop, args=(laser, state), daemon=True)
        draw_thread.start()
        
        while True:
            try:
                user_input = input("> ").strip().lower()
            except EOFError:
                break
            
            if user_input == 'q':
                break
            
            elif user_input == '0':
                state['pattern'] = None
                laser.center()
                print("Stopped tracing")
            
            elif user_input in PATTERNS:
                state['pattern'] = user_input
                name = PATTERNS[user_input][0]
                print(f"Tracing: {name}  (speed: {state['speed']*1000:.1f}ms)")
            
            elif user_input.startswith('x-lag '):
                try:
                    val = float(user_input.split()[1])
                    if -50 <= val <= 50:
                        cal["x_lag"] = val
                        print(f"✓ X-axis lag = {val}")
                    else:
                        print("❌ Range: -50 to 50")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('y-lag '):
                try:
                    val = float(user_input.split()[1])
                    if -50 <= val <= 50:
                        cal["y_lag"] = val
                        print(f"✓ Y-axis lag = {val}")
                    else:
                        print("❌ Range: -50 to 50")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('x-scale '):
                try:
                    val = float(user_input.split()[1])
                    if 0.8 <= val <= 1.2:
                        cal["x_scale"] = val
                        print(f"✓ X-axis scale = {val}")
                    else:
                        print("❌ Range: 0.8 to 1.2")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('y-scale '):
                try:
                    val = float(user_input.split()[1])
                    if 0.8 <= val <= 1.2:
                        cal["y_scale"] = val
                        print(f"✓ Y-axis scale = {val}")
                    else:
                        print("❌ Range: 0.8 to 1.2")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('x-offset '):
                try:
                    val = float(user_input.split()[1])
                    if -20 <= val <= 20:
                        cal["x_offset"] = val
                        print(f"✓ X-axis offset = {val}")
                    else:
                        print("❌ Range: -20 to 20")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('y-offset '):
                try:
                    val = float(user_input.split()[1])
                    if -20 <= val <= 20:
                        cal["y_offset"] = val
                        print(f"✓ Y-axis offset = {val}")
                    else:
                        print("❌ Range: -20 to 20")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input == 'status':
                print("\nCurrent calibration:")
                for key, value in cal.items():
                    print(f"  {key}: {value}")
                print(f"  trace speed: {state['speed']*1000:.1f}ms")
                print()
            
            elif user_input == 'reset':
                cal.clear()
                cal.update(DEFAULT_CALIBRATION.copy())
                state['cal'] = cal
                print("✓ Calibration reset to defaults")
            
            elif user_input == 'save':
                save_calibration(cal)
            
            elif user_input == 'faster':
                state['speed'] = max(0.0005, state['speed'] - 0.001)
                print(f"Trace speed: {state['speed']*1000:.1f}ms")
            
            elif user_input == 'slower':
                state['speed'] = min(0.05, state['speed'] + 0.001)
                print(f"Trace speed: {state['speed']*1000:.1f}ms")
            
            elif user_input:
                print("❌ Unknown command")
        
        # Cleanup
        state['running'] = False
        time.sleep(0.05)
        
        laser.off()
        time.sleep(0.3)
        
        # Prompt to save if changed
        if cal != cal_on_load:
            save_input = input("Save calibration before exiting? (y/N): ").strip().lower()
            if save_input == 'y':
                save_calibration(cal)
        
        print("✓ Done!")
    
    except KeyboardInterrupt:
        print("\nInterrupted")
        state['running'] = False
        time.sleep(0.05)
        laser.off()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        state['running'] = False
        driver.stop()
        print("DMX driver stopped")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Custom Shape Drawing with Calibration
Example of using galvo calibration to draw custom shapes

This demonstrates how to:
1. Load saved calibration from galvo_tuning.py
2. Apply corrections when drawing custom shapes
3. Draw smooth lines and shapes with set_position()
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


def load_calibration():
    """Load calibration if it exists, otherwise return None"""
    cal_file = "laser_calibration.json"
    if os.path.exists(cal_file):
        try:
            with open(cal_file, 'r') as f:
                cal = json.load(f)
                print(f"✓ Loaded calibration from {cal_file}")
                return cal
        except Exception as e:
            print(f"⚠️  Error loading calibration: {e}")
    return None


def apply_calibration(x, y, cal):
    """Apply calibration corrections"""
    if cal is None or (x <= 10 and y <= 10):
        return (x, y)
    
    center = 128
    x_centered = (x - center) * cal["x_scale"] + cal["x_offset"] + cal["x_lag"]
    y_centered = (y - center) * cal["y_scale"] + cal["y_offset"] + cal["y_lag"]
    
    x_final = int(center + x_centered)
    y_final = int(center + y_centered)
    
    return (max(11, min(255, x_final)), max(11, min(255, y_final)))


def draw_line(laser, x1, y1, x2, y2, cal=None, steps=20, delay=0.02):
    """Draw a line from (x1,y1) to (x2,y2)"""
    for i in range(steps + 1):
        t = i / steps
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        x_cal, y_cal = apply_calibration(x, y, cal)
        laser.set_position(x_cal, y_cal)
        time.sleep(delay)


def draw_square(laser, center_x, center_y, size, cal=None):
    """Draw a square"""
    half = size // 2
    corners = [
        (center_x - half, center_y - half),  # Bottom-left
        (center_x + half, center_y - half),  # Bottom-right
        (center_x + half, center_y + half),  # Top-right
        (center_x - half, center_y + half),  # Top-left
        (center_x - half, center_y - half),  # Back to start
    ]
    
    for i in range(len(corners) - 1):
        x1, y1 = corners[i]
        x2, y2 = corners[i + 1]
        draw_line(laser, x1, y1, x2, y2, cal)


def draw_triangle(laser, center_x, center_y, size, cal=None):
    """Draw a triangle"""
    h = int(size * 0.866)  # height = size * sqrt(3)/2
    corners = [
        (center_x, center_y - h // 2),              # Top
        (center_x + size // 2, center_y + h // 2),  # Bottom-right
        (center_x - size // 2, center_y + h // 2),  # Bottom-left
        (center_x, center_y - h // 2),              # Back to start
    ]
    
    for i in range(len(corners) - 1):
        x1, y1 = corners[i]
        x2, y2 = corners[i + 1]
        draw_line(laser, x1, y1, x2, y2, cal)


def draw_star(laser, center_x, center_y, outer_radius, cal=None):
    """Draw a 5-point star"""
    inner_radius = outer_radius * 0.38  # Golden ratio approximation
    points = []
    
    for i in range(10):
        angle = (math.pi / 2) - (i * 2 * math.pi / 10)  # Start at top
        radius = outer_radius if i % 2 == 0 else inner_radius
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y - radius * math.sin(angle))
        points.append((x, y))
    
    points.append(points[0])  # Close the star
    
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        draw_line(laser, x1, y1, x2, y2, cal)


def draw_circle_manual(laser, center_x, center_y, radius, cal=None, steps=36):
    """Draw a circle by moving through points"""
    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        x_cal, y_cal = apply_calibration(x, y, cal)
        laser.set_position(x_cal, y_cal)
        time.sleep(0.02)


def main():
    print("=" * 60)
    print("LaserPi - Custom Shape Drawing with Calibration")
    print("=" * 60)
    print()
    
    # Load calibration
    cal = load_calibration()
    if cal:
        print("Using calibration to correct galvo motor lag")
    else:
        print("⚠️  No calibration found. Run galvo_tuning.py first for best results.")
        print("   Drawing without calibration...")
    print()
    
    # Create DMX universe and driver
    universe = DMXUniverse()
    driver = DMXDriver()
    
    # Use laser 1
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    
    try:
        # Start DMX
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure laser - use a simple dot pattern
        print("Configuring laser...")
        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(0)  # Single dot
        laser.center()
        laser.set_color(255)  # White
        laser.set_color_segment(0)
        laser.set_zoom(128)
        laser.set_scanning_speed(200)  # Fast for smooth drawing
        time.sleep(0.5)
        
        print("✓ Laser ready! Drawing shapes...")
        print()
        
        # Draw shapes in sequence
        center_x, center_y = 128, 128
        
        print("Drawing square...")
        draw_square(laser, center_x, center_y, size=100, cal=cal)
        time.sleep(1)
        
        print("Drawing triangle...")
        draw_triangle(laser, center_x, center_y, size=100, cal=cal)
        time.sleep(1)
        
        print("Drawing star...")
        draw_star(laser, center_x, center_y, outer_radius=60, cal=cal)
        time.sleep(1)
        
        print("Drawing circle...")
        draw_circle_manual(laser, center_x, center_y, radius=50, cal=cal)
        time.sleep(1)
        
        print("Drawing diagonal lines (test for straightness)...")
        # Diagonal 1: ↗
        draw_line(laser, 50, 50, 200, 200, cal=cal)
        time.sleep(0.5)
        
        # Diagonal 2: ↘
        draw_line(laser, 50, 200, 200, 50, cal=cal)
        time.sleep(0.5)
        
        print()
        print("✓ Drawing complete!")
        print()
        print("Compare diagonal line straightness with/without calibration.")
        print("If diagonals are still curved, adjust lag values in galvo_tuning.py")
        
        # Return to center
        laser.center()
        time.sleep(2)
        
        # Turn off
        print("\nTurning laser off...")
        laser.off()
        time.sleep(0.5)
        
        print("✓ Done!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        laser.off()
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

#!/usr/bin/env python3
"""
Fast Shape Drawing with Laser

Draws shapes by rapidly tracing vertices with minimal delay,
using the smallest possible line pattern for a tight "pen".

The key to visible shapes: continuously re-trace the path at high speed
so persistence of vision makes the full shape appear simultaneously.

Controls:
  1-5  - Select shape (square, triangle, star, diamond, arrow)
  +/-  - Zoom pattern size (smaller = tighter pen)
  w/s  - Move shape up/down
  a/d  - Move shape left/right
  r/f  - Increase/decrease shape size
  c    - Cycle colors
  p    - Cycle pen pattern (dot, h-line, v-line)
  q    - Quit
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


# Shape definitions as lists of (x, y) vertices (normalized -1 to 1)
SHAPES = {
    'square': [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)],
    'triangle': [(0, -1), (1, 0.73), (-1, 0.73), (0, -1)],
    'star': [],  # Generated below
    'diamond': [(0, -1), (1, 0), (0, 1), (-1, 0), (0, -1)],
    'arrow': [(0, -1), (0.7, 0.2), (0.25, 0), (0.25, 1), (-0.25, 1), (-0.25, 0), (-0.7, 0.2), (0, -1)],
}

# Generate 5-point star vertices
def _make_star():
    pts = []
    for i in range(11):
        angle = -math.pi / 2 + (i * 2 * math.pi / 10)
        r = 1.0 if i % 2 == 0 else 0.38
        pts.append((r * math.cos(angle), r * math.sin(angle)))
    return pts

SHAPES['star'] = _make_star()

# Pen patterns (smallest possible)
PEN_PATTERNS = [
    (0, "dot"),       # Pattern 0: single dot
    (60, "h-line"),   # Pattern 60: horizontal line
    (70, "v-line"),   # Pattern 70: vertical line
]


def load_calibration():
    """Load calibration if it exists"""
    cal_file = "laser_calibration.json"
    if os.path.exists(cal_file):
        try:
            with open(cal_file, 'r') as f:
                cal = json.load(f)
                print(f"✓ Loaded calibration from {cal_file}")
                return cal
        except Exception:
            pass
    return None


def apply_calibration(x, y, cal):
    """Apply calibration corrections"""
    if cal is None or (x <= 10 and y <= 10):
        return (x, y)
    center = 128
    x_c = (x - center) * cal["x_scale"] + cal["x_offset"] + cal["x_lag"]
    y_c = (y - center) * cal["y_scale"] + cal["y_offset"] + cal["y_lag"]
    return (max(11, min(255, int(center + x_c))),
            max(11, min(255, int(center + y_c))))


def interpolate_shape(vertices, points_per_segment=4):
    """
    Convert shape vertices into a dense point list for smooth tracing.
    Fewer points = faster retrace = more solid appearance.
    """
    points = []
    for i in range(len(vertices) - 1):
        x1, y1 = vertices[i]
        x2, y2 = vertices[i + 1]
        for j in range(points_per_segment):
            t = j / points_per_segment
            points.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    return points


def shape_to_dmx(norm_points, center_x, center_y, size, cal):
    """Convert normalized points to DMX coordinates with calibration."""
    dmx_points = []
    for nx, ny in norm_points:
        x = int(center_x + nx * size)
        y = int(center_y + ny * size)
        x = max(11, min(255, x))
        y = max(11, min(255, y))
        x, y = apply_calibration(x, y, cal)
        dmx_points.append((x, y))
    return dmx_points


def draw_loop(laser, state, cal):
    """
    Continuously trace the current shape at maximum speed.
    Runs in a background thread.
    """
    while state['running']:
        shape_name = state['shape']
        vertices = SHAPES[shape_name]
        
        # Interpolate: fewer points = faster loop = more solid shape
        points_per_seg = state['density']
        norm_points = interpolate_shape(vertices, points_per_seg)
        
        # Convert to DMX coordinates
        dmx_points = shape_to_dmx(
            norm_points,
            state['cx'], state['cy'],
            state['size'], cal
        )
        
        if not dmx_points:
            time.sleep(0.01)
            continue
        
        # Trace all points as fast as possible
        # The bottleneck is DMX refresh (40Hz = 25ms), but we update
        # the universe buffer immediately - the TX thread sends the
        # latest state at 40Hz automatically
        for x, y in dmx_points:
            if not state['running']:
                break
            laser.set_position(x, y)
            # Tiny delay - just enough for the galvo to move
            # Lower = faster trace but more flicker
            # Higher = smoother lines but visible dot movement
            time.sleep(state['speed'])


def main():
    print("=" * 60)
    print("LaserPi - Fast Shape Drawing")
    print("=" * 60)
    print()
    
    cal = load_calibration()
    if cal:
        print("✓ Using galvo calibration")
    else:
        print("⚠️  No calibration. Run galvo_tuning.py for best results.")
    print()
    
    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    
    # Drawing state
    state = {
        'running': True,
        'shape': 'square',
        'cx': 128,        # Center X
        'cy': 128,        # Center Y
        'size': 50,       # Shape half-size in DMX units
        'speed': 0.002,   # Delay between points (2ms = ~500 points/sec)
        'density': 3,     # Points per line segment
        'pen_idx': 0,     # Current pen pattern index
        'color': 255,     # Color value
        'zoom': 0,        # Pen zoom (0 = smallest)
    }
    
    shape_names = list(SHAPES.keys())
    colors = [255, 50, 100, 150, 200, 0]  # white, red, green, etc.
    color_idx = 0
    
    try:
        driver.start(universe)
        time.sleep(0.5)
        
        # Configure laser with smallest possible pen
        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(PEN_PATTERNS[0][0])
        laser.set_zoom(0)  # Smallest possible
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(255)  # Maximum scan speed
        laser.center()
        time.sleep(0.3)
        
        print("✓ Laser ready!")
        print()
        print("Controls:")
        print("  1-5    Shape: square, triangle, star, diamond, arrow")
        print("  +/-    Pen zoom (smaller/larger)")
        print("  w/s    Move up/down")
        print("  a/d    Move left/right")
        print("  r/f    Shape bigger/smaller")
        print("  [/]    Trace speed slower/faster")
        print("  ,/.    Point density less/more")
        print("  c      Cycle color")
        print("  p      Cycle pen pattern (dot/h-line/v-line)")
        print("  q      Quit")
        print()
        print(f"Shape: {state['shape']}  Pen: {PEN_PATTERNS[0][1]}  "
              f"Zoom: {state['zoom']}  Speed: {state['speed']*1000:.1f}ms")
        
        # Start drawing thread
        draw_thread = threading.Thread(target=draw_loop, args=(laser, state, cal), daemon=True)
        draw_thread.start()
        
        while True:
            try:
                cmd = input().strip().lower()
            except EOFError:
                break
            
            if cmd == 'q':
                break
            
            elif cmd in ('1', '2', '3', '4', '5'):
                idx = int(cmd) - 1
                if idx < len(shape_names):
                    state['shape'] = shape_names[idx]
            
            elif cmd == 'w':
                state['cy'] = max(30, state['cy'] - 10)
            elif cmd == 's':
                state['cy'] = min(225, state['cy'] + 10)
            elif cmd == 'a':
                state['cx'] = max(30, state['cx'] - 10)
            elif cmd == 'd':
                state['cx'] = min(225, state['cx'] + 10)
            
            elif cmd == 'r':
                state['size'] = min(100, state['size'] + 5)
            elif cmd == 'f':
                state['size'] = max(10, state['size'] - 5)
            
            elif cmd == '+' or cmd == '=':
                state['zoom'] = min(255, state['zoom'] + 10)
                laser.set_zoom(state['zoom'])
            elif cmd == '-':
                state['zoom'] = max(0, state['zoom'] - 10)
                laser.set_zoom(state['zoom'])
            
            elif cmd == '[':
                state['speed'] = min(0.05, state['speed'] + 0.001)
            elif cmd == ']':
                state['speed'] = max(0.0005, state['speed'] - 0.001)
            
            elif cmd == ',':
                state['density'] = max(1, state['density'] - 1)
            elif cmd == '.':
                state['density'] = min(20, state['density'] + 1)
            
            elif cmd == 'c':
                color_idx = (color_idx + 1) % len(colors)
                state['color'] = colors[color_idx]
                laser.set_color(state['color'])
            
            elif cmd == 'p':
                state['pen_idx'] = (state['pen_idx'] + 1) % len(PEN_PATTERNS)
                pat, name = PEN_PATTERNS[state['pen_idx']]
                laser.set_pattern(pat)
            else:
                continue
            
            pat_name = PEN_PATTERNS[state['pen_idx']][1]
            total_pts = state['density'] * (len(SHAPES[state['shape']]) - 1)
            trace_ms = total_pts * state['speed'] * 1000
            fps = 1000 / trace_ms if trace_ms > 0 else 999
            print(f"Shape: {state['shape']:8s}  Pen: {pat_name:6s}  "
                  f"Zoom: {state['zoom']:3d}  Speed: {state['speed']*1000:.1f}ms  "
                  f"Density: {state['density']}  ~{fps:.0f} traces/sec  "
                  f"Size: {state['size']}  Pos: ({state['cx']},{state['cy']})")
        
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()
        print("Done")


if __name__ == "__main__":
    main()

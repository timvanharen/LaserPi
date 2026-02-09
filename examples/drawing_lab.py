#!/usr/bin/env python3
"""
Drawing Lab - Experimental approaches for precise laser drawing

Tests multiple techniques to push the MK2 beyond its intended DMX capabilities:

  Mode 1: PEN FINDER
    Compare all potentially-small patterns at various zoom levels to find
    the absolute smallest dot. Cycles through candidates automatically.

  Mode 2: LINE COMPOSER
    Use horizontal/vertical LINE patterns (60, 70) as wide brushes.
    The MK2's internal scanner draws the line at kHz speed (persistent).
    We just reposition the line via DMX at 40Hz to compose shapes.
    Example: 4 horizontal lines + 2 vertical lines = rectangle.

  Mode 3: FAST DMX COMPOSER
    Same as Mode 2, but bypasses the 40Hz DMX limiter.
    With only 22 channels, each DMX frame takes ~1.2ms, so we can
    potentially send 200-800 frames/sec. More segments = more shape.

  Mode 4: PATTERN STROBE
    Start a full pattern, then rapidly toggle color 0/255 to see if
    we can "slice" or interrupt the internal scan to create partials.

  Mode 5: DUAL LASER
    Both lasers simultaneously - one draws horizontal segments, the
    other draws vertical. No time-sharing needed = solid lines.

Run:  python drawing_lab.py [mode]
"""
import sys
import time
import os
import math
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import (
    LASER1_ADDRESS, LASER2_ADDRESS, SERIAL_PORT,
    DMX_BAUD, DMX_CHANNEL_COUNT, DMX_BREAK_TIME_US, DMX_MAB_TIME_US
)


# ──────────────────────────────────────────────────────
#  MODE 1: PEN FINDER
# ──────────────────────────────────────────────────────

# Patterns that might be small at zoom=0
PEN_CANDIDATES = [
    (0,   "Octagon (default dot)"),
    (5,   "Wiggly octagon"),
    (10,  "Dashed octagon"),
    (20,  "Two circles"),
    (45,  "H-line expanding"),
    (50,  "H-line shrinking"),
    (60,  "H-line static"),
    (70,  "V-line static"),
    (80,  "Diagonal line"),
    (120, "Triangle ▽"),
    (130, "Triangle △"),
    (140, "Cross +"),
    (150, "Square"),
    (200, "Pentagon"),
]


def mode_pen_finder():
    """Cycle through patterns at low zoom to find the smallest dot."""
    print("\n" + "=" * 60)
    print("MODE 1: PEN FINDER")
    print("=" * 60)
    print("Cycles through small patterns at zoom 0, 10, 30, 50")
    print("Watch the laser and note which pattern gives the smallest dot.")
    print("Press Enter to advance, 'q' to quit.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    try:
        driver.start(universe)
        time.sleep(0.5)

        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.center()
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(255)
        time.sleep(0.3)

        zooms = [0, 10, 30, 50, 128]

        for zoom in zooms:
            print(f"\n── Zoom = {zoom} ──")
            laser.set_zoom(zoom)
            time.sleep(0.2)

            for pat_num, pat_name in PEN_CANDIDATES:
                laser.set_pattern(pat_num)
                time.sleep(0.1)
                result = input(f"  Pattern {pat_num:3d}: {pat_name:25s}  [Enter=next, s=star, q=quit] ")
                if result.lower() == 'q':
                    return
                if result.lower() == 's':
                    print(f"    ★ Starred: pattern {pat_num} at zoom {zoom}")

        print("\nDone! Note your starred patterns for use in other modes.")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 2: LINE COMPOSER
# ──────────────────────────────────────────────────────

# Define shapes as lists of line segments: (pattern, x, y, zoom)
# Pattern 60 = horizontal line, 70 = vertical line, 80 = diagonal
# Each segment is positioned at specific X/Y and displayed for 1 DMX frame

# Simple rectangle from 4 line segments
RECT_SEGMENTS = [
    # Horizontal lines (pattern 60)
    (60, 128, 70,  40),   # Top edge
    (60, 128, 190, 40),   # Bottom edge
    # Vertical lines (pattern 70)
    (70, 70,  128, 40),   # Left edge
    (70, 190, 128, 40),   # Right edge
]

# Letter "Q" approximation
Q_SEGMENTS = [
    (60, 128,  55, 40),   # Top
    (60, 128, 200, 40),   # Bottom
    (70,  60, 128, 40),   # Left
    (70, 195, 128, 40),   # Right
    (80, 175, 195, 25),   # Diagonal tail
]

# Letter "W" approximation (4 vertical-ish strokes)
W_SEGMENTS = [
    (70,  50, 128, 50),   # Left stroke
    (80,  90, 170, 35),   # Down-right
    (80, 130, 100, 35),   # Up-right  (would need "other diagonal" - doesn't exist cleanly)
    (70, 170, 128, 50),   # Middle-right stroke
    (70, 200, 128, 50),   # Right stroke
]

# Cross / plus sign
CROSS_SEGMENTS = [
    (60, 128, 128, 60),   # Horizontal bar
    (70, 128, 128, 60),   # Vertical bar
]

# Triangle
TRI_SEGMENTS = [
    (60, 128,  70, 50),   # Top edge
    (60, 100, 190, 35),   # Bottom-left edge
    (60, 160, 190, 35),   # Bottom-right edge
    (70,  80, 130, 30),   # Left side
    (70, 180, 130, 30),   # Right side
]

COMPOSE_SHAPES = {
    '1': ("Rectangle", RECT_SEGMENTS),
    '2': ("Letter Q", Q_SEGMENTS),
    '3': ("Letter W", W_SEGMENTS),
    '4': ("Cross +", CROSS_SEGMENTS),
    '5': ("Triangle", TRI_SEGMENTS),
}


def compose_loop(laser, state):
    """Rapidly cycle through line segments to compose shapes."""
    while state['running']:
        segments = state['segments']
        if not segments:
            time.sleep(0.01)
            continue

        for pat, x, y, zoom in segments:
            if not state['running']:
                break
            # Set pattern type (h-line, v-line, diagonal)
            laser.set_pattern(pat)
            laser.set_zoom(zoom + state['zoom_offset'])
            laser.set_position(x + state['x_off'], y + state['y_off'])
            # Hold this segment for a fraction of a DMX frame
            # The DMX TX thread will transmit whatever's in the buffer
            time.sleep(state['hold_time'])


def mode_line_composer(fast_dmx=False):
    """Compose shapes from positioned line pattern segments."""
    mode_name = "FAST DMX COMPOSER" if fast_dmx else "LINE COMPOSER"
    print("\n" + "=" * 60)
    print(f"MODE {'3' if fast_dmx else '2'}: {mode_name}")
    print("=" * 60)
    print("Composes shapes by rapidly cycling H/V/diagonal line segments.")
    print("Each line is a full MK2 pattern positioned at specific X/Y.\n")

    universe = DMXUniverse()

    if fast_dmx:
        # Override DMX refresh rate for maximum speed
        print("⚡ Fast DMX mode: overriding refresh rate to MAX")
        print("   22 channels × 44μs = ~1.2ms per frame = ~800 fps theoretical\n")
        driver = DMXDriver(refresh_hz=500)  # 500Hz instead of 40Hz
    else:
        driver = DMXDriver()

    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    state = {
        'running': True,
        'segments': RECT_SEGMENTS,
        'hold_time': 0.005,  # 5ms per segment = 200 segment-draws/sec
        'x_off': 0,
        'y_off': 0,
        'zoom_offset': 0,
    }

    try:
        driver.start(universe)
        time.sleep(0.5)

        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(255)
        laser.center()
        time.sleep(0.3)

        print("✓ Laser ready!")
        print("\nShapes:")
        for k, (name, _) in COMPOSE_SHAPES.items():
            segs = len(COMPOSE_SHAPES[k][1])
            print(f"  {k} - {name} ({segs} segments)")
        print("\nControls:")
        print("  w/a/s/d     Move shape")
        print("  +/-         Segment zoom offset")
        print("  faster      Decrease hold time (faster cycling)")
        print("  slower      Increase hold time (slower cycling)")
        print("  status      Show current settings")
        print("  q           Quit\n")

        # Start composing
        thread = threading.Thread(target=compose_loop, args=(laser, state), daemon=True)
        thread.start()

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd in COMPOSE_SHAPES:
                name, segs = COMPOSE_SHAPES[cmd]
                state['segments'] = segs
                cycle_ms = len(segs) * state['hold_time'] * 1000
                fps = 1000 / cycle_ms if cycle_ms > 0 else 0
                print(f"Shape: {name} ({len(segs)} segments, {cycle_ms:.0f}ms/cycle, ~{fps:.0f} cycles/sec)")
            elif cmd == 'w':
                state['y_off'] = max(-80, state['y_off'] - 10)
            elif cmd == 's':
                state['y_off'] = min(80, state['y_off'] + 10)
            elif cmd == 'a':
                state['x_off'] = max(-80, state['x_off'] - 10)
            elif cmd == 'd':
                state['x_off'] = min(80, state['x_off'] + 10)
            elif cmd in ('+', '='):
                state['zoom_offset'] = min(100, state['zoom_offset'] + 5)
                print(f"Zoom offset: {state['zoom_offset']}")
            elif cmd == '-':
                state['zoom_offset'] = max(-40, state['zoom_offset'] - 5)
                print(f"Zoom offset: {state['zoom_offset']}")
            elif cmd == 'faster':
                state['hold_time'] = max(0.001, state['hold_time'] - 0.002)
                print(f"Hold: {state['hold_time']*1000:.1f}ms")
            elif cmd == 'slower':
                state['hold_time'] = min(0.05, state['hold_time'] + 0.002)
                print(f"Hold: {state['hold_time']*1000:.1f}ms")
            elif cmd == 'status':
                segs = len(state['segments'])
                cycle_ms = segs * state['hold_time'] * 1000
                fps = 1000 / cycle_ms if cycle_ms > 0 else 0
                print(f"  Hold: {state['hold_time']*1000:.1f}ms  Segments: {segs}")
                print(f"  Cycle: {cycle_ms:.0f}ms  ~{fps:.0f} shapes/sec")
                print(f"  Offset: ({state['x_off']}, {state['y_off']})  Zoom+: {state['zoom_offset']}")
                dmx_hz = driver.refresh_hz
                print(f"  DMX refresh: {dmx_hz} Hz ({'FAST' if fast_dmx else 'normal'})")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 4: PATTERN STROBE
# ──────────────────────────────────────────────────────

def mode_pattern_strobe():
    """Test rapid pattern interruption via color/mode toggling."""
    print("\n" + "=" * 60)
    print("MODE 4: PATTERN STROBE")
    print("=" * 60)
    print("Displays a full pattern and rapidly toggles visibility (color on/off)")
    print("to see if we can 'slice' the internal scan and create partial shapes.\n")
    print("Also tests rapid mode switching (STATIC ↔ OFF) as an alternative.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    state = {
        'running': True,
        'strobe_method': 'color',  # 'color' or 'mode'
        'on_time': 0.005,    # Time visible (seconds)
        'off_time': 0.020,   # Time dark (seconds)
        'pattern': 0,
        'zoom': 128,
    }

    def strobe_loop():
        while state['running']:
            method = state['strobe_method']
            if method == 'color':
                # ON: set color
                laser.set_color(255)
                time.sleep(state['on_time'])
                # OFF: blank
                laser.set_color(0)
                time.sleep(state['off_time'])
            elif method == 'mode':
                # ON: static pattern
                laser.set_mode(MK2Mode.STATIC_PATTERN)
                time.sleep(state['on_time'])
                # OFF: laser off
                laser.set_mode(MK2Mode.OFF)
                time.sleep(state['off_time'])
            elif method == 'zoom':
                # ON: normal zoom
                laser.set_zoom(state['zoom'])
                time.sleep(state['on_time'])
                # OFF: zoom to zero (smallest)
                laser.set_zoom(0)
                time.sleep(state['off_time'])

    try:
        driver.start(universe)
        time.sleep(0.5)

        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(0)
        laser.set_zoom(128)
        laser.center()
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(128)
        time.sleep(0.3)

        print("✓ Laser ready!")
        print("\nControls:")
        print("  p [num]    Set pattern (0-255)")
        print("  z [num]    Set zoom (0-255)")
        print("  c          Strobe method: color toggle")
        print("  m          Strobe method: mode toggle (OFF↔STATIC)")
        print("  v          Strobe method: zoom toggle")
        print("  on [ms]    Set ON time in ms")
        print("  off [ms]   Set OFF time in ms")
        print("  stop       Stop strobing (full pattern visible)")
        print("  start      Start strobing")
        print("  q          Quit\n")

        strobing = False
        thread = None

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd == 'start':
                if not strobing:
                    state['running'] = True
                    thread = threading.Thread(target=strobe_loop, daemon=True)
                    thread.start()
                    strobing = True
                    print("Strobing started")
            elif cmd == 'stop':
                state['running'] = False
                if thread:
                    thread.join(timeout=1)
                strobing = False
                laser.set_mode(MK2Mode.STATIC_PATTERN)
                laser.set_color(255)
                laser.set_zoom(state['zoom'])
                print("Strobing stopped - full pattern visible")
            elif cmd == 'c':
                state['strobe_method'] = 'color'
                print("Method: color toggle (color 255↔0)")
            elif cmd == 'm':
                state['strobe_method'] = 'mode'
                print("Method: mode toggle (STATIC↔OFF)")
            elif cmd == 'v':
                state['strobe_method'] = 'zoom'
                print("Method: zoom toggle (zoom↔0)")
            elif cmd.startswith('p '):
                try:
                    val = int(cmd.split()[1])
                    state['pattern'] = max(0, min(255, val))
                    laser.set_pattern(state['pattern'])
                    print(f"Pattern: {state['pattern']}")
                except ValueError:
                    print("Usage: p [0-255]")
            elif cmd.startswith('z '):
                try:
                    val = int(cmd.split()[1])
                    state['zoom'] = max(0, min(255, val))
                    laser.set_zoom(state['zoom'])
                    print(f"Zoom: {state['zoom']}")
                except ValueError:
                    print("Usage: z [0-255]")
            elif cmd.startswith('on '):
                try:
                    val = float(cmd.split()[1])
                    state['on_time'] = val / 1000.0
                    print(f"ON time: {val:.1f}ms")
                except ValueError:
                    print("Usage: on [ms]")
            elif cmd.startswith('off '):
                try:
                    val = float(cmd.split()[1])
                    state['off_time'] = val / 1000.0
                    print(f"OFF time: {val:.1f}ms")
                except ValueError:
                    print("Usage: off [ms]")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 5: DUAL LASER COMPOSER
# ──────────────────────────────────────────────────────

def mode_dual_laser():
    """Use both lasers simultaneously - no time-sharing needed."""
    print("\n" + "=" * 60)
    print("MODE 5: DUAL LASER COMPOSER")
    print("=" * 60)
    print("Uses BOTH lasers simultaneously. Each laser can display a")
    print("different line segment persistently (no flicker). Together")
    print("they compose shapes from 2 persistent segments.\n")
    print("One laser draws horizontal elements, the other vertical.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1 (H-lines)")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2 (V-lines)")

    # Preset compositions using 2 lasers
    DUAL_PRESETS = {
        '1': ("Cross +",
              (60, 128, 128, 60),    # L1: horizontal bar
              (70, 128, 128, 60)),   # L2: vertical bar
        '2': ("T-shape",
              (60, 128,  80, 60),    # L1: horizontal top bar
              (70, 128, 150, 50)),   # L2: vertical stem
        '3': ("L-shape",
              (60, 128, 200, 50),    # L1: horizontal bottom
              (70,  80, 128, 60)),   # L2: vertical left
        '4': ("Corner ┐",
              (60, 128,  80, 50),    # L1: horizontal top
              (70, 190, 140, 50)),   # L2: vertical right
    }

    try:
        driver.start(universe)
        time.sleep(0.5)

        for laser in [laser1, laser2]:
            laser.set_mode(MK2Mode.STATIC_PATTERN)
            laser.set_color(255)
            laser.set_color_segment(0)
            laser.set_scanning_speed(255)
            laser.center()
        time.sleep(0.3)

        print("✓ Both lasers ready!")
        print("\nPresets:")
        for k, (name, _, _) in DUAL_PRESETS.items():
            print(f"  {k} - {name}")
        print("\n  Manual control:")
        print("  l1p [pat]  l1x [x]  l1y [y]  l1z [zoom]   (laser 1)")
        print("  l2p [pat]  l2x [x]  l2y [y]  l2z [zoom]   (laser 2)")
        print("  q - Quit\n")

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd in DUAL_PRESETS:
                name, l1_cfg, l2_cfg = DUAL_PRESETS[cmd]
                pat1, x1, y1, z1 = l1_cfg
                pat2, x2, y2, z2 = l2_cfg
                laser1.set_pattern(pat1)
                laser1.set_position(x1, y1)
                laser1.set_zoom(z1)
                laser2.set_pattern(pat2)
                laser2.set_position(x2, y2)
                laser2.set_zoom(z2)
                print(f"Preset: {name}")
                print(f"  L1: pat={pat1} pos=({x1},{y1}) zoom={z1}")
                print(f"  L2: pat={pat2} pos=({x2},{y2}) zoom={z2}")
            else:
                # Manual commands: l1p, l1x, l1y, l1z, l2p, l2x, l2y, l2z
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        val = int(parts[1])
                        target = parts[0]
                        laser_obj = laser1 if target.startswith('l1') else laser2 if target.startswith('l2') else None
                        if laser_obj:
                            if target.endswith('p'):
                                laser_obj.set_pattern(val)
                            elif target.endswith('x'):
                                laser_obj.set_x_position(val)
                            elif target.endswith('y'):
                                laser_obj.set_y_position(val)
                            elif target.endswith('z'):
                                laser_obj.set_zoom(val)
                            print(f"OK: {target} = {val}")
                    except (ValueError, Exception) as e:
                        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        laser1.off()
        laser2.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 6: MIXED APPROACH - Dot tracing + Line segments
# ──────────────────────────────────────────────────────

def mode_mixed():
    """
    Hybrid approach: one laser does dot-tracing (like draw_shapes.py),
    the other displays a positioned line segment for fill/structure.

    Laser 1: continuously traces a shape outline with dot pen
    Laser 2: static line pattern positioned for structure
    """
    print("\n" + "=" * 60)
    print("MODE 6: MIXED (Dot trace + Line segment)")
    print("=" * 60)
    print("Laser 1: dot-traces a shape outline at high speed")
    print("Laser 2: displays a static line segment for structure\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser1 = MK2(universe, LASER1_ADDRESS, name="Tracer")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Line")

    # Circle outline points for laser 1
    def make_circle(cx, cy, r, n=30):
        pts = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        return pts

    # Square outline
    def make_square(cx, cy, s, n=8):
        pts = []
        corners = [(cx-s, cy-s), (cx+s, cy-s), (cx+s, cy+s), (cx-s, cy+s), (cx-s, cy-s)]
        for i in range(len(corners) - 1):
            x1, y1 = corners[i]
            x2, y2 = corners[i + 1]
            for j in range(n):
                t = j / n
                pts.append((int(x1 + (x2-x1)*t), int(y1 + (y2-y1)*t)))
        return pts

    shapes = {
        '1': ("Circle", lambda: make_circle(128, 128, 60)),
        '2': ("Square", lambda: make_square(128, 128, 50)),
    }

    state = {
        'running': True,
        'points': make_circle(128, 128, 60),
        'speed': 0.002,
    }

    def trace_loop():
        while state['running']:
            for x, y in state['points']:
                if not state['running']:
                    break
                laser1.set_position(max(11, min(255, x)), max(11, min(255, y)))
                time.sleep(state['speed'])

    try:
        driver.start(universe)
        time.sleep(0.5)

        # Laser 1: dot tracer
        laser1.set_mode(MK2Mode.STATIC_PATTERN)
        laser1.set_pattern(0)
        laser1.set_zoom(0)
        laser1.set_color(255)
        laser1.set_color_segment(0)
        laser1.set_scanning_speed(255)
        laser1.center()

        # Laser 2: static positioned line
        laser2.set_mode(MK2Mode.STATIC_PATTERN)
        laser2.set_pattern(60)   # Horizontal line
        laser2.set_zoom(40)
        laser2.set_color(200)    # Slightly different color
        laser2.set_color_segment(0)
        laser2.set_scanning_speed(255)
        laser2.set_position(128, 128)
        time.sleep(0.3)

        print("✓ Both lasers ready!")
        print("\nLaser 1 traces outline, Laser 2 shows a positioned line")
        print("Controls:")
        print("  1/2           Circle / Square outline")
        print("  l2p/l2x/l2y/l2z [val]  Control laser 2")
        print("  q             Quit\n")

        thread = threading.Thread(target=trace_loop, daemon=True)
        thread.start()

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break
            if cmd == 'q':
                break
            elif cmd in shapes:
                name, gen = shapes[cmd]
                state['points'] = gen()
                print(f"Tracing: {name}")
            else:
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        val = int(parts[1])
                        if parts[0] == 'l2p':
                            laser2.set_pattern(val)
                        elif parts[0] == 'l2x':
                            laser2.set_x_position(val)
                        elif parts[0] == 'l2y':
                            laser2.set_y_position(val)
                        elif parts[0] == 'l2z':
                            laser2.set_zoom(val)
                        print(f"OK: {parts[0]} = {val}")
                    except Exception as e:
                        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser1.off()
        laser2.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("LaserPi - Drawing Lab")
    print("=" * 60)
    print()
    print("Experimental techniques for precise laser drawing.")
    print()
    print("Modes:")
    print("  1  Pen Finder        - Find the smallest dot pattern")
    print("  2  Line Composer     - Compose shapes from line segments (40Hz DMX)")
    print("  3  Fast DMX Composer - Same but with ~500Hz DMX refresh")
    print("  4  Pattern Strobe    - Interrupt patterns with rapid blanking")
    print("  5  Dual Laser        - Two lasers, one shape, no flicker")
    print("  6  Mixed             - Dot tracing + line segment (both lasers)")
    print()

    # Check command-line argument
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("Select mode (1-6): ").strip()

    if mode == '1':
        mode_pen_finder()
    elif mode == '2':
        mode_line_composer(fast_dmx=False)
    elif mode == '3':
        mode_line_composer(fast_dmx=True)
    elif mode == '4':
        mode_pattern_strobe()
    elif mode == '5':
        mode_dual_laser()
    elif mode == '6':
        mode_mixed()
    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Drawing Lab - Experimental approaches for precise laser drawing

The MK2 uses an STC 89C516RD+ (8051) MCU that processes DMX at ~25-40Hz.
Sending faster than that just means it picks up random intermediate states.
All modes in this lab are designed around that constraint.

  Mode 1: PEN FINDER
    Compare all small patterns at various zoom levels to find the
    absolute smallest dot.

  Mode 2: MCU RATE FINDER
    Discover the MK2's actual DMX processing rate by toggling between
    two visible states and finding the fastest rate where both appear.

  Mode 3: LINE COMPOSER (synced)
    Compose shapes from line segments, synced to the MCU's processing
    rate. Each segment is held long enough for the MCU to display it.

  Mode 4: DUAL LASER
    Both lasers simultaneously - one draws H-lines, the other V-lines.
    No time-sharing, no flicker. Perfect for 2-segment shapes.

  Mode 5: DUAL + COMPOSE
    Both lasers show persistent elements, PLUS time-share additional
    segments. 2 solid + N flickering = more complex shapes.

  Mode 6: PATTERN STROBE
    Rapid color/mode toggling to test pattern interruption.

  Mode 7: GALVO SIGNAL PROBE
    For hardware hacking: identifies galvo driver signals when you
    have the laser open. Steps through known positions for probing.

Run:  python drawing_lab.py [mode]
"""
import sys
import time
import os
import math
import threading
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import (
    LASER1_ADDRESS, LASER2_ADDRESS, SERIAL_PORT,
    DMX_BAUD, DMX_CHANNEL_COUNT, DMX_BREAK_TIME_US, DMX_MAB_TIME_US
)

# ──────────────────────────────────────────────────────
#  PRESET SYSTEM
# ──────────────────────────────────────────────────────

PRESETS_FILE = os.path.join(os.path.dirname(__file__), 'visual_presets.json')

# Default presets (saved on first run)
DEFAULT_PRESETS = {
    "mode2": {  # MCU Rate Finder presets
        "Fast Circle": {
            "description": "Fast alternating circle",
            "hold_ms": 35,
            "scan_speed": 5,
            "dynamic_speed": 1,
            "zoom": 255,
            "laser_mode": "STATIC_PATTERN",
            "pattern": 1,
        }
    },
    "mode4": {  # Dual Laser presets
        "Two Eyes": {
            "description": "Two eyes - L1 alternates positions (2 circles), L2=flapping bird",
            "scan_speed": 5,
            "dynamic_speed": 5,
            "laser1": {
                "mode": "STATIC_PATTERN",
                "pattern": 1,  # Circle
                "zoom": 255,
                "toggle": [
                    {"x": 60, "y": 128},
                    {"x": 200, "y": 128}
                ],
                "hold_ms": 35,
            },
            "laser2": {
                "mode": "DYNAMIC_PATTERN",
                "pattern": 235,  # Flapping bird
                "x": 128,
                "y": 128,
                "zoom": 255,
            }
        }
    }
}

def load_presets(mode=None):
    """Load visual presets from JSON file.
    
    Args:
        mode: Optional mode filter (e.g., 'mode2', 'mode4')
    """
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, 'r') as f:
                all_presets = json.load(f)
            # Merge with defaults to ensure new default presets are available
            needs_save = False
            for mode_key, mode_defaults in DEFAULT_PRESETS.items():
                if mode_key not in all_presets:
                    all_presets[mode_key] = mode_defaults.copy()
                    needs_save = True
            if needs_save:
                save_presets(all_presets, silent=True)
        except Exception as e:
            print(f"Warning: Could not load presets: {e}")
            all_presets = DEFAULT_PRESETS.copy()
    else:
        # First run - save defaults
        save_presets(DEFAULT_PRESETS)
        all_presets = DEFAULT_PRESETS.copy()
    
    if mode:
        return all_presets.get(mode, {})
    return all_presets

def save_presets(presets, silent=False):
    """Save visual presets to JSON file."""
    try:
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)
        if not silent:
            print(f"✓ Saved presets to {PRESETS_FILE}")
    except Exception as e:
        print(f"Error saving presets: {e}")

def find_preset(presets, name):
    """Case-insensitive preset lookup. Returns (actual_key, preset_data) or (None, None)."""
    name_lower = name.lower()
    for key, data in presets.items():
        if key.lower() == name_lower:
            return key, data
    return None, None


# ──────────────────────────────────────────────────────
#  MODE 1: PEN FINDER
# ──────────────────────────────────────────────────────

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
    (120, "Triangle"),
    (130, "Triangle"),
    (140, "Cross +"),
    (150, "Square"),
    (200, "Pentagon"),
]


def mode_pen_finder():
    """Cycle through patterns at low zoom to find the smallest dot."""
    print("\n" + "=" * 60)
    print("MODE 1: PEN FINDER")
    print("=" * 60)
    print("Cycles through patterns at zoom 0, 10, 30, 50, 128")
    print("Press Enter=next, s=star, q=quit\n")

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

        starred = []
        zooms = [0, 10, 30, 50, 128]

        for zoom in zooms:
            print(f"\n── Zoom = {zoom} ──")
            laser.set_zoom(zoom)
            time.sleep(0.2)

            for pat_num, pat_name in PEN_CANDIDATES:
                laser.set_pattern(pat_num)
                time.sleep(0.1)
                result = input(f"  Pattern {pat_num:3d}: {pat_name:25s}  ")
                if result.lower() == 'q':
                    if starred:
                        print("\n★ Starred patterns:")
                        for p, z in starred:
                            print(f"    Pattern {p} @ zoom {z}")
                    return
                if result.lower() == 's':
                    starred.append((pat_num, zoom))
                    print(f"    ★ Starred: pattern {pat_num} at zoom {zoom}")

        if starred:
            print("\n★ Starred patterns:")
            for p, z in starred:
                print(f"    Pattern {p} @ zoom {z}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 2: MCU RATE FINDER
# ──────────────────────────────────────────────────────

def mode_rate_finder():
    """
    Discover the MK2's actual DMX processing rate.
    
    Method: Alternate between two clearly different states (left dot / right dot)
    at varying rates. If you see BOTH dots, the rate is slow enough for the MCU
    to process both states. If you see only one (or random), it's too fast.
    
    The fastest rate where you reliably see both states = the MCU's update rate.
    """
    print("\n" + "=" * 60)
    print("MODE 2: MCU RATE FINDER")
    print("=" * 60)
    print()
    print("Alternates the laser between LEFT and RIGHT positions.")
    print("At the right speed, you should see TWO dots (persistence")
    print("of vision). Too fast = MCU misses updates, you see random.")
    print()
    print("This tells us the MCU's actual DMX processing rate.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    # Two clearly different states
    STATE_A = {'x': 60,  'y': 128}   # Left
    STATE_B = {'x': 200, 'y': 128}   # Right

    state = {
        'running': True,
        'hold_ms': 50.0,     # Start slow (50ms = 20Hz total, 10Hz per state)
        'mode': 'position',  # 'position' or 'pattern'
        'pattern': 145,      # Cross-dashed (fast shape)
        'zoom': 255,         # Max zoom
        'scan_speed': 1,     # Slowest scan = sharpest
        'dyn_speed': 255,    # Max pattern/dynamic speed
        'laser_mode': MK2Mode.STATIC_PATTERN,  # or DYNAMIC_PATTERN
    }

    def apply_settings():
        """Apply current pattern/zoom/speed settings to the laser."""
        laser.set_mode(state['laser_mode'])
        laser.set_pattern(state['pattern'])
        laser.set_zoom(state['zoom'])
        laser.set_scanning_speed(state['scan_speed'])
        laser.set_dynamic_speed(state['dyn_speed'])

    def toggle_loop():
        """Alternate between two states at the configured rate."""
        while state['running']:
            hold = state['hold_ms'] / 1000.0

            if state['mode'] == 'position':
                # State A: left
                laser.set_position(STATE_A['x'], STATE_A['y'])
                time.sleep(hold)
                # State B: right
                laser.set_position(STATE_B['x'], STATE_B['y'])
                time.sleep(hold)
            elif state['mode'] == 'pattern':
                # State A: horizontal line
                laser.set_pattern(60)
                time.sleep(hold)
                # State B: vertical line
                laser.set_pattern(70)
                time.sleep(hold)

    try:
        driver.start(universe)
        time.sleep(0.5)

        laser.set_mode(state['laser_mode'])
        laser.set_pattern(state['pattern'])
        laser.set_zoom(state['zoom'])
        laser.center()
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(state['scan_speed'])
        laser.set_dynamic_speed(state['dyn_speed'])
        time.sleep(0.3)

        print("✓ Laser ready!")
        print()
        print("Controls:")
        print("  faster       Decrease hold time (press repeatedly)")
        print("  slower       Increase hold time")
        print("  [number]     Set hold time in ms directly (e.g. '25')")
        print("  pos          Toggle position mode (left↔right)")
        print("  pat          Toggle pattern mode (h-line↔v-line)")
        print("  p [n]        Set pattern number (e.g. 'p 145')")
        print("  z [n]        Set zoom 0-255 (e.g. 'z 255')")
        print("  ss [n]       Set scan speed 0-255 (e.g. 'ss 1')")
        print("  ds [n]       Set dynamic speed 0-255 (e.g. 'ds 255')")
        print("  static       Switch to STATIC_PATTERN mode")
        print("  dynamic      Switch to DYNAMIC_PATTERN mode")
        print("  load [name]  Load preset by name")
        print("  list         List all available presets")
        print("  save [name]  Save current settings as preset")
        print("  q            Quit")
        print()
        mode_name = "STATIC" if state['laser_mode'] == MK2Mode.STATIC_PATTERN else "DYNAMIC"
        print(f"Mode: {mode_name}  Pattern: {state['pattern']}  Zoom: {state['zoom']}  "
              f"Scan: {state['scan_speed']}  DynSpeed: {state['dyn_speed']}")
        print("Start: Do you see TWO shapes alternating?")
        print(f"Hold time: {state['hold_ms']:.0f}ms per state "
              f"({1000/state['hold_ms']/2:.0f} full cycles/sec)\n")

        thread = threading.Thread(target=toggle_loop, daemon=True)
        thread.start()

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd == 'faster':
                state['hold_ms'] = max(2, state['hold_ms'] - 5)
            elif cmd == 'slower':
                state['hold_ms'] = min(200, state['hold_ms'] + 5)
            elif cmd == 'pos':
                state['mode'] = 'position'
                apply_settings()
                print(f"Mode: position (left↔right, pat {state['pattern']} "
                      f"zoom {state['zoom']} scan {state['scan_speed']})")
            elif cmd == 'pat':
                state['mode'] = 'pattern'
                laser.center()
                laser.set_zoom(80)
                print("Mode: pattern (h-line↔v-line)")
            elif cmd.startswith('p ') and not cmd.startswith('pa'):
                try:
                    val = int(cmd.split()[1])
                    state['pattern'] = max(0, min(255, val))
                    apply_settings()
                    print(f"Pattern: {state['pattern']}")
                except (ValueError, IndexError):
                    print("Usage: p [0-255]")
            elif cmd.startswith('z '):
                try:
                    val = int(cmd.split()[1])
                    state['zoom'] = max(0, min(255, val))
                    apply_settings()
                    print(f"Zoom: {state['zoom']}")
                except (ValueError, IndexError):
                    print("Usage: z [0-255]")
            elif cmd.startswith('ss '):
                try:
                    val = int(cmd.split()[1])
                    state['scan_speed'] = max(0, min(255, val))
                    apply_settings()
                    print(f"Scan speed: {state['scan_speed']}")
                except (ValueError, IndexError):
                    print("Usage: ss [0-255]")
            elif cmd.startswith('ds '):
                try:
                    val = int(cmd.split()[1])
                    state['dyn_speed'] = max(0, min(255, val))
                    apply_settings()
                    print(f"Dynamic speed: {state['dyn_speed']}")
                except (ValueError, IndexError):
                    print("Usage: ds [0-255]")
            elif cmd == 'static':
                state['laser_mode'] = MK2Mode.STATIC_PATTERN
                apply_settings()
                print("Mode: STATIC_PATTERN")
            elif cmd == 'dynamic':
                state['laser_mode'] = MK2Mode.DYNAMIC_PATTERN
                apply_settings()
                print("Mode: DYNAMIC_PATTERN")
            elif cmd.startswith('load '):
                preset_name = cmd[5:].strip()
                if preset_name:
                    presets = load_presets('mode2')
                    actual_name, preset = find_preset(presets, preset_name)
                    if preset:
                        # Apply preset settings
                        state['hold_ms'] = preset.get('hold_ms', 35.0)
                        state['scan_speed'] = preset.get('scan_speed', 5)
                        state['dyn_speed'] = preset.get('dynamic_speed', 1)
                        state['zoom'] = preset.get('zoom', 255)
                        state['pattern'] = preset.get('pattern', 1)
                        
                        # Handle laser mode
                        mode_str = preset.get('laser_mode', 'STATIC_PATTERN')
                        if mode_str == 'DYNAMIC_PATTERN':
                            state['laser_mode'] = MK2Mode.DYNAMIC_PATTERN
                        else:
                            state['laser_mode'] = MK2Mode.STATIC_PATTERN
                        
                        apply_settings()
                        mode_name = "STATIC" if state['laser_mode'] == MK2Mode.STATIC_PATTERN else "DYNAMIC"
                        print(f"✓ Loaded preset '{actual_name}'")
                        print(f"  {preset.get('description', '')}")
                        print(f"  Mode: {mode_name}  Pattern: {state['pattern']}  Zoom: {state['zoom']}")
                        print(f"  Scan: {state['scan_speed']}  DynSpeed: {state['dyn_speed']}  Hold: {state['hold_ms']:.0f}ms")
                    else:
                        print(f"❌ Preset '{preset_name}' not found. Use 'list' to see available presets.")
                else:
                    print("Usage: load [preset_name]")
            elif cmd == 'list':
                presets = load_presets('mode2')
                if presets:
                    print("\nAvailable Mode 2 presets:")
                    for name, data in presets.items():
                        desc = data.get('description', 'No description')
                        mode = data.get('laser_mode', 'STATIC_PATTERN')
                        pattern = data.get('pattern', 0)
                        print(f"  • {name:20s} - {desc}")
                        print(f"    Mode: {mode}  Pattern: {pattern}  Hold: {data.get('hold_ms', 35):.0f}ms")
                    print()
                else:
                    print("No presets saved yet.")
            elif cmd.startswith('save '):
                preset_name = cmd[5:].strip()
                if preset_name:
                    all_presets = load_presets()
                    if 'mode2' not in all_presets:
                        all_presets['mode2'] = {}
                    mode_name = "STATIC_PATTERN" if state['laser_mode'] == MK2Mode.STATIC_PATTERN else "DYNAMIC_PATTERN"
                    all_presets['mode2'][preset_name] = {
                        "description": "User-saved preset",
                        "hold_ms": state['hold_ms'],
                        "scan_speed": state['scan_speed'],
                        "dynamic_speed": state['dyn_speed'],
                        "zoom": state['zoom'],
                        "laser_mode": mode_name,
                        "pattern": state['pattern'],
                    }
                    save_presets(all_presets)
                    print(f"✓ Saved preset '{preset_name}'")
                else:
                    print("Usage: save [preset_name]")
            else:
                try:
                    val = float(cmd)
                    state['hold_ms'] = max(2, min(200, val))
                except ValueError:
                    continue

            hz = 1000 / state['hold_ms'] / 2
            print(f"Hold: {state['hold_ms']:.0f}ms  ({hz:.0f} full cycles/sec, "
                  f"MCU needs {state['hold_ms']:.0f}ms to process each state)")

        state['running'] = False
        time.sleep(0.05)

        # Report findings
        print(f"\n{'='*60}")
        print(f"RESULT: Last working hold time = {state['hold_ms']:.0f}ms")
        print(f"MCU processing rate: ~{1000/state['hold_ms']:.0f} DMX updates/sec")
        print(f"For line composer, use hold = {state['hold_ms']:.0f}ms per segment")
        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 3: LINE COMPOSER (synced to MCU rate)
# ──────────────────────────────────────────────────────

# Shapes as lists of line segments: (pattern, x, y, zoom)
# Pattern 60 = horizontal, 70 = vertical, 80 = diagonal

RECT_SEGMENTS = [
    (60, 128,  70, 40),   # Top edge
    (60, 128, 190, 40),   # Bottom edge
    (70,  70, 128, 40),   # Left edge
    (70, 190, 128, 40),   # Right edge
]

Q_SEGMENTS = [
    (60, 128,  55, 40),   # Top
    (60, 128, 200, 40),   # Bottom
    (70,  60, 128, 40),   # Left
    (70, 195, 128, 40),   # Right
    (80, 175, 195, 25),   # Diagonal tail
]

W_SEGMENTS = [
    (70,  50, 128, 50),   # Left stroke
    (80,  90, 170, 35),   # Down-right
    (80, 130, 100, 35),   # Up-right
    (70, 170, 128, 50),   # Middle-right stroke
    (70, 200, 128, 50),   # Right stroke
]

CROSS_SEGMENTS = [
    (60, 128, 128, 60),   # Horizontal bar
    (70, 128, 128, 60),   # Vertical bar
]

TRI_SEGMENTS = [
    (60, 128,  70, 50),   # Top edge
    (60, 100, 190, 35),   # Bottom-left edge
    (60, 160, 190, 35),   # Bottom-right edge
    (70,  80, 130, 30),   # Left side
    (70, 180, 130, 30),   # Right side
]

# QW logo simplified: Using special double-line patterns
# Pattern 150 = Square, Pattern 90 = Double horizontal, Pattern 100 = Double vertical
QW_SIMPLIFIED = [
    (150,  75, 110, 60),   # Q: Square (left side)
    (90,  135, 175, 80),   # Base: Double horizontal lines (bottom, spans both letters)
    (100, 175, 115, 55),   # W: Double vertical lines (left-center legs)
    (100, 205, 115, 55),   # W: Double vertical lines (right-center legs)
]

COMPOSE_SHAPES = {
    '1': ("Rectangle", RECT_SEGMENTS),
    '2': ("Letter Q", Q_SEGMENTS),
    '3': ("Letter W", W_SEGMENTS),
    '4': ("Cross +", CROSS_SEGMENTS),
    '5': ("Triangle", TRI_SEGMENTS),
    '6': ("QW Simplified", QW_SIMPLIFIED),
}


def compose_loop_synced(laser, driver, state):
    """
    Cycle through line segments, synced to DMX frame transmission.
    
    Key insight: we must hold each segment for at least 1 full DMX frame
    (25ms at 40Hz) so the MCU sees and processes it. Changing the buffer
    faster than the TX rate is pointless — the MCU only sees what the
    TX thread actually sends.
    
    Strategy: update the buffer, then WAIT for the DMX TX thread to send
    at least 1-2 frames before changing to the next segment.
    """
    while state['running']:
        segments = state['segments']
        if not segments:
            time.sleep(0.01)
            continue

        for pat, x, y, zoom in segments:
            if not state['running']:
                break
            if state['segments'] is not segments:
                break  # Shape changed, restart

            # Set all properties at once
            laser.set_pattern(pat)
            laser.set_zoom(max(0, min(255, zoom + state['zoom_offset'])))
            laser.set_position(
                max(11, min(255, x + state['x_off'])),
                max(11, min(255, y + state['y_off']))
            )

            # Wait for MCU to process this segment
            # The DMX TX thread runs at 40Hz (25ms per frame)
            # We need the MCU to receive AND display this segment,
            # so hold for hold_ms (should be >= 25ms for 40Hz)
            time.sleep(state['hold_ms'] / 1000.0)


def mode_line_composer():
    """Compose shapes from positioned line segments, synced to MCU rate."""
    print("\n" + "=" * 60)
    print("MODE 3: LINE COMPOSER (MCU-synced)")
    print("=" * 60)
    print()
    print("Composes shapes by cycling line segments. Each segment is held")
    print("long enough for the STC 89C516RD+ MCU to process and display it.")
    print()
    print("The MCU processes DMX at ~25-40Hz. With N segments, each shows")
    print("at 40/N Hz. For 2 segments (cross): ~20Hz each = visible.")
    print("For 5 segments (Q letter): ~8Hz each = flickery but recognizable.")
    print()
    print("Tip: run Mode 2 first to find your MCU's exact processing rate.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    state = {
        'running': True,
        'segments': CROSS_SEGMENTS,  # Start with cross (only 2 segments)
        'hold_ms': 35.0,  # ms to hold each segment (user-discovered optimal)
        'scan_speed': 5,  # User-discovered optimal for sharp dots
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
        laser.set_scanning_speed(state['scan_speed'])
        laser.center()
        time.sleep(0.3)

        print("✓ Laser ready!")
        print("\nShapes:")
        for k, (name, segs) in COMPOSE_SHAPES.items():
            n = len(segs)
            each_hz = 1000 / (state['hold_ms'] * n)
            print(f"  {k} - {name:12s} ({n} segs, ~{each_hz:.0f}Hz each)")
        print("\nControls:")
        print("  w/a/s/d     Move")
        print("  +/-         Zoom offset")
        print("  hold [ms]   Set hold time per segment (default: 35)")
        print("  ss [n]      Set scan speed 0-255 (default: 5)")
        print("  status      Current settings")
        print("  q           Quit\n")

        n = len(state['segments'])
        each_hz = 1000 / (state['hold_ms'] * n)
        print(f"Starting with Cross + (2 segments, {state['hold_ms']:.0f}ms hold, "
              f"scan speed {state['scan_speed']}, ~{each_hz:.0f}Hz per segment)\n")

        thread = threading.Thread(
            target=compose_loop_synced,
            args=(laser, driver, state),
            daemon=True
        )
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
                n = len(segs)
                each_hz = 1000 / (state['hold_ms'] * n)
                cycle_ms = n * state['hold_ms']
                print(f"Shape: {name} ({n} segs, {cycle_ms:.0f}ms/cycle, "
                      f"~{each_hz:.0f}Hz per segment)")
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
            elif cmd.startswith('hold '):
                try:
                    val = float(cmd.split()[1])
                    state['hold_ms'] = max(5, min(200, val))
                    n = len(state['segments'])
                    each_hz = 1000 / (state['hold_ms'] * n)
                    print(f"Hold: {state['hold_ms']:.0f}ms  "
                          f"(~{each_hz:.0f}Hz per segment with {n} segments)")
                except ValueError:
                    print("Usage: hold [ms]")
            elif cmd.startswith('ss '):
                try:
                    val = int(cmd.split()[1])
                    state['scan_speed'] = max(0, min(255, val))
                    laser.set_scanning_speed(state['scan_speed'])
                    print(f"Scan speed: {state['scan_speed']}")
                except (ValueError, IndexError):
                    print("Usage: ss [0-255]")
            elif cmd == 'status':
                n = len(state['segments'])
                cycle_ms = n * state['hold_ms']
                each_hz = 1000 / (state['hold_ms'] * max(1, n))
                print(f"  Hold: {state['hold_ms']:.0f}ms  Segments: {n}  Scan speed: {state['scan_speed']}")
                print(f"  Cycle: {cycle_ms:.0f}ms  ~{each_hz:.0f}Hz per segment")
                print(f"  Offset: ({state['x_off']}, {state['y_off']})  "
                      f"Zoom+: {state['zoom_offset']}")
                print(f"  DMX TX rate: {driver.refresh_hz}Hz")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 4: DUAL LASER
# ──────────────────────────────────────────────────────

def mode_dual_laser():
    """Both lasers showing persistent line segments simultaneously."""
    print("\n" + "=" * 60)
    print("MODE 4: DUAL LASER COMPOSER")
    print("=" * 60)
    print("Both lasers show a persistent segment simultaneously.")
    print("No time-sharing = no flicker. Perfect for 2-segment shapes.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")

    DUAL_PRESETS = {
        '1': ("Cross +",
              (60, 128, 128, 60),
              (70, 128, 128, 60)),
        '2': ("T-shape",
              (60, 128,  80, 60),
              (70, 128, 150, 50)),
        '3': ("L-shape",
              (60, 128, 200, 50),
              (70,  80, 128, 60)),
        '4': ("Corner",
              (60, 128,  80, 50),
              (70, 190, 140, 50)),
        '5': ("= equals",
              (60, 128, 100, 60),
              (60, 128, 160, 60)),
        '6': ("|| parallel",
              (70, 100, 128, 60),
              (70, 160, 128, 60)),
    }

    # Toggle state for position-alternating on Laser 1
    toggle_state = {
        'active': False,
        'running': True,
        'positions': [{'x': 60, 'y': 128}, {'x': 200, 'y': 128}],
        'hold_ms': 35.0,
    }

    def toggle_loop():
        """Alternate Laser 1 between positions to create multiple shapes via POV."""
        while toggle_state['running']:
            if not toggle_state['active']:
                time.sleep(0.05)
                continue
            hold = toggle_state['hold_ms'] / 1000.0
            for pos in toggle_state['positions']:
                if not toggle_state['active'] or not toggle_state['running']:
                    break
                laser1.set_position(pos['x'], pos['y'])
                time.sleep(hold)

    try:
        driver.start(universe)
        time.sleep(0.5)

        for laser in [laser1, laser2]:
            laser.set_mode(MK2Mode.STATIC_PATTERN)
            laser.set_color(255)
            laser.set_color_segment(0)
            laser.set_scanning_speed(255)
            laser.set_dynamic_speed(255)
            laser.center()
        time.sleep(0.3)

        print("✓ Both lasers ready!")
        print("\nBuilt-in Presets:")
        for k, (name, _, _) in DUAL_PRESETS.items():
            print(f"  {k} - {name}")
        print("\nCommands:")
        print("  load [name]   Load saved dual-laser preset (e.g. 'load Two Eyes')")
        print("  list          List all saved presets")
        print("  save [name]   Save current config as preset")
        print("  l1p/l1x/l1y/l1z [val]   Laser 1 manual")
        print("  l2p/l2x/l2y/l2z [val]   Laser 2 manual")
        print("  l1mode/l2mode [static/dynamic]   Set laser mode")
        print("  ss [val]      Set scan speed (both lasers)")
        print("  ds [val]      Set dynamic speed (both lasers)")
        print("  toggle        Start/stop L1 position alternating")
        print("  hold [ms]     Set toggle hold time (default 35ms)")
        print("  q             Quit\n")

        toggle_thread = threading.Thread(target=toggle_loop, daemon=True)
        toggle_thread.start()

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd in DUAL_PRESETS:
                toggle_state['active'] = False  # Stop toggle when switching presets
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
            elif cmd == 'toggle':
                toggle_state['active'] = not toggle_state['active']
                if toggle_state['active']:
                    n = len(toggle_state['positions'])
                    print(f"Toggle ON: L1 alternating {n} positions at {toggle_state['hold_ms']:.0f}ms")
                    for i, pos in enumerate(toggle_state['positions']):
                        print(f"  Pos {i+1}: x={pos['x']}, y={pos['y']}")
                else:
                    print("Toggle OFF: L1 position fixed")
            elif cmd.startswith('hold '):
                try:
                    val = float(cmd.split()[1])
                    toggle_state['hold_ms'] = max(5, min(200, val))
                    print(f"Toggle hold: {toggle_state['hold_ms']:.0f}ms")
                except (ValueError, IndexError):
                    print("Usage: hold [ms]")
            elif cmd.startswith('load '):
                preset_name = cmd[5:].strip()
                if preset_name:
                    presets = load_presets('mode4')
                    actual_name, preset = find_preset(presets, preset_name)
                    if preset:
                        l1 = preset.get('laser1', {})
                        l2 = preset.get('laser2', {})
                        
                        # Apply L1 settings
                        if l1.get('mode') == 'DYNAMIC_PATTERN':
                            laser1.set_mode(MK2Mode.DYNAMIC_PATTERN)
                        else:
                            laser1.set_mode(MK2Mode.STATIC_PATTERN)
                        laser1.set_pattern(l1.get('pattern', 0))
                        laser1.set_zoom(l1.get('zoom', 60))
                        
                        # Check if L1 has toggle positions
                        if 'toggle' in l1 and l1['toggle']:
                            toggle_state['positions'] = l1['toggle']
                            toggle_state['hold_ms'] = l1.get('hold_ms', 35.0)
                            toggle_state['active'] = True
                            print(f"  L1 toggle: {len(l1['toggle'])} positions at {toggle_state['hold_ms']:.0f}ms")
                        else:
                            toggle_state['active'] = False
                            laser1.set_position(l1.get('x', 128), l1.get('y', 128))
                        
                        # Apply L2 settings
                        if l2.get('mode') == 'DYNAMIC_PATTERN':
                            laser2.set_mode(MK2Mode.DYNAMIC_PATTERN)
                        else:
                            laser2.set_mode(MK2Mode.STATIC_PATTERN)
                        laser2.set_pattern(l2.get('pattern', 0))
                        laser2.set_position(l2.get('x', 128), l2.get('y', 128))
                        laser2.set_zoom(l2.get('zoom', 60))
                        
                        # Apply global settings
                        ss = preset.get('scan_speed', 255)
                        laser1.set_scanning_speed(ss)
                        laser2.set_scanning_speed(ss)
                        ds = preset.get('dynamic_speed', 255)
                        laser1.set_dynamic_speed(ds)
                        laser2.set_dynamic_speed(ds)
                        
                        print(f"✓ Loaded preset '{actual_name}'")
                        print(f"  {preset.get('description', '')}")
                    else:
                        print(f"❌ Preset '{preset_name}' not found. Use 'list' to see available presets.")
                else:
                    print("Usage: load [preset_name]")
            elif cmd == 'list':
                presets = load_presets('mode4')
                if presets:
                    print("\nAvailable Mode 4 (Dual Laser) presets:")
                    for name, data in presets.items():
                        desc = data.get('description', 'No description')
                        print(f"  • {name}")
                        print(f"    {desc}")
                    print()
                else:
                    print("No dual-laser presets saved yet.")
            elif cmd.startswith('ss '):
                try:
                    val = int(cmd.split()[1])
                    laser1.set_scanning_speed(val)
                    laser2.set_scanning_speed(val)
                    print(f"Scan speed: {val} (both lasers)")
                except (ValueError, IndexError):
                    print("Usage: ss [0-255]")
            elif cmd.startswith('ds '):
                try:
                    val = int(cmd.split()[1])
                    laser1.set_dynamic_speed(val)
                    laser2.set_dynamic_speed(val)
                    print(f"Dynamic speed: {val} (both lasers)")
                except (ValueError, IndexError):
                    print("Usage: ds [0-255]")
            elif cmd == 'l1mode static':
                laser1.set_mode(MK2Mode.STATIC_PATTERN)
                print("L1: STATIC_PATTERN")
            elif cmd == 'l1mode dynamic':
                laser1.set_mode(MK2Mode.DYNAMIC_PATTERN)
                print("L1: DYNAMIC_PATTERN")
            elif cmd == 'l2mode static':
                laser2.set_mode(MK2Mode.STATIC_PATTERN)
                print("L2: STATIC_PATTERN")
            elif cmd == 'l2mode dynamic':
                laser2.set_mode(MK2Mode.DYNAMIC_PATTERN)
                print("L2: DYNAMIC_PATTERN")
            elif cmd.startswith('save '):
                preset_name = cmd[5:].strip()
                if preset_name:
                    all_presets = load_presets()
                    if 'mode4' not in all_presets:
                        all_presets['mode4'] = {}
                    
                    # Get current state of both lasers
                    l1_state = laser1.get_state()
                    l2_state = laser2.get_state()
                    
                    l1_mode = "DYNAMIC_PATTERN" if l1_state['mode'] == MK2Mode.DYNAMIC_PATTERN.value else "STATIC_PATTERN"
                    l2_mode = "DYNAMIC_PATTERN" if l2_state['mode'] == MK2Mode.DYNAMIC_PATTERN.value else "STATIC_PATTERN"
                    
                    all_presets['mode4'][preset_name] = {
                        "description": "User-saved dual laser preset",
                        "scan_speed": l1_state.get('scanning_speed', 255),
                        "dynamic_speed": l1_state.get('dynamic_speed', 255),
                        "laser1": {
                            "mode": l1_mode,
                            "pattern": l1_state.get('pattern', 0),
                            "x": l1_state.get('x_position', 128),
                            "y": l1_state.get('y_position', 128),
                            "zoom": l1_state.get('zoom', 60),
                        },
                        "laser2": {
                            "mode": l2_mode,
                            "pattern": l2_state.get('pattern', 0),
                            "x": l2_state.get('x_position', 128),
                            "y": l2_state.get('y_position', 128),
                            "zoom": l2_state.get('zoom', 60),
                        }
                    }
                    save_presets(all_presets)
                    print(f"✓ Saved dual-laser preset '{preset_name}'")
                else:
                    print("Usage: save [preset_name]")
            else:
                parts = cmd.split()
                if len(parts) == 2:
                    try:
                        val = int(parts[1])
                        target = parts[0]
                        lobj = laser1 if target.startswith('l1') else \
                               laser2 if target.startswith('l2') else None
                        if lobj:
                            if target.endswith('p'):
                                lobj.set_pattern(val)
                            elif target.endswith('x'):
                                lobj.set_x_position(val)
                            elif target.endswith('y'):
                                lobj.set_y_position(val)
                            elif target.endswith('z'):
                                lobj.set_zoom(val)
                            print(f"OK: {target} = {val}")
                    except (ValueError, Exception) as e:
                        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        toggle_state['running'] = False
        toggle_state['active'] = False
        time.sleep(0.05)
        laser1.off()
        laser2.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 5: DUAL LASER + TIME-SHARED EXTRAS
# ──────────────────────────────────────────────────────

def mode_dual_compose():
    """
    2 persistent segments (one per laser) + time-shared extras on laser 1.
    
    Laser 2: always shows one persistent segment (no switching).
    Laser 1: alternates between its persistent segment and bonus segments.
    
    This gives you 2 solid lines + 1-3 flickering lines = more complex shapes.
    """
    print("\n" + "=" * 60)
    print("MODE 5: DUAL + COMPOSE")
    print("=" * 60)
    print("Laser 2 = 1 persistent segment (always visible)")
    print("Laser 1 = alternates between N segments (time-shared)")
    print("Result: 1 solid + N flickering lines. Best with few segments.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1 (switching)")
    laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2 (persistent)")

    # Presets: (name, laser2_config, [laser1_segments...])
    PRESETS = {
        '1': ("Box (V + 3H)",
              (70, 128, 128, 60),                            # L2: vertical bar (persistent)
              [(60, 128,  70, 50),                            # L1: top H
               (60, 128, 190, 50),                            # L1: bottom H
               (70, 200, 128, 60)]),                          # L1: right V (L2 covers left)
        '2': ("H + cross inside",
              (60, 128,  60, 70),                             # L2: top bar (persistent)
              [(60, 128, 200, 70),                            # L1: bottom bar
               (60, 128, 128, 40),                            # L1: middle H (short)
               (70, 128, 128, 40)]),                          # L1: middle V (short)
        '3': ("Cross + corners",
              (60, 128, 128, 80),                             # L2: horizontal (persistent)
              [(70, 128, 128, 80),                            # L1: vertical
               (80, 100, 100, 20),                            # L1: corner accent
               (80, 160, 160, 20)]),                          # L1: corner accent
    }

    state = {
        'running': True,
        'l1_segments': [(60, 128, 128, 60), (70, 128, 128, 60)],
        'hold_ms': 30.0,
    }

    def l1_loop():
        while state['running']:
            segs = state['l1_segments']
            for pat, x, y, zoom in segs:
                if not state['running']:
                    break
                laser1.set_pattern(pat)
                laser1.set_zoom(zoom)
                laser1.set_position(x, y)
                time.sleep(state['hold_ms'] / 1000.0)

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
        for k, (name, _, _) in PRESETS.items():
            print(f"  {k} - {name}")
        print("\nControls:")
        print("  hold [ms]   Set hold time")
        print("  l2p/l2x/l2y/l2z [val]  Laser 2 (persistent)")
        print("  q - Quit\n")

        thread = threading.Thread(target=l1_loop, daemon=True)
        thread.start()

        while True:
            try:
                cmd = input("> ").strip().lower()
            except EOFError:
                break

            if cmd == 'q':
                break
            elif cmd in PRESETS:
                name, l2_cfg, l1_segs = PRESETS[cmd]
                pat2, x2, y2, z2 = l2_cfg
                laser2.set_pattern(pat2)
                laser2.set_position(x2, y2)
                laser2.set_zoom(z2)
                state['l1_segments'] = l1_segs
                n = len(l1_segs)
                each_hz = 1000 / (state['hold_ms'] * n)
                print(f"Preset: {name}")
                print(f"  L2 (persistent): pat={pat2} pos=({x2},{y2}) zoom={z2}")
                print(f"  L1 (switching): {n} segments @ ~{each_hz:.0f}Hz each")
            elif cmd.startswith('hold '):
                try:
                    val = float(cmd.split()[1])
                    state['hold_ms'] = max(10, min(200, val))
                    n = len(state['l1_segments'])
                    each_hz = 1000 / (state['hold_ms'] * n)
                    print(f"Hold: {state['hold_ms']:.0f}ms (~{each_hz:.0f}Hz per segment)")
                except ValueError:
                    print("Usage: hold [ms]")
            else:
                parts = cmd.split()
                if len(parts) == 2 and parts[0].startswith('l2'):
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
#  MODE 6: PATTERN STROBE
# ──────────────────────────────────────────────────────

def mode_pattern_strobe():
    """Rapid color/mode toggling to interrupt patterns."""
    print("\n" + "=" * 60)
    print("MODE 6: PATTERN STROBE")
    print("=" * 60)
    print("Toggle pattern visibility rapidly via color/mode switching.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    state = {
        'running': True,
        'strobe_method': 'color',
        'on_time': 0.005,
        'off_time': 0.020,
        'pattern': 0,
        'zoom': 128,
    }

    def strobe_loop():
        while state['running']:
            method = state['strobe_method']
            if method == 'color':
                laser.set_color(255)
                time.sleep(state['on_time'])
                laser.set_color(0)
                time.sleep(state['off_time'])
            elif method == 'mode':
                laser.set_mode(MK2Mode.STATIC_PATTERN)
                time.sleep(state['on_time'])
                laser.set_mode(MK2Mode.OFF)
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
        print("  p [num]    Pattern (0-255)")
        print("  z [num]    Zoom (0-255)")
        print("  c          Method: color (255↔0)")
        print("  m          Method: mode (STATIC↔OFF)")
        print("  on [ms]    ON time")
        print("  off [ms]   OFF time")
        print("  start/stop Toggle strobing")
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
                print("Stopped")
            elif cmd == 'c':
                state['strobe_method'] = 'color'
                print("Method: color")
            elif cmd == 'm':
                state['strobe_method'] = 'mode'
                print("Method: mode")
            elif cmd.startswith('p '):
                try:
                    val = int(cmd.split()[1])
                    state['pattern'] = max(0, min(255, val))
                    laser.set_pattern(state['pattern'])
                    print(f"Pattern: {state['pattern']}")
                except ValueError:
                    pass
            elif cmd.startswith('z '):
                try:
                    val = int(cmd.split()[1])
                    state['zoom'] = max(0, min(255, val))
                    laser.set_zoom(state['zoom'])
                    print(f"Zoom: {state['zoom']}")
                except ValueError:
                    pass
            elif cmd.startswith('on '):
                try:
                    state['on_time'] = float(cmd.split()[1]) / 1000
                    print(f"ON: {state['on_time']*1000:.1f}ms")
                except ValueError:
                    pass
            elif cmd.startswith('off '):
                try:
                    state['off_time'] = float(cmd.split()[1]) / 1000
                    print(f"OFF: {state['off_time']*1000:.1f}ms")
                except ValueError:
                    pass

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        state['running'] = False
        time.sleep(0.05)
        laser.off()
        time.sleep(0.3)
        driver.stop()


# ──────────────────────────────────────────────────────
#  MODE 7: GALVO SIGNAL PROBE
# ──────────────────────────────────────────────────────

def mode_galvo_probe():
    """
    For hardware hacking with the laser case open.
    
    Steps through known galvo positions so you can probe the PCB with a
    multimeter or oscilloscope to identify the galvo drive signals.
    
    The STC 89C516RD+ doesn't have a built-in DAC, so it likely drives
    the galvos through:
    
    Option A: External DAC chip (look for 8-16 pin DIP/SOP near galvo wires)
              Common: DAC0808, TLC5615, MCP4921
    
    Option B: PWM from MCU → RC filter → op-amp → galvo
              Look for capacitors + op-amp (LM358, TL072) near galvo wires
    
    Option C: Dedicated galvo driver IC
              Look for a separate board near the galvo motors
    
    Identifying these signals lets you inject your own X/Y voltages.
    
    SAFETY: The galvos use 5-12V. The laser diodes use higher voltage.
    NEVER probe laser diode power supplies. Only probe the galvo signal path.
    """
    print("\n" + "=" * 60)
    print("MODE 7: GALVO SIGNAL PROBE")
    print("=" * 60)
    print()
    print("For probing the MK2 PCB with multimeter/oscilloscope.")
    print("Steps through known positions so you can identify galvo signals.")
    print()
    print("STC 89C516RD+ pinout (relevant pins):")
    print("  8051 has NO built-in DAC. It must use external conversion.")
    print("  Look for: PWM output pins → RC filter → galvo driver")
    print("  Or: parallel bus → external DAC → galvo driver")
    print()
    print("WHAT TO LOOK FOR on the PCB:")
    print("  1. Follow wires from X/Y galvo motors back to the PCB")
    print("  2. Identify the galvo driver (op-amp or driver IC)")
    print("  3. Find the input to that driver (this is our injection point)")
    print("  4. Measure voltage range at that point during the tests below")
    print()
    print("SAFETY: Don't probe near laser diode power! Only galvo signals.\n")

    universe = DMXUniverse()
    driver = DMXDriver()
    laser = MK2(universe, LASER1_ADDRESS, name="Laser 1")

    # Probe test sequences
    TESTS = [
        ("CENTER",      5,   5,   "Both galvos at center. Measure baseline voltages."),
        ("X-LEFT",      11,  128, "X galvo to minimum. Note X signal voltage."),
        ("X-CENTER",    128, 128, "X galvo to center."),
        ("X-RIGHT",     255, 128, "X galvo to maximum. Calculate X voltage range."),
        ("Y-TOP",       128, 11,  "Y galvo to minimum. Note Y signal voltage."),
        ("Y-CENTER",    128, 128, "Y galvo to center."),
        ("Y-BOTTOM",    128, 255, "Y galvo to maximum. Calculate Y voltage range."),
        ("CORNER-TL",   11,  11,  "Both at min. Verify both channels independent."),
        ("CORNER-BR",   255, 255, "Both at max."),
        ("X-SWEEP",     None, 128, "X sweeping slowly (watch on scope for waveform)."),
        ("Y-SWEEP",     128, None, "Y sweeping slowly."),
    ]

    try:
        driver.start(universe)
        time.sleep(0.5)

        laser.set_mode(MK2Mode.STATIC_PATTERN)
        laser.set_pattern(0)
        laser.set_zoom(0)
        laser.center()
        laser.set_color(255)
        laser.set_color_segment(0)
        laser.set_scanning_speed(255)
        time.sleep(0.5)

        print("✓ Laser on. Starting probe sequence.\n")
        print("Press Enter to advance to next test, 'q' to quit.\n")

        for i, (name, x, y, desc) in enumerate(TESTS):
            print(f"{'─'*60}")
            print(f"TEST {i+1}/{len(TESTS)}: {name}")
            print(f"  {desc}")

            if x is None:
                # X sweep
                print("  Sweeping X from 11→255→11 (5 seconds)...")
                for cycle in range(2):
                    for pos in range(11, 256, 5):
                        laser.set_position(pos, y)
                        time.sleep(0.02)
                    for pos in range(255, 10, -5):
                        laser.set_position(pos, y)
                        time.sleep(0.02)
                laser.set_position(128, y)
                print("  Sweep done. Did you see the waveform on scope?")
            elif y is None:
                # Y sweep
                print("  Sweeping Y from 11→255→11 (5 seconds)...")
                for cycle in range(2):
                    for pos in range(11, 256, 5):
                        laser.set_position(x, pos)
                        time.sleep(0.02)
                    for pos in range(255, 10, -5):
                        laser.set_position(x, pos)
                        time.sleep(0.02)
                laser.set_position(x, 128)
                print("  Sweep done.")
            else:
                laser.set_position(x, y)
                print(f"  Position: X={x:3d}  Y={y:3d}")

            print()
            result = input("  [Enter=next, r=repeat sweep, q=quit] ")
            if result.lower() == 'q':
                break
            if result.lower() == 'r' and (x is None or y is None):
                # Repeat sweep
                if x is None:
                    for pos in range(11, 256, 3):
                        laser.set_position(pos, y)
                        time.sleep(0.015)
                    for pos in range(255, 10, -3):
                        laser.set_position(pos, y)
                        time.sleep(0.015)
                else:
                    for pos in range(11, 256, 3):
                        laser.set_position(x, pos)
                        time.sleep(0.015)
                    for pos in range(255, 10, -3):
                        laser.set_position(x, pos)
                        time.sleep(0.015)

        print(f"\n{'='*60}")
        print("WHAT TO REPORT:")
        print("  1. What voltage did you measure at X-LEFT vs X-RIGHT?")
        print("  2. What voltage at Y-TOP vs Y-BOTTOM?")
        print("  3. Did you see a clean ramp on the sweep tests?")
        print("  4. What chip/IC is near the galvo wires?")
        print("  5. What does the trace from MCU to galvo driver look like?")
        print(f"{'='*60}\n")
        print("With this info we can design the direct drive circuit.")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        laser.off()
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
    print("MK2 MCU: STC 89C516RD+ (8051, processes DMX at ~25-40Hz)")
    print()
    print("Modes:")
    print("  1  Pen Finder       Find the smallest dot pattern")
    print("  2  MCU Rate Finder  Discover actual DMX processing speed")
    print("  3  Line Composer    Compose shapes (MCU-synced segments)")
    print("  4  Dual Laser       2 lasers, 2 segments, zero flicker")
    print("  5  Dual + Compose   2 lasers: 1 persistent + N switching")
    print("  6  Pattern Strobe   Rapid blanking experiments")
    print("  7  Galvo Probe      Hardware hacking: identify signals")
    print()

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("Select mode (1-7): ").strip()

    if mode == '1':
        mode_pen_finder()
    elif mode == '2':
        mode_rate_finder()
    elif mode == '3':
        mode_line_composer()
    elif mode == '4':
        mode_dual_laser()
    elif mode == '5':
        mode_dual_compose()
    elif mode == '6':
        mode_pattern_strobe()
    elif mode == '7':
        mode_galvo_probe()
    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Draw pattern — select a pattern and trace it with the laser.

Run: python3 examples/draw_pattern.py [pattern_name] [--color R G B] [--speed N]
"""
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.control.coordinator import LaserController
from direct_laser.control.patterns import list_patterns, get_pattern, PATTERN_REGISTRY
from direct_laser.laser.rgb_driver import COLOR_NAMES
from direct_laser import config


def main():
    parser = argparse.ArgumentParser(description='Draw a laser pattern')
    parser.add_argument('pattern', nargs='?', default='circle',
                        help=f'Pattern name ({", ".join(PATTERN_REGISTRY.keys())})')
    parser.add_argument('--color', nargs=3, type=int, default=[255, 0, 0],
                        metavar=('R', 'G', 'B'), help='RGB color (0-255)')
    parser.add_argument('--preset', type=str, default=None,
                        help=f'Color preset ({", ".join(COLOR_NAMES.keys())})')
    parser.add_argument('--speed', type=int, default=None,
                        help='Motor speed in microsteps/s')
    parser.add_argument('--size', type=float, default=0.8,
                        help='Pattern scale 0.0-1.0 (default: 0.8)')
    parser.add_argument('--loops', type=int, default=0,
                        help='Number of trace loops (0 = infinite until Ctrl+C)')
    parser.add_argument('--points', type=int, default=60,
                        help='Number of points in the pattern (default: 60)')
    parser.add_argument('--list', action='store_true',
                        help='List available patterns and exit')
    args = parser.parse_args()

    if args.list:
        print("Available patterns:")
        for p in list_patterns():
            print(f"  {p}")
        sys.exit(0)

    if args.pattern not in PATTERN_REGISTRY:
        print(f"Unknown pattern: {args.pattern}")
        print(f"Available: {', '.join(PATTERN_REGISTRY.keys())}")
        sys.exit(1)

    # Resolve color
    r, g, b = args.color
    if args.preset:
        if args.preset.lower() not in COLOR_NAMES:
            print(f"Unknown color preset: {args.preset}")
            sys.exit(1)
        color = COLOR_NAMES[args.preset.lower()]
        r, g, b = color.value

    print("=== Draw Pattern ===")
    print(f"Pattern: {args.pattern}")
    print(f"Color:   ({r}, {g}, {b})")
    print(f"Size:    {args.size}")
    print(f"Points:  {args.points}")
    print()

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Cannot connect to pigpiod.")
        sys.exit(1)

    controller = LaserController(pi)
    try:
        if args.speed:
            controller.galvo.x_stepper.set_speed(args.speed)
            controller.galvo.y_stepper.set_speed(args.speed)
            print(f"Speed set to {args.speed} µsteps/s")

        # Build pattern kwargs
        kwargs = {'points': args.points}
        if args.pattern in ('rectangle', 'star', 'grid', 'spiral'):
            kwargs['radius'] = args.size
        else:
            kwargs['radius'] = args.size

        # Generate path
        path = list(get_pattern(args.pattern, **kwargs))
        print(f"Generated {len(path)} points")

        controller.laser.on()
        controller.laser.set_color(r, g, b)

        if args.loops == 0:
            # Continuous trace
            print("Tracing (Ctrl+C to stop)...")
            controller.trace_loop(path)
            try:
                while controller.is_tracing:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print("\nStopping...")
                controller.stop_tracing()
        else:
            # Fixed number of loops
            for loop_num in range(args.loops):
                print(f"Loop {loop_num + 1}/{args.loops}")
                controller.draw_path(path)
                time.sleep(0.05)

        print("Done.")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        controller.shutdown()
        pi.stop()
        print("Shutdown complete.")


if __name__ == '__main__':
    main()

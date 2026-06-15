#!/usr/bin/env python3
"""
Image draw — convert an image to laser paths and trace it.

Converts a bitmap image to black/white paths and draws them with the laser.

Run: python3 examples/image_draw.py <image_path> [--threshold 128] [--resolution 64]
"""
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.control.coordinator import LaserController
from direct_laser.conversion.image_converter import (
    image_to_paths, optimize_path, get_image_stats
)
from direct_laser import config


def main():
    parser = argparse.ArgumentParser(description='Draw an image with the laser')
    parser.add_argument('image', help='Path to the image file')
    parser.add_argument('--threshold', type=int, default=128,
                        help='Black/white threshold 0-255 (default: 128)')
    parser.add_argument('--resolution', type=int, default=64,
                        help='Scan resolution in pixels (default: 64)')
    parser.add_argument('--invert', action='store_true',
                        help='Invert black/white')
    parser.add_argument('--color', nargs=3, type=int, default=[255, 0, 0],
                        metavar=('R', 'G', 'B'), help='RGB color (default: 255 0 0)')
    parser.add_argument('--speed', type=int, default=None,
                        help='Motor speed in microsteps/s')
    parser.add_argument('--optimize', action='store_true', default=True,
                        help='Optimize path order (default: on)')
    parser.add_argument('--no-optimize', dest='optimize', action='store_false',
                        help='Disable path optimization')
    parser.add_argument('--loops', type=int, default=1,
                        help='Number of trace loops (0 = infinite)')
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"ERROR: File not found: {args.image}")
        sys.exit(1)

    # Convert image
    print(f"Loading: {args.image}")
    print(f"Threshold: {args.threshold}, Resolution: {args.resolution}")
    print(f"Invert: {args.invert}")
    print()

    strokes = image_to_paths(
        args.image,
        threshold=args.threshold,
        resolution=args.resolution,
        invert=args.invert
    )

    if not strokes:
        print("No paths found in image. Try adjusting threshold or inverting.")
        sys.exit(1)

    stats = get_image_stats(strokes)
    print(f"Strokes:      {stats['stroke_count']}")
    print(f"Total points: {stats['total_points']}")
    print(f"X range:      {stats['x_range'][0]:.3f} to {stats['x_range'][1]:.3f}")
    print(f"Y range:      {stats['y_range'][0]:.3f} to {stats['y_range'][1]:.3f}")
    print()

    if args.optimize:
        print("Optimizing path order... ", end='', flush=True)
        strokes = optimize_path(strokes)
        print("done.")

    # Flatten to single path with blanking moves indicated by None separators
    all_points = []
    for stroke in strokes:
        all_points.extend(stroke)

    print(f"\nReady to draw {len(all_points)} total points in {len(strokes)} strokes.")
    r, g, b = args.color
    print(f"Color: ({r}, {g}, {b})")
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

        controller.laser.on()
        controller.laser.set_color(r, g, b)

        if args.loops == 0:
            print("Drawing continuously (Ctrl+C to stop)...")
            loop_count = 0
            while True:
                loop_count += 1
                for stroke in strokes:
                    controller.draw_path(stroke)
                if loop_count % 10 == 0:
                    print(f"  Loop {loop_count}...")
        else:
            for loop_num in range(args.loops):
                if args.loops > 1:
                    print(f"Loop {loop_num + 1}/{args.loops}")
                for i, stroke in enumerate(strokes):
                    controller.draw_path(stroke)
                    if (i + 1) % 20 == 0:
                        print(f"  Stroke {i + 1}/{len(strokes)}")

        print("\nDone.")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        controller.shutdown()
        pi.stop()
        print("Shutdown complete.")


if __name__ == '__main__':
    main()

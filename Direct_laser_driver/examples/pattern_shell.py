#!/usr/bin/env python3
"""
Pattern shell — interactive command-line for laser control.

Commands:
    pattern <name> [points] [size]  — Draw a pattern
    text <string>                   — Draw text
    color <r> <g> <b>              — Set color by RGB
    color <preset>                  — Set color by preset name
    speed <usteps/s>               — Set motor speed
    trace                          — Re-trace current pattern continuously
    stop                           — Stop re-tracing
    home                           — Home the galvo to center
    off                            — Laser off
    on                             — Laser on
    status                         — Show system status
    list                           — List available patterns
    help                           — Show this help
    quit / q                       — Exit

Run: python3 examples/pattern_shell.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.control.coordinator import LaserController
from direct_laser.control.patterns import (
    list_patterns, get_pattern, text_path, PATTERN_REGISTRY
)
from direct_laser.laser.rgb_driver import COLOR_NAMES
from direct_laser import config


class PatternShell:
    def __init__(self, controller):
        self.ctrl = controller
        self.current_path = None
        self.color = (255, 0, 0)

    def run(self):
        print("=== Pattern Shell ===")
        print("Type 'help' for commands, 'quit' to exit.\n")

        self.ctrl.laser.on()
        self.ctrl.laser.set_color(*self.color)

        while True:
            try:
                line = input("laser> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ('quit', 'q', 'exit'):
                break
            elif cmd == 'help':
                self._cmd_help()
            elif cmd == 'list':
                self._cmd_list()
            elif cmd == 'pattern':
                self._cmd_pattern(parts[1:])
            elif cmd == 'text':
                self._cmd_text(parts[1:])
            elif cmd == 'color':
                self._cmd_color(parts[1:])
            elif cmd == 'speed':
                self._cmd_speed(parts[1:])
            elif cmd == 'trace':
                self._cmd_trace()
            elif cmd == 'stop':
                self._cmd_stop()
            elif cmd == 'home':
                self._cmd_home()
            elif cmd == 'off':
                self.ctrl.laser.off()
                print("Laser OFF")
            elif cmd == 'on':
                self.ctrl.laser.on()
                self.ctrl.laser.set_color(*self.color)
                print("Laser ON")
            elif cmd == 'status':
                self._cmd_status()
            else:
                print(f"Unknown command: {cmd}")

    def _cmd_help(self):
        print(__doc__)

    def _cmd_list(self):
        print("Available patterns:")
        for name in list_patterns():
            print(f"  {name}")
        print("\nAlso: text <string>")

    def _cmd_pattern(self, args):
        if not args:
            print("Usage: pattern <name> [points] [size]")
            return

        name = args[0].lower()
        if name not in PATTERN_REGISTRY:
            print(f"Unknown pattern: {name}")
            return

        points = int(args[1]) if len(args) > 1 else 60
        size = float(args[2]) if len(args) > 2 else 0.8

        self._cmd_stop()  # stop any active trace

        path = list(get_pattern(name, points=points, radius=size))
        self.current_path = path
        print(f"Drawing {name} ({len(path)} points, size={size})...")
        self.ctrl.laser.set_color(*self.color)
        self.ctrl.draw_path(path)
        print("Done.")

    def _cmd_text(self, args):
        if not args:
            print("Usage: text <string>")
            return

        message = ' '.join(args).upper()
        self._cmd_stop()

        strokes = text_path(message, scale=0.6)
        if not strokes:
            print("No drawable characters.")
            return

        print(f'Drawing "{message}" ({len(strokes)} strokes)...')
        self.ctrl.laser.set_color(*self.color)
        for stroke in strokes:
            self.ctrl.draw_path(stroke)
        print("Done.")

    def _cmd_color(self, args):
        if not args:
            print(f"Current color: {self.color}")
            print(f"Presets: {', '.join(COLOR_NAMES.keys())}")
            return

        if len(args) == 1:
            name = args[0].lower()
            if name in COLOR_NAMES:
                self.color = COLOR_NAMES[name].value
                self.ctrl.laser.set_color(*self.color)
                print(f"Color set to {name} {self.color}")
            else:
                print(f"Unknown preset. Available: {', '.join(COLOR_NAMES.keys())}")
            return

        if len(args) >= 3:
            try:
                r, g, b = int(args[0]), int(args[1]), int(args[2])
                self.color = (r, g, b)
                self.ctrl.laser.set_color(r, g, b)
                print(f"Color set to ({r}, {g}, {b})")
            except ValueError:
                print("Usage: color <r> <g> <b>  or  color <preset>")
            return

        print("Usage: color <r> <g> <b>  or  color <preset>")

    def _cmd_speed(self, args):
        if not args:
            status = self.ctrl.galvo.get_status()
            print(f"Current speed: {status['x']['speed']} µsteps/s")
            return

        try:
            speed = int(args[0])
            self.ctrl.galvo.x_stepper.set_speed(speed)
            self.ctrl.galvo.y_stepper.set_speed(speed)
            print(f"Speed set to {speed} µsteps/s")
        except ValueError:
            print("Usage: speed <usteps_per_sec>")

    def _cmd_trace(self):
        if self.current_path is None:
            print("No pattern loaded. Draw a pattern first.")
            return

        if self.ctrl.is_tracing:
            print("Already tracing. Use 'stop' first.")
            return

        print("Continuous tracing started (type 'stop' to end)...")
        self.ctrl.laser.set_color(*self.color)
        self.ctrl.trace_loop(self.current_path)

    def _cmd_stop(self):
        if self.ctrl.is_tracing:
            self.ctrl.stop_tracing()
            print("Tracing stopped.")

    def _cmd_home(self):
        self._cmd_stop()
        self.ctrl.laser.set_color(0, 0, 0)
        self.ctrl.galvo.home()
        print("Galvo homed to center.")

    def _cmd_status(self):
        galvo = self.ctrl.galvo.get_status()
        laser = self.ctrl.laser.get_status()
        print(f"  Galvo pos:  raw ({galvo['x']['position']}, {galvo['y']['position']})")
        print(f"  Galvo norm: ({galvo['normalized_x']:.3f}, {galvo['normalized_y']:.3f})")
        print(f"  Motor speed: {galvo['x']['speed']} µsteps/s")
        print(f"  Laser: {'ON' if laser['enabled'] else 'OFF'}")
        print(f"  Color: ({laser['red']}, {laser['green']}, {laser['blue']})")
        print(f"  Tracing: {self.ctrl.is_tracing}")


def main():
    print("⚠  WARNING: LASER RADIATION — WEAR SAFETY GOGGLES ⚠\n")

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Cannot connect to pigpiod.")
        sys.exit(1)

    controller = LaserController(pi)
    shell = PatternShell(controller)
    try:
        shell.run()
    finally:
        controller.shutdown()
        pi.stop()
        print("Shutdown complete.")


if __name__ == '__main__':
    main()

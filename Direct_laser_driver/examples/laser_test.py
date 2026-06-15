#!/usr/bin/env python3
"""
Laser test — RGB laser driver verification.
Tests individual channels, color presets, and PWM dimming.

WARNING: Ensure laser safety goggles are worn!

Run: python3 examples/laser_test.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.laser.rgb_driver import RGBLaser, Color, COLOR_NAMES
from direct_laser import config


def test_individual_channels(laser):
    """Test each channel independently."""
    print("\n--- Individual channel test ---")
    channels = [
        ("Red", lambda v: laser.set_color(v, 0, 0)),
        ("Green", lambda v: laser.set_color(0, v, 0)),
        ("Blue", lambda v: laser.set_color(0, 0, v)),
    ]

    for name, setter in channels:
        print(f"  {name}: ON... ", end='', flush=True)
        setter(255)
        time.sleep(1.5)
        print("OFF")
        laser.set_color(0, 0, 0)
        time.sleep(0.5)


def test_color_presets(laser):
    """Cycle through all color presets."""
    print("\n--- Color preset cycle ---")
    for color in Color:
        print(f"  {color.name}... ", end='', flush=True)
        laser.set_color_preset(color)
        time.sleep(1.5)
        print("OK")

    laser.set_color(0, 0, 0)


def test_pwm_ramp(laser):
    """Ramp brightness up and down on red and blue channels."""
    print("\n--- PWM brightness ramp ---")
    print("  (Green is DPSS / on/off only — no dimming expected)")

    for name, setter in [("Red", laser.set_red), ("Blue", laser.set_blue)]:
        print(f"  {name} ramp up... ", end='', flush=True)
        for v in range(0, 256, 5):
            setter(v)
            time.sleep(0.02)
        print("down... ", end='', flush=True)
        for v in range(255, -1, -5):
            setter(v)
            time.sleep(0.02)
        setter(0)
        print("OK")
        time.sleep(0.3)


def interactive_mode(laser):
    """Interactive color control."""
    print("\n--- Interactive mode ---")
    print("Commands:")
    print("  <color name>     — Apply preset (red, green, blue, white, etc.)")
    print("  <r> <g> <b>      — Set RGB values (0-255 each)")
    print("  off              — Turn off")
    print("  status           — Show current state")
    print("  q                — Quit")
    print()

    while True:
        try:
            cmd = input("laser> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        if cmd == 'q':
            break
        if cmd == 'off':
            laser.set_color(0, 0, 0)
            print("  Off")
            continue
        if cmd == 'status':
            print(f"  {laser.get_status()}")
            continue

        # Try as color name
        if cmd in COLOR_NAMES:
            laser.set_color_preset(cmd)
            print(f"  Set to {cmd}")
            continue

        # Try as R G B values
        parts = cmd.split()
        if len(parts) == 3:
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                laser.set_color(r, g, b)
                print(f"  Set to ({r}, {g}, {b})")
                continue
            except ValueError:
                pass

        print(f"  Unknown command. Colors: {list(COLOR_NAMES.keys())}")


def main():
    print("=== Laser Test ===")
    print()
    print("⚠  WARNING: LASER RADIATION — WEAR SAFETY GOGGLES ⚠")
    print()
    print(f"GPIO pins: R=GPIO{config.LASER_RED_PIN}, G=GPIO{config.LASER_GREEN_PIN}, "
          f"B=GPIO{config.LASER_BLUE_PIN}, EN=GPIO{config.LASER_ENABLE_PIN}")
    print(f"PWM frequency: {config.LASER_PWM_FREQUENCY} Hz")
    print(f"Green DPSS mode: {config.LASER_GREEN_DPSS_MODE}")
    print()

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Cannot connect to pigpiod.")
        print("  Start with: sudo systemctl start pigpiod")
        sys.exit(1)

    laser = RGBLaser(pi)
    try:
        laser.on()
        print("Laser master enable: ON\n")

        test_individual_channels(laser)
        test_color_presets(laser)
        test_pwm_ramp(laser)
        interactive_mode(laser)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        laser.off()
        pi.stop()
        print("Laser OFF, pigpio stopped.")


if __name__ == '__main__':
    main()

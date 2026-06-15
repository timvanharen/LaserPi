#!/usr/bin/env python3
"""
Boundary probe — detect mechanical limits of the galvo mirror assembly.

Two modes:
  A) Manual probing — slowly moves each axis, user confirms when limit is hit
  B) StallGuard (if TMC2209 UART available) — automatic stall detection

Saves calibration to galvo_calibration.json.

Run: python3 examples/boundary_probe.py
"""
import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.motor.stepper import Stepper
from direct_laser import config


def manual_probe_axis(pi, step_pin, dir_pin, en_pin, name):
    """
    Manually probe an axis by moving slowly and waiting for user confirmation.

    Returns (min_position, max_position) in microsteps.
    """
    motor = Stepper(pi, step_pin, dir_pin, en_pin, name=name)
    motor.enable()
    motor.set_speed(500)  # Slow speed for safety

    print(f"\n--- Manual probe: {name} axis ---")
    print("The motor will move slowly in one direction.")
    print("Press ENTER when it reaches the mechanical limit.")
    print("Type 'skip' to skip this axis.\n")

    # Probe positive direction
    print(f"  Probing {name}+ direction...")
    print("  Press ENTER when the motor hits the limit (or 'skip'):")
    motor.clear_boundaries()

    # Move in small increments, checking for user input between moves
    step_batch = 50
    while True:
        motor.step(Stepper.POSITIVE, step_batch)
        # Check for input (non-blocking is complex; use batched approach)
        try:
            # Give user a moment to react
            user = input(f"    pos={motor.position:+5d}  [ENTER=limit reached, c=continue, s=skip]: ")
            if user.strip().lower() == 's':
                max_pos = motor.position
                print(f"  Skipped. Using current position as max: {max_pos}")
                break
            elif user.strip().lower() == 'c' or user.strip() == '':
                if user.strip() == '':
                    max_pos = motor.position
                    print(f"  {name}+ limit: {max_pos}")
                    break
                # Continue moving
                continue
        except EOFError:
            max_pos = motor.position
            break

    # Return to start
    print("  Returning to origin...")
    motor.move_to(0)
    time.sleep(0.5)

    # Probe negative direction
    print(f"\n  Probing {name}- direction...")
    print("  Press ENTER when the motor hits the limit:")

    while True:
        motor.step(Stepper.NEGATIVE, step_batch)
        try:
            user = input(f"    pos={motor.position:+5d}  [ENTER=limit reached, c=continue, s=skip]: ")
            if user.strip().lower() == 's':
                min_pos = motor.position
                print(f"  Skipped. Using current position as min: {min_pos}")
                break
            elif user.strip().lower() == 'c' or user.strip() == '':
                if user.strip() == '':
                    min_pos = motor.position
                    print(f"  {name}- limit: {min_pos}")
                    break
                continue
        except EOFError:
            min_pos = motor.position
            break

    # Return to center
    center = (min_pos + max_pos) // 2
    print(f"  Moving to center ({center})...")
    motor.move_to(center)

    motor.disable()
    return min_pos, max_pos


def add_safety_margin(min_pos, max_pos, margin_percent=5):
    """Add a safety margin to boundaries (shrink range by margin%)."""
    range_size = max_pos - min_pos
    margin = int(range_size * margin_percent / 100)
    return min_pos + margin, max_pos - margin


def main():
    print("=== Galvo Boundary Probe ===")
    print()
    print("This tool finds the mechanical limits of your mirror assembly.")
    print("The motors will move slowly — watch carefully and press ENTER")
    print("when each axis reaches its physical limit.")
    print()
    print("SAFETY: Make sure nothing is obstructing the mirrors!")
    print()

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Cannot connect to pigpiod.")
        print("  Start with: sudo systemctl start pigpiod")
        sys.exit(1)

    try:
        # Probe X axis
        x_min, x_max = manual_probe_axis(
            pi,
            config.MOTOR_X_STEP, config.MOTOR_X_DIR, config.MOTOR_X_EN,
            "X"
        )

        # Probe Y axis
        y_min, y_max = manual_probe_axis(
            pi,
            config.MOTOR_Y_STEP, config.MOTOR_Y_DIR, config.MOTOR_Y_EN,
            "Y"
        )

        # Apply safety margin
        print("\n--- Results ---")
        print(f"  Raw boundaries:")
        print(f"    X: [{x_min}, {x_max}] ({x_max - x_min} microsteps)")
        print(f"    Y: [{y_min}, {y_max}] ({y_max - y_min} microsteps)")

        margin = input("\n  Safety margin % (default 5): ").strip()
        margin = int(margin) if margin else 5

        x_min_safe, x_max_safe = add_safety_margin(x_min, x_max, margin)
        y_min_safe, y_max_safe = add_safety_margin(y_min, y_max, margin)

        print(f"\n  With {margin}% safety margin:")
        print(f"    X: [{x_min_safe}, {x_max_safe}] ({x_max_safe - x_min_safe} microsteps)")
        print(f"    Y: [{y_min_safe}, {y_max_safe}] ({y_max_safe - y_min_safe} microsteps)")

        # Save calibration
        save = input("\n  Save calibration? (Y/n): ").strip().lower()
        if save != 'n':
            config.save_calibration(x_min_safe, x_max_safe, y_min_safe, y_max_safe)
            print(f"  Saved to {config.CALIBRATION_FILE}")

            # Verify
            cal = config.load_calibration()
            print(f"  Verification: {cal}")
        else:
            print("  Not saved.")

        # Optional: run sweep test within boundaries
        test = input("\n  Run boundary sweep test? (y/N): ").strip().lower()
        if test == 'y':
            from direct_laser.motor.galvo import Galvo

            galvo = Galvo(pi)
            galvo.reload_calibration()
            galvo.enable()
            galvo.set_speed(2000)

            print("  Sweeping corners within calibrated boundaries...")
            corners_norm = [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]
            for nx, ny in corners_norm:
                print(f"    Moving to normalized ({nx}, {ny})...")
                galvo.move_to_normalized(nx, ny)
                pos = galvo.get_position()
                print(f"      → position: {pos}")
                time.sleep(0.5)

            galvo.home()
            galvo.disable()
            print("  Sweep complete!")

        print("\n=== Boundary probe complete ===")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        for en_pin in (config.MOTOR_X_EN, config.MOTOR_Y_EN):
            pi.write(en_pin, 1)
        pi.stop()
        print("Motors disabled, pigpio stopped.")


if __name__ == '__main__':
    main()

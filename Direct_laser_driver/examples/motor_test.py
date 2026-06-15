#!/usr/bin/env python3
"""
Motor test — basic stepper motor movement verification.
Tests each axis independently, then a simple square pattern.

Run: python3 examples/motor_test.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.motor.stepper import Stepper
from direct_laser import config


def test_single_axis(pi, step_pin, dir_pin, en_pin, name):
    """Test a single motor axis."""
    motor = Stepper(pi, step_pin, dir_pin, en_pin, name=name)
    motor.enable()
    motor.set_speed(config.DEFAULT_SPEED)

    print(f"\n--- Testing {name} axis ---")
    print(f"  Speed: {config.DEFAULT_SPEED} microsteps/s")

    # Move positive
    steps = 400
    print(f"  Moving +{steps} microsteps...")
    motor.step(Stepper.POSITIVE, steps)
    print(f"  Position: {motor.position}")
    time.sleep(0.3)

    # Move negative
    print(f"  Moving -{steps} microsteps...")
    motor.step(Stepper.NEGATIVE, steps)
    print(f"  Position: {motor.position}")
    time.sleep(0.3)

    # Move to absolute position
    target = 200
    print(f"  Moving to position {target}...")
    motor.move_to(target)
    print(f"  Position: {motor.position}")
    time.sleep(0.3)

    # Return to zero
    print(f"  Returning to 0...")
    motor.move_to(0)
    print(f"  Position: {motor.position}")

    motor.disable()
    return motor


def test_speed_ramp(pi, step_pin, dir_pin, en_pin, name):
    """Test different speeds."""
    motor = Stepper(pi, step_pin, dir_pin, en_pin, name=name)
    motor.enable()

    print(f"\n--- Speed test ({name} axis) ---")
    speeds = [500, 1000, 2000, 4000, 8000]

    for speed in speeds:
        if speed > config.MAX_SPEED:
            continue
        motor.set_speed(speed)
        print(f"  Speed: {speed} µsteps/s ... ", end='', flush=True)
        start = time.perf_counter()
        motor.step(Stepper.POSITIVE, 800)
        elapsed = time.perf_counter() - start
        actual_speed = 800 / elapsed if elapsed > 0 else 0
        print(f"actual: {actual_speed:.0f} µsteps/s ({elapsed:.3f}s)")
        motor.step(Stepper.NEGATIVE, 800)
        time.sleep(0.2)

    motor.disable()


def test_square_pattern(pi):
    """Move both motors in a square pattern (no laser)."""
    from direct_laser.motor.galvo import Galvo

    galvo = Galvo(pi)
    galvo.enable()
    galvo.set_speed(2000)

    print("\n--- Square pattern (galvo) ---")
    corners = [
        (200, 200),
        (200, -200),
        (-200, -200),
        (-200, 200),
        (200, 200),  # close
    ]

    for i, (x, y) in enumerate(corners):
        print(f"  Corner {i+1}: ({x}, {y})...", end='', flush=True)
        galvo.move_to(x, y)
        pos = galvo.get_position()
        print(f" arrived at {pos}")
        time.sleep(0.3)

    print("  Returning home...")
    galvo.home()
    print(f"  Position: {galvo.get_position()}")

    galvo.disable()


def main():
    print("=== Motor Test ===")
    print(f"Motor X: STEP=GPIO{config.MOTOR_X_STEP}, DIR=GPIO{config.MOTOR_X_DIR}, EN=GPIO{config.MOTOR_X_EN}")
    print(f"Motor Y: STEP=GPIO{config.MOTOR_Y_STEP}, DIR=GPIO{config.MOTOR_Y_DIR}, EN=GPIO{config.MOTOR_Y_EN}")

    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Cannot connect to pigpiod. Is it running?")
        print("  Start with: sudo systemctl start pigpiod")
        sys.exit(1)

    try:
        # Test X axis
        test_single_axis(pi, config.MOTOR_X_STEP, config.MOTOR_X_DIR, config.MOTOR_X_EN, "X")

        # Test Y axis
        test_single_axis(pi, config.MOTOR_Y_STEP, config.MOTOR_Y_DIR, config.MOTOR_Y_EN, "Y")

        # Speed ramp test on X
        test_speed_ramp(pi, config.MOTOR_X_STEP, config.MOTOR_X_DIR, config.MOTOR_X_EN, "X")

        # Square pattern with both motors
        test_square_pattern(pi)

        print("\n=== All tests complete ===")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Ensure motors are disabled
        for en_pin in (config.MOTOR_X_EN, config.MOTOR_Y_EN):
            pi.write(en_pin, 1)
        pi.stop()
        print("Motors disabled, pigpio stopped.")


if __name__ == '__main__':
    main()

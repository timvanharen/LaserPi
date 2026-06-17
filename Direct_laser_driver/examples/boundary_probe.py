#!/usr/bin/env python3
"""
Interactive boundary calibration for galvo mirror assembly.

Flow per axis:
  1. Jog motor to the + mechanical limit using keyboard commands
  2. Confirm — this sets the + boundary
  3. Motor drifts slowly toward - direction; press ENTER to stop
  4. Fine-tune with small jog steps
  5. Confirm — this sets the - boundary
  6. Saves calibration to galvo_calibration.json

Run: python3 examples/boundary_probe.py
"""
import sys
import os
import time
import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pigpio
from direct_laser.motor.stepper import Stepper
from direct_laser.tmc2209_uart import TMC2209
from direct_laser import config


def check_keypress():
    """Non-blocking stdin check. Returns stripped line or None."""
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.readline().strip()
    return None


def jog_interface(motor, prompt):
    """
    Interactive jog loop. User moves the motor to a limit, then types 'ok'.

    Commands:
      +         → +10 µsteps
      ++        → +100 µsteps
      <N>+      → +N µsteps  (e.g. 50+)
      -         → -10 µsteps
      --        → -100 µsteps
      <N>-      → -N µsteps
      ok/ENTER  → confirm current position and exit
    """
    print(f"\n  Jog commands:  +/- = ±10    ++/-- = ±100    <N>+/<N>- = ±N steps")
    print(f"  Type 'ok' or press ENTER when at the limit.\n")

    while True:
        cmd = input(f"  {prompt}  pos={motor.position:+6d}  > ").strip().lower()

        if cmd in ('ok', '', 'done'):
            return motor.position
        elif cmd == '+':
            motor.step(Stepper.POSITIVE, 10)
        elif cmd == '++':
            motor.step(Stepper.POSITIVE, 100)
        elif cmd == '-':
            motor.step(Stepper.NEGATIVE, 10)
        elif cmd == '--':
            motor.step(Stepper.NEGATIVE, 100)
        elif cmd.endswith('+') and cmd[:-1].isdigit():
            motor.step(Stepper.POSITIVE, int(cmd[:-1]))
        elif cmd.endswith('-') and cmd[:-1].isdigit():
            motor.step(Stepper.NEGATIVE, int(cmd[:-1]))
        else:
            print(f"    Unknown: '{cmd}' — use +/- or 'ok'")


def drift_to_limit(motor, name):
    """
    Move motor slowly toward - direction until ENTER is pressed,
    then allow fine-tuning with small jog steps.
    Returns confirmed - limit position.
    """
    DRIFT_SPEED    = 150   # µsteps/s — slow enough to react in time
    DRIFT_BATCH    = 3     # µsteps per tick (keep small for responsiveness)

    motor.set_speed(DRIFT_SPEED)

    print(f"\n  Motor will drift slowly toward - direction.")
    print(f"  Press ENTER at any time to stop.")
    print(f"  Starting in 2 seconds...")
    time.sleep(2)

    # Flush any buffered input
    while check_keypress() is not None:
        pass

    print(f"  Drifting...  (ENTER to stop)\n")

    while True:
        motor.step(Stepper.NEGATIVE, DRIFT_BATCH)
        print(f"\r    pos={motor.position:+6d}  (ENTER to stop)", end='', flush=True)
        if check_keypress() is not None:
            print()
            break

    print(f"\n  Stopped at {motor.position}.")
    print(f"  Fine-tune to the exact - limit, then 'ok' to confirm.")

    motor.set_speed(150)
    return jog_interface(motor, f"{name}-limit")


def calibrate_axis(pi, step_pin, dir_pin, en_pin, name):
    """Full calibration for one axis. Returns (min_pos, max_pos) with safety margins."""
    motor = Stepper(pi, step_pin, dir_pin, en_pin, name=name)
    motor.enable()
    motor.set_speed(300)

    print(f"\n{'='*52}")
    print(f"  Calibrating {name} axis")
    print(f"{'='*52}")

    # Step 1: find + limit
    print(f"\nStep 1 — Jog to the + mechanical limit (mirror fully deflected one way).")
    max_pos = jog_interface(motor, f"{name}+limit")
    print(f"  ✓  {name}+ limit: {max_pos}")

    # Step 2: drift to - limit
    print(f"\nStep 2 — Motor will drift toward - limit.")
    min_pos = drift_to_limit(motor, name)
    print(f"  ✓  {name}- limit: {min_pos}")

    if min_pos >= max_pos:
        print(f"  WARNING: min ({min_pos}) >= max ({max_pos}). Swap direction or redo.")
        min_pos, max_pos = max_pos, min_pos

    # Apply 5% safety margins
    span   = max_pos - min_pos
    margin = int(span * 0.05)
    safe_min = min_pos + margin
    safe_max = max_pos - margin

    print(f"\n  Raw range:   {min_pos} to {max_pos}  ({span} µsteps)")
    print(f"  Safe range:  {safe_min} to {safe_max}  ({safe_max - safe_min} µsteps, 5% margins)")

    # Return to center
    center = (safe_min + safe_max) // 2
    print(f"  Returning to center ({center})...")
    motor.set_speed(1000)
    motor.move_to(center)
    motor.disable()

    return safe_min, safe_max


def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: pigpiod not running.  Run: sudo systemctl start pigpiod")
        sys.exit(1)

    print("\n=== Galvo Boundary Calibration ===")
    print("Finds the mechanical limits of each mirror axis.")
    print("SAFETY: Keep the beam path clear during calibration.\n")

    # Initialize TMC2209 drivers via UART
    print("Configuring TMC2209 drivers via UART...")
    try:
        tmc_x = TMC2209('/dev/ttyAMA0', address=0)  # X motor, address 0 (MS1=GND, MS2=GND)
        tmc_x.set_current_rms(400)     # 400mA limit
        tmc_x.set_microstepping(16)    # 16x microstepping
        tmc_x.set_pwm_autoscale(True)  # Smoother low-speed motion
        tmc_x.get_status()
        
        tmc_y = TMC2209('/dev/ttyAMA0', address=1)  # Y motor, address 1 (MS1=3.3V, MS2=GND)
        tmc_y.set_current_rms(400)     # 400mA limit
        tmc_y.set_microstepping(16)    # 16x microstepping
        tmc_y.set_pwm_autoscale(True)
        tmc_y.get_status()
        
        print("✓ TMC2209 drivers configured.\n")
    except Exception as e:
        print(f"WARNING: Could not configure TMC2209 via UART: {e}")
        print("Continuing with GPIO-only control (current limit may not be set).\n")

    results = {}

    try:
        for name, step, dir_, en in [
            ('X', config.MOTOR_X_STEP, config.MOTOR_X_DIR, config.MOTOR_X_EN),
            ('Y', config.MOTOR_Y_STEP, config.MOTOR_Y_DIR, config.MOTOR_Y_EN),
        ]:
            ans = input(f"Calibrate {name} axis? [Y/n]: ").strip().lower()
            if ans == 'n':
                print(f"  Skipping {name}.")
                continue

            safe_min, safe_max = calibrate_axis(pi, step, dir_, en, name)
            results[name] = (safe_min, safe_max)
            print(f"\n  {name}: {safe_min} to {safe_max}  ✓\n")

        if not results:
            print("No axes calibrated. Nothing saved.")
            return

        # Build calibration dict, keeping existing values for skipped axes
        existing = config.load_calibration()
        cal = {
            'x_min': results['X'][0] if 'X' in results else existing.get('x_min', -1600),
            'x_max': results['X'][1] if 'X' in results else existing.get('x_max',  1600),
            'y_min': results['Y'][0] if 'Y' in results else existing.get('y_min', -1600),
            'y_max': results['Y'][1] if 'Y' in results else existing.get('y_max',  1600),
        }

        config.save_calibration(cal)
        print(f"\n✓ Saved to galvo_calibration.json")
        print(f"  X: {cal['x_min']} → {cal['x_max']}")
        print(f"  Y: {cal['y_min']} → {cal['y_max']}")
        print("\n=== Done ===")

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    finally:
        for en_pin in (config.MOTOR_X_EN, config.MOTOR_Y_EN):
            pi.write(en_pin, 1)  # Disable both motors
        pi.stop()


if __name__ == '__main__':
    main()



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

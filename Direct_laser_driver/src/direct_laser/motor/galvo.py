"""
Coordinated X/Y galvo controller using two stepper motors.
Maps normalized coordinates to microstep positions.
"""
from .. import config
from .stepper import Stepper


class Galvo:
    """
    Coordinated X/Y mirror positioning using two stepper motors.

    Uses a normalized coordinate system (-1.0 to 1.0) that maps to the
    calibrated microstep range. (0, 0) is the center of the scan area.

    Args:
        pi: pigpio.pi instance
    """

    def __init__(self, pi):
        self._pi = pi

        self.x_motor = Stepper(
            pi,
            step_pin=config.MOTOR_X_STEP,
            dir_pin=config.MOTOR_X_DIR,
            enable_pin=config.MOTOR_X_EN,
            name="X",
        )
        self.y_motor = Stepper(
            pi,
            step_pin=config.MOTOR_Y_STEP,
            dir_pin=config.MOTOR_Y_DIR,
            enable_pin=config.MOTOR_Y_EN,
            name="Y",
        )

        # Load calibration boundaries
        cal = config.load_calibration()
        self._x_min = cal['x_min']
        self._x_max = cal['x_max']
        self._y_min = cal['y_min']
        self._y_max = cal['y_max']

        self.x_motor.set_boundaries(self._x_min, self._x_max)
        self.y_motor.set_boundaries(self._y_min, self._y_max)

    def enable(self):
        """Enable both motor drivers."""
        self.x_motor.enable()
        self.y_motor.enable()

    def disable(self):
        """Disable both motor drivers (release holding torque)."""
        self.x_motor.disable()
        self.y_motor.disable()

    def set_speed(self, speed):
        """Set speed for both axes (microsteps per second)."""
        self.x_motor.set_speed(speed)
        self.y_motor.set_speed(speed)

    def get_position(self):
        """Return current position as (x, y) in microsteps."""
        return (self.x_motor.position, self.y_motor.position)

    def get_position_normalized(self):
        """Return current position as (x, y) normalized to -1.0..1.0."""
        x = self._microsteps_to_normalized(self.x_motor.position, self._x_min, self._x_max)
        y = self._microsteps_to_normalized(self.y_motor.position, self._y_min, self._y_max)
        return (x, y)

    def move_to(self, x, y):
        """
        Move to an absolute position in microsteps.

        Uses linear interpolation (Bresenham-style) to move both axes
        simultaneously, producing straight-line motion.

        Args:
            x: Target X position in microsteps
            y: Target Y position in microsteps
        """
        dx = x - self.x_motor.position
        dy = y - self.y_motor.position

        if dx == 0 and dy == 0:
            return

        # For simultaneous movement, interleave steps on both axes.
        # The axis with more steps to travel is the "major" axis.
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        steps = max(abs_dx, abs_dy)

        if steps == 0:
            return

        # Determine direction
        x_dir = Stepper.POSITIVE if dx >= 0 else Stepper.NEGATIVE
        y_dir = Stepper.POSITIVE if dy >= 0 else Stepper.NEGATIVE

        self._pi.write(self.x_motor._dir_pin, x_dir)
        self._pi.write(self.y_motor._dir_pin, y_dir)

        # Bresenham-style interpolation for coordinated movement
        x_err = 0
        y_err = 0
        x_sign = 1 if dx >= 0 else -1
        y_sign = 1 if dy >= 0 else -1

        # Calculate step delay from the faster axis
        speed = min(self.x_motor._speed, self.y_motor._speed)
        delay_us = max(1, int(1_000_000 / speed))
        pulse_us = config.STEP_PULSE_WIDTH_US

        import time

        for _ in range(steps):
            x_err += abs_dx
            y_err += abs_dy

            step_x = False
            step_y = False

            if x_err >= steps:
                x_err -= steps
                step_x = True

            if y_err >= steps:
                y_err -= steps
                step_y = True

            # Generate pulses
            if step_x and step_y:
                # Step both simultaneously
                self._pi.write(self.x_motor._step_pin, 1)
                self._pi.write(self.y_motor._step_pin, 1)
                time.sleep(pulse_us / 1_000_000)
                self._pi.write(self.x_motor._step_pin, 0)
                self._pi.write(self.y_motor._step_pin, 0)
                self.x_motor._position += x_sign
                self.y_motor._position += y_sign
            elif step_x:
                self._pi.gpio_trigger(self.x_motor._step_pin, pulse_us, 1)
                self.x_motor._position += x_sign
            elif step_y:
                self._pi.gpio_trigger(self.y_motor._step_pin, pulse_us, 1)
                self.y_motor._position += y_sign

            remaining = delay_us - pulse_us
            if remaining > 0:
                time.sleep(remaining / 1_000_000)

    def move_to_normalized(self, x, y):
        """
        Move to a position given in normalized coordinates (-1.0 to 1.0).

        Args:
            x: X position, -1.0 (min) to 1.0 (max)
            y: Y position, -1.0 (min) to 1.0 (max)
        """
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))

        x_steps = self._normalized_to_microsteps(x, self._x_min, self._x_max)
        y_steps = self._normalized_to_microsteps(y, self._y_min, self._y_max)

        self.move_to(x_steps, y_steps)

    def home(self):
        """Move to center position (0, 0)."""
        self.move_to(0, 0)

    def reload_calibration(self):
        """Reload boundary calibration from the config file."""
        cal = config.load_calibration()
        self._x_min = cal['x_min']
        self._x_max = cal['x_max']
        self._y_min = cal['y_min']
        self._y_max = cal['y_max']
        self.x_motor.set_boundaries(self._x_min, self._x_max)
        self.y_motor.set_boundaries(self._y_min, self._y_max)

    def get_status(self):
        """Return a dict of current galvo state."""
        return {
            'x': self.x_motor.get_status(),
            'y': self.y_motor.get_status(),
            'boundaries': {
                'x_min': self._x_min, 'x_max': self._x_max,
                'y_min': self._y_min, 'y_max': self._y_max,
            },
        }

    @staticmethod
    def _normalized_to_microsteps(val, min_pos, max_pos):
        """Convert a -1.0..1.0 value to microsteps within [min_pos, max_pos]."""
        center = (min_pos + max_pos) / 2
        half_range = (max_pos - min_pos) / 2
        return int(center + val * half_range)

    @staticmethod
    def _microsteps_to_normalized(steps, min_pos, max_pos):
        """Convert microsteps to a -1.0..1.0 normalized value."""
        center = (min_pos + max_pos) / 2
        half_range = (max_pos - min_pos) / 2
        if half_range == 0:
            return 0.0
        return (steps - center) / half_range

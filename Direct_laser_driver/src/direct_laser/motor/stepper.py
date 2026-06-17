"""
Single-axis stepper motor driver using pigpio for hardware-timed step pulses.
Designed for TMC2209-based ATD5833 driver boards.
"""
import time
import math
import pigpio

from .. import config


class Stepper:
    """
    Controls a single stepper motor axis via STEP/DIR/EN pins.

    Uses pigpio wave generation for precise, DMA-timed step pulses
    that don't suffer from Linux scheduler jitter.

    Args:
        pi: pigpio.pi instance (connected to pigpiod)
        step_pin: BCM GPIO number for STEP signal
        dir_pin: BCM GPIO number for DIR signal
        enable_pin: BCM GPIO number for ENABLE signal (active LOW)
        name: Friendly name for this axis (e.g., "X" or "Y")
    """

    # Direction constants
    POSITIVE = 1
    NEGATIVE = 0

    def __init__(self, pi, step_pin, dir_pin, enable_pin, name="stepper"):
        if not pi.connected:
            raise RuntimeError("pigpio not connected — is pigpiod running?")

        self._pi = pi
        self._step_pin = step_pin
        self._dir_pin = dir_pin
        self._enable_pin = enable_pin
        self.name = name

        self._position = 0      # Current position in microsteps (signed)
        self._enabled = False
        self._speed = config.DEFAULT_SPEED  # Microsteps per second
        self._min_pos = None     # Boundary limits (None = unlimited)
        self._max_pos = None

        # Configure GPIO modes
        self._pi.set_mode(self._step_pin, pigpio.OUTPUT)
        self._pi.set_mode(self._dir_pin, pigpio.OUTPUT)
        self._pi.set_mode(self._enable_pin, pigpio.OUTPUT)

        # Start disabled (EN HIGH = disabled on TMC2209)
        self._pi.write(self._enable_pin, 1)
        self._pi.write(self._step_pin, 0)
        self._pi.write(self._dir_pin, 0)

    @property
    def position(self):
        """Current position in microsteps."""
        return self._position

    @property
    def enabled(self):
        """Whether the motor driver is enabled."""
        return self._enabled

    def set_boundaries(self, min_pos, max_pos):
        """
        Set movement boundaries in microsteps.

        Args:
            min_pos: Minimum allowed position (inclusive)
            max_pos: Maximum allowed position (inclusive)

        Raises:
            ValueError: If min_pos >= max_pos
        """
        if min_pos >= max_pos:
            raise ValueError(f"min_pos ({min_pos}) must be less than max_pos ({max_pos})")
        self._min_pos = min_pos
        self._max_pos = max_pos

    def clear_boundaries(self):
        """Remove movement boundaries."""
        self._min_pos = None
        self._max_pos = None

    def set_speed(self, speed):
        """
        Set movement speed in microsteps per second.

        Args:
            speed: Microsteps per second (1 to MAX_SPEED)

        Raises:
            ValueError: If speed is out of range
        """
        if not 1 <= speed <= config.MAX_SPEED:
            raise ValueError(f"Speed must be 1-{config.MAX_SPEED}, got {speed}")
        self._speed = speed

    def enable(self):
        """Enable the motor driver (engages holding torque)."""
        self._pi.write(self._enable_pin, 0)  # Active LOW
        self._enabled = True

    def disable(self):
        """Disable the motor driver (releases holding torque)."""
        self._pi.write(self._enable_pin, 1)  # HIGH = disabled
        self._enabled = False

    def set_position(self, position):
        """Override the current position counter without moving the motor."""
        self._position = position

    def step(self, direction, count):
        """
        Move a specified number of microsteps in the given direction.

        Uses pigpio waveforms for precise timing. Implements trapezoidal
        acceleration/deceleration ramp for smooth motion.

        Args:
            direction: Stepper.POSITIVE or Stepper.NEGATIVE
            count: Number of microsteps to move

        Raises:
            RuntimeError: If motor is not enabled
        """
        if not self._enabled:
            raise RuntimeError(f"Motor '{self.name}' is not enabled")
        if count <= 0:
            return

        # Check boundaries
        sign = 1 if direction == self.POSITIVE else -1
        target = self._position + sign * count
        if self._min_pos is not None and target < self._min_pos:
            count = max(0, abs(self._position - self._min_pos))
            if count == 0:
                return
        if self._max_pos is not None and target > self._max_pos:
            count = max(0, abs(self._max_pos - self._position))
            if count == 0:
                return

        # Set direction
        self._pi.write(self._dir_pin, direction)
        time.sleep(0.000005)  # 5 µs direction setup time

        # Generate step pulses with acceleration ramp
        self._execute_ramp(count, sign)

    def _execute_ramp(self, total_steps, sign):
        """
        Execute steps with trapezoidal acceleration profile using DMA waveforms.

        pigpio waveforms are timed by the DMA engine, bypassing Linux scheduler
        jitter entirely. This gives accurate step timing at all speeds.
        """
        if total_steps == 0:
            return

        accel = config.ACCELERATION
        target_speed = self._speed
        min_speed = max(200, target_speed // 20)

        # Calculate ramp steps: v² = v0² + 2*a*s → s = (v²-v0²)/(2a)
        ramp_steps = int((target_speed ** 2 - min_speed ** 2) / (2 * accel))
        ramp_steps = min(ramp_steps, total_steps // 2)

        cruise_steps = total_steps - 2 * ramp_steps
        if cruise_steps < 0:
            ramp_steps = total_steps // 2
            cruise_steps = total_steps - 2 * ramp_steps

        pulse_us = config.STEP_PULSE_WIDTH_US
        step_bit = 1 << self._step_pin

        # Build pulse list — each step = 2 pigpio pulses (HIGH then LOW)
        pulses = []

        def add_step(delay_us):
            pulses.append(pigpio.pulse(step_bit, 0, pulse_us))
            pulses.append(pigpio.pulse(0, step_bit, max(1, delay_us - pulse_us)))

        for i in range(ramp_steps):
            speed = min_speed + (target_speed - min_speed) * (i + 1) / ramp_steps
            add_step(int(1_000_000 / speed))

        cruise_delay = int(1_000_000 / target_speed)
        for _ in range(cruise_steps):
            add_step(cruise_delay)

        for i in range(ramp_steps):
            speed = target_speed - (target_speed - min_speed) * (i + 1) / ramp_steps
            add_step(int(1_000_000 / max(min_speed, speed)))

        # Send via DMA in batches (pigpio wave limit is ~12000 pulses = 6000 steps)
        MAX_PULSES = 10000  # 5000 steps per wave, leaving headroom
        total_sent = 0

        for i in range(0, len(pulses), MAX_PULSES):
            batch = pulses[i:i + MAX_PULSES]
            self._pi.wave_add_generic(batch)
            wid = self._pi.wave_create()
            if wid < 0:
                # Fallback: software timing for this batch
                for j in range(0, len(batch), 2):
                    self._pi.gpio_trigger(self._step_pin, pulse_us, 1)
                    time.sleep(max(0, (batch[j + 1].delay) / 1_000_000))
            else:
                self._pi.wave_send_once(wid)
                while self._pi.wave_tx_busy():
                    time.sleep(0.001)
                self._pi.wave_delete(wid)
            total_sent += len(batch) // 2

        self._position += sign * total_sent

    def move_to(self, target):
        """
        Move to an absolute position in microsteps.

        Args:
            target: Target position in microsteps (signed)
        """
        delta = target - self._position
        if delta == 0:
            return
        direction = self.POSITIVE if delta > 0 else self.NEGATIVE
        self.step(direction, abs(delta))

    def move_relative(self, delta):
        """
        Move by a relative number of microsteps.

        Args:
            delta: Signed number of microsteps (+ve = positive direction)
        """
        if delta == 0:
            return
        direction = self.POSITIVE if delta > 0 else self.NEGATIVE
        self.step(direction, abs(delta))

    def get_status(self):
        """Return a dict of current motor state."""
        return {
            'name': self.name,
            'position': self._position,
            'enabled': self._enabled,
            'speed': self._speed,
            'min_pos': self._min_pos,
            'max_pos': self._max_pos,
        }

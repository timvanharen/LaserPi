"""
RGB laser driver using pigpio PWM for GPIO-driven laser diode control.
Supports per-channel intensity (0-255) and DPSS green on/off mode.
"""
from contextlib import contextmanager
from enum import IntEnum

import pigpio

from .. import config


class Color(IntEnum):
    """Preset color indices for quick selection."""
    OFF = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4
    CYAN = 5
    MAGENTA = 6
    WHITE = 7


# Color presets as (R, G, B) tuples, 0-255
COLOR_PRESETS = {
    Color.OFF:     (0, 0, 0),
    Color.RED:     (255, 0, 0),
    Color.GREEN:   (0, 255, 0),
    Color.BLUE:    (0, 0, 255),
    Color.YELLOW:  (255, 255, 0),
    Color.CYAN:    (0, 255, 255),
    Color.MAGENTA: (255, 0, 255),
    Color.WHITE:   (255, 255, 255),
}

# Name-based lookup
COLOR_NAMES = {c.name.lower(): c for c in Color}


class RGBLaser:
    """
    Controls three laser diodes (R, G, B) via GPIO PWM.

    Uses pigpio's DMA-timed PWM for stable, jitter-free dimming on any GPIO pin.
    The green channel is configured as on/off only by default (DPSS module behavior).

    Args:
        pi: pigpio.pi instance (connected to pigpiod)
    """

    def __init__(self, pi):
        if not pi.connected:
            raise RuntimeError("pigpio not connected — is pigpiod running?")

        self._pi = pi
        self._red_pin = config.LASER_RED_PIN
        self._green_pin = config.LASER_GREEN_PIN
        self._blue_pin = config.LASER_BLUE_PIN
        self._enable_pin = config.LASER_ENABLE_PIN

        self._red = 0
        self._green = 0
        self._blue = 0
        self._master_on = False
        self._dpss_mode = config.LASER_GREEN_DPSS_MODE

        # Configure all laser pins as outputs, start LOW (off)
        for pin in (self._red_pin, self._green_pin, self._blue_pin, self._enable_pin):
            self._pi.set_mode(pin, pigpio.OUTPUT)
            self._pi.write(pin, 0)

        # Set PWM frequency
        for pin in (self._red_pin, self._green_pin, self._blue_pin):
            self._pi.set_PWM_frequency(pin, config.LASER_PWM_FREQUENCY)
            self._pi.set_PWM_range(pin, 255)
            self._pi.set_PWM_dutycycle(pin, 0)

    def on(self):
        """Enable the master laser output."""
        self._pi.write(self._enable_pin, 1)
        self._master_on = True
        self._apply()

    def off(self):
        """Disable all laser output immediately."""
        for pin in (self._red_pin, self._green_pin, self._blue_pin):
            self._pi.set_PWM_dutycycle(pin, 0)
        self._pi.write(self._enable_pin, 0)
        self._master_on = False

    def set_color(self, r, g, b):
        """
        Set laser color as RGB values (0-255 per channel).

        For the green DPSS channel in DPSS mode, any value > 0 is treated as full-on.

        Args:
            r: Red intensity (0-255)
            g: Green intensity (0-255)
            b: Blue intensity (0-255)
        """
        self._red = self._clamp(r)
        self._green = self._clamp(g)
        self._blue = self._clamp(b)
        if self._master_on:
            self._apply()

    def set_color_preset(self, color):
        """
        Set color from a Color enum preset.

        Args:
            color: Color enum value or string name
        """
        if isinstance(color, str):
            color = COLOR_NAMES.get(color.lower())
            if color is None:
                raise ValueError(f"Unknown color name. Options: {list(COLOR_NAMES.keys())}")
        r, g, b = COLOR_PRESETS[color]
        self.set_color(r, g, b)

    def set_red(self, value):
        """Set red channel intensity (0-255)."""
        self._red = self._clamp(value)
        if self._master_on:
            self._apply_channel(self._red_pin, self._red, config.LASER_RED_MAX_DUTY)

    def set_green(self, value):
        """Set green channel intensity (0-255). In DPSS mode, >0 = full-on."""
        self._green = self._clamp(value)
        if self._master_on:
            self._apply_green()

    def set_blue(self, value):
        """Set blue channel intensity (0-255)."""
        self._blue = self._clamp(value)
        if self._master_on:
            self._apply_channel(self._blue_pin, self._blue, config.LASER_BLUE_MAX_DUTY)

    def get_color(self):
        """Return current color as (r, g, b) tuple."""
        return (self._red, self._green, self._blue)

    @contextmanager
    def blanked(self):
        """
        Context manager that temporarily turns the laser off.

        Used during galvo repositioning to prevent stray beams.

        Example:
            with laser.blanked():
                galvo.move_to(new_x, new_y)
            # Laser restores previous color on exit
        """
        saved = (self._red, self._green, self._blue)
        was_on = self._master_on
        # Kill output immediately
        for pin in (self._red_pin, self._green_pin, self._blue_pin):
            self._pi.set_PWM_dutycycle(pin, 0)
        try:
            yield
        finally:
            # Restore color
            self._red, self._green, self._blue = saved
            if was_on:
                self._apply()

    def get_status(self):
        """Return a dict of current laser state."""
        return {
            'red': self._red,
            'green': self._green,
            'blue': self._blue,
            'master_on': self._master_on,
            'dpss_mode': self._dpss_mode,
        }

    def _apply(self):
        """Apply current color to all channels."""
        self._apply_channel(self._red_pin, self._red, config.LASER_RED_MAX_DUTY)
        self._apply_green()
        self._apply_channel(self._blue_pin, self._blue, config.LASER_BLUE_MAX_DUTY)

    def _apply_green(self):
        """Apply green channel with DPSS mode handling."""
        if self._dpss_mode:
            # DPSS: on/off only — any value > 0 is treated as full-on
            duty = config.LASER_GREEN_MAX_DUTY if self._green > 0 else 0
        else:
            duty = int(self._green * config.LASER_GREEN_MAX_DUTY / 255)
        self._pi.set_PWM_dutycycle(self._green_pin, duty)

    def _apply_channel(self, pin, value, max_duty):
        """Apply a PWM value to a channel, scaled by max duty."""
        duty = int(value * max_duty / 255)
        self._pi.set_PWM_dutycycle(pin, duty)

    @staticmethod
    def _clamp(value):
        """Clamp a value to 0-255."""
        return max(0, min(255, int(value)))

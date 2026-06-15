"""
Configuration constants for Direct Laser Driver
"""
import os
import json

# ---------------------------------------------------------------------------
# GPIO Pin Assignments (BCM numbering)
# ---------------------------------------------------------------------------

# Motor X (mirror tilt axis 1)
MOTOR_X_STEP = 17
MOTOR_X_DIR = 18
MOTOR_X_EN = 4

# Motor Y (mirror tilt axis 2)
MOTOR_Y_STEP = 27
MOTOR_Y_DIR = 22
MOTOR_Y_EN = 5

# TMC2209 UART (shared bus, drivers addressed via MS1/MS2 at boot)
TMC_UART_TX = 14
TMC_UART_RX = 15
TMC_UART_BAUD = 115200

# Laser RGB PWM outputs
LASER_RED_PIN = 23
LASER_GREEN_PIN = 24
LASER_BLUE_PIN = 25

# Laser master enable (active HIGH — drives a MOSFET that gates 12V to all drivers)
LASER_ENABLE_PIN = 6

# ---------------------------------------------------------------------------
# Motor Parameters
# ---------------------------------------------------------------------------

STEPS_PER_REV = 200           # 1.8° step angle
MICROSTEPPING = 16            # TMC2209 microstep setting (8, 16, 32, 64)
MICROSTEPS_PER_REV = STEPS_PER_REV * MICROSTEPPING  # 3200

# Speed and acceleration
MAX_SPEED = 8000              # Maximum microsteps per second
DEFAULT_SPEED = 4000          # Default microsteps per second
ACCELERATION = 20000          # Microsteps per second² for ramp-up/down

# Step pulse timing (microseconds)
STEP_PULSE_WIDTH_US = 5       # Minimum pulse width for TMC2209 is 100 ns; 5 µs is safe

# TMC2209 UART addresses (set by MS1/MS2 at boot)
TMC_X_ADDRESS = 0             # MS1=GND, MS2=GND
TMC_Y_ADDRESS = 1             # MS1=VCC, MS2=GND

# TMC2209 motor current (RMS milliamps)
MOTOR_CURRENT_RUN = 400       # Running current (mA RMS) — max for 39BYG101-1
MOTOR_CURRENT_HOLD = 200      # Holding current (mA RMS)

# ---------------------------------------------------------------------------
# Boundary Limits (microstep positions)
# Populated after running boundary_probe.py calibration
# ---------------------------------------------------------------------------

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'galvo_calibration.json')

# Default boundaries (before calibration) — conservative symmetric range
DEFAULT_X_MIN = -800
DEFAULT_X_MAX = 800
DEFAULT_Y_MIN = -800
DEFAULT_Y_MAX = 800


def load_calibration():
    """Load boundary calibration from JSON file, or return defaults."""
    try:
        with open(CALIBRATION_FILE, 'r') as f:
            data = json.load(f)
        return {
            'x_min': data.get('x_min', DEFAULT_X_MIN),
            'x_max': data.get('x_max', DEFAULT_X_MAX),
            'y_min': data.get('y_min', DEFAULT_Y_MIN),
            'y_max': data.get('y_max', DEFAULT_Y_MAX),
        }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {
            'x_min': DEFAULT_X_MIN,
            'x_max': DEFAULT_X_MAX,
            'y_min': DEFAULT_Y_MIN,
            'y_max': DEFAULT_Y_MAX,
        }


def save_calibration(x_min, x_max, y_min, y_max):
    """Save boundary calibration to JSON file."""
    data = {
        'x_min': x_min,
        'x_max': x_max,
        'y_min': y_min,
        'y_max': y_max,
    }
    with open(CALIBRATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Laser Parameters
# ---------------------------------------------------------------------------

LASER_PWM_FREQUENCY = 5000    # Hz (5 kHz — no flicker, no audible noise)

# Maximum PWM duty cycle per channel (0-255 → 0-100%)
# Tweak these after measuring actual laser output with a power meter
LASER_RED_MAX_DUTY = 255
LASER_GREEN_MAX_DUTY = 255
LASER_BLUE_MAX_DUTY = 255

# Green DPSS mode: True = on/off only (values > 0 treated as full-on)
# Set to False if you replace the green DPSS with a direct green diode
LASER_GREEN_DPSS_MODE = True

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

# Settle time after moving to a new position before turning laser on (seconds)
BLANKING_SETTLE_TIME = 0.001  # 1 ms — adjust based on mechanical response

# Minimum time the laser stays on at each point (seconds)
MIN_POINT_DWELL_TIME = 0.0005  # 0.5 ms

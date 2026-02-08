"""
Configuration constants for LaserPi
"""
import os

# Serial port configuration
SERIAL_PORT = os.getenv("DMX_SERIAL_PORT", "/dev/ttyUSB0")
DMX_BAUD = 250000  # DMX512 standard baud rate
DMX_REFRESH_HZ = 40  # DMX packet refresh rate (25-44 Hz is typical)

# Laser DMX addresses
LASER1_ADDRESS = 1  # First MK2 laser base address
LASER2_ADDRESS = 10  # Second MK2 laser base address

# Hazer/Smoke generator DMX address
HAZER_ADDRESS = 21  # Hazer base address

# DMX timing (microseconds)
DMX_BREAK_TIME_US = 150  # Break signal duration (min 92 μs)
DMX_MAB_TIME_US = 12  # Mark After Break duration (min 12 μs)

# Number of channels to transmit (optimize for 2 lasers × 9 channels + hazer)
DMX_CHANNEL_COUNT = 21  # Covers addresses 1-21

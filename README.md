# LaserPi

DMX controller for Raspberry Pi 4 to control Laserworld EL-230RGB MK2 lasers

## Overview

LaserPi is a Python-based DMX512 controller designed to run on a Raspberry Pi 4 Model B. It controls two Laserworld EL-230RGB MK2 lasers via USB-to-RS485 interface, enabling programmatic control of laser patterns, colors, positions, and effects.

## Hardware Requirements

- **Raspberry Pi 4 Model B** (hostname: `laserpi`)
- **USB to RS485 adapter** (CH340, FTDI FT232, or CP2102)
- **Two Laserworld EL-230RGB MK2 lasers**
  - Laser 1: DMX address 1
  - Laser 2: DMX address 10
- **DMX cables** (3-pin or 5-pin XLR)
- **120Ω termination resistor** (at end of DMX chain, if not built into last fixture)

## Wiring

### XLR-3 DMX Connector Pinout

```
XLR-3 Male (looking at pins):
  1   Ground/Common (Shield)
  2   Data- (DMX Data Complement)
  3   Data+ (DMX Data True)
```

### Connection Diagram

```
Raspberry Pi USB port
    |
    +--> USB-to-RS485 Adapter
             |
             +--> RS485 A (D+) → XLR Pin 3 (Data+)
             +--> RS485 B (D-) → XLR Pin 2 (Data-)
             +--> Ground       → XLR Pin 1 (Common)
                      |
                      +--> Laser 1 (DMX In, address 1)
                               |
                               +--> DMX Out → Laser 2 (DMX In, address 10)
```

⚠️ **Important Notes**:
- Ensure lasers are set to DMX mode with correct addresses (1 and 10)
- **If lasers don't respond, try swapping RS485 A/B wires** - polarity labeling varies between adapters
- Use proper DMX cable (not standard mic cable) for reliable operation

## MK2 DMX Channel Map

Each MK2 laser uses 9 DMX channels:

| Channel | Range | Function |
|---------|-------|----------|
| 1 | 0-49 | Laser off |
| | 50-99 | Sound mode |
| | 100-149 | Automatic mode |
| | 150-199 | **Static pattern** (DMX mode) |
| | 200-255 | **Dynamic pattern** (DMX mode) |
| 2 | 0-255 | Pattern selection |
| 3 | 1-10 | Center position on X axis |
| | 11-255 | X axis positioning |
| 4 | 1-10 | Center position on Y axis |
| | 11-255 | Y axis positioning |
| 5 | 0-255 | Scanning speed (mirror movement speed) |
| 6 | 0-255 | Dynamic pattern speed (pattern change rate) |
| 7 | 0-255 | Zoom / size |
| 8 | 0-255 | Color |
| 9 | 0-255 | Color segment |

📖 Full manual: [docs/MK2_manual.pdf](docs/MK2_manual.pdf)

## Installation

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/LaserPi.git
cd LaserPi
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```

This script will:
- Set hostname to `laserpi` (optional)
- Add your user to the `dialout` group
- Create udev rules for stable device naming (`/dev/dmx0`)
- Install Python dependencies from `requirements.txt`
- Verify USB adapter detection

**Important**: Log out and back in after running the setup script (for group membership to take effect).

### 3. Manual Installation (Alternative)

```bash
# Install dependencies
pip3 install --user -r requirements.txt

# Add user to dialout group
sudo usermod -aG dialout $USER

# Log out and back in
```

## Configuration

Edit [src/laserpi/config.py](src/laserpi/config.py) if needed:

```python
SERIAL_PORT = "/dev/ttyUSB0"  # or "/dev/dmx0" if udev rule is active
DMX_REFRESH_HZ = 40           # DMX packet rate (25-44 Hz typical)
LASER1_ADDRESS = 1            # First laser DMX address
LASER2_ADDRESS = 10           # Second laser DMX address
```

## Usage

### Example Scripts

All examples are in the [examples/](examples/) directory.

#### 1. Basic Control Test

Turn on both lasers in static pattern mode:

```bash
cd examples
python3 basic_on.py
```

This runs for 10 seconds with both lasers showing pattern 0, centered, white color.

#### 2. Pattern Scanner

Interactively cycle through all 256 pattern values to discover which patterns create circles or other shapes:

```bash
python3 pattern_scan.py
```

Controls:
- `[Enter]` - Next pattern
- `[Number]` - Jump to specific pattern
- `q` - Quit

**Take notes** of interesting pattern numbers (especially circles) for later use!

#### 3. Circle Pattern Control

Once you've found a good circle pattern, use this script for interactive control:

```bash
python3 circle_test.py
```

Commands:
- `p [0-255]` - Set pattern number
- `c [0-255]` - Set color
- `z [0-255]` - Set zoom/size
- `s [0-255]` - Set scanning speed
- `x [1-255]` - Set X position
- `y [1-255]` - Set Y position
- `center` - Center both lasers
- `status` - Show current settings
- `q` - Quit

#### 4. RS485 Communication Test

Test if your USB-RS485 adapter is working before trying DMX:

```bash
python3 test_rs485.py
```

This sends "hej bro" every second at 9600 baud. If you see no errors, your adapter is working. You can verify reception with another RS485 device or a USB-serial adapter in receive mode.

#### 5. Color & Color Segment Explorer

Understand what Channel 8 (Color) and Channel 9 (Color Segment) do:

```bash
python3 color_test.py
```

Commands:
- `c [0-255]` - Set color
- `s [0-255]` - Set color segment
- `scan-c` - Auto-scan through all color values
- `scan-s` - Auto-scan through all color segment values
- `scan-both` - Scan both simultaneously
- `p [0-255]` - Change pattern to see effects on different patterns

**What these channels typically do:**
- **Channel 8 (Color)**: Selects color from a palette (0=Red → 64=Green → 128=Blue → 192=White, approximately)
- **Channel 9 (Color Segment)**: Controls which parts of the pattern are colored vs. blank, or may enable multicolor effects
- Behavior varies by pattern - experiment to find what works best!

### Python API

Create your own scripts using the LaserPi API:

```python
import sys
sys.path.insert(0, '../src')

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
from laserpi.config import LASER1_ADDRESS, LASER2_ADDRESS
import time

# Initialize
universe = DMXUniverse()
driver = DMXDriver()

# Create laser controllers
laser1 = MK2(universe, LASER1_ADDRESS, name="Laser 1")
laser2 = MK2(universe, LASER2_ADDRESS, name="Laser 2")

# Start DMX transmission (40 Hz continuous update)
driver.start(universe)
time.sleep(0.5)

# Configure laser 1
laser1.set_mode(MK2Mode.STATIC_PATTERN)
laser1.set_pattern(42)  # Use pattern number you discovered
laser1.center()
laser1.set_color(255)
laser1.set_zoom(128)
laser1.set_scanning_speed(128)

# Run for 10 seconds
time.sleep(10)

# Cleanup
laser1.off()
laser2.off()
driver.stop()
```

## Project Structure

```
LaserPi/
├── src/laserpi/
│   ├── dmx/
│   │   ├── driver.py       # DMX512 serial driver
│   │   └── universe.py     # 512-channel DMX buffer
│   ├── laser/
│   │   └── mk2.py          # MK2 laser abstraction
│   ├── effects/
│   │   └── shapes.py       # Shape generation helpers
│   └── config.py           # Configuration constants
├── examples/
│   ├── basic_on.py         # Basic control test
│   ├── pattern_scan.py     # Pattern discovery tool (static & dynamic)
│   ├── circle_test.py      # Interactive circle control
│   ├── color_test.py       # Color & color segment explorer
│   └── test_rs485.py       # RS485 communication test
├── scripts/
│   └── setup_pi.sh         # Raspberry Pi setup script
├── docs/
│   └── MK2_manual.pdf      # Laser manual
├── CONTRIBUTING.md         # How to contribute your discoveries
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### RS485 adapter not working

**First, test basic communication:**
```bash
python3 examples/test_rs485.py
```

If this shows errors, the issue is with the adapter/port, not DMX protocol.

### No `/dev/ttyUSB0` device

1. Check USB adapter is connected: `lsusb`
2. Check kernel messages: `dmesg | grep tty`
3. Verify user is in `dialout` group: `groups`

### Lasers not responding

1. **Check wiring**: Verify RS485 A/B polarity (swap if needed)
2. **Check DMX addresses**: Lasers must be set to address 1 and 10
3. **Check laser mode**: Lasers must be in DMX mode (not standalone/sound mode)
4. **Check termination**: Add 120Ω resistor between Data+/Data- at last laser
5. **Test with simple commands**:
   ```python
   laser1.set_mode(MK2Mode.STATIC_PATTERN)
   laser1.set_pattern(0)
   # Laser should light up immediately
   ```

### Permission denied on serial port

```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Log out and back in
```

### DMX timing issues

If patterns flicker or lasers reset randomly, the break signal timing may be off. Try adjusting in [config.py](src/laserpi/config.py):

```python
DMX_BREAK_TIME_US = 200  # Increase if needed (min 92 μs, max ~1000 μs)
```

## Goals

- ✅ Generate DMX commands from Raspberry Pi
- ✅ Control two MK2 lasers independently
- ✅ Discover and control circular patterns via Channel 2
- 🎯 Fine-tune colors, position, zoom, and speed for circles
- 🎯 Attempt to create custom shapes or logo patterns (experimental)

## Contributing

Found interesting patterns? Discovered what the color channels do? **Please share your findings!**

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to:
- Document pattern discoveries in [docs/pattern_reference.md](docs/pattern_reference.md)
- Submit improvements to the codebase
- Report bugs or request features

Your contributions help everyone understand these lasers better! 🎆

## Technical Details

- **Protocol**: DMX512 (USITT DMX512-A)
- **Baud rate**: 250,000 baud, 8N2
- **Refresh rate**: 40 Hz (25 packets/second)
- **Break signal**: 150 μs low + 12 μs mark-after-break
- **Library**: `pyserial` 3.5+
- **Threading**: Background transmit thread for continuous DMX output

## License

See [LICENSE](LICENSE)

## References

- [Laserworld MK2 Manual](docs/MK2_manual.pdf)
- [DMX512 Standard](https://en.wikipedia.org/wiki/DMX512)
- [pyserial Documentation](https://pyserial.readthedocs.io/)
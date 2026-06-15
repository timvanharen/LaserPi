# Direct Laser Driver

Direct galvo-style laser control system for Raspberry Pi 3B+. Drives two stepper motors (X/Y mirror deflection) and an RGB laser module directly via GPIO, bypassing DMX entirely.

## Overview

This system replaces the commercial laser controller with direct hardware control:

- **X/Y positioning**: Two NEMA 16 stepper motors (Shangyeng 39BYG101-1) driven by TMC2209-based ATD5833 breakout boards, each tilting a mirror for one axis
- **RGB laser**: Three laser diodes (650nm red, 532nm green, 445nm blue) driven by a DIY constant-current driver circuit controlled via GPIO PWM
- **Raspberry Pi 3B+**: Runs the control software, generates step pulses and PWM signals via pigpio (DMA-timed)

### Capabilities

- Point-to-point laser positioning
- Pattern tracing (circles, squares, stars, spirals, grids, text)
- Continuous re-tracing for persistence-of-vision effects
- Interactive pattern selection shell
- Image-to-laser-path conversion
- Mechanical boundary detection and calibration

## Safety

**This project involves Class 3B lasers. Permanent eye damage occurs instantly.**

- Never look into the laser aperture or at specular reflections
- Always wear appropriate laser safety goggles (OD 4+ for all wavelengths present)
- The 532nm green laser contains an invisible 808nm IR pump beam — green-only goggles are NOT sufficient
- Ensure the laser is enclosed during operation
- Hardware pull-down resistors on all laser GPIO pins ensure lasers are OFF at boot
- All software uses try/finally blocks to guarantee laser shutdown on exit or crash
- Never bypass the software or hardware safety interlocks
- Keep a laser safety interlock/kill switch accessible at all times

## Hardware

| Component | Specification |
|-----------|--------------|
| Raspberry Pi | 3B+ |
| X motor | Shangyeng 39BYG101-1 (NEMA 16, 1.8°, 12V, 4-wire, 0.66 kg·cm) |
| Y motor | Shangyeng 39BYG101-1 (same as above) |
| Motor drivers | 2× ATD5833/ATD6833 (TMC2209-based breakout) |
| Red laser | 100 mW, 650 nm (Vf ≈ 2.12 V @ 49 mA threshold) |
| Green laser | 20 mW, 532 nm DPSS (pump diode Vf ≈ 1.71 V @ 110 mA threshold) |
| Blue laser | 50 mW, 445 nm (Vf ≈ 4.34 V @ 26.6 mA visible) |
| Power supply | 12 V main + buck converter for 5 V |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Raspberry Pi 3B+                    │
│                                                      │
│   ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│   │ Motor X  │  │ Motor Y  │  │  Laser Driver  │   │
│   │ STEP/DIR │  │ STEP/DIR │  │  R/G/B PWM     │   │
│   └────┬─────┘  └────┬─────┘  └───┬──┬──┬──────┘   │
│        │              │            │  │  │           │
└────────┼──────────────┼────────────┼──┼──┼───────────┘
         │              │            │  │  │
    ┌────▼─────┐  ┌─────▼────┐  ┌───▼──▼──▼───┐
    │ ATD5833  │  │ ATD5833  │  │ DIY Driver   │
    │ TMC2209  │  │ TMC2209  │  │ LM317 CC     │
    │ Driver X │  │ Driver Y │  │ + MOSFET     │
    └────┬─────┘  └─────┬────┘  └───┬──┬──┬───┘
         │              │           │  │  │
    ┌────▼─────┐  ┌─────▼────┐  ┌──▼──▼──▼────┐
    │ Stepper  │  │ Stepper  │  │ R   G   B    │
    │ Motor X  │  │ Motor Y  │  │ Laser diodes │
    │ (mirror) │  │ (mirror) │  │              │
    └──────────┘  └──────────┘  └──────────────┘
```

### Software Layers

```
examples/                          # User-facing scripts
  └── pattern_shell.py             # Interactive CLI
      └── control/coordinator.py   # Synchronized laser + galvo
          ├── motor/galvo.py       # Coordinated X/Y movement
          │   └── motor/stepper.py # Single-axis step/dir
          └── laser/rgb_driver.py  # GPIO PWM laser control
              └── config.py        # Pin assignments & parameters
```

## Installation

```bash
# On the Raspberry Pi:
cd Direct_laser_driver
bash scripts/setup.sh

# Or manually:
sudo apt-get install pigpio python3-pigpio
pip3 install -r requirements.txt
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Quick Start

```bash
# 1. Test motors (no laser needed)
python3 examples/motor_test.py

# 2. Calibrate mechanical boundaries
python3 examples/boundary_probe.py

# 3. Test laser colors (motors not needed)
python3 examples/laser_test.py

# 4. Draw a pattern
python3 examples/draw_pattern.py

# 5. Interactive shell
python3 examples/pattern_shell.py

# 6. Draw from an image
python3 examples/image_draw.py path/to/image.png
```

## Documentation

- [Motor Wiring Guide](docs/motor_wiring_guide.md) — ATD5833 ↔ motor ↔ Pi connections
- [Laser Driver Guide](docs/laser_driver_guide.md) — DIY RGB constant-current driver circuit
- [PCB Notes](docs/pcb_notes.md) — Custom PCB connector layout

## Project Structure

```
Direct_laser_driver/
├── README.md
├── requirements.txt
├── docs/
│   ├── motor_wiring_guide.md
│   ├── laser_driver_guide.md
│   └── pcb_notes.md
├── src/
│   └── direct_laser/
│       ├── config.py              # GPIO pins, motor params, limits
│       ├── motor/
│       │   ├── stepper.py         # Single-axis step/dir control
│       │   └── galvo.py           # Coordinated X/Y controller
│       ├── laser/
│       │   └── rgb_driver.py      # GPIO PWM RGB laser control
│       ├── control/
│       │   ├── coordinator.py     # Synchronized laser+galvo
│       │   └── patterns.py        # Pattern generators
│       └── conversion/
│           └── image_converter.py # Image → laser path
├── examples/
│   ├── motor_test.py
│   ├── boundary_probe.py
│   ├── laser_test.py
│   ├── draw_pattern.py
│   ├── pattern_shell.py
│   └── image_draw.py
└── scripts/
    └── setup.sh
```

## Notes

- The green 532nm laser is a DPSS module (IR pump diode → frequency-doubled green). It behaves as on/off only — PWM dimming below the lasing threshold produces no visible output. Brightness is set via the trim pot on the driver circuit.
- Stepper motors are much slower than real galvo scanners. Simple shapes (4-8 points) can achieve reasonable persistence-of-vision effects. Complex shapes will flicker.
- The TMC2209 supports UART configuration for microstepping and StallGuard sensorless homing. Check if your ATD5833 board exposes the PDN_UART pin.

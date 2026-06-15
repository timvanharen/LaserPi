# PCB Design Notes

Custom PCB to connect the Raspberry Pi 3B+, two ATD5833 stepper drivers, and the DIY laser driver circuit. The board sits between the Pi and the laser components inside the enclosure.

## Board Overview

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │  ATD5833 #1  │   │  ATD5833 #2  │   │  LASER DRIVER   │  │
│  │  (X motor)   │   │  (Y motor)   │   │  R  G  B        │  │
│  │              │   │              │   │  LM317 × 3      │  │
│  │  ┌────────┐  │   │  ┌────────┐  │   │  MOSFET × 3     │  │
│  │  │HEADERS │  │   │  │HEADERS │  │   │                 │  │
│  └──┴────────┴──┘   └──┴────────┴──┘   └─────────────────┘  │
│                                                              │
│  ┌────────┐  ┌────────┐  ┌────────┐         ┌────────────┐  │
│  │MOTOR X │  │MOTOR Y │  │ LASER  │         │ 12V INPUT  │  │
│  │ JST-XH │  │ JST-XH │  │HEADER  │         │ (screw     │  │
│  │ 4-pin  │  │ 4-pin  │  │ 3-pin  │         │  terminal) │  │
│  └────────┘  └────────┘  └────────┘         └────────────┘  │
│                                                              │
│   ┌─────────────────────────────────┐    ┌────────────────┐  │
│   │   Raspberry Pi GPIO Header      │    │  Buck Conv.    │  │
│   │   2×20 pin socket               │    │  12V → 5V      │  │
│   │   (or ribbon cable connector)   │    │  module socket  │  │
│   └─────────────────────────────────┘    └────────────────┘  │
│                                                              │
│                    ●  ●  ●  (mounting holes)                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Connectors

### 12V Power Input

- **Type**: 2-position screw terminal (5.08 mm pitch) or DC barrel jack (5.5 × 2.1 mm)
- **Rating**: 5A minimum (12V motors + laser driver + buck converter)
- **Protection**: 1N5819 Schottky diode for reverse polarity, 470µF 25V electrolytic bulk cap
- **Fuse**: 5A blade fuse holder on the 12V rail (recommended)

### Motor Connectors (× 2)

- **Type**: JST-XH 4-pin (2.5 mm pitch) — keyed, prevents wrong insertion
- **Pinout**:

| Pin | Signal | Color (suggested) |
|-----|--------|-------------------|
| 1 | Coil A+ (1A) | Red |
| 2 | Coil A- (1B) | Blue |
| 3 | Coil B+ (2A) | Green |
| 4 | Coil B- (2B) | Black |

> Wire colors are suggestions only. Always verify coil pairs with a multimeter.

### Laser Output Connector

- **Type**: JST-XH 5-pin or Molex KK 5-pin
- **Pinout**:

| Pin | Signal | Notes |
|-----|--------|-------|
| 1 | Red laser anode (+) | From LM317/resistor output |
| 2 | Green laser anode (+) | From LM317/resistor output |
| 3 | Blue laser anode (+) | From LM317/resistor output |
| 4 | Common cathode (−) | MOSFET drain connections |
| 5 | GND | Power ground reference |

> **Note**: If each laser has a separate cathode (not common-cathode), use individual MOSFET channels as designed. The connector pinout above assumes the MOSFET drains route to separate cathode connections.

### Raspberry Pi Header

- **Option A**: 2×20 pin female socket — Pi plugs directly onto the PCB (stacking)
- **Option B**: 2×20 IDC ribbon cable connector — Pi connects via flat cable (more flexible placement)

**Used GPIO pins** (directly routed on PCB):

| BCM GPIO | Pi Header Pin | Function |
|----------|--------------|----------|
| GPIO 4 | Pin 7 | Motor X ENABLE |
| GPIO 17 | Pin 11 | Motor X STEP |
| GPIO 18 | Pin 12 | Motor X DIR |
| GPIO 5 | Pin 29 | Motor Y ENABLE |
| GPIO 27 | Pin 13 | Motor Y STEP |
| GPIO 22 | Pin 15 | Motor Y DIR |
| GPIO 23 | Pin 16 | Laser RED PWM |
| GPIO 24 | Pin 18 | Laser GREEN PWM |
| GPIO 25 | Pin 22 | Laser BLUE PWM |
| GPIO 6 | Pin 31 | Laser ENABLE (master) |
| GPIO 14 | Pin 8 | UART TX (TMC2209) |
| GPIO 15 | Pin 10 | UART RX (TMC2209) |
| 3.3V | Pin 1, 17 | VCC_IO for ATD5833s |
| 5V | Pin 2, 4 | Pi power input (from buck) |
| GND | Pin 6, 9, 14, 20, 25 | Common ground |

RPi 40-pin header

      3.3V    [ 1] [ 2]  5V
      (SDA)   [ 3] [ 4]  5V
      (SCL)   [ 5] [ 6]  GND  ──── Motor GND / Laser GND
BCM 4  EN_X   [ 7] [ 8]  BCM 14  TMC_UART_TX
       GND    [ 9] [10]  BCM 15  TMC_UART_RX
BCM 17 STEP_X [11] [12]  BCM 18  DIR_X
BCM 27 STEP_Y [13] [14]  GND
BCM 22 DIR_Y  [15] [16]  BCM 23  LASER_RED
      3.3V    [17] [18]  BCM 24  LASER_GREEN
              [19] [20]  GND
              [21] [22]  BCM 25  LASER_BLUE
              [23] [24]
       GND    [25] [26]
              [27] [28]
BCM 5  EN_Y   [29] [30]  GND
              [31] [32]
              [33] [34]  GND
              [35] [36]
              [37] [38]
       GND    [39] [40]  BCM 6   LASER_EN (master)

### ATD5833 Module Sockets (× 2)

- **Type**: 2× 8-pin female headers (2.54 mm pitch), matching ATD5833 pinout
- **Pin routing**: See motor wiring guide for complete ATD5833 pin assignments
- **VCC_IO**: Both boards share 3.3V from Pi header
- **VM**: Both boards share 12V from power input
- **GND**: Common ground plane

### Buck Converter Socket

- **Type**: Pin headers or screw terminals for a drop-in buck converter module (e.g., LM2596 module)
- **Input**: 12V from power rail
- **Output**: 5V to Pi header pins 2/4
- **Rating**: 3A module recommended (Pi 3B+ draws up to 1A under load)

## PCB Layout Guidelines

### Ground Plane

- Use a solid ground plane on one layer (bottom recommended)
- Star-ground topology if noise is an issue: motor ground, laser ground, and logic ground meet at a single point near the power input
- Keep motor traces and laser traces separated from GPIO signal traces

### Power Traces

| Rail | Minimum Width | Typical Current |
|------|--------------|----------------|
| 12V motor | 1.5 mm (60 mil) | 1.0 A per motor |
| 12V laser | 1.0 mm (40 mil) | 0.5 A total |
| 5V Pi | 1.5 mm (60 mil) | 1.0 A |
| 3.3V logic | 0.5 mm (20 mil) | < 50 mA |
| GPIO signals | 0.25 mm (10 mil) | < 10 mA |

### Component Placement

1. **ATD5833 modules**: Near their respective motor connectors, minimize trace length for motor phase outputs (high-current, noisy)
2. **Laser driver section**: Group LM317s, MOSFETs, and resistors together. Place heatsinks on LM317s
3. **Bypass caps**: 100nF ceramic as close as possible to each ATD5833 VM pin and each LM317 input
4. **Bulk cap**: Near the 12V input connector
5. **Pull-down resistors**: Close to MOSFET gates (short path to GND)
6. **Buck converter**: Near 12V input, away from sensitive signal traces

### Thermal Considerations

- **LM317s**: Each dissipates 0.6–1.7W. Use TO-220 packages with copper pour or small clip-on heatsinks
- **ATD5833/TMC2209**: The IC handles motor current (up to ~2A) with internal dissipation. Boards typically have a thermal pad on the bottom — ensure airflow or thermal relief
- **MOSFETs**: Dissipation is negligible at these currents (< 1 mW). No heatsink needed

### Board Dimensions

Target size should fit inside the laser enclosure. Suggested constraints:
- Maximum width: 80 mm (to fit alongside existing components)
- Maximum length: 120 mm
- Mounting holes: M3, matching enclosure standoff positions
- Height clearance: account for ATD5833 module height (~15 mm) and heatsinks

## Schematic Checklist

- [ ] 12V input with reverse-polarity diode and bulk capacitor
- [ ] Fuse holder on 12V rail
- [ ] Buck converter pads (12V → 5V)
- [ ] 5V to Pi header power pins
- [ ] 3.3V from Pi to both ATD5833 VCC_IO
- [ ] 12V to both ATD5833 VM pins
- [ ] ATD5833 #1: STEP/DIR/EN routed to GPIO 17/18/4
- [ ] ATD5833 #2: STEP/DIR/EN routed to GPIO 27/22/5
- [ ] ATD5833 motor outputs to JST-XH connectors
- [ ] UART TX (GPIO 14) through 1kΩ to both PDN_UART pins
- [ ] UART RX (GPIO 15) direct to both PDN_UART pins
- [ ] MS1/MS2 configurable (jumpers or hard-wired)
- [ ] 3× laser driver channels (LM317 + MOSFET + R_set + gate resistors)
- [ ] 3× 10kΩ pull-downs on MOSFET gates
- [ ] Laser enable GPIO (GPIO 6) to control master power (optional: additional MOSFET cutting 12V to all three laser driver circuits)
- [ ] 100nF bypass capacitors on all IC power pins
- [ ] Copper ground plane
- [ ] Mounting holes (M3 × 4)
- [ ] Silkscreen labels for all connectors and polarities

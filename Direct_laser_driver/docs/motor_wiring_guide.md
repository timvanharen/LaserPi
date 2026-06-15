# Motor Wiring Guide

Connecting the ATD5833/ATD6833 (TMC2209-based) stepper driver to the Shangyeng 39BYG101-1 motor and Raspberry Pi 3B+.

## ATD5833/ATD6833 Breakout Board Pinout

The ATD5833 is a breakout board for the Trinamic TMC2209 stepper driver IC. It follows the standard StepStick/Pololu form factor. Pin layout (looking at the board with the chip facing up, potentiometer on top):

```
           ┌─────────────────┐
    EN  ──►│ 1             16│◄── VM (motor supply, 12V)
    MS1 ──►│ 2             15│◄── GND
    MS2 ──►│ 3             14│◄── 2B (coil B-)
   PDN  ──►│ 4             13│◄── 2A (coil B+)
   CLK  ──►│ 5             12│◄── 1A (coil A+)
  STEP  ──►│ 6             11│◄── 1B (coil A-)
   DIR  ──►│ 7             10│◄── VCC_IO (logic supply, 3.3V)
   GND  ──►│ 8              9│◄── DIAG
           └─────────────────┘
```
Watch this video: https://www.youtube.com/watch?v=d-u_mzvw_eY

> **Note**: Pin layout may vary by manufacturer. Always verify against **your specific board's** silkscreen markings. Some boards label PDN as "UART" or "PDN_UART".

### Pin Descriptions

| Pin | Name | Function |
|-----|------|----------|
| EN | Enable | Active LOW — pull LOW to enable driver, HIGH to disable (high-impedance) |
| MS1 | Microstep 1 | Microstepping config bit 1 (active when PDN_UART not used for UART) |
| MS2 | Microstep 2 | Microstepping config bit 2 |
| PDN/UART | PDN_UART | UART interface for TMC2209 configuration. Also functions as power-down input when UART not used |
| CLK | Clock | External clock input (usually tied to GND or left NC if using internal oscillator) |
| STEP | Step | Rising edge = one microstep. Pulse width minimum: 100 ns |
| DIR | Direction | HIGH = one direction, LOW = other. Set before STEP pulse |
| GND | Ground | Common ground (connect to Pi GND and power supply GND) |
| DIAG | Diagnostics | Output — goes HIGH on StallGuard detection or driver error |
| VCC_IO | Logic supply | Reference voltage for logic inputs: **connect to 3.3V** from Pi |
| 1A, 1B | Coil A | Motor coil A outputs (one winding pair) |
| 2A, 2B | Coil B | Motor coil B outputs (other winding pair) |
| VM | Motor voltage | Motor power supply: **connect to 12V** |

## Shangyeng 39BYG101-1 Motor Wiring

### Motor Specifications

| Parameter | Value |
|-----------|-------|
| Size | NEMA 16 (39.3 × 39.3 × 22 mm) |
| Voltage | 12V |
| Wire configuration | 4-wire bipolar |
| Step angle | 1.8° (200 steps/revolution) |
| Holding torque | 0.66 kg·cm |

### Identifying Coil Pairs

The motor has 4 wires (or 5, with the 5th being NC/shield). You need to identify which two wires belong to **Coil A** and which two belong to **Coil B**.

**Method — Multimeter continuity/resistance:**

1. Set your multimeter to resistance (Ω) mode
2. Measure resistance between all wire combinations
3. Two wires that show **low resistance** (typically 5-50 Ω) are one coil pair
4. The other two wires with low resistance between them are the other coil pair
5. Wires from different coils show **infinite resistance** (open circuit)

```
Example:
  Wire 1 ←→ Wire 2 : 30 Ω  → Coil A (1A, 1B)
  Wire 1 ←→ Wire 3 : ∞     → different coils
  Wire 1 ←→ Wire 4 : ∞     → different coils
  Wire 3 ←→ Wire 4 : 30 Ω  → Coil B (2A, 2B)
```

**Quick test:** Touch two wires together and try to turn the motor shaft by hand. If it feels **noticeably harder to turn**, those two wires are a coil pair (you're shorting the coil, creating back-EMF braking).

### 5-Pin Connector

If your motor has a 5-pin connector:

| Connector Pin | Function |
|--------------|----------|
| Pin 1 | Coil A wire 1 |
| Pin 2 | Coil A wire 2 |
| Pin 3 | Coil B wire 1 |
| Pin 4 | Coil B wire 2 |
| Pin 5 | NC (not connected) or shield/ground |

> **Important**: The exact pinout depends on the connector and manufacturer. Always verify with a multimeter. Do NOT guess — swapping wires within a coil just reverses motor direction (harmless), but connecting wires from different coils to the same output can cause erratic behavior or damage the driver.

### Motor → ATD5833 Connection

| Motor Wire | ATD5833 Pin | Notes |
|-----------|-------------|-------|
| Coil A wire 1 | **1A** (pin 12) | |
| Coil A wire 2 | **1B** (pin 11) | Swap these two to reverse direction |
| Coil B wire 1 | **2A** (pin 13) | |
| Coil B wire 2 | **2B** (pin 14) | Swap these two to reverse direction |

## Raspberry Pi GPIO → ATD5833 Connections

### GPIO Pin Assignments

Two drivers are needed — one for X axis, one for Y axis:

| Function | X Motor GPIO (BCM) | Y Motor GPIO (BCM) | ATD5833 Pin |
|----------|-------------------|-------------------|-------------|
| STEP | GPIO 17 | GPIO 27 | STEP (pin 6) |
| DIR | GPIO 18 | GPIO 22 | DIR (pin 7) |
| EN | GPIO 4 | GPIO 5 | EN (pin 1) |

**Optional UART (for TMC2209 configuration / StallGuard):**

| Function | GPIO (BCM) | Notes |
|----------|-----------|-------|
| TX | GPIO 14 (UART TX) | Connect to PDN_UART on Driver X |
| RX | GPIO 15 (UART RX) | Connect to PDN_UART on Driver X |

> **Note**: TMC2209 uses a single-wire UART interface — TX and RX share the same PDN_UART pin via a 1kΩ resistor on the TX line. To address two drivers on one UART bus, each TMC2209 must be configured with a different address (0-3) via MS1/MS2 pins at power-up.

### UART Single-Wire Connection

```
Pi GPIO 14 (TX) ──[1kΩ]──┬── ATD5833 PDN_UART pin
                          │
Pi GPIO 15 (RX) ──────────┘
```

The 1kΩ resistor on TX prevents bus contention when the TMC2209 is transmitting responses.

### Addressing Two Drivers on One UART

At power-up, the TMC2209 reads MS1 and MS2 to set its UART address:

| MS1 | MS2 | UART Address |
|-----|-----|-------------|
| GND | GND | 0 |
| VCC | GND | 1 |
| GND | VCC | 2 |
| VCC | VCC | 3 |

**Recommended**: X driver = address 0 (MS1=GND, MS2=GND), Y driver = address 1 (MS1=VCC, MS2=GND).

> After UART is initialized, microstepping can be configured via software (overriding the MS1/MS2 hardware settings). If UART is **not** used, MS1/MS2 set the microstepping directly.

### Microstepping via MS1/MS2 (without UART)

If not using UART, MS1/MS2 set microstep resolution directly:

| MS1 | MS2 | Microsteps | Steps/Rev |
|-----|-----|-----------|-----------|
| GND | GND | 8 | 1,600 |
| VCC | GND | 2 (half-step) | 400 |
| GND | VCC | 4 (quarter-step) | 800 |
| VCC | VCC | 16 | 3,200 |

**Recommended for non-UART operation**: MS1=VCC, MS2=VCC → 16 microsteps (3,200 steps/rev). Good balance of resolution and speed.

## Power Wiring

```
                     ┌────────────────────┐
                     │   12V Power Supply  │
                     └───┬────────────┬───┘
                         │            │
                    12V ─┤       GND ─┤
                         │            │
          ┌──────────────┼────────────┼──────────────┐
          │              │            │              │
     ┌────▼────┐    ┌────▼────┐      │         ┌────▼────┐
     │ ATD5833 │    │ ATD5833 │      │         │  Buck   │
     │ X motor │    │ Y motor │      │         │ Conv.   │
     │ VM=12V  │    │ VM=12V  │      │         │ 12V→5V  │
     │ GND     │    │ GND     │      │         └────┬────┘
     └────┬────┘    └────┬────┘      │              │
          │              │           │         5V───┤
          │              │           │              │
          │              │      ┌────▼────────────────────┐
          │              │      │      Raspberry Pi 3B+   │
          │              │      │  3.3V → VCC_IO (both)   │
          │              │      │  GND  → GND (common)    │
          │              │      │  GPIO → STEP/DIR/EN     │
          │              │      └─────────────────────────┘
          │              │
     ┌────▼────┐    ┌────▼────┐
     │ Motor X │    │ Motor Y │
     └─────────┘    └─────────┘
```

### Power Requirements

| Component | Voltage | Current (typical) |
|-----------|---------|-------------------|
| Motor X | 12V | ~0.3-0.5 A (TMC2209 manages current) |
| Motor Y | 12V | ~0.3-0.5 A |
| Raspberry Pi 3B+ | 5V | ~0.5-1.0 A |
| ATD5833 logic (×2) | 3.3V (from Pi) | < 10 mA each |
| **Total from 12V** | | **~2-3 A** (including laser driver) |

> Use a 12V supply rated for at least **5A** to have headroom for the laser driver circuit as well.

### Critical Wiring Notes

1. **Common ground**: ALL grounds must be connected together — Pi GND, ATD5833 GND, power supply GND, laser driver GND
2. **VCC_IO to 3.3V**: Connect VCC_IO on both ATD5833 boards to the Pi's 3.3V pin. This sets the logic level for STEP/DIR/EN inputs
3. **EN pin default**: EN is active LOW. Leave it floating or pull HIGH to keep the driver disabled at boot. The software pulls it LOW when ready
4. **Never disconnect motor while driver is powered**: The TMC2209 can be damaged by back-EMF spikes from disconnecting a motor under power
5. **Current limiting**: Set the TMC2209 current limit via the onboard potentiometer (if present) or UART. The 39BYG101-1 rated current is typically ~0.4-0.6A per phase — do not exceed this

### TMC2209 Current Setting

**Via onboard potentiometer** (if present on ATD5833 board):
- Turn potentiometer clockwise to increase current
- Measure Vref voltage at the potentiometer wiper
- $I_{RMS} = \frac{V_{ref}}{1.41 \times R_{sense}}$
- Typical R_sense = 0.11Ω, so for 0.4A: $V_{ref} = 0.4 \times 1.41 \times 0.11 ≈ 0.062V$

**Via UART** (recommended):
- Set IRUN and IHOLD registers
- IRUN range: 0-31, maps to current via: $I = \frac{(IRUN + 1)}{32} \times \frac{V_{FS}}{R_{sense}}$
- Much more precise than potentiometer adjustment

## Wiring Checklist

- [ ] Identify motor coil pairs with multimeter
- [ ] Connect Coil A → ATD5833 1A/1B
- [ ] Connect Coil B → ATD5833 2A/2B
- [ ] Connect 12V → VM on both ATD5833 boards
- [ ] Connect Pi 3.3V → VCC_IO on both boards
- [ ] Connect ALL GNDs together (Pi, boards, PSU)
- [ ] Connect STEP/DIR/EN GPIOs (see pin table above)
- [ ] (Optional) Connect UART TX/RX for TMC2209 config
- [ ] Set MS1/MS2 for microstepping or UART addressing
- [ ] Set current limit via potentiometer or UART
- [ ] Double-check all connections before powering on
- [ ] Power on 12V supply, then Pi (or simultaneously)
- [ ] Run `motor_test.py` to verify operation

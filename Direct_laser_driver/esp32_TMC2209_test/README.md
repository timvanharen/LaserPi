# ESP32-S3 TMC2209 Test

Arduino sketch for testing TMC2209 stepper driver with NEMA16 motor on ESP32-S3-N16R8.

## Hardware

- **MCU**: ESP32-S3-N16R8 (16MB Flash, 8MB PSRAM)
- **Driver**: TMC2209 (ATD5833/ATD6833 breakout or compatible)
- **Motor**: NEMA16 5-wire stepper (e.g., Shangyeng 39BYG101-1)
  - 1.8° step angle (200 steps/rev)
  - 12V nominal
  - **5-wire unipolar motor**: Has center tap (common wire)
  - **For TMC2209 (bipolar driver)**: Use only 4 wires, leave common disconnected

**Note on 5-wire motors**: Your original hardware likely had the common at 12V because it used a **unipolar driver** (e.g., ULN2003). TMC2209 is a **bipolar driver** and works best with the common wire **disconnected**, which gives you full torque and proper current control.

## Wiring

### TMC2209 Pinout (Your Board)

**Right side (top to bottom):**
```
VM   ← 12V power supply
GND  ← Ground
M1B  ← Motor coil 1, phase B (e.g., Red wire)
M1A  ← Motor coil 1, phase A (e.g., Orange wire)
M2A  ← Motor coil 2, phase A (e.g., Brown wire)
M2B  ← Motor coil 2, phase B (e.g., Black wire)
VIO  ← 3.3V logic power
GND  ← Ground
```

**Left side (top to bottom):**
```
EN    ← Enable (active LOW)
MS1   ← Microstepping select 1
MS2   ← Microstepping select 2
PDN   ← Power down / UART address (keep HIGH or use for UART)
USART ← Single-wire UART
CLK   ← External clock (leave open)
STEP  ← Step pulse
DIR   ← Direction
```

### TMC2209 → ESP32-S3 Connections

| TMC2209 Pin | ESP32-S3 Pin | Function | Notes |
|-------------|--------------|----------|-------|
| STEP        | GPIO 4       | Step pulse | |
| DIR         | GPIO 5       | Direction | |
| EN          | GPIO 6       | Enable (active LOW) | Pull LOW to enable |
| MS1         | GND or 3.3V  | Microstepping select | See table below |
| MS2         | GND or 3.3V  | Microstepping select | See table below |
| PDN         | GPIO 16 (RX) | UART (via 1kΩ) | Optional for advanced config |
| USART       | GPIO 16 (RX) | UART single-wire | Connect via 1kΩ resistor |
| CLK         | (not used)   | Leave open | |
| VIO         | 3.3V         | Logic power | |
| GND         | GND          | Ground | Common ground required |
| VM          | 12V          | Motor power | 2A+ supply recommended |

### Microstepping Selection (MS1/MS2 Pins)

The MS1 and MS2 pins select microstepping mode **without UART**:

| MS1 | MS2 | Microsteps | Resolution | Recommended |
|-----|-----|------------|------------|-------------|
| GND | GND | 8          | 1/8 step   | Lower resolution |
| 3.3V| GND | 2          | 1/2 step   | Very coarse |
| GND | 3.3V| 4          | 1/4 step   | Coarse |
| 3.3V| 3.3V| 16         | 1/16 step  | ✅ **Best** (smoothest) |

**Recommended setup**: 
- Connect **MS1 → 3.3V** (hardwire or via GPIO 7)
- Connect **MS2 → 3.3V** (hardwire or via GPIO 8)
- This gives 16x microstepping = **3200 microsteps per revolution**

**Note**: UART configuration can override these hardware settings. The test sketch uses UART to change microstepping dynamically, so you can hardwire MS1=MS2=3.3V and control everything via software.

### UART Connection (Optional Advanced Features)

For current control, StallGuard, and microstepping override via software:

1. **Bridge PDN and USART pins together** on the TMC2209 (some boards pre-connect these)
2. **Connect to ESP32 GPIO 16** through a **1kΩ resistor**

```
TMC2209: PDN ──┐
               ├─── 1kΩ resistor ─── ESP32 GPIO 16 (RX2)
TMC2209: USART ┘
```

This single-wire UART allows the TMCStepper library to read/write driver registers.

### Motor → TMC2209

**Important**: You have a 5-wire **unipolar** motor. The original hardware connected the common (center tap) to 12V because it used a **unipolar driver**. However, the TMC2209 is a **bipolar driver** and requires a different wiring approach.

#### Option 1: Use as Bipolar (Recommended for TMC2209)

Connect only the coil ends, **leave common wire disconnected**:

| Wire Color | Function | TMC2209 Pin |
|------------|----------|-------------|
| Red        | Coil A, end 1 | M1B |
| Orange     | Coil A, end 2 | M1A |
| **Yellow** | **Common (center tap)** | **Leave disconnected** |
| Brown      | Coil B, end 1 | M2A |
| Black      | Coil B, end 2 | M2B |

**Why?** TMC2209 reverses current direction through the coils for bipolar control. The center tap isn't needed and would interfere with operation.

#### Option 2: Connect Common to VM (If Original Setup Used 12V)

Some unipolar motors can work with common tied to VM (12V) on bipolar drivers, but **this reduces torque by ~50%** and may cause issues:

| Wire Color | Function | TMC2209 Pin |
|------------|----------|-------------|
| Red        | Coil A, end 1 | M1B |
| Orange     | Coil A, end 2 | M1A |
| **Yellow** | **Common** | **VM (12V)** ⚠️ |
| Brown      | Coil B, end 1 | M2A |
| Black      | Coil B, end 2 | M2B |

⚠️ **Not recommended** — This configuration limits the driver to half-stepping and reduces efficiency.

#### How to Identify Coils

Use a multimeter in continuity/resistance mode:
1. Find **center tap (common)**: Measure resistance between all wire pairs
   - Common to any coil end: ~half the total coil resistance (e.g., 6Ω)
   - Coil end to coil end (same coil): full resistance (e.g., 12Ω)
2. **Coil A**: Two wires that show continuity through the common (e.g., Red + Orange)
3. **Coil B**: The other two wires (e.g., Brown + Black)
4. **Common wire**: The wire that connects to both coils

**For your motor**, if the original device had common at 12V, that wire is the center tap. Use **Option 1** (leave it disconnected) for best TMC2209 performance.

### Power Supply

- **12V 2A+** supply to TMC2209 VM and motor ground
- **3.3V** from ESP32 to TMC2209 VDD (or use separate 3.3V regulator)
- **Common ground** between ESP32 and driver
### Quick Start Wiring Checklist

1. ✅ **Motor**: Connect coil ends to M1A/M1B and M2A/M2B — **leave common (yellow) disconnected**
2. ✅ **Power**: 12V to VM, 3.3V to VIO, common GND
3. ✅ **Control**: STEP=GPIO4, DIR=GPIO5, EN=GPIO6
4. ✅ **Microstepping**: MS1=3.3V, MS2=3.3V (for 16x mode)
5. ⚠️ **UART** (optional): PDN+USART → 1kΩ resistor → GPIO16
## Software Setup

### Arduino IDE

1. Install ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "esp32" → Install "ESP32 by Espressif"

2. Install TMCStepper library:
   - Sketch → Include Library → Manage Libraries
   - Search "TMCStepper" → Install by teemuatlut

3. Board settings:
   - Board: "ESP32S3 Dev Module"
   - PSRAM: "OPI PSRAM"
   - Flash Size: "16MB (128Mb)"
   - Partition Scheme: "16M Flash (3MB APP/9.9MB FATFS)"
   - Upload Speed: 921600
   - **USB CDC On Boot: "Enabled"** ← CRITICAL for serial output!

4. Select the correct USB port:
   - Tools → Port → **COM#** (should show "USB-JTAG/Serial debug unit")

### ESP32-S3 USB-C Connectors

The ESP32-S3 has **two USB-C ports**:

| Port | Purpose | Use For |
|------|---------|---------|
| **USB-C (left/main)** | USB-JTAG debugger + Serial | ✅ Upload code + Serial Monitor |
| **USB-C (right)** | Battery charging / serial (if configured) | ❌ Don't use for debugging |

**For this project**, use the **left USB-C port** (the one labeled "USB" or closest to the edge).

### Troubleshooting: No Serial Output

If you don't see debug messages:

1. ✅ **Use the correct USB-C port** (the left one marked "USB")
2. ✅ **Set "USB CDC On Boot: Enabled"** in Arduino IDE
3. ✅ **Verify baud rate matches**: 115200
4. ✅ **Check COM port**: Tools → Port should show "USB-JTAG/Serial debug unit"
5. ✅ **Upload sketch**: Click Upload (not just Verify)
6. ✅ **Open Serial Monitor**: Tools → Serial Monitor (Ctrl+Shift+M)
7. ✅ **Press EN button** (reset) on the board after uploading to see startup messages

If still no output:
- Try unplugging and re-plugging the USB-C cable
- Try a different USB-C cable (some cables are charge-only)
- Check Device Manager to see if COM port appears when plugged in
- Try selecting "USB Serial/JTAG Controller" in Device Manager if port doesn't appear

### PlatformIO (Optional)

See `platformio.ini` in this directory.

## Usage

1. Upload the sketch
2. Open Serial Monitor (115200 baud)
3. Use interactive commands:

### Commands

- `s` — Single step forward
- `r` — Run continuous (3000 steps)
- `d` — Toggle direction
- `1-5` — Speed test (500, 1000, 2000, 4000, 8000 steps/s)
- `m` — Microstepping test (1x to 16x)
- `c` — Configure TMC2209 via UART
- `g` — StallGuard test
- `i` — Print driver info
- `e` — Enable driver
- `x` — Disable driver
- `h` — Help

## Features

- **Basic stepping**: Single-step and continuous motion
- **Speed ramping**: Tests from 500 to 8000 steps/s
- **UART configuration**: Sets microstepping, current, and StallGuard threshold
- **StallGuard detection**: Monitors for stalls during motion
- **Interactive control**: Real-time serial commands

## Troubleshooting

### Motor doesn't move
- Check power supply (12V present at VM?)
- Verify EN pin is LOW (driver enabled)
- Confirm motor wiring (coil pairs correct)
- Check MS1/MS2 are set (recommend both at 3.3V)
- Verify STEP pulse visible (use LED or oscilloscope on GPIO 4)

### Motor vibrates but doesn't turn
- **Wrong coil pairing**: Swap one coil's wires (swap M1A↔M1B or M2A↔M2B)
- **Unipolar mode issue**: If common wire is connected to 12V, disconnect it (see Option 1 above)
- Microstepping too high with insufficient current
- Loose or intermittent wiring

### Weak torque or overheating
- **5-wire motor with common at 12V**: Change to bipolar mode (disconnect common) for ~2x torque improvement
- Current setting too low (increase I_run) or too high (motor overheats)
- Check holding current (I_hold should be 50-70% of I_run)

### UART communication fails
- Verify 1kΩ resistor on TX line
- Check MS1/MS2 address pins (default 0b00)
- Confirm HardwareSerial(1) uses GPIO 16 (RX)
- Try lower baud rate (57600)

### Motor overheats
- Current too high (adjust Vref or I_run in code)
- Holding current not reduced (set I_hold lower)
- Driver not in stealth mode (enable StealthChop)

## Current Setting

### Finding Your R_sense Value

Check your TMC2209 board for resistors marked **R110** or **R100**:
- **R110** = 0.11Ω (110 milliohms) — **Most common**
- **R100** = 0.10Ω (100 milliohms)

You mentioned seeing **two R110 resistors** — this is normal. Each sense resistor measures current for one motor phase. Use **R_sense = 0.11Ω** in calculations.

### Potentiometer (Vref) Method

**Formula**: `Vref = I_rms × 8 × R_sense`

**For 0.4A current limit with R_sense = 0.11Ω:**
```
Vref = 0.4A × 8 × 0.11Ω
Vref = 0.352V = 352mV
```

**Set your potentiometer to 352mV** (0.352V) for 0.4A current limit.

### Common Current Settings

| Desired Current | Vref (R_sense = 0.11Ω) |
|-----------------|-------------------------|
| 0.3A            | 264mV (0.264V)         |
| **0.4A**        | **352mV (0.352V)**     |
| 0.5A            | 440mV (0.440V)         |
| 0.6A            | 528mV (0.528V)         |
| 0.8A            | 704mV (0.704V)         |
| 1.0A            | 880mV (0.880V)         |
| 1.2A            | 1.056V                 |

### How to Measure Vref

**CRITICAL: The driver must be fully powered for Vref to work!**

1. **Connect power FIRST**:
   - ✅ **VM (12V)** connected to 12V supply ← **Most important!**
   - ✅ **VIO (3.3V)** connected to 3.3V
   - ✅ **GND** connected to common ground
   - ✅ **EN pin** set to **LOW (GND)** to enable the driver

2. **Set multimeter to DC voltage** (200mV or 2V range)

3. **Measure between**:
   - **Positive (red) probe**: Potentiometer wiper (center pin) or Vref test point
   - **Negative (black) probe**: Any GND pin

4. **Slowly turn pot clockwise** while watching voltage increase

5. **Adjust until you read 352mV** for 0.4A

### Troubleshooting Vref Measurement

**Problem: Pot only goes 0 to 0.2V**

This means **VM (12V motor power) is NOT connected**. The Vref circuit requires the power stage to be active.

✅ **Fix**:
1. Connect 12V to **VM** pin (top of right side)
2. Connect 12V ground to **GND** (next to VM)
3. Connect 3.3V to **VIO** pin
4. Connect **EN pin to GND** (or pull LOW via ESP32)
5. Now measure Vref - should go up to 1V+ as you turn the pot

**Problem: Voltage won't change**

- Pot might be damaged or is a different adjustment (some boards have multiple pots)
- Try measuring between the outer pins of the pot (should be ~10kΩ)
- Check if your board has a dedicated **Vref test pad** (usually labeled)

**Problem: No Vref test point visible**

- Carefully probe the **center pin** of the potentiometer (the middle terminal)
- Or measure between pot wiper and the large GND copper area

### UART Method (Recommended - Easier!)

**Skip the potentiometer hassle** - the test sketch sets current via UART, which is more precise and doesn't require a multimeter:

```cpp
#define MOTOR_CURRENT_RUN  400   // Set 400mA (0.4A) - line 18
```

Change line 18 in the Arduino sketch from `600` to `400` for 0.4A limit. This **overrides the Vref potentiometer** - you can leave the pot at any position and the UART command will set the correct current.

**Why UART is better:**
- ✅ No multimeter needed
- ✅ More accurate than pot adjustment
- ✅ Can change current on-the-fly via serial commands
- ✅ Displays actual current setting in Serial Monitor

**Note:** TMC2209 sets RMS current directly; hold current is controlled via internal registers (advanced mode).

## Safety

- **Do not connect/disconnect motor while powered**
- **Use heatsink on driver if running > 1A continuously**
- **Monitor driver temperature** during extended tests
- **Fuse the 12V supply** (2-3A fast-blow recommended)

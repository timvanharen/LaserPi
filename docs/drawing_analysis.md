# Precise Laser Drawing: Technical Analysis

How far can we push the MK2's DMX interface for custom shape drawing, and
what would it take to go beyond those limits?

---

## Hardware Findings (from opening the laser)

**MCU: STC 89C516RD+** — an enhanced 8051 architecture:
- 8-bit CPU, ~11-40MHz clock (likely 11.0592MHz for UART baud accuracy)
- 64KB flash ROM (stores all 256 patterns)
- 1280 bytes RAM
- NO built-in DAC — uses external DAC or PWM+filter for galvo drive
- NO ILDA connector found on PCB

**Galvo motors:** NOT stepper motors — they're **galvanometers** (voice coil
actuators). Like a speaker cone but rotating a mirror. Driven by analog
voltage, not digital pulses. This is actually EASIER to drive directly
than steppers — just need the right voltage.

**Observed MCU behavior:**
- Processes DMX at approximately **25-40Hz** (one read per main loop cycle)
- Sending DMX faster than ~40Hz causes the MCU to see random intermediate
  states (it reads the DMX buffer at its own pace, not ours)
- At 500Hz DMX: cross pattern showed random switching between H and V lines
  because the MCU was catching the buffer mid-update
- At zoom 100, lines were long enough to almost overlap → "cross" appeared,
  but timing was still inconsistent

**Architecture (confirmed):**

```
DMX-512 input                                    Galvo X/Y mirrors
    │                                                ↑
    ▼                                                │
┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│ DMX Receiver │────▶│ STC 89C516RD+  │────▶│ DAC or PWM    │
│ (RS485→UART) │     │ (8051, ~11MHz) │     │ → Op-amp      │
└──────────────┘     │ Pattern ROM    │     │ → Galvo coils  │
                     └────────────────┘     └───────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ RGB Laser    │
                     │ diode driver │
                     └──────────────┘
```

**What DMX controls (9 channels):**
- Which pattern to display (from 256 ROM patterns)
- Where to position that pattern (X/Y galvo offset)
- How big (zoom), what color, scan speed

**What DMX does NOT control:**
- Individual galvo mirror angles (direct motor control)
- Laser on/off at arbitrary points in a scan
- Custom scan paths or waveforms
- The update rate (fixed by MCU main loop speed)

---

## DMX-Based Approaches (Software Only)

### Approach 1: Dot-Tracing (draw_shapes.py)

**How it works:** Use smallest pattern (0) at zoom 0 as a "pen", move
X/Y position rapidly to trace shapes via persistence of vision.

**Speed:** The DMX TX thread sends at 40Hz. The MCU processes at ~25-40Hz.
Effective resolution is ~25-40 unique positions per second.

**Pen size:** Pattern 0 at zoom 0 is still a small octagon. The internal
scanner traces that shape at kHz speed, so you see a small bright shape
at each position, not a true point.

**Verdict:** ⭐⭐⭐ Works for simple shapes (10-20 points = 1-2 traces/sec).

---

### Approach 2: Line Segment Composition (drawing_lab.py Mode 3)

**How it works:** Use line patterns (60=H, 70=V, 80=diagonal) as wide
brushes, position them via X/Y to build shapes from segments.

**Key insight from testing:** The MCU processes at ~25-40Hz. With N segments,
each shows at 40/N Hz. Must hold each segment for ≥25ms (1 DMX frame)
for the MCU to reliably process it.

| Segments | Refresh per segment | Quality |
|----------|-------------------|---------|
| 2 (cross) | ~20Hz | Visible, slight flicker |
| 3 | ~13Hz | Flickery but recognizable |
| 4 (box) | ~10Hz | Very flickery |
| 5+ (QW logo) | <8Hz | Strobing, not useful |

**MCU race condition issue:** When we update the DMX buffer faster than the
MCU reads it, the MCU catches partial updates (e.g., new pattern number but
old X/Y position). This causes random glitching. Solution: hold each segment
for 30ms+ to ensure the MCU sees a consistent state.

**Verdict:** ⭐⭐⭐ Best for 2-3 segment shapes. Not enough for complex logos.

---

### Approach 3: Dual Laser (drawing_lab.py Mode 4)

**How it works:** Both lasers simultaneously, one H-line, one V-line.
Both channels are in the same DMX universe → same DMX frame → MCU reads
both at once → both segments persistent with ZERO flicker.

**Sweet spot:** Cross, T-shape, L-shape, corner — all 2-segment shapes
are perfectly solid and bright.

**Verdict:** ⭐⭐⭐⭐ Best DMX approach. Limited to 2 persistent segments.

---

### Approach 4: Dual + Compose (drawing_lab.py Mode 5)

**How it works:** Laser 2 shows one persistent segment (always visible),
Laser 1 time-shares between additional segments.

**Result:** 1 rock-solid line + 2-3 flickering lines = more complex shapes
than dual alone. The persistent segment anchors the shape visually.

**Verdict:** ⭐⭐⭐⭐ Best DMX approach for 3+ segment shapes.

---

## Beyond DMX: Direct Galvo Drive

Since there's no ILDA connector, we need to tap into the galvo signal path
directly. The STC 89C516RD+ doesn't have a DAC, so it drives the galvos
through one of these methods:

### Finding the signal path (Mode 7: Galvo Probe)

Run `drawing_lab.py 7` with the laser case open and a multimeter to:

1. **Follow the galvo motor wires** back to the PCB
2. **Find the driver stage** — look for:
   - Op-amps (LM358, TL072, NE5532) — 8-pin DIP/SOP near galvo wires
   - External DAC chips (DAC0808, TLC5615, MCP4921) — 8-16 pin
   - Transistor H-bridge or push-pull drivers
3. **Measure the voltage range** at the driver input:
   - If ±5V or ±10V bipolar → standard galvo signals (needs bipolar DAC)
   - If 0-5V unipolar → easier, can drive from Pi's SPI DAC directly
   - If PWM → MCU outputs PWM, RC filters to analog, then driver

### The Direct Drive Plan

**Goal:** Bypass the STC 89C516RD+ and send our own X/Y analog signals
directly to the galvo drivers. Add a switch to select MCU vs Pi control.

```
                    ┌──── Switch position A ────┐
STC 89C516RD+ ─────┤                           ├──▶ Galvo Driver → Mirror
                    │                           │
Raspberry Pi 4 ─┐  └──── Switch position B ────┘
                │         ▲
                │         │
    SPI bus     ▼         │
┌──────────────────┐      │
│ MCP4922 (dual    │──────┘
│ 12-bit DAC, $3)  │  0-3.3V or ±5V (with level shifting)
└──────────────────┘
```

### Approach A: Raspberry Pi Pico co-processor (RECOMMENDED, ~$15)

The Pi 4 can't do real-time galvo control — Python + Linux aren't
deterministic enough for 20kHz+ output. Use a Pico as a bridge:

```
 Raspberry Pi 4                    Pico ($4)                  Laser
 ┌────────────┐    USB serial     ┌──────────┐    SPI       ┌────────┐
 │ Python     │◄──────────────────│ Real-time│───────────▶─│ MCP4922│
 │ sends      │   point data     │ loop at  │   10MHz     │ DAC    │
 │ point lists│   @ 115200 baud  │ 20-30kHz │             │ → galvo│
 └────────────┘                   └──────────┘             └────────┘
                                       │
                                       │ GPIO
                                       ▼
                                  ┌──────────┐
                                  │ R/G/B    │
                                  │ blanking │
                                  │ (MOSFET) │
                                  └──────────┘
```

**Parts list (~$15):**
| Part | Purpose | Price |
|------|---------|-------|
| Raspberry Pi Pico | Real-time point output at 20kHz+ | $4 |
| MCP4922 | Dual 12-bit SPI DAC (X + Y channels) | $3 |
| TL072 | Dual op-amp for level shifting (if bipolar needed) | $1 |
| 2N7000 × 3 | MOSFETs for RGB laser blanking | $1 |
| Resistors, caps | Voltage dividers, filtering | $2 |
| DPDT switch | MCU ↔ Pi selector | $2 |
| Breadboard + wires | Prototyping | $2 |

**Pico firmware (MicroPython or C):**
- Receives point stream over USB serial from Pi
- Outputs X/Y to MCP4922 via hardware SPI at 20-30kHz
- Controls RGB blanking via GPIO
- Double-buffered: receives next frame while outputting current

**Pi software (Python):**
- Generates point lists (shapes, text, animations)
- Sends to Pico over serial: `x16bit, y16bit, r8, g8, b8` per point
- At 30kHz, 1000 points = 33 retraces/sec = smooth, solid shapes

### Approach B: Helios DAC (~$100)

Pre-built USB ILDA DAC. Outputs ±5V differential (ILDA standard).
Would need wiring to the galvo driver inputs, but no custom electronics.
Python library available. Simplest if you want to skip the electronics.

**Problem:** The Helios outputs ILDA standard signals (±5V differential
on DB-25). Without an ILDA connector on the MK2, you'd need to wire the
Helios output directly to the galvo driver inputs. Need to confirm the
voltage levels from Mode 7 probing first.

### Approach C: Pi direct with pigpio DMA

Use the Pi 4's DMA engine via pigpio to output SPI at precise timing.
No Pico needed, but:
- Harder to get deterministic timing from Linux
- pigpio wave chains can do 1-2MHz SPI bursts but timing gaps exist
- Workable for 10-15kHz, maybe not clean enough for 30kHz
- More complex software

---

## Which Galvo Signals to Look For

When probing with Mode 7, measure between these points:

**Option 1: PWM from MCU → RC filter → Op-amp**
```
STC Pin ──► [R]──┬──[C]──GND  ──► Op-amp input
               filtered
               analog
```
- You'll see a smooth DC voltage that changes with position
- The MCU output pin will show PWM (square wave at >>1kHz)
- The RC filter smooths it to analog
- **Injection point:** between RC filter output and op-amp input

**Option 2: Parallel bus → External DAC → Op-amp**
```
STC P0/P1/P2 bus ──► DAC chip ──► Op-amp ──► Galvo
```
- Look for an 8 or 16-pin DIP/SOP connected to many MCU pins
- Common DACs: DAC0808 (8-bit), TLC5615 (10-bit SPI)
- **Injection point:** between DAC output and op-amp input

**What to measure:**
- At X-LEFT (DMX X=11): note voltage. Should be one extreme.
- At X-RIGHT (DMX X=255): note voltage. Should be other extreme.
- Typical range: either 0-5V unipolar or ±2.5V to ±5V bipolar
- Same for Y axis.

---

## Recommended Next Steps

### Step 1: Run `drawing_lab.py 2` — Find MCU rate
Determine the exact DMX processing speed of your specific MK2.
Start at 50ms hold, decrease until you stop seeing both states.
This tells you the minimum hold time for segment composition.

### Step 2: Run `drawing_lab.py 4` — Dual laser cross
This should give you a perfect, solid, no-flicker cross immediately.
Best DMX result possible.

### Step 3: Run `drawing_lab.py 7` — Probe galvo signals
With laser case open and multimeter:
1. Find galvo motor wires (2 per motor, usually thin flexible wires)
2. Trace back to PCB
3. Measure voltage at X-LEFT, X-RIGHT, Y-TOP, Y-BOTTOM positions
4. Identify the chip driving the galvos (op-amp? DAC?)
5. Report findings so we can design the direct drive circuit

### Step 4: Build Pico ILDA controller (~$15, ~1 day of work)
Once we know the voltage levels:
1. Wire MCP4922 DAC to Pico (4 SPI wires + CS)
2. Add level shifting if needed (op-amp circuit)
3. Add DPDT switch between MCU output and Pico output
4. Flash Pico with galvo controller firmware
5. Full arbitrary drawing at 20-30kHz!

---

## Summary

| Approach | Quality | Segments | Cost | Status |
|----------|---------|----------|------|--------|
| Dot tracing | ⭐⭐⭐ | N/A (points) | $0 | Working |
| Line compose (1 laser) | ⭐⭐⭐ | 2-3 usable | $0 | Working |
| Dual laser | ⭐⭐⭐⭐ | 2 solid | $0 | Working |
| Dual + compose | ⭐⭐⭐⭐ | 2 solid + N | $0 | Working |
| Pico direct drive | ⭐⭐⭐⭐⭐ | Unlimited | ~$15 | Needs probing |
| Helios DAC | ⭐⭐⭐⭐⭐ | Unlimited | ~$100 | Needs probing |

The STC 89C516RD+ is the bottleneck. At ~25-40Hz processing, DMX-only
approaches max out at 2-3 time-shared segments (plus 2 solid via dual laser).
For the QW logo and arbitrary shapes, direct galvo drive is the path forward.

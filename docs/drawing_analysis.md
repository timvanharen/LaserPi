# Precise Laser Drawing: Technical Analysis

How far can we push the MK2's DMX interface for custom shape drawing, and
what would it take to go beyond those limits?

---

## The Core Limitation

The EL-230RGB MK2 is a **pattern laser**, not an ILDA laser. Its architecture:

```
DMX-512 input                                    Galvo X/Y motors
    │                                                ↑
    ▼                                                │
┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│ DMX Receiver │────▶│ Microcontroller│────▶│ Galvo Drivers  │
│ (reads 9 ch) │     │ (pattern ROM)  │     │ (kHz scanning) │
└──────────────┘     └────────────────┘     └───────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ RGB Lasers   │
                     │ (blanking)   │
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

The MK2's microcontroller reads DMX at ~40Hz and generates galvo waveforms
from internal pattern ROM at **thousands of Hz**. We can't inject our own
scan paths through DMX — there's a microcontroller in the middle interpreting
our commands and running its own scan algorithm.

---

## DMX-Based Approaches (Software Only)

### Approach 1: Dot-Tracing (Current — draw_shapes.py)

**How it works:** Use smallest pattern (0) at zoom 0 as a "pen", move
X/Y position rapidly to trace shapes via persistence of vision.

**Speed:** We update the DMX buffer continuously. The DMX TX thread sends
frames at 40Hz, but the universe buffer is updated in real-time by the
draw thread (~500 updates/sec). The MK2 sees new X/Y values each DMX frame.

**Effective resolution:** ~40 unique positions per second (DMX refresh rate).
At 40 points/sec, a shape with 40 points retraces once per second —
visible but flickery. Simpler shapes (10-20 points) retrace 2-4 times/sec.

**Pen size:** Pattern 0 at zoom 0 is the smallest, but it's still a small
octagon, not a true point. The galvo mirrors are scanning that octagon at
the internal kHz rate, so you see a small bright shape at each position.

**Verdict:** ⭐⭐⭐ Works for simple shapes. Flickery for complex ones.

---

### Approach 2: Line Segment Composition (drawing_lab.py Mode 2/3)

**How it works:** Instead of a dot pen, use **full line patterns** (60=horizontal,
70=vertical, 80=diagonal) as wide "brushes". Position each line at a specific
X/Y to build shapes from line segments.

```
Example: Rectangle from 4 line segments

  ═══════════  ← horizontal line pattern at (128, 70)
  ║         ║
  ║         ║  ← vertical line patterns at (70, 128) and (190, 128)
  ║         ║
  ═══════════  ← horizontal line pattern at (128, 190)
```

**Key advantage:** Each line segment is drawn by the MK2's **internal scanner
at kHz speed** — so while that segment is active, it's a persistent, solid,
bright line. No flickering within a single segment.

**Limitation:** We can only show ONE segment per DMX frame. At 40Hz with
4 segments, each shows 10 times/sec. That's borderline — you'll see each
line flash. With more segments, it gets worse.

**Optimization:** Our DMX universe is only 22 channels. A full 22-channel
DMX frame takes ~1.2ms to transmit:
- Break: 150μs + MAB: 12μs + Start: 44μs + 22×44μs = ~1.2ms
- Theoretical max: ~800 frames/sec

Mode 3 (Fast DMX) overrides the refresh rate to 500Hz, which could make
4 segments display at 125Hz each — smooth enough for persistence of vision.

**Verdict:** ⭐⭐⭐⭐ Most promising DMX approach. Best for blocky shapes
made of H/V lines (like text, logos). Need to test if MK2 responds at >40Hz.

---

### Approach 3: Pattern Strobe / Interruption (drawing_lab.py Mode 4)

**How it works:** Display a full pattern, then rapidly toggle color=0
(dark) / color=255 (lit) to "slice" the pattern at arbitrary moments.

**Problem:** The MK2's internal scan is asynchronous to our DMX updates.
We can't control WHERE in the scan the blanking occurs. The result
would be random partial patterns — not useful for precise drawing.

**Possible use:** Could create interesting visual effects (strobing,
partial patterns) even if not precisely controllable.

**Verdict:** ⭐⭐ Interesting for effects, not for precise drawing.

---

### Approach 4: Dual Laser Composition (drawing_lab.py Mode 5)

**How it works:** Use BOTH lasers at the same time. Each displays a
different positioned line segment — no time-sharing needed.

**With 2 lasers:** 2 persistent line segments simultaneously.
- Cross/plus = perfect (1 horizontal + 1 vertical)
- T-shape, L-shape, corners = all work

**Limitation:** Only 2 simultaneous segments. For complex shapes,
you'd need to combine with time-sharing.

**Verdict:** ⭐⭐⭐ Perfect for 2-segment shapes. Combine with
time-sharing for more complex compositions.

---

### Approach 5: Mixed Mode (drawing_lab.py Mode 6)

**How it works:** One laser dot-traces an outline (persistence of vision),
the other displays a static positioned line for structure/fill.

**Best of both worlds:** The traced outline provides shape recognition,
the static line adds a bright persistent element.

**Verdict:** ⭐⭐⭐ Good for shapes that combine curves and straight lines.

---

## Beyond DMX: Hardware Approaches

### Option A: ILDA Input Hack (Recommended)

Most budget laser projectors, including the MK2, use standard galvo scanner
boards internally. Many have **unused ILDA connectors** on the PCB that
aren't wired to the housing.

**What to look for inside the MK2:**

1. **Open the case** (screws on bottom/back, watch for the interlock switch)
2. **Find the main PCB** — the controller board with the DMX connector
3. **Look for:**
   - A DB-25 connector or unpopulated DB-25 footprint (standard ILDA)
   - Labeled test points: X+, X-, Y+, Y-, R, G, B, GND, INTERLOCK
   - A ribbon cable or wire harness going to the galvo driver boards
4. **Identify galvo driver inputs** — usually ±5V or ±10V differential analog

**If you find ILDA inputs or even just the galvo driver inputs, you can:**

```
Raspberry Pi 4
    │
    │ SPI bus (10 MHz)
    ▼
┌──────────────┐
│ MCP4922      │  ← Dual 12-bit DAC ($3)
│ (or MCP4822) │     2 channels: X + Y
└──────┬───────┘
       │ 0-3.3V unipolar
       ▼
┌──────────────┐
│ Op-amp       │  ← TL072 or similar ($1)
│ circuit      │     Convert to ±5V or ±10V bipolar
└──────┬───────┘
       │ ±5V/±10V differential
       ▼
┌──────────────┐
│ MK2 Galvo    │  ← Connect to X+/X- and Y+/Y- inputs
│ Driver Board │
└──────────────┘

For RGB blanking:
Pi GPIO → MOSFET/transistor → MK2 laser diode enable pins
```

**Required components (~$10-15):**
- MCP4922 dual 12-bit SPI DAC
- TL072 dual op-amp
- A few resistors and capacitors (for bipolar conversion)
- 2N7000 MOSFETs or BC547 transistors (for RGB blanking)
- Toggle switch (to choose between MCU or Pi control)

**Software approach:**
- Can't use Python directly — too slow for kHz galvo rates
- Use **pigpio** library's wave/DMA functions for hardware-timed SPI
- Or use a **Pico/ESP32** as an intermediate ILDA controller:
  Pi → USB serial → Pico → SPI → DAC → galvos (Pico runs real-time loop)

**Sample rate needed:** 20-30kHz for smooth curves, 10kHz minimum.
At 12-bit resolution, that's ~20k points/sec = smooth, flicker-free shapes.

---

### Option B: External ILDA DAC (Easiest Hardware Approach)

Buy a dedicated ILDA DAC and connect it to the MK2's galvo inputs:

| Device | Price | Connection | Software |
|--------|-------|------------|----------|
| **Helios DAC** | ~$100 | USB → ILDA DB-25 | Python SDK available |
| **EtherDream** | ~$200 | Ethernet → ILDA DB-25 | Python library |
| **LaserCube** | ~$300 | WiFi/USB → ILDA | App + SDK |

**Helios DAC** is the best budget option:
- 65kHz max sample rate
- USB connection to Pi
- Python library: `pip install helios-dac`
- Outputs ±5V differential (ILDA standard)
- Just need to wire it to the MK2's galvo inputs

```python
# Example with Helios DAC (hypothetical)
import helios

dac = helios.DAC()
dac.connect()

# Draw a circle at 30kHz
points = []
for i in range(1000):
    angle = 2 * math.pi * i / 1000
    x = int(2048 + 2000 * math.cos(angle))  # 12-bit: 0-4095
    y = int(2048 + 2000 * math.sin(angle))
    r, g, b = 255, 255, 255
    points.append(helios.Point(x, y, r, g, b))

dac.write_frame(points, 30000)  # 30kHz
```

---

### Option C: Full DIY ILDA Controller

Build a complete ILDA output from the Pi using:
- **Raspberry Pi Pico** as a real-time co-processor ($4)
- Pi sends point data over USB serial to Pico
- Pico outputs to dual DAC at 20kHz+ via hardware SPI
- Most flexible, most work

---

## Recommendation: What to Try First

### 1. Software experiments (today)

Run `drawing_lab.py` and test each mode on the actual hardware:

```bash
python examples/drawing_lab.py 1   # Find smallest pen
python examples/drawing_lab.py 2   # Line composition at 40Hz
python examples/drawing_lab.py 3   # Line composition at 500Hz (key test!)
python examples/drawing_lab.py 4   # Pattern strobe experiments
python examples/drawing_lab.py 5   # Dual laser composition
python examples/drawing_lab.py 6   # Mixed approach
```

**Mode 3 is the key experiment**: if the MK2 responds to DMX faster than
40Hz, line segment composition becomes very practical. Even at 100Hz with
4 segments, each refreshes 25 times/sec = smooth.

### 2. Peek inside the laser (this week)

Open the case and photograph the PCB. Look for:
- ILDA connector or test points
- Galvo driver board model numbers
- Wire colors going to galvo motors

Post photos and I can help identify the signals.

### 3. Hardware hack (if ILDA inputs exist)

If you find ILDA inputs inside, a Helios DAC (~$100) gives you full
arbitrary shape drawing at 30kHz+ with a Python API. No soldering DAC
circuits — just wire the DB-25 to the galvo inputs.

---

## QW Logo Strategy

Without seeing the exact logo, for blocky text made of straight lines:

**Best DMX approach:** Mode 2/3 (Line Composer)
- Define each stroke of "Q" and "W" as a positioned H/V line segment
- Q ≈ 5 segments (top, bottom, left, right, diagonal tail)
- W ≈ 5-6 segments (depends on style)
- Total: ~10-11 segments
- At 40Hz: each shows ~4x/sec (flickery) → need Fast DMX (Mode 3)
- At 500Hz: each shows ~45x/sec (smooth!)

**Best hardware approach:** Helios DAC drawing the vector outline
- Unlimited complexity, smooth, bright, no flicker
- Would look like a professional laser show

---

## Summary

| Approach | Complexity | Quality | Cost |
|----------|-----------|---------|------|
| Dot tracing (current) | Done ✓ | ⭐⭐⭐ | $0 |
| Line composition 40Hz | Done ✓ | ⭐⭐⭐ | $0 |
| Line composition 500Hz | Done ✓ | ⭐⭐⭐⭐ | $0 |
| Dual laser | Done ✓ | ⭐⭐⭐ | $0 |
| Pattern strobe | Done ✓ | ⭐⭐ | $0 |
| ILDA hack (Helios DAC) | Medium | ⭐⭐⭐⭐⭐ | ~$100 |
| DIY ILDA (MCP4922+Pico) | Hard | ⭐⭐⭐⭐⭐ | ~$15 |

The DMX experiments in `drawing_lab.py` will tell you how far you can push
the MK2 via software alone. If you want true arbitrary drawing, cracking
the case and adding an ILDA DAC is the way to go.

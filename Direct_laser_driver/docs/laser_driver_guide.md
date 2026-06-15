# Laser Driver Circuit Guide

DIY constant-current RGB laser driver for Raspberry Pi GPIO control. All three channels run from the **12V rail** (the blue laser's Vf exceeds 4.3V, making 5V insufficient).

## Measured Laser Diode Characteristics

### Red — 650 nm, 100 mW

| Voltage (V) | Current (mA) | Notes |
|-------------|-------------|-------|
| 1.73 | 1.02 | Below threshold |
| 1.88 | 8.68 | Below threshold |
| 2.12 | 49 | **Lasing threshold — starts shining** |

Standard laser diode behavior. Vf rises gradually with current. At operating power (100 mW), expect ~150–250 mA and Vf around 2.2–2.5V.

### Green — 532 nm, 20 mW (DPSS module)

| Voltage (V) | Current (mA) | Notes |
|-------------|-------------|-------|
| 1.31 | 0.166 | |
| 1.41 | 1.02 | |
| 1.53 | 7 | |
| 1.56 | 12 | |
| 1.71 | 110 | **Starts shining dimly** |

**This is a DPSS (Diode-Pumped Solid-State) laser.** The low Vf (~1.7V) confirms you're driving an 808 nm infrared pump diode, not a direct green emitter. Inside the module, the IR pump beam passes through frequency-doubling crystals (typically Nd:YVO₄ + KTP) to produce 532 nm green light.

**DPSS implications:**
- Hard lasing threshold at ~100–110 mA pump current — below this, zero green output
- PWM dimming does NOT work below threshold (the laser simply turns off at low duty cycles)
- For brightness control, vary the pump current above threshold instead of using PWM
- DPSS pump diodes are **very sensitive to overcurrent** — destruction is instant and permanent
- The module may also emit invisible 808 nm IR light from the pump — green-only laser goggles are NOT sufficient

### Blue — 445 nm, 50 mW

| Voltage (V) | Current (mA) | Notes |
|-------------|-------------|-------|
| 3.09 | 1.0 | Below threshold |
| 3.60 | 5.06 | Very faint dot |
| 3.92 | 12.2 | Below full threshold |
| 4.34 | 26.6 | **Sharper dot visible** |

InGaN laser diode. High Vf characteristic of blue/violet diodes. At operating power (50 mW), expect ~50–120 mA and Vf around 4.5–5.0V. **A 5V supply cannot drive this diode** — there's no headroom for current limiting. The 12V supply is mandatory.

## Circuit Design: LM317 Constant-Current Driver

The LM317 voltage regulator can be configured as a precision constant-current source. This is **much safer** for unknown laser diodes — the current is regulated regardless of temperature changes or Vf drift.

**Per-channel schematic: Made by myself not from AI agent**

```
    12V ────┐                          ┌─────────┬────────────────────┬─────────────────────┐
            │                          │         |                    |                     |                          
            │  ┌─────────┐             │         |                    |                     | 
            ├──┤ IN   OUT├─────────────┤         |                    |                  ───┴───
            │  │  LM317  │            ┌┴┐        |                    |                  \     / Laser diode
            │  │      ADJ├──┐         │ │ 260    |                    |                   \   /
            │  └─────────┘  │         │ │        |                    |                  ───┬───
            │               │         └┬┘       ─┴─                ───┴───                  |    
           ─┴─             ┌┴┐         │  100nF      Cout    D1     /   \  1N4004           /  collector                             
     100nF     Cin     10k │ │ R_set   │        ─┬─                /     \              b |/    NPN S8050                              
           ─┬─             │ │<────────┘         |                 ───┬───  GPIO─┬─R=560──┤                                     
            │              └┬┘                   |                    |         ┌┴┐       |\                            
            │               │                    |                    |         │ │ R10k    \  emitter                          
            │               │                    |                    |         └┬┘          |                                                                                  
    GND ────┴───────────────┴────────────────────┴────────────────────┴──────────┴───────────┘z
```

**LM317 current formula:  BULLSHIT**

$$I_{out} = \frac{1.25V}{R_{set}}$$

| Channel | Target I | R_set | R_set power | LM317 dissipation |
|---------|----------|-------|-------------|-------------------|
| Red 650nm | 200 mA | 6.25Ω (use 6.2Ω) | 0.25W | (12-2.5-1.25)×0.2 = 1.65W |
| Green 532nm | 150 mA | 8.33Ω (use 8.2Ω) | 0.19W | (12-1.7-1.25)×0.15 = 1.36W |
| Blue 445nm | 100 mA | 12.5Ω (use 12Ω) | 0.125W | (12-4.5-1.25)×0.1 = 0.625W |

> **Adjustable alternative**: Replace R_set with a fixed resistor + trim pot in parallel. For example, Red: 12Ω fixed ∥ R_trim — as you decrease R_trim, total resistance drops, current increases. Start with trim pot disconnected (infinite resistance, only R_fixed), then slowly bring in the trim pot to increase current.

**LM317 heat dissipation**: The LM317 dissipates $(V_{in} - V_{out} - 1.25V) \times I_{out}$. At 1.65W for the red channel, use a **small heatsink** (TO-220 clip-on or PCB copper area). Without a heatsink, the LM317 will thermal-shutdown at ~1.5W.

### MOSFET Selection

**IRLZ44N** (recommended):
- Logic-level gate: turns fully ON at 3.3V (Vgs(th) = 1.0–2.0V)
- Rds(on) = 0.022Ω at Vgs = 5V (negligible voltage drop)
- Package: TO-220
- Way overkill for this current range, but cheap and widely available

**Alternatives**: IRLZ34N, IRL540N, IRL3803 — any logic-level N-channel MOSFET with Vgs(th) < 2.5V.

### Gate Drive Circuit

```
Pi GPIO ──[1kΩ]──┬── MOSFET Gate
                  │
                 [10kΩ]
                  │
                 GND
```

- **1kΩ series resistor**: Limits transient gate charge current, protects GPIO pin
- **10kΩ pull-down to GND**: Ensures MOSFET is **OFF** when GPIO is floating (at boot, during reset, or if the Pi crashes). **This is a critical safety feature** — without it, the laser may turn ON uncontrolled

## Bill of Materials (per channel × 3)

### Option A (resistor-based)

| Component | Value | Rating | Qty | Notes |
|-----------|-------|--------|-----|-------|
| R_fixed | See table | 5W | 1 | Current limiting |
| R_trim | 50–100Ω | Multi-turn | 1 | Fine current adjust |
| MOSFET | IRLZ44N | TO-220 | 1 | Logic-level N-channel |
| R_gate | 1kΩ | 1/4W | 1 | Gate current limit |
| R_pulldown | 10kΩ | 1/4W | 1 | Gate pull-down (safety) |
| C_bypass | 100nF | 25V ceramic | 1 | Local decoupling |

### Option B (LM317 constant-current, recommended)

| Component | Value | Rating | Qty | Notes |
|-----------|-------|--------|-----|-------|
| LM317 | — | TO-220 | 1 | Constant-current regulator |
| R_set | See table | 1/2W | 1 | Sets current |
| R_trim (optional) | 0–50Ω | Multi-turn | 1 | Fine current adjust (parallel with R_set) |
| MOSFET | IRLZ44N | TO-220 | 1 | On/off switching |
| R_gate | 1kΩ | 1/4W | 1 | Gate current limit |
| R_pulldown | 10kΩ | 1/4W | 1 | Gate pull-down (safety) |
| C_in | 100nF | 25V ceramic | 1 | LM317 input bypass |
| Heatsink | TO-220 clip | — | 1 | For LM317 dissipation |

### Shared components (× 1)

| Component | Value | Notes |
|-----------|-------|-------|
| C_bulk | 470µF 25V | Electrolytic, on 12V input rail |
| D_protection | 1N5819 | Schottky diode, reverse polarity protection on 12V input |

## Assembly & Testing Procedure

### Step 1: Bench-Test Each Channel

**Before soldering to the PCB**, test each laser channel on a breadboard or with flying leads:

1. Assemble one channel circuit (LM317 + R_set or R_fixed)
2. Connect to 12V supply with a **current-limited bench supply** if available
3. **Without the laser connected**, measure the current through a dummy load (resistor matching approximate Vf):
   - Red: use a 10Ω dummy → expect ~200mA
   - Green: use a 5Ω dummy → expect ~150mA
   - Blue: use a 20Ω dummy → expect ~100mA
4. Verify current matches expectations
5. Connect the actual laser diode
6. For the **green DPSS module**: slowly increase current (adjust trim pot) until green light appears. Note the threshold current. Set the operating point 10–20% above threshold for reliable lasing. **Do NOT go higher without knowing the absolute maximum rating.**
7. For red and blue: adjust trim pot to desired brightness. If unsure of maximum rating, stay conservative (50–70% of estimated max current).

### Step 2: Verify Safety Features

1. **Boot test**: Power cycle the Pi with laser driver connected. Laser must stay **OFF** throughout boot (10kΩ pull-down holds MOSFET gate low)
2. **Crash test**: Kill the Python process with Ctrl+C. Laser must turn OFF (try/finally in software + pull-down on hardware)
3. **Pull-down check**: Disconnect GPIO wire from gate. Laser must be OFF (pull-down holds gate low)

### Step 3: PWM Test

1. Run `examples/laser_test.py`
2. Verify red and blue dim smoothly with PWM (0–100% duty)
3. Verify green turns on/off cleanly (no dimming expected — DPSS is on/off only at the lasing-threshold boundary)

## PWM Frequency

Use **1–10 kHz** PWM frequency:
- Below 100 Hz: visible flicker
- 100–500 Hz: may cause audible noise in the circuit
- 1–10 kHz: smooth dimming, no audible noise, within pigpio capability
- Above 20 kHz: may cause EMI issues, unnecessary

The `pigpio` library provides DMA-timed PWM on all GPIO pins with 0–100% duty cycle at configurable frequency. Even software-timed PWM from pigpio is far more stable than RPi.GPIO because pigpio runs as a separate daemon with real-time priority.

## Green DPSS Dimming Strategies

Since the green DPSS module doesn't support proportional PWM dimming (it's either lasing or not):

1. **Binary on/off** (simplest): GPIO HIGH = green on, GPIO LOW = green off. No brightness control — set brightness via the trim pot/R_set once and leave it.

2. **Threshold-biased PWM** (advanced): Keep the MOSFET on continuously (green always conducting above threshold), and use a second MOSFET or transistor to add/remove a small current delta for fine brightness control. Complex — only attempt if you need it.

3. **On-time modulation** (for patterns): If the green channel feels too bright during pattern tracing, reduce the "on" time per point instead of PWM duty. During a shape trace, skip the green channel on some points. This is handled in software by the pattern coordinator.

**Recommendation**: Start with binary on/off (option 1). It's simple, reliable, and you set the brightness once with the trim pot.

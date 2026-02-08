# MK2 Pattern Reference

Discovered patterns for EL-230RGB MK2 lasers

**How to use this document**: As you test patterns using `pattern_scan.py` and `color_test.py`, document your findings here!

---

## Channel Behavior Summary

### Channel 5: Scanning Speed
- Controls how fast the galvo mirrors move
- **0**: Slowest mirror movement (slow scanning)
- **128**: Medium speed (recommended default)
- **255**: Fastest movement (may cause flickering or instability)
- **Effect**: Higher values = faster/more energetic patterns

### Channel 8: Color
Determines which color(s) are displayed. Exact behavior may vary by pattern.

**Typical behavior** (document actual findings below):
- **0-63**: Red tones
- **64-127**: Green tones  
- **128-191**: Blue tones
- **192-255**: White/mixed colors

| Value | Observed Color | Notes |
|-------|----------------|-------|
| 0 | ? | Test and document |
| 64 | ? | |
| 128 | ? | |
| 192 | ? | |
| 255 | ? | Typically white/full spectrum |

### Channel 9: Color Segment
Controls segmentation or colorization of pattern elements. Behavior is pattern-dependent.

**Possible behaviors**:
- Selects which portions of pattern are colored
- Enables multicolor effects
- Splits pattern into colored segments

| Value | Observed Effect | Notes |
|-------|-----------------|-------|
| 0 | ? | Test and document |
| 128 | ? | |
| 255 | ? | |

---

## Static Patterns (Channel 1: 150-199)

Set Channel 1 to any value between 150-199 to enable static pattern mode, then use Channel 2 to select patterns.

| Pattern # (Ch 2) | Description | Best Settings | Notes |
|------------------|-------------|---------------|-------|
| 0 | ? | | Default pattern |
1-4: octagon
5-9: Wiggly octagon?
10 - : dashed lined octagon
15: Chaser octagon
20: two circles in horizontal allignment
25: 
30
35
40
45
50
55
60
65
70
75
80
85
90
95
100
105
110
115
120
125
130
135
140
145
150
155
160
165
170
175
180
185
190
195
200
205
210
215
220
225
230
235
240
245
250
255


**Circle patterns**: Document which pattern numbers create circles here!

**Other interesting patterns**:
- Pattern ?: Description
- Pattern ?: Description

---

## Dynamic Patterns (Channel 1: 200-255)

Set Channel 1 to any value between 200-255 to enable dynamic pattern mode (animated patterns).

Channel 6 controls the animation speed for dynamic patterns.

| Pattern # (Ch 2) | Description | Best Settings | Notes |
|------------------|-------------|---------------|-------|
| 0 | ? | | Default dynamic pattern |
| 1 | ? | | |
| ... | | | |

**Note**: Dynamic patterns often look better with:
- Lower scanning speed (Channel 5: 64-128)
- Adjust dynamic speed (Channel 6) to taste

---

## Recommended Presets

Document your favorite working combinations here!

### Preset: "Circle - Basic"
```
Mode: Static Pattern (Ch1: 175)
Pattern: ? (Ch2: ?)
Color: 255 (white)
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 128
Scanning Speed: 128
```

### Preset: "Your Custom Name"
```
Mode: ?
Pattern: ?
Color: ?
Color Segment: ?
X/Y: ?
Zoom: ?
Scanning Speed: ?
Dynamic Speed: ? (if using dynamic mode)
```

---

## Testing Notes

**Date**: YYYY-MM-DD  
**Tester**: Your Name  
**Laser Model**: EL-230RGB MK2  
**Firmware Version**: (if known)

### General Observations:
- 
- 

### Quirks & Tips:
- 
- 

### Best Combinations Discovered:
- 
- 

---

## Contributing

Please share your discoveries! See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to submit your pattern findings to the project.

**To update this file**:
1. Test patterns using the example scripts
2. Document what you observe
3. Share interesting combinations
4. Note any unexpected behaviors

Your contributions help everyone use these lasers more effectively! 🎆

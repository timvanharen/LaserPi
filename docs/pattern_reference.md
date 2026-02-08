# MK2 Pattern Reference

Complete pattern documentation for Laserworld EL-230RGB MK2 lasers  
**Tested and documented patterns for all 256 values in both Static and Dynamic modes**

---

## Quick Reference

### Channel Behavior Summary

| Channel | Function | Range | Notes |
|---------|----------|-------|-------|
| **1** | Mode Selection | 0-49: Off<br>50-99: Sound<br>100-149: Auto<br>**150-199: Static**<br>**200-255: Dynamic** | Set to 150-199 for static patterns, 200-255 for dynamic |
| **2** | Pattern Selection | 0-255 | Selects which pattern to display |
| **3** | X Position | 1-10: Center<br>11-255: Position | Horizontal positioning |
| **4** | Y Position | 1-10: Center<br>11-255: Position | Vertical positioning |
| **5** | Scanning Speed | 0-255 | **Higher = faster mirror movement**<br>Recommended: 128 |
| **6** | Dynamic Speed | 0-255 | Animation speed (dynamic mode only) |
| **7** | Zoom/Size | 0-255 | Pattern size |
| **8** | Color | 0-255 | Color palette selection |
| **9** | Color Segment | 0-255 | Color distribution/segmentation |

### Recommended Settings for Testing

```
Mode: Static Pattern (Ch1: 175)
Color: 255 (full/white)
Color Segment: 0
X/Y: Centered (5, 5)  
Zoom: 128 (medium)
Scanning Speed: 128 (medium)
```

---

## Static Patterns (Channel 1: 150-199, Channel 2: 0-255)

Set **Channel 1** to any value between **150-199** to enable static pattern mode.  
Use **Channel 2** (0-255) to select specific patterns.

### Geometric Shapes - Basic

| Pattern # | Description | Category |
|-----------|-------------|----------|
| **0-4** | Octagon | Polygon |
| **5-9** | Wiggly octagon | Polygon - distorted |
| **10-14** | Dashed octagon | Polygon - dashed |
| **15-19** | Chaser octagon | Polygon - animated effect |

### Circles & Multi-Circle Patterns

| Pattern # | Description | Notes |
|-----------|-------------|-------|
| **20-24** | Two circles - horizontal alignment | Side by side |
| **25-29** | Three circles - triangle formation | △ arrangement |
| **30-34** | Four circles - square formation | □ arrangement |
| **35-39** | Two circles | Variation |
| **40-44** | Two circles - dashed | Dashed effect |

### Lines - Animated

| Pattern # | Description | Behavior |
|-----------|-------------|----------|
| **45-49** | Horizontal line expanding | Extends from middle outward |
| **50-54** | Horizontal line shrinking | Shrinks exponentially over time |
| **55-59** | Horizontal line pulsing | Continuously extends/shrinks (variable time steps) |

### Lines - Static

| Pattern # | Description | Orientation | Length |
|-----------|-------------|-------------|--------|
| **60-64** | Horizontal line | — | ~40% |
| **65-69** | Horizontal line - dashed | - - - | ~40% |
| **70-74** | Vertical line | \| | ~40% |
| **75-79** | Vertical line - dashed | : | ~40% |
| **80-84** | Diagonal line | / | ~40% |
| **85-89** | Diagonal line - dashed | / - / | ~40% |

### Lines - Dual/Paired

| Pattern # | Description | Configuration |
|-----------|-------------|---------------|
| **90-94** | Two horizontal lines | = = |
| **95-99** | Two horizontal lines - dashed | - - - - |
| **100-104** | Two vertical lines | \|\| |
| **105-109** | Two vertical lines - dashed | : : |
| **110-114** | Two diagonal lines diverging | \ / (20% length each) |
| **115-119** | Two diagonal lines diverging - dashed | \ / dashed |

### Triangles & Basic Shapes

| Pattern # | Description | Orientation |
|-----------|-------------|-------------|
| **120-124** | Triangle | Tip pointing down ▽ |
| **125-129** | Triangle - dashed | Tip pointing down ▽ (dashed) |
| **130-134** | Triangle | Tip pointing up △ |
| **135-139** | Triangle - dashed | Tip pointing up △ (dashed) |
| **140-144** | Cross | + |
| **145-149** | Cross - dashed | + (dashed) |

### Squares & Rectangles

| Pattern # | Description | Size |
|-----------|-------------|------|
| **150-154** | Square | Standard |
| **155-159** | Square - dashed | Standard |
| **160-164** | Square | Slightly larger |
| **165-169** | Square - dashed | Slightly larger |

### Complex Patterns

| Pattern # | Description | Details |
|-----------|-------------|---------|
| **170-174** | Five horizontal lines | "Staircase" pattern (left bottom → right top) |
| **175-179** | Five vertical lines | "V-shape" formation |
| **180-184** | Jagged 4-point star | ✦ |
| **185-189** | Jagged 4-point star | ✦ (rotated 90°) |
| **190-194** | 5-point star (jagged) | ★ |
| **195-199** | 5-point star | ★ (rotated 90°) |

### Waves & Spirals

| Pattern # | Description | Wavelengths |
|-----------|-------------|-------------|
| **200-204** | Pentagon | 5-sided polygon |
| **205-209** | Wave symbol | 2 wavelengths |
| **210-214** | Wave symbol | 3 wavelengths (smaller) |
| **215-219** | Wave symbol | 7 wavelengths |
| **220-224** | Wave - dashed | 2 wavelengths |
| **225-255** | Spiral | Expanding outward |

---

## Dynamic Patterns (Channel 1: 200-255, Channel 2: 0-255)

Set **Channel 1** to any value between **200-255** to enable dynamic (animated) pattern mode.  
Use **Channel 2** (0-255) to select specific patterns.  
**Channel 6** controls animation speed.

💡 **Tip**: Dynamic patterns often look better with lower scanning speed (Ch5: 64-128)

### Circles - Growing/Moving

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **0-4** | Circle enlarging | 9 steps, changes horizontal position every 3 cycles |
| **5-9** | Circle enlarging | Perforated lines, similar to 0-4 |
| **10-14** | Circle enlarging - dashed | 9 steps, changes position |
| **15-19** | Small circles | Moving in circular orbit |
| **20-24** | Dots to octagon | Increases from 3 dots → octagonal → full circle/"chaser" |

### Circles - Complex Animations

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **45-49** | Random circles | Appear and disappear randomly |
| **50-54** | Chaser circles | Different sizes with chaser effect |
| **55-59** | Circles moving | Growing/shrinking, moving around, dashed or full, random |
| **60-64** | Large dashed circle | Dashed circle with moving gaps (rotating holes) |
| **65-69** | Two circles | Opposite circular paths, collide with constructive interference |
| **70-74** | Three circles | Rotating around center |

### Lines - Random/Moving

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **75-79** | Random lines | Moving around, sometimes dashed |
| **80-84** | Horizontal lines | Random positions, shrinking/growing |
| **85-89** | Horizontal lines - dashed | Random positions, shrinking/growing |
| **90-94** | Random lines | Growing, shrinking, moving, rotating (various timesteps) |
| **95-99** | Random lines - dashed | Growing, shrinking, moving, rotating |

### Lines - Rotating

| Pattern # | Description | Rotation Behavior |
|-----------|-------------|-------------------|
| **100-104** | Single line rotating | Rotation point at center of line, clockwise |
| **105-109** | Single line rotating | Rotation point at one tip, clockwise |
| **110-114** | Three lines | Radiating from center, rotating clockwise |

### Lines - Translating

| Pattern # | Description | Movement |
|-----------|-------------|----------|
| **120-124** | Horizontal line - dashed | Moving upward and growing |
| **125-129** | Horizontal line splitting | One line splits into two, reaches extremes, returns to center |
| **130-134** | Horizontal line splitting - dashed | Same as 125-129 but dashed |
| **135-139** | Vertical line | Moving left → right → left |
| **140-144** | Vertical line - dashed | Moving left → right → left |
| **145-149** | Vertical line splitting | One line splits into two, reaches extremes, returns to center |
| **150-154** | Vertical line splitting - dashed | Same as 145-149 but dashed |

### Squares & Rectangles - Animated

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **155-159** | Square | Growing and shrinking |
| **160-164** | Square - dashed | Growing and shrinking |
| **165-169** | Rectangle | Growing/shrinking in width |
| **170-174** | Square | Rotating |
| **175-179** | Rectangle | Rotating |

### Tracing/Scanning Patterns

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **180-184** | Octagon tracing | Single line traces octagon outline in steps |
| **185-189** | Octagon tracing - dashed | Same as 180-184 but dashed |

### Waves & Oscillations

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **190-194** | Wave (2 wavelengths) | Rotating anti-clockwise |
| **195-199** | Wave (2 wavelengths) - dashed | Rotating anti-clockwise |
| **200-204** | Wave (2 wavelengths) | Horizontal, changing phase, moving around, frequency increases |
| **205-209** | Wave (2 wavelengths) - dashed | Same as 200-204 but dashed |
| **210-214** | Wave (1 wavelength) | Amplitude increase/decrease, 180° phase shift, repeat |
| **215-219** | Wave (1 wavelength) - dashed | Same as 210-214 but dashed |

### Stars & Polygons - Rotating

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **220-224** | 4-point star | Rotating ✦ |
| **225-229** | 5-point star | Rotating ★ |
| **230-234** | Pentagon | Rotating |

### Special Effects

| Pattern # | Description | Animation |
|-----------|-------------|-----------|
| **235-239** | Parabola | Orientation changes like bird flapping wings |
| **240-255** | V-shape | Size increases, flips upside down, decreases; becomes dashed after 3 cycles |

---

## Recommended Presets

Tested configurations that produce good results:

### Static Patterns

**Single Dot (for position testing)**
```yaml
Mode: Static Pattern (Ch1: 175)
Pattern: 0
Color: 255 (white)
Color Segment: 0
X/Y: Centered (5, 5) or custom
Zoom: 128
Scanning Speed: 128
```

**Circles - Dual Horizontal**
```yaml
Mode: Static Pattern (Ch1: 175)
Pattern: 20-24
Color: 255 (white)
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 150 (larger circles)
Scanning Speed: 128
```

**Static Lines (for calibration)**
```yaml
Mode: Static Pattern (Ch1: 175)
Pattern: 60 (horizontal), 70 (vertical), 80 (diagonal)
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 128
Scanning Speed: 200 (fast for smooth lines)
```

**5-Point Star**
```yaml
Mode: Static Pattern (Ch1: 175)
Pattern: 190-194
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 150
Scanning Speed: 128
```

### Dynamic Patterns

**Rotating Circle Trail**
```yaml
Mode: Dynamic Pattern (Ch1: 225)
Pattern: 15-19 (small circles in orbit)
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 128
Scanning Speed: 100 (slower for smooth animation)
Dynamic Speed: 128
```

**Expanding Circle**
```yaml
Mode: Dynamic Pattern (Ch1: 225)
Pattern: 0-4
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 128
Scanning Speed: 100
Dynamic Speed: 100 (adjust to taste)
```

**Rotating Star**
```yaml
Mode: Dynamic Pattern (Ch1: 225)
Pattern: 225-229 (5-point star)
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 150
Scanning Speed: 80
Dynamic Speed: 80 (slower rotation)
```

**Wave Animation**
```yaml
Mode: Dynamic Pattern (Ch1: 225)
Pattern: 200-204
Color: 255
Color Segment: 0
X/Y: Centered (5, 5)
Zoom: 128
Scanning Speed: 100
Dynamic Speed: 120
```

---

## Usage Tips

### Pattern Selection Strategy

1. **For positioning/alignment**: Use static patterns 60-89 (straight lines)
2. **For visual effects**: Dynamic patterns 0-74 (circles and organic movements)
3. **For geometric shows**: Static patterns 120-199 (triangles, squares, stars)
4. **For calibration**: Static patterns 80-84 (diagonal lines show motor lag most clearly)

### Scanning Speed Guidelines

| Speed Range | Best For | Notes |
|-------------|----------|-------|
| **0-50** | Slow animations, precise positioning | May appear sluggish |
| **50-100** | Dynamic patterns with smooth movement | Good for organic effects |
| **100-150** | General purpose, balanced performance | **Recommended default** |
| **150-200** | Fast scanning, sharp static patterns | Good for lines |
| **200-255** | Maximum speed | May cause flickering |

### Known Issues

- **Diagonal lines (80-84)**: Single-motor axis lines (horizontal/vertical) appear straighter than diagonal lines due to galvo motor response differences
  - **Solution**: Use the `galvo_tuning.py` script to calibrate lag compensation
- **Pattern 225-255 (spirals)**: May not respect zoom settings consistently
- **Some dynamic patterns**: Animation speed (Ch6) may override scanning speed (Ch5)

---

## Testing Notes

**Date**: February 2026  
**Laser Model**: EL-230RGB MK2  
**Firmware**: Unknown  
**Tested By**: LaserPi Project Contributors

### General Observations

- Horizontal and vertical lines are visibly straighter than diagonal lines
- This is due to galvo motor dynamics - single-axis movements require only one motor
- Diagonal movements require both X and Y motors simultaneously, exposing timing differences
- Higher scanning speeds can mask this effect slightly but don't eliminate it
- Static patterns respond instantly to DMX changes
- Dynamic patterns may have slight delay when changing pattern numbers
- Color and zoom changes take effect immediately

### Quirks & Tips

- **Pattern ranges**: Many patterns are grouped in sets of 5 (e.g., 0-4, 5-9), with variations
- **Dashed variants**: Often offset by 5 from their solid counterparts
- **Rotation direction**: Most rotating patterns go clockwise
- **Center positioning**: Values 1-10 on Ch3/Ch4 center the pattern; use this before adjusting zoom
- **Color segment (Ch9)**: Most patterns work best with this set to 0; experiment on complex patterns 

---

## Contributing

Please share your discoveries! See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to submit your pattern findings to the project.

**To update this file**:
1. Test patterns using the example scripts
2. Document what you observe
3. Share interesting combinations
4. Note any unexpected behaviors

Your contributions help everyone use these lasers more effectively! 🎆

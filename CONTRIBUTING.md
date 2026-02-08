# Contributing to LaserPi

Thanks for experimenting with LaserPi! Here's how you can contribute your findings and improvements.

## 📝 Documenting Pattern Discoveries

As you test patterns, please document what you find!

### Create a Pattern Reference File

Create `docs/pattern_reference.md` with your discoveries:

```markdown
# MK2 Pattern Reference

Discovered patterns for EL-230RGB MK2 lasers

## Static Patterns (Channel 1: 150-199)

| Pattern # | Description | Notes |
|-----------|-------------|-------|
| 0 | Single dot | Basic test pattern |
| 15 | Circle | Perfect for positioning tests |
| 42 | ? | Your discovery here |

## Dynamic Patterns (Channel 1: 200-255)

| Pattern # | Description | Notes |
|-----------|-------------|-------|
| 0 | Rotating star | Moderate speed |
| ? | ? | Document what you find! |

## Color Channel (Ch 8) Behavior

- 0-63: Red tones
- 64-127: Green tones
- 128-191: Blue tones  
- 192-255: White/mixed
- (Document actual behavior you observe)

## Color Segment Channel (Ch 9) Behavior

- 0: Full pattern
- 128: Half pattern?
- 255: Segment effect?
- (Document actual behavior)

## Scanning Speed (Ch 5) Effect

- 0: Slowest mirror movement
- 128: Medium speed (good default)
- 255: Fastest (may cause flickering)
```

### Share Your Findings

1. **Fork the repository** on GitHub
2. **Add your discoveries** to `docs/pattern_reference.md`
3. **Submit a Pull Request** with:
   - Clear descriptions of patterns
   - Which laser effects work best
   - Any quirks or tips you discovered

## 🐛 Reporting Bugs

Found an issue? Open a GitHub issue with:

- **Description**: What went wrong?
- **Steps to reproduce**: How can we recreate it?
- **Expected vs actual behavior**
- **Environment**: Python version, Raspberry Pi OS version, USB adapter model
- **Error messages**: Full traceback if applicable

## 💡 Feature Requests

Have an idea? Open an issue with:

- **Use case**: What problem does it solve?
- **Proposed solution**: How would it work?
- **Examples**: Show what it would look like

## 🔧 Code Contributions

### Project Structure

```
src/laserpi/
├── dmx/          # Low-level DMX protocol
├── laser/        # Device abstractions (MK2, future devices)
├── effects/      # High-level effects and patterns
└── config.py     # Configuration constants

examples/         # User-facing scripts
docs/            # Documentation
tests/           # Unit tests (future)
```

### Adding New Features

#### 1. New Laser Device Support

To add support for another DMX laser:

```python
# src/laserpi/laser/newdevice.py
from ..dmx.universe import DMXUniverse

class NewDevice:
    def __init__(self, universe: DMXUniverse, base_address: int):
        self.universe = universe
        self.base_address = base_address
    
    def set_something(self, value: int):
        self.universe.set_channel(self.base_address, value)
```

#### 2. New Effects

Add effects to `src/laserpi/effects/`:

```python
# src/laserpi/effects/animations.py
def pulse_zoom(mk2, min_zoom=50, max_zoom=200, duration=2.0):
    """Pulse zoom in and out over duration"""
    import time
    from .shapes import oscillate
    
    for zoom in oscillate(min_zoom, max_zoom, steps=40):
        mk2.set_zoom(zoom)
        time.sleep(duration / 40)
```

#### 3. New Example Scripts

```python
#!/usr/bin/env python3
"""
Your Effect Name
Brief description
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laserpi.dmx import DMXUniverse, DMXDriver
from laserpi.laser import MK2, MK2Mode
# ... your code here
```

### Code Style

- **Python 3.7+** compatible
- **Type hints** where helpful
- **Docstrings** for classes and public methods
- **Comments** for complex logic
- **Descriptive variable names**

### Testing

Before submitting:

1. **Test on actual hardware** if possible
2. **Check for errors**: Run your script and verify no exceptions
3. **Test edge cases**: What if pattern is 0? 255? Invalid input?
4. **Document behavior**: Add comments explaining non-obvious parts

### Pull Request Process

1. **Create a feature branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes** with clear commit messages
3. **Update documentation**: README, docstrings, etc.
4. **Test thoroughly** on Raspberry Pi
5. **Submit PR** with:
   - Description of changes
   - Why it's useful
   - Testing done
   - Screenshots/videos if applicable

## 📚 Documentation Improvements

Documentation is as valuable as code! You can improve:

- **README.md**: Setup instructions, troubleshooting tips
- **Code comments**: Explain complex DMX timing or laser behavior
- **Docstrings**: API documentation
- **Examples**: More example scripts for common use cases
- **Pattern reference**: Document which patterns do what

## 🎨 Example Contributions

### Useful additions:

- **Preset patterns file**: JSON/YAML with named patterns like `{"circle": 15, "star": 23}`
- **CLI tool**: `laserpi --pattern circle --color red --zoom 100`
- **Web UI**: Simple web interface for pattern control
- **Synchronization effects**: Make both lasers work together in interesting ways
- **Music sync**: Beat detection and pattern triggering
- **Logo drawing**: If you manage to make this work, definitely share how!

## 💬 Questions?

- **Open a GitHub Discussion** for general questions
- **Check existing issues** before opening new ones
- **Be respectful** and patient - this is a community project

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

**Thank you for making LaserPi better!** 🎆

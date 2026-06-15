"""
Pattern generators for laser drawing.
All generators yield normalized (x, y) coordinate tuples in the range -1.0 to 1.0.
"""
import math
from typing import Generator, List, Tuple


def circle(cx=0.0, cy=0.0, radius=0.8, steps=36) -> Generator[Tuple[float, float], None, None]:
    """
    Generate points around a circle.

    Args:
        cx, cy: Center position (normalized)
        radius: Circle radius (normalized, 0.0-1.0)
        steps: Number of points around the circle

    Yields:
        (x, y) normalized coordinate tuples
    """
    for i in range(steps + 1):  # +1 to close the circle
        angle = 2 * math.pi * i / steps
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        yield (_clamp(x), _clamp(y))


def square(cx=0.0, cy=0.0, size=0.8) -> Generator[Tuple[float, float], None, None]:
    """
    Generate corner points of a square (closed path).

    Args:
        cx, cy: Center position (normalized)
        size: Side length (normalized)

    Yields:
        (x, y) for each corner, then back to start
    """
    half = size / 2
    corners = [
        (cx - half, cy - half),
        (cx + half, cy - half),
        (cx + half, cy + half),
        (cx - half, cy + half),
        (cx - half, cy - half),  # Close the square
    ]
    for x, y in corners:
        yield (_clamp(x), _clamp(y))


def rectangle(cx=0.0, cy=0.0, width=0.8, height=0.5) -> Generator[Tuple[float, float], None, None]:
    """
    Generate corner points of a rectangle (closed path).

    Args:
        cx, cy: Center position (normalized)
        width: Width (normalized)
        height: Height (normalized)

    Yields:
        (x, y) for each corner, then back to start
    """
    hw = width / 2
    hh = height / 2
    corners = [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
        (cx - hw, cy - hh),
    ]
    for x, y in corners:
        yield (_clamp(x), _clamp(y))


def triangle(cx=0.0, cy=0.0, radius=0.8) -> Generator[Tuple[float, float], None, None]:
    """
    Generate vertices of an equilateral triangle (closed path).

    Args:
        cx, cy: Center position (normalized)
        radius: Circumscribed circle radius (normalized)

    Yields:
        (x, y) for each vertex, then back to start
    """
    for i in range(4):  # 3 vertices + close
        angle = 2 * math.pi * i / 3 - math.pi / 2  # Start at top
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        yield (_clamp(x), _clamp(y))


def line(x1, y1, x2, y2, steps=10) -> Generator[Tuple[float, float], None, None]:
    """
    Generate interpolated points along a line segment.

    Args:
        x1, y1: Start position (normalized)
        x2, y2: End position (normalized)
        steps: Number of intermediate points

    Yields:
        (x, y) interpolated coordinate tuples
    """
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        yield (_clamp(x), _clamp(y))


def star(cx=0.0, cy=0.0, outer_radius=0.8, inner_radius=0.35,
         points=5) -> Generator[Tuple[float, float], None, None]:
    """
    Generate vertices of a star shape (closed path).

    Alternates between outer and inner radius points.

    Args:
        cx, cy: Center position (normalized)
        outer_radius: Outer point radius (normalized)
        inner_radius: Inner point radius (normalized)
        points: Number of outer points (5 = classic star)

    Yields:
        (x, y) for each vertex (2 * points + 1 total)
    """
    total_points = points * 2
    for i in range(total_points + 1):  # +1 to close
        idx = i % total_points
        angle = 2 * math.pi * idx / total_points - math.pi / 2
        r = outer_radius if idx % 2 == 0 else inner_radius
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        yield (_clamp(x), _clamp(y))


def spiral(cx=0.0, cy=0.0, r_start=0.1, r_end=0.8,
           rotations=3.0, steps=100) -> Generator[Tuple[float, float], None, None]:
    """
    Generate points along a spiral path.

    Args:
        cx, cy: Center position (normalized)
        r_start: Starting radius (normalized)
        r_end: Ending radius (normalized)
        rotations: Number of full rotations
        steps: Total number of points

    Yields:
        (x, y) coordinate tuples
    """
    for i in range(steps + 1):
        progress = i / steps
        radius = r_start + (r_end - r_start) * progress
        angle = 2 * math.pi * rotations * progress
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        yield (_clamp(x), _clamp(y))


def grid(rows=5, cols=5, size=0.8) -> Generator[Tuple[float, float], None, None]:
    """
    Generate a grid pattern drawn as connected horizontal lines.

    Draws left-to-right on even rows, right-to-left on odd rows (serpentine)
    to minimize travel distance.

    Args:
        rows: Number of horizontal lines
        cols: Number of vertical divisions
        size: Grid size (normalized, centered at origin)

    Yields:
        (x, y) coordinate tuples
    """
    half = size / 2
    for row in range(rows):
        y = -half + size * row / max(1, rows - 1)
        if row % 2 == 0:
            # Left to right
            for col in range(cols):
                x = -half + size * col / max(1, cols - 1)
                yield (_clamp(x), _clamp(y))
        else:
            # Right to left
            for col in range(cols - 1, -1, -1):
                x = -half + size * col / max(1, cols - 1)
                yield (_clamp(x), _clamp(y))


def cross(cx=0.0, cy=0.0, size=0.8) -> Generator[Tuple[float, float], None, None]:
    """
    Generate a plus/cross shape.

    Args:
        cx, cy: Center position (normalized)
        size: Arm length (normalized)

    Yields:
        (x, y) coordinate tuples (horizontal line, then vertical line)
    """
    half = size / 2
    # Horizontal line
    yield (_clamp(cx - half), _clamp(cy))
    yield (_clamp(cx + half), _clamp(cy))
    # Move to vertical start (will be blanked by coordinator)
    yield (_clamp(cx), _clamp(cy - half))
    yield (_clamp(cx), _clamp(cy + half))


def figure_eight(cx=0.0, cy=0.0, radius=0.4,
                 steps=48) -> Generator[Tuple[float, float], None, None]:
    """
    Generate a figure-8 (lemniscate) shape.

    Args:
        cx, cy: Center position (normalized)
        radius: Size of each lobe (normalized)
        steps: Number of points

    Yields:
        (x, y) coordinate tuples
    """
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        # Parametric lemniscate of Bernoulli
        denom = 1 + math.sin(t) ** 2
        x = cx + radius * math.cos(t) / denom
        y = cy + radius * math.sin(t) * math.cos(t) / denom
        yield (_clamp(x), _clamp(y))


# ---------------------------------------------------------------------------
# Simple block-letter text paths
# ---------------------------------------------------------------------------

# Each letter is defined as a list of strokes.
# Each stroke is a list of (x, y) points (normalized to a 0-1 character cell).
# Letters are 5 units tall, 3 units wide for proportional spacing.
_FONT = {
    'A': [[(0,1), (0.5,0), (1,1)], [(0.25,0.6), (0.75,0.6)]],
    'B': [[(0,0), (0,1), (0.8,1), (0.8,0.6), (0,0.6), (0.8,0.6), (0.8,0), (0,0)]],
    'C': [[(1,0), (0,0), (0,1), (1,1)]],
    'D': [[(0,0), (0,1), (0.8,1), (1,0.8), (1,0.2), (0.8,0), (0,0)]],
    'E': [[(1,0), (0,0), (0,0.5), (0.7,0.5), (0,0.5), (0,1), (1,1)]],
    'F': [[(0,1), (0,0), (1,0), (0,0), (0,0.5), (0.7,0.5)]],
    'G': [[(1,0), (0,0), (0,1), (1,1), (1,0.5), (0.5,0.5)]],
    'H': [[(0,0), (0,1)], [(0,0.5), (1,0.5)], [(1,0), (1,1)]],
    'I': [[(0,0), (1,0)], [(0.5,0), (0.5,1)], [(0,1), (1,1)]],
    'J': [[(0,0), (1,0), (1,1), (0.5,1), (0,0.8)]],
    'K': [[(0,0), (0,1)], [(1,0), (0,0.5), (1,1)]],
    'L': [[(0,0), (0,1), (1,1)]],
    'M': [[(0,1), (0,0), (0.5,0.4), (1,0), (1,1)]],
    'N': [[(0,1), (0,0), (1,1), (1,0)]],
    'O': [[(0,0), (1,0), (1,1), (0,1), (0,0)]],
    'P': [[(0,1), (0,0), (1,0), (1,0.5), (0,0.5)]],
    'Q': [[(0,0), (1,0), (1,1), (0,1), (0,0)], [(0.6,0.7), (1,1)]],
    'R': [[(0,1), (0,0), (1,0), (1,0.5), (0,0.5), (1,1)]],
    'S': [[(1,0), (0,0), (0,0.5), (1,0.5), (1,1), (0,1)]],
    'T': [[(0,0), (1,0)], [(0.5,0), (0.5,1)]],
    'U': [[(0,0), (0,1), (1,1), (1,0)]],
    'V': [[(0,0), (0.5,1), (1,0)]],
    'W': [[(0,0), (0.25,1), (0.5,0.6), (0.75,1), (1,0)]],
    'X': [[(0,0), (1,1)], [(1,0), (0,1)]],
    'Y': [[(0,0), (0.5,0.5), (1,0)], [(0.5,0.5), (0.5,1)]],
    'Z': [[(0,0), (1,0), (0,1), (1,1)]],
    '0': [[(0,0), (1,0), (1,1), (0,1), (0,0)], [(0,1), (1,0)]],
    '1': [[(0.3,0.2), (0.5,0), (0.5,1)], [(0.2,1), (0.8,1)]],
    '2': [[(0,0.2), (0.2,0), (0.8,0), (1,0.2), (0,1), (1,1)]],
    '3': [[(0,0), (1,0), (1,0.5), (0.3,0.5), (1,0.5), (1,1), (0,1)]],
    '4': [[(0,0), (0,0.5), (1,0.5)], [(1,0), (1,1)]],
    '5': [[(1,0), (0,0), (0,0.5), (1,0.5), (1,1), (0,1)]],
    '6': [[(1,0), (0,0), (0,1), (1,1), (1,0.5), (0,0.5)]],
    '7': [[(0,0), (1,0), (0.5,1)]],
    '8': [[(0,0.5), (0,0), (1,0), (1,0.5), (0,0.5), (0,1), (1,1), (1,0.5)]],
    '9': [[(1,0.5), (0,0.5), (0,0), (1,0), (1,1), (0,1)]],
    ' ': [],
    '-': [[(0.2,0.5), (0.8,0.5)]],
    '.': [[(0.4,0.9), (0.5,1), (0.6,0.9)]],
}


def text_path(text, size=0.3, spacing=0.15,
              cx=0.0, cy=0.0) -> List[List[Tuple[float, float]]]:
    """
    Convert a text string to laser path segments.

    Returns a list of strokes (each stroke is a list of points).
    Strokes should be drawn with laser ON; the coordinator should blank
    between strokes.

    Args:
        text: Text string to convert (uppercase A-Z, 0-9, space, dash, dot)
        size: Character height (normalized)
        spacing: Space between characters (normalized)
        cx, cy: Position of the text center

    Returns:
        List of strokes, where each stroke is a list of (x, y) tuples
    """
    text = text.upper()
    char_width = size * 0.6  # Aspect ratio
    total_width = len(text) * (char_width + spacing) - spacing
    start_x = cx - total_width / 2

    all_strokes = []
    for i, char in enumerate(text):
        char_x = start_x + i * (char_width + spacing)
        char_strokes = _FONT.get(char, [])
        for stroke in char_strokes:
            mapped = []
            for px, py in stroke:
                x = char_x + px * char_width
                y = cy - size / 2 + py * size
                mapped.append((_clamp(x), _clamp(y)))
            if mapped:
                all_strokes.append(mapped)

    return all_strokes


# ---------------------------------------------------------------------------
# Pattern registry for the interactive shell
# ---------------------------------------------------------------------------

PATTERN_REGISTRY = {
    'circle': {'fn': circle, 'desc': 'Circle'},
    'square': {'fn': square, 'desc': 'Square'},
    'rectangle': {'fn': rectangle, 'desc': 'Rectangle'},
    'triangle': {'fn': triangle, 'desc': 'Equilateral triangle'},
    'star': {'fn': star, 'desc': '5-pointed star'},
    'spiral': {'fn': spiral, 'desc': 'Spiral (outward)'},
    'grid': {'fn': grid, 'desc': 'Serpentine grid'},
    'cross': {'fn': cross, 'desc': 'Plus/cross shape'},
    'figure8': {'fn': figure_eight, 'desc': 'Figure-8 (lemniscate)'},
}


def list_patterns():
    """Return list of available pattern names and descriptions."""
    return [(name, info['desc']) for name, info in PATTERN_REGISTRY.items()]


def get_pattern(name, **kwargs):
    """
    Get pattern points by name.

    Args:
        name: Pattern name (from PATTERN_REGISTRY)
        **kwargs: Override default parameters (cx, cy, radius, size, steps, etc.)

    Returns:
        List of (x, y) tuples

    Raises:
        KeyError: If pattern name is unknown
    """
    if name not in PATTERN_REGISTRY:
        raise KeyError(f"Unknown pattern '{name}'. Available: {list(PATTERN_REGISTRY.keys())}")
    return list(PATTERN_REGISTRY[name]['fn'](**kwargs))


def _clamp(v):
    """Clamp value to -1.0..1.0."""
    return max(-1.0, min(1.0, v))

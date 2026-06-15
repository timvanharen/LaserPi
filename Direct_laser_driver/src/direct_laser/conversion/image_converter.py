"""
Image to laser path conversion.
Converts raster images to sets of line segments for laser drawing.
"""
import numpy as np
from PIL import Image
from typing import List, Tuple


def image_to_paths(image_path, threshold=128, resolution=64,
                   invert=False) -> List[List[Tuple[float, float]]]:
    """
    Convert an image file to laser-drawable path segments.

    Process:
    1. Load image and convert to grayscale
    2. Resize to target resolution (keeps aspect ratio)
    3. Threshold to binary (black/white)
    4. Scan rows for contiguous "on" pixel segments
    5. Return as normalized coordinate line segments

    Args:
        image_path: Path to the image file
        threshold: Brightness threshold (0-255). Pixels above = off, below = on.
        resolution: Target width in pixels (height scales proportionally)
        invert: If True, bright pixels are "on" instead of dark pixels

    Returns:
        List of strokes. Each stroke is a list of (x, y) normalized tuples.
    """
    img = Image.open(image_path).convert('L')

    # Resize maintaining aspect ratio
    aspect = img.height / img.width
    new_w = resolution
    new_h = max(1, int(resolution * aspect))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    pixels = np.array(img)

    # Threshold to binary
    if invert:
        binary = pixels >= threshold
    else:
        binary = pixels < threshold

    # Scan rows for contiguous segments
    segments = []
    for row in range(new_h):
        in_segment = False
        seg_start = 0
        for col in range(new_w):
            if binary[row, col]:
                if not in_segment:
                    seg_start = col
                    in_segment = True
            else:
                if in_segment:
                    segments.append((seg_start, row, col - 1, row))
                    in_segment = False
        if in_segment:
            segments.append((seg_start, row, new_w - 1, row))

    # Convert pixel coordinates to normalized (-1.0 to 1.0)
    strokes = []
    for x1, y1, x2, y2 in segments:
        nx1 = (x1 / max(1, new_w - 1)) * 2.0 - 1.0
        ny1 = (y1 / max(1, new_h - 1)) * 2.0 - 1.0
        nx2 = (x2 / max(1, new_w - 1)) * 2.0 - 1.0
        ny2 = (y2 / max(1, new_h - 1)) * 2.0 - 1.0
        strokes.append([(nx1, ny1), (nx2, ny2)])

    return strokes


def optimize_path(strokes) -> List[List[Tuple[float, float]]]:
    """
    Reorder strokes to minimize total travel distance (nearest-neighbor).

    This is a greedy optimization: starting from (0,0), each next stroke
    is the one whose start point is closest to the current position.
    Strokes may also be reversed if the end point is closer.

    Args:
        strokes: List of strokes (each a list of (x, y) tuples)

    Returns:
        Reordered list of strokes
    """
    if len(strokes) <= 1:
        return strokes

    remaining = list(range(len(strokes)))
    ordered = []
    current_pos = (0.0, 0.0)

    while remaining:
        best_idx = None
        best_dist = float('inf')
        best_reversed = False

        for idx in remaining:
            stroke = strokes[idx]
            start = stroke[0]
            end = stroke[-1]

            dist_start = _dist(current_pos, start)
            dist_end = _dist(current_pos, end)

            if dist_start < best_dist:
                best_dist = dist_start
                best_idx = idx
                best_reversed = False

            if dist_end < best_dist:
                best_dist = dist_end
                best_idx = idx
                best_reversed = True

        remaining.remove(best_idx)
        stroke = strokes[best_idx]
        if best_reversed:
            stroke = list(reversed(stroke))
        ordered.append(stroke)
        current_pos = stroke[-1]

    return ordered


def get_image_stats(strokes):
    """
    Return statistics about the converted image paths.

    Args:
        strokes: List of strokes from image_to_paths()

    Returns:
        Dict with stroke count, total point count, and estimated bounds
    """
    total_points = sum(len(s) for s in strokes)
    all_x = [p[0] for s in strokes for p in s]
    all_y = [p[1] for s in strokes for p in s]
    return {
        'stroke_count': len(strokes),
        'total_points': total_points,
        'x_range': (min(all_x), max(all_x)) if all_x else (0, 0),
        'y_range': (min(all_y), max(all_y)) if all_y else (0, 0),
    }


def _dist(a, b):
    """Euclidean distance between two 2D points."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

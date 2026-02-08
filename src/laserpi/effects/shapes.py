"""
Shape and pattern generation helpers
"""
import math
from typing import Tuple, Generator


def circle_path(radius: int = 50, steps: int = 36) -> Generator[Tuple[int, int], None, None]:
    """
    Generate X/Y coordinates for a circular path.
    
    Note: This is for manual circle drawing by sweeping X/Y positions.
    The MK2 may have built-in circular patterns that work better.
    
    Args:
        radius: Circle radius in DMX units (recommended: 30-100)
        steps: Number of points around the circle
    
    Yields:
        (x, y) tuples with DMX position values
        
    Example:
        >>> for x, y in circle_path(radius=50, steps=36):
        ...     laser.set_position(x, y)
        ...     time.sleep(0.05)
    """
    center_x = 128  # Middle of DMX range (11-255)
    center_y = 128
    
    for i in range(steps):
        angle = 2 * math.pi * i / steps
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        
        # Clamp to valid DMX position range (11-255)
        x = max(11, min(255, x))
        y = max(11, min(255, y))
        
        yield (x, y)


def oscillate(min_val: int, max_val: int, steps: int) -> Generator[int, None, None]:
    """
    Generate oscillating values for smooth parameter changes.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        steps: Number of steps for one complete oscillation
    
    Yields:
        Values that smoothly oscillate between min and max
        
    Example:
        >>> for zoom in oscillate(50, 200, 100):
        ...     laser.set_zoom(zoom)
        ...     time.sleep(0.05)
    """
    half_steps = steps // 2
    mid_val = (min_val + max_val) / 2
    amplitude = (max_val - min_val) / 2
    
    for i in range(steps):
        # Sine wave from min to max and back
        angle = 2 * math.pi * i / steps
        value = int(mid_val + amplitude * math.sin(angle))
        yield value


def spiral_path(
    start_radius: int = 20, 
    end_radius: int = 100, 
    rotations: float = 3, 
    steps: int = 100
) -> Generator[Tuple[int, int], None, None]:
    """
    Generate X/Y coordinates for a spiral path.
    
    Args:
        start_radius: Starting radius
        end_radius: Ending radius
        rotations: Number of full rotations
        steps: Total number of points
    
    Yields:
        (x, y) tuples with DMX position values
    """
    center_x = 128
    center_y = 128
    
    for i in range(steps):
        progress = i / steps
        radius = start_radius + (end_radius - start_radius) * progress
        angle = 2 * math.pi * rotations * progress
        
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        
        # Clamp to valid range
        x = max(11, min(255, x))
        y = max(11, min(255, y))
        
        yield (x, y)

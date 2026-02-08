"""
EL-230RGB MK2 Laser DMX Control
Abstraction layer for Laserworld MK2 laser control via DMX
"""
from enum import IntEnum
from typing import Optional
from ..dmx.universe import DMXUniverse


class MK2Mode(IntEnum):
    """DMX mode values for MK2 Channel 1"""
    OFF = 0  # Laser off (0-49)
    SOUND = 75  # Sound-activated mode (50-99)
    AUTO = 125  # Automatic mode (100-149)
    STATIC_PATTERN = 175  # Static pattern, DMX control (150-199)
    DYNAMIC_PATTERN = 225  # Dynamic pattern, DMX control (200-255)


class MK2:
    """
    EL-230RGB MK2 Laser controller.
    
    DMX Channel Map:
    - Channel 1 (offset 0): Mode (off/sound/auto/static/dynamic)
    - Channel 2 (offset 1): Pattern selection (0-255)
    - Channel 3 (offset 2): X axis (1-10 center, 11-255 position)
    - Channel 4 (offset 3): Y axis (1-10 center, 11-255 position)
    - Channel 5 (offset 4): Scanning speed (0-255)
    - Channel 6 (offset 5): Dynamic pattern speed (0-255)
    - Channel 7 (offset 6): Zoom/size (0-255)
    - Channel 8 (offset 7): Color (0-255)
    - Channel 9 (offset 8): Color segment (0-255)
    """
    
    def __init__(self, universe: DMXUniverse, base_address: int, name: str = "MK2"):
        """
        Initialize MK2 laser controller.
        
        Args:
            universe: DMXUniverse instance to control
            base_address: Base DMX address for this laser (e.g., 1 or 10)
            name: Friendly name for this laser
        
        Raises:
            ValueError: If base_address is out of valid range
        """
        if not 1 <= base_address <= 503:  # Max is 503 (512 - 9 channels)
            raise ValueError(f"Base address must be between 1 and 503, got {base_address}")
        
        self.universe = universe
        self.base_address = base_address
        self.name = name
    
    def _set_channel(self, offset: int, value: int) -> None:
        """Set a channel relative to base address."""
        self.universe.set_channel(self.base_address + offset, value)
    
    def _get_channel(self, offset: int) -> int:
        """Get a channel relative to base address."""
        return self.universe.get_channel(self.base_address + offset)
    
    # Channel 1: Mode
    def set_mode(self, mode: MK2Mode) -> None:
        """
        Set laser operating mode.
        
        Args:
            mode: MK2Mode enum value
        """
        self._set_channel(0, mode)
    
    def off(self) -> None:
        """Turn laser off."""
        self.set_mode(MK2Mode.OFF)
    
    def get_mode(self) -> int:
        """Get current mode value."""
        return self._get_channel(0)
    
    # Channel 2: Pattern
    def set_pattern(self, pattern: int) -> None:
        """
        Set pattern number.
        
        Args:
            pattern: Pattern number (0-255)
        """
        if not 0 <= pattern <= 255:
            raise ValueError(f"Pattern must be between 0 and 255, got {pattern}")
        self._set_channel(1, pattern)
    
    def get_pattern(self) -> int:
        """Get current pattern number."""
        return self._get_channel(1)
    
    # Channel 3: X Position
    def set_x_position(self, x: int) -> None:
        """
        Set X axis position.
        
        Args:
            x: X position (1-10 for center, 11-255 for positioning)
        """
        if not 1 <= x <= 255:
            raise ValueError(f"X position must be between 1 and 255, got {x}")
        self._set_channel(2, x)
    
    def get_x_position(self) -> int:
        """Get current X position."""
        return self._get_channel(2)
    
    # Channel 4: Y Position
    def set_y_position(self, y: int) -> None:
        """
        Set Y axis position.
        
        Args:
            y: Y position (1-10 for center, 11-255 for positioning)
        """
        if not 1 <= y <= 255:
            raise ValueError(f"Y position must be between 1 and 255, got {y}")
        self._set_channel(3, y)
    
    def get_y_position(self) -> int:
        """Get current Y position."""
        return self._get_channel(3)
    
    def center(self) -> None:
        """Center the laser output (X=5, Y=5)."""
        self.set_x_position(5)
        self.set_y_position(5)
    
    def set_position(self, x: int, y: int) -> None:
        """
        Set both X and Y position.
        
        Args:
            x: X position (1-255)
            y: Y position (1-255)
        """
        self.set_x_position(x)
        self.set_y_position(y)
    
    # Channel 5: Scanning Speed
    def set_scanning_speed(self, speed: int) -> None:
        """
        Set scanning speed.
        
        Args:
            speed: Speed value (0-255, higher = faster)
        """
        if not 0 <= speed <= 255:
            raise ValueError(f"Speed must be between 0 and 255, got {speed}")
        self._set_channel(4, speed)
    
    def get_scanning_speed(self) -> int:
        """Get current scanning speed."""
        return self._get_channel(4)
    
    # Channel 6: Dynamic Pattern Speed
    def set_dynamic_speed(self, speed: int) -> None:
        """
        Set dynamic pattern speed.
        
        Args:
            speed: Speed value (0-255)
        """
        if not 0 <= speed <= 255:
            raise ValueError(f"Dynamic speed must be between 0 and 255, got {speed}")
        self._set_channel(5, speed)
    
    def get_dynamic_speed(self) -> int:
        """Get current dynamic pattern speed."""
        return self._get_channel(5)
    
    # Channel 7: Zoom
    def set_zoom(self, zoom: int) -> None:
        """
        Set zoom/size.
        
        Args:
            zoom: Zoom value (0-255, higher = larger)
        """
        if not 0 <= zoom <= 255:
            raise ValueError(f"Zoom must be between 0 and 255, got {zoom}")
        self._set_channel(6, zoom)
    
    def get_zoom(self) -> int:
        """Get current zoom value."""
        return self._get_channel(6)
    
    # Channel 8: Color
    def set_color(self, color: int) -> None:
        """
        Set color.
        
        Args:
            color: Color value (0-255)
        """
        if not 0 <= color <= 255:
            raise ValueError(f"Color must be between 0 and 255, got {color}")
        self._set_channel(7, color)
    
    def get_color(self) -> int:
        """Get current color value."""
        return self._get_channel(7)
    
    # Channel 9: Color Segment
    def set_color_segment(self, segment: int) -> None:
        """
        Set color segment.
        
        Args:
            segment: Color segment value (0-255)
        """
        if not 0 <= segment <= 255:
            raise ValueError(f"Color segment must be between 0 and 255, got {segment}")
        self._set_channel(8, segment)
    
    def get_color_segment(self) -> int:
        """Get current color segment value."""
        return self._get_channel(8)
    
    def get_all_values(self) -> dict:
        """
        Get all current channel values.
        
        Returns:
            Dictionary with all channel values
        """
        return {
            "mode": self.get_mode(),
            "pattern": self.get_pattern(),
            "x_position": self.get_x_position(),
            "y_position": self.get_y_position(),
            "scanning_speed": self.get_scanning_speed(),
            "dynamic_speed": self.get_dynamic_speed(),
            "zoom": self.get_zoom(),
            "color": self.get_color(),
            "color_segment": self.get_color_segment(),
        }
    
    def __repr__(self) -> str:
        return f"MK2(name='{self.name}', address={self.base_address})"

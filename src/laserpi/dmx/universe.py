"""
DMX Universe - 512-channel buffer for DMX512 protocol
Provides thread-safe access to channel data
"""
import threading
from typing import List


class DMXUniverse:
    """
    Represents a DMX512 universe of 512 channels.
    Channels are 1-indexed (1-512) to match DMX convention.
    """
    
    def __init__(self):
        """Initialize a DMX universe with all channels set to 0"""
        self._channels = bytearray(512)
        self._lock = threading.Lock()
    
    def set_channel(self, channel: int, value: int) -> None:
        """
        Set a single DMX channel value.
        
        Args:
            channel: Channel number (1-512)
            value: Channel value (0-255)
        
        Raises:
            ValueError: If channel or value is out of range
        """
        if not 1 <= channel <= 512:
            raise ValueError(f"Channel must be between 1 and 512, got {channel}")
        if not 0 <= value <= 255:
            raise ValueError(f"Value must be between 0 and 255, got {value}")
        
        with self._lock:
            self._channels[channel - 1] = value
    
    def get_channel(self, channel: int) -> int:
        """
        Get a single DMX channel value.
        
        Args:
            channel: Channel number (1-512)
        
        Returns:
            Channel value (0-255)
        
        Raises:
            ValueError: If channel is out of range
        """
        if not 1 <= channel <= 512:
            raise ValueError(f"Channel must be between 1 and 512, got {channel}")
        
        with self._lock:
            return self._channels[channel - 1]
    
    def set_channels(self, start_channel: int, values: List[int]) -> None:
        """
        Set multiple consecutive DMX channels.
        
        Args:
            start_channel: First channel number (1-512)
            values: List of values (0-255)
        
        Raises:
            ValueError: If any channel or value is out of range
        """
        if not 1 <= start_channel <= 512:
            raise ValueError(f"Start channel must be between 1 and 512, got {start_channel}")
        if start_channel + len(values) - 1 > 512:
            raise ValueError(f"Channel range exceeds 512 channels")
        
        for value in values:
            if not 0 <= value <= 255:
                raise ValueError(f"All values must be between 0 and 255, got {value}")
        
        with self._lock:
            for i, value in enumerate(values):
                self._channels[start_channel - 1 + i] = value
    
    def get_channels(self, start_channel: int, count: int) -> List[int]:
        """
        Get multiple consecutive DMX channels.
        
        Args:
            start_channel: First channel number (1-512)
            count: Number of channels to retrieve
        
        Returns:
            List of channel values
        
        Raises:
            ValueError: If channel range is invalid
        """
        if not 1 <= start_channel <= 512:
            raise ValueError(f"Start channel must be between 1 and 512, got {start_channel}")
        if start_channel + count - 1 > 512:
            raise ValueError(f"Channel range exceeds 512 channels")
        
        with self._lock:
            return list(self._channels[start_channel - 1:start_channel - 1 + count])
    
    def get_frame_data(self, channel_count: int = 512) -> bytes:
        """
        Get a snapshot of channel data for transmission.
        
        Args:
            channel_count: Number of channels to include (1-512)
        
        Returns:
            Bytes containing channel data (not including start code)
        """
        if not 1 <= channel_count <= 512:
            raise ValueError(f"Channel count must be between 1 and 512, got {channel_count}")
        
        with self._lock:
            return bytes(self._channels[:channel_count])
    
    def clear(self) -> None:
        """Set all channels to 0"""
        with self._lock:
            for i in range(512):
                self._channels[i] = 0

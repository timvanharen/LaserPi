"""
BeamZ S1500 DMX MKII Smoke Machine Controller

DMX control for the BeamZ S1500 MKII fog/smoke machine.
This machine uses 2 DMX channels.

⚠️ IMPORTANT: The S1500 needs 5-8 minutes warm-up time after power-on!
The heater must reach operating temperature before it can produce smoke.

How to know the S1500 heater is ready:
- The S1500 has a RED LED on the back panel
- RED LED ON (solid) = still heating up → WAIT
- RED LED OFF = heater ready → can produce smoke
- Warm-up takes approximately 5-8 minutes

The timer remote is NOT required for DMX operation.
The S1500 works in DMX mode independently of the timer remote.
"""
import time as _time

from ..dmx.universe import DMXUniverse


class Hazer:
    """
    BeamZ S1500 DMX MKII Smoke Machine controller.
    
    ⚠️ WARM-UP: Wait 5-8 min after power-on! Red LED OFF = ready.
    
    DMX Channel Map (2 channels):
    - Channel 1 (offset 0): Smoke output (0-255, 0=off, 255=full)
    - Channel 2 (offset 1): Duration control (0-255)
        0     = continuous output (as long as ch1 > 0)
        1-255 = timed burst duration
    
    The timer remote is NOT required for DMX mode.
    
    Troubleshooting:
    - No smoke output? Check:
      1. Is the RED LED off? (If on → still heating, wait 5-8 min)
      2. Is fluid tank full?
      3. Is DMX address correct? (Use address_scanner.py to verify)
      4. Is the machine set to DMX mode? (Check DIP switches)
      5. Try setting Channel 1 to 255 AND Channel 2 to 0
    
    Usage:
        hazer = Hazer(universe, base_address=21, name="S1500")
        hazer.set_output(50)       # 50% smoke output (continuous)
        hazer.set_duration(128)    # Set burst duration
        hazer.off()                # Turn off
    """
    
    # Number of DMX channels this device uses
    CHANNEL_COUNT = 2
    
    def __init__(self, universe: DMXUniverse, base_address: int, name: str = "S1500"):
        """
        Initialize smoke machine controller.
        
        Args:
            universe: DMXUniverse instance to control
            base_address: Base DMX address (e.g., 21)
            name: Friendly name for this unit
        
        Raises:
            ValueError: If base_address is out of valid range
        """
        if not 1 <= base_address <= 512:
            raise ValueError(f"Base address must be between 1 and 512, got {base_address}")
        
        self.universe = universe
        self.base_address = base_address
        self.name = name
    
    def _set_channel(self, offset: int, value: int) -> None:
        """Set a channel relative to base address."""
        self.universe.set_channel(self.base_address + offset, value)
    
    def _get_channel(self, offset: int) -> int:
        """Get a channel relative to base address."""
        return self.universe.get_channel(self.base_address + offset)
    
    def set_output(self, percent: float) -> None:
        """
        Set smoke output level.
        
        Args:
            percent: Output level as percentage (0.0 to 100.0)
        
        Raises:
            ValueError: If percent is out of range
        """
        if not 0 <= percent <= 100:
            raise ValueError(f"Output percent must be between 0 and 100, got {percent}")
        
        # Convert percentage to DMX value (0-255)
        dmx_value = int((percent / 100.0) * 255)
        self._set_channel(0, dmx_value)
    
    def get_output(self) -> float:
        """
        Get current smoke output level as percentage.
        
        Returns:
            Output level (0.0 to 100.0)
        """
        dmx_value = self._get_channel(0)
        return (dmx_value / 255.0) * 100.0
    
    def set_duration(self, value: int) -> None:
        """
        Set burst duration on channel 2.
        
        Args:
            value: Duration value (0-255)
                   0 = continuous output
                   1-255 = timed burst
        """
        if not 0 <= value <= 255:
            raise ValueError(f"Duration must be between 0 and 255, got {value}")
        self._set_channel(1, value)
    
    def get_duration(self) -> int:
        """Get current duration channel value."""
        return self._get_channel(1)
    
    def on(self, percent: float = 100.0) -> None:
        """
        Turn smoke machine on at specified output level (continuous mode).
        
        Args:
            percent: Output level (default: 100%)
        """
        self.set_duration(0)  # Continuous mode
        self.set_output(percent)
    
    def off(self) -> None:
        """Turn smoke machine off."""
        self.set_output(0)
        self.set_duration(0)
    
    def burst(self, percent: float = 100.0, duration_value: int = 128) -> None:
        """
        Fire a timed burst of smoke.
        
        Args:
            percent: Output level (default: 100%)
            duration_value: Burst duration (1-255, higher = longer)
        """
        self.set_duration(duration_value)
        self.set_output(percent)
    
    def fade(self, target_percent: float, duration: float = 2.0, steps: int = 20) -> None:
        """
        Fade from current output to target output over duration.
        
        Args:
            target_percent: Target output level (0-100)
            duration: Fade duration in seconds
            steps: Number of steps in the fade
            
        Example:
            hazer.fade(50, duration=3.0)  # Fade to 50% over 3 seconds
        """
        current = self.get_output()
        step_size = (target_percent - current) / steps
        step_delay = duration / steps
        
        for i in range(steps + 1):
            output = current + (step_size * i)
            self.set_output(output)
            _time.sleep(step_delay)
    
    def __repr__(self) -> str:
        return f"Hazer(name='{self.name}', address={self.base_address}, channels={self.CHANNEL_COUNT})"

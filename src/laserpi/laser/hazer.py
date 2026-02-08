"""
Hazer/Smoke Generator DMX Control
Simple abstraction for fog/haze machines with single-channel control

⚠️ IMPORTANT: Most hazers require 3-5 minutes warm-up time after power-on
before they can produce smoke. Wait for the heater to reach temperature!

Typical hazer warm-up indicators:
- Ready LED lights up (green)
- Warm-up LED turns off (red)
- Some have audio beeps when ready
- Check your hazer's manual for specific indicators
"""
from ..dmx.universe import DMXUniverse


class Hazer:
    """
    Simple hazer/smoke generator controller.
    
    ⚠️ WARM-UP REQUIRED: Wait 3-5 minutes after power-on before expecting smoke!
    
    DMX Channel Map:
    - Channel 1 (offset 0): Smoke output (0-100%, maps to DMX 0-255)
    
    Troubleshooting:
    - No smoke output? Check:
      1. Is the heater warmed up? (Wait 3-5 minutes, check ready indicator)
      2. Is fluid tank full?
      3. Is DMX address correct? (Use address_scanner.py to verify)
      4. Is the hazer powered on?
    
    Usage:
        hazer = Hazer(universe, base_address=21, name="Main Hazer")
        hazer.set_output(50)  # 50% smoke output
        hazer.off()           # Turn off
    """
    
    def __init__(self, universe: DMXUniverse, base_address: int, name: str = "Hazer"):
        """
        Initialize hazer controller.
        
        Args:
            universe: DMXUniverse instance to control
            base_address: Base DMX address for this hazer (e.g., 21)
            name: Friendly name for this hazer
        
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
        Set smoke/haze output level.
        
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
        Get current smoke/haze output level as percentage.
        
        Returns:
            Output level (0.0 to 100.0)
        """
        dmx_value = self._get_channel(0)
        return (dmx_value / 255.0) * 100.0
    
    def on(self, percent: float = 100.0) -> None:
        """
        Turn hazer on at specified output level.
        
        Args:
            percent: Output level (default: 100%)
        """
        self.set_output(percent)
    
    def off(self) -> None:
        """Turn hazer off."""
        self.set_output(0)
    
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
        import time
        
        current = self.get_output()
        step_size = (target_percent - current) / steps
        step_delay = duration / steps
        
        for i in range(steps + 1):
            output = current + (step_size * i)
            self.set_output(output)
            time.sleep(step_delay)
    
    def __repr__(self) -> str:
        return f"Hazer(name='{self.name}', address={self.base_address})"

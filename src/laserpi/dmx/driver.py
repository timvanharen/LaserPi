"""
DMX512 Driver - Low-level serial communication for DMX over RS485
Handles break signal generation and continuous packet transmission
"""
import time
import threading
import serial
from typing import Optional
from ..config import (
    SERIAL_PORT, DMX_BAUD, DMX_REFRESH_HZ,
    DMX_BREAK_TIME_US, DMX_MAB_TIME_US, DMX_CHANNEL_COUNT
)


class DMXDriver:
    """
    Low-level DMX512 driver using pyserial.
    Continuously transmits DMX frames in a background thread.
    """
    
    def __init__(self, port: str = SERIAL_PORT, baud: int = DMX_BAUD,
                 channel_count: int = DMX_CHANNEL_COUNT, refresh_hz: int = DMX_REFRESH_HZ):
        """
        Initialize DMX driver.
        
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0')
            baud: Baud rate (DMX standard is 250000)
            channel_count: Number of channels to transmit (1-512)
            refresh_hz: Frame refresh rate in Hz
        """
        self.port = port
        self.baud = baud
        self.channel_count = channel_count
        self.refresh_hz = refresh_hz
        self.frame_time = 1.0 / refresh_hz
        
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._universe = None  # Set by user
    
    def start(self, universe) -> None:
        """
        Start the DMX transmission thread.
        
        Args:
            universe: DMXUniverse instance to transmit
        
        Raises:
            RuntimeError: If driver is already running
        """
        if self._running:
            raise RuntimeError("DMX driver is already running")
        
        self._universe = universe
        
        # Open serial port
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        # Start transmission thread
        self._running = True
        self._thread = threading.Thread(target=self._tx_loop, daemon=True, name="DMX-TX")
        self._thread.start()
        
        print(f"DMX driver started on {self.port} at {self.baud} baud, {self.refresh_hz} Hz")
    
    def stop(self) -> None:
        """Stop the DMX transmission thread and close serial port."""
        if not self._running:
            return
        
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._serial = None
        
        print("DMX driver stopped")
    
    def _tx_loop(self) -> None:
        """Background thread that continuously transmits DMX frames."""
        while self._running:
            frame_start = time.perf_counter()
            
            try:
                self._send_dmx_packet()
            except Exception as e:
                print(f"DMX transmission error: {e}")
                time.sleep(0.1)  # Brief pause on error before retry
                continue
            
            # Sleep until next frame
            elapsed = time.perf_counter() - frame_start
            sleep_time = self.frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _send_dmx_packet(self) -> None:
        """
        Send a single DMX512 packet.
        
        Packet structure:
        1. BREAK: TX held low for ~150 μs
        2. MAB (Mark After Break): TX high for ~12 μs
        3. Start code: 0x00
        4. Channel data: 1-512 bytes
        """
        # Generate BREAK signal
        self._serial.break_condition = True
        self._busy_wait_us(DMX_BREAK_TIME_US)
        self._serial.break_condition = False
        
        # MAB (Mark After Break)
        self._busy_wait_us(DMX_MAB_TIME_US)
        
        # Send start code + channel data
        start_code = b'\x00'
        channel_data = self._universe.get_frame_data(self.channel_count)
        self._serial.write(start_code + channel_data)
        
        # Flush to ensure data is sent
        self._serial.flush()
    
    @staticmethod
    def _busy_wait_us(microseconds: int) -> None:
        """
        Busy-wait for a precise number of microseconds.
        More accurate than time.sleep() for sub-millisecond delays.
        
        Args:
            microseconds: Duration to wait
        """
        target = time.perf_counter() + microseconds / 1_000_000
        while time.perf_counter() < target:
            pass
    
    def is_running(self) -> bool:
        """Check if the driver is currently running."""
        return self._running
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures driver is stopped."""
        self.stop()
        return False

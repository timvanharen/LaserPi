"""
TMC2209 UART configuration via Raspberry Pi serial port.

Single-wire UART interface for configuring TMC2209 stepper drivers.
Allows setting current limit, microstepping, and other parameters.
"""
import serial
import struct
import time


class TMC2209:
    """
    Communicate with a single TMC2209 via UART.
    
    Args:
        port: Serial port (e.g., '/dev/ttyAMA0' for Pi UART0)
        address: UART slave address (0-3, set via MS1/MS2 at power-up)
        baudrate: UART speed (default 115200)
    """
    
    # Register addresses (from TMC2209 datasheet)
    GCONF = 0x00
    GSTAT = 0x01
    IOIN = 0x06
    IHOLD_IRUN = 0x10
    CHOPCONF = 0x6C
    COOLCONF = 0x6D
    PWMCONF = 0x70
    
    def __init__(self, port, address=0, baudrate=115200):
        self.port = serial.Serial(port, baudrate=baudrate, timeout=1.0)
        self.address = address
        self.name = f"TMC2209(addr={address})"
        time.sleep(0.1)
        print(f"[{self.name}] Connected on {port}")
    
    def close(self):
        """Close serial port."""
        if self.port.is_open:
            self.port.close()
    
    def _write_register(self, addr, value):
        """
        Write a 32-bit value to a register.
        
        UART packet format (single-wire):
          [sync] [addr] [reg] [data_3] [data_2] [data_1] [data_0] [CRC]
        """
        # Build packet
        sync = 0x05  # Sync byte
        addr_byte = (0x80 | (self.address & 0x03))  # Write bit + address
        reg = addr & 0x7F
        
        data = struct.pack('>I', value)
        
        # Calculate CRC (simple XOR for now — TMC2209 uses more complex CRC)
        # For compatibility, we'll use proper CRC8
        packet = bytes([sync, addr_byte, reg, data[0], data[1], data[2], data[3]])
        crc = self._calculate_crc(packet[1:])
        
        full_packet = packet + bytes([crc])
        
        # Send packet
        self.port.write(full_packet)
        self.port.flush()
        time.sleep(0.01)
    
    def _read_register(self, addr):
        """
        Read a 32-bit value from a register.
        
        Returns: 32-bit register value, or None if read fails
        """
        # Build read packet
        sync = 0x05
        addr_byte = (self.address & 0x03)  # Read bit = 0
        reg = addr & 0x7F
        
        packet = bytes([sync, addr_byte, reg])
        crc = self._calculate_crc(packet[1:])
        full_packet = packet + bytes([crc])
        
        # Send read request
        self.port.write(full_packet)
        self.port.flush()
        
        # Read response (sync + addr + reg + 4 bytes data + CRC)
        response = self.port.read(8)
        
        if len(response) < 8:
            print(f"[{self.name}] Read timeout for register 0x{addr:02X}")
            return None
        
        value = struct.unpack('>I', response[3:7])[0]
        return value
    
    def _calculate_crc(self, data):
        """Calculate CRC8 for TMC2209 UART (polynomial 0x07)."""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc << 1) ^ 0x07 if (crc & 0x80) else (crc << 1)
                crc &= 0xFF
        return crc
    
    def set_current_rms(self, current_ma):
        """
        Set RMS current limit.
        
        Args:
            current_ma: RMS current in mA (e.g., 400 for 0.4A)
        
        Mapping: I_RMS = (IRUN + 1) / 32 * V_FS / R_sense
                 Typical: V_FS = 0.325V, R_sense = 0.11Ω
                 IRUN = (I_RMS * 32 * R_sense / V_FS) - 1
        """
        V_FS = 0.325
        R_sense = 0.11
        I_RMS = current_ma / 1000.0
        
        IRUN = int((I_RMS * 32 * R_sense / V_FS) - 1)
        IRUN = max(0, min(31, IRUN))  # Clamp to 0-31
        
        # Read current IHOLD_IRUN register
        ihold_irun = self._read_register(self.IHOLD_IRUN)
        if ihold_irun is None:
            ihold_irun = 0x00100400  # Default: IHOLD=0, IRUN=4
        
        # Update IRUN (bits 12-16)
        ihold_irun = (ihold_irun & 0xFFFFF0FF) | ((IRUN & 0x1F) << 8)
        
        # Also set reasonable IHOLD (bits 0-4) — typically half of IRUN
        IHOLD = IRUN // 2
        ihold_irun = (ihold_irun & 0xFFFFFFF0) | (IHOLD & 0x0F)
        
        self._write_register(self.IHOLD_IRUN, ihold_irun)
        print(f"[{self.name}] Set current: {current_ma}mA (IRUN={IRUN}, IHOLD={IHOLD})")
    
    def set_microstepping(self, microsteps):
        """
        Set microstepping resolution.
        
        Args:
            microsteps: 1, 2, 4, 8, or 16
        
        Maps to MRES in CHOPCONF register (bits 24-27):
          1  → MRES=8
          2  → MRES=7
          4  → MRES=6
          8  → MRES=5
          16 → MRES=4
        """
        mres_map = {1: 8, 2: 7, 4: 6, 8: 5, 16: 4}
        
        if microsteps not in mres_map:
            print(f"[{self.name}] Invalid microstepping: {microsteps}. Using 16.")
            microsteps = 16
        
        MRES = mres_map[microsteps]
        
        # Read CHOPCONF
        chopconf = self._read_register(self.CHOPCONF)
        if chopconf is None:
            chopconf = 0x10000053  # Default value
        
        # Clear MRES (bits 24-27) and set new value
        chopconf = (chopconf & 0xF0FFFFFF) | ((MRES & 0x0F) << 24)
        
        self._write_register(self.CHOPCONF, chopconf)
        print(f"[{self.name}] Set microstepping: {microsteps}x (MRES={MRES})")
    
    def set_pwm_autoscale(self, enable=True):
        """Enable/disable PWM auto-scaling (for smoother low-speed motion)."""
        pwmconf = self._read_register(self.PWMCONF)
        if pwmconf is None:
            pwmconf = 0x00050480
        
        if enable:
            pwmconf |= (1 << 18)  # PWMAUTOSCALE bit
        else:
            pwmconf &= ~(1 << 18)
        
        self._write_register(self.PWMCONF, pwmconf)
        mode = "enabled" if enable else "disabled"
        print(f"[{self.name}] PWM autoscale: {mode}")
    
    def get_status(self):
        """Read and print status registers."""
        gstat = self._read_register(self.GSTAT)
        print(f"[{self.name}] GSTAT = 0x{gstat:08X}" if gstat else f"[{self.name}] Failed to read GSTAT")

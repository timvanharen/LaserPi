#!/usr/bin/env python3
"""
Minimal TMC2209 UART probe for Raspberry Pi 3B+.

Uses the Pi hardware serial port (/dev/serial0) and the TMC2209 UART
framing from TMCStepper to verify that the bus is alive.

Important:
  - Pi UART is GPIO14 TXD0 + GPIO15 RXD0
  - This script does NOT use GPIO16 for UART
  - The TMC2209 PDN/UART pins must be wired to that shared bus through
    the usual 1k resistor on TX
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import serial

UART_PORT = "/dev/serial0"
UART_BAUD = 115200

TMC_SYNC = 0x05
TMC_READ = 0x00

REG_GSTAT = 0x01
REG_IFCNT = 0x02
REG_IOIN = 0x06


def crc8(datagram):
    crc = 0
    for current_byte in datagram:
        for _ in range(8):
            if ((crc >> 7) ^ (current_byte & 0x01)):
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            current_byte >>= 1
    return crc


class TMC2209Probe:
    def __init__(self, port=UART_PORT, baud=UART_BAUD):
        self.port_name = port
        self.ser = serial.Serial(port, baudrate=baud, timeout=0.05)

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def read_register(self, slave, register, timeout=0.3):
        request = bytes([TMC_SYNC, slave & 0x03, register | TMC_READ])
        request += bytes([crc8(request)])

        self.ser.reset_input_buffer()
        self.ser.write(request)
        self.ser.flush()

        sync_target = bytes([TMC_SYNC, slave & 0x03, register | TMC_READ])
        window = bytearray()
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            byte = self.ser.read(1)
            if not byte:
                continue
            window.append(byte[0])
            if len(window) > 3:
                del window[:-3]

            if len(window) == 3 and bytes(window) == sync_target:
                frame = bytearray(window)
                while len(frame) < 8 and time.monotonic() < deadline:
                    more = self.ser.read(8 - len(frame))
                    if more:
                        frame.extend(more)

                if len(frame) < 8:
                    return None, "timeout waiting for response body", request, bytes(frame)

                expected = crc8(frame[:7])
                if expected != frame[7]:
                    return None, f"crc mismatch expected 0x{expected:02X} got 0x{frame[7]:02X}", request, bytes(frame)

                value = int.from_bytes(frame[3:7], byteorder="big")
                return value, None, request, bytes(frame)

        return None, "timeout waiting for sync frame", request, b""


def decode_ioin(value):
    return {
        "version": (value >> 24) & 0xFF,
        "enn": bool(value & 0x01),
        "ms1": bool(value & (1 << 2)),
        "ms2": bool(value & (1 << 3)),
        "diag": bool(value & (1 << 4)),
        "pdn_uart": bool(value & (1 << 6)),
        "step": bool(value & (1 << 7)),
        "sel_a": bool(value & (1 << 8)),
        "dir": bool(value & (1 << 9)),
    }


def probe_driver(probe, slave, name):
    print(f"\n[{name}] slave={slave}")
    for reg_name, reg in [("GSTAT", REG_GSTAT), ("IFCNT", REG_IFCNT), ("IOIN", REG_IOIN)]:
        value, err, request, frame = probe.read_register(slave, reg)
        print(f"  request: {request.hex(' ')}")
        if frame:
            print(f"  raw rsp: {frame.hex(' ')}")
        if err:
            print(f"  {reg_name}: ERROR ({err})")
            continue
        print(f"  {reg_name}: 0x{value:08X}")
        if reg == REG_IOIN:
            decoded = decode_ioin(value)
            print(
                "  IOIN decoded: "
                f"version=0x{decoded['version']:02X}, "
                f"enn={decoded['enn']}, ms1={decoded['ms1']}, ms2={decoded['ms2']}, "
                f"pdn_uart={decoded['pdn_uart']}, step={decoded['step']}, dir={decoded['dir']}"
            )


def main():
    print("=== TMC2209 UART probe ===")
    print(f"Port: {UART_PORT} @ {UART_BAUD}")
    print("Pi UART should be GPIO14 (TXD0) and GPIO15 (RXD0).")

    try:
        probe = TMC2209Probe()
    except Exception as exc:
        print(f"ERROR: could not open {UART_PORT}: {exc}")
        print("If this is a permissions error, add your user to the dialout group or run with sudo.")
        sys.exit(1)

    try:
        probe_driver(probe, 0, "X/address0")
        probe_driver(probe, 1, "Y/address1")
    finally:
        probe.close()


if __name__ == "__main__":
    main()
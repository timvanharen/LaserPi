#!/usr/bin/env python3
"""
ESP32-style dual TMC2209 test for Raspberry Pi 3B+.

This mirrors the ESP32 test workflow as closely as possible:
  - independent X/Y STEP, DIR, EN control
  - optional UART configuration for TMC2209
  - single-step, continuous run, speed tests, enable/disable, info

Pi BCM pin map used by this script:
    X STEP = GPIO 17
    X DIR  = GPIO 18
    Y STEP = GPIO 27
    Y DIR  = GPIO 22
    X EN   = GPIO 4
    Y EN   = GPIO 5
    Lasers = GPIO 23, 24, 25

UART uses the Pi hardware serial port:
  /dev/serial0  (GPIO 14 TXD0, GPIO 15 RXD0)
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pigpio
import serial

from direct_laser import config


STEP_PIN_X = config.MOTOR_X_STEP
DIR_PIN_X = config.MOTOR_X_DIR
STEP_PIN_Y = config.MOTOR_Y_STEP
DIR_PIN_Y = config.MOTOR_Y_DIR

LASER_RED_PIN = config.LASER_RED_PIN
LASER_GREEN_PIN = config.LASER_GREEN_PIN
LASER_BLUE_PIN = config.LASER_BLUE_PIN

EN_PIN_X = config.MOTOR_X_EN
EN_PIN_Y = config.MOTOR_Y_EN

UART_PORT = "/dev/serial0"
UART_BAUD = 115200

TMC_SYNC = 0x05
TMC_READ = 0x00
TMC_WRITE = 0x80

TMC_REG_GCONF = 0x00
TMC_REG_GSTAT = 0x01
TMC_REG_IOIN = 0x06
TMC_REG_IHOLD_IRUN = 0x10
TMC_REG_CHOPCONF = 0x6C
TMC_REG_PWMCONF = 0x70
TMC_REG_SGTHRS = 0x40

R_SENSE = 0.11


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


class TMC2209Bus:
    def __init__(self, port=UART_PORT, baud=UART_BAUD):
        self.port_name = port
        self.serial = serial.Serial(port, baudrate=baud, timeout=0.05)

    def close(self):
        if self.serial.is_open:
            self.serial.close()

    def write_register(self, slave, register, value):
        payload = bytes([
            TMC_SYNC,
            slave & 0x03,
            register | TMC_WRITE,
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])
        packet = payload + bytes([crc8(payload)])
        self.serial.reset_input_buffer()
        self.serial.write(packet)
        self.serial.flush()
        time.sleep(0.01)

    def read_register(self, slave, register, timeout=0.25):
        request = bytes([TMC_SYNC, slave & 0x03, register | TMC_READ])
        request += bytes([crc8(request)])

        self.serial.reset_input_buffer()
        self.serial.write(request)
        self.serial.flush()

        sync_target = bytes([TMC_SYNC, slave & 0x03, register | TMC_READ])
        window = bytearray()
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            chunk = self.serial.read(1)
            if not chunk:
                continue
            window.append(chunk[0])
            if len(window) > 3:
                del window[:-3]

            if len(window) == 3 and bytes(window) == sync_target:
                frame = bytearray(window)
                while len(frame) < 8 and time.monotonic() < deadline:
                    more = self.serial.read(8 - len(frame))
                    if more:
                        frame.extend(more)

                if len(frame) < 8:
                    return None, "timeout waiting for response body"

                if crc8(frame[:7]) != frame[7]:
                    expected = crc8(frame[:7])
                    return None, f"crc mismatch: got 0x{frame[7]:02X}, expected 0x{expected:02X}"

                value = int.from_bytes(frame[3:7], byteorder="big")
                return value, None

        return None, "timeout waiting for sync frame"

    def set_current_rms(self, slave, current_ma, hold_multiplier=0.5):
        vsense = False
        cs = int(32.0 * 1.41421 * current_ma / 1000.0 * (R_SENSE + 0.02) / 0.325 - 1)
        if cs < 16:
            vsense = True
            cs = int(32.0 * 1.41421 * current_ma / 1000.0 * (R_SENSE + 0.02) / 0.180 - 1)
        cs = max(0, min(31, cs))

        irun = cs
        ihold = max(0, min(31, int(cs * hold_multiplier)))
        iholddelay = 8
        ihold_irun = (iholddelay << 16) | (irun << 8) | ihold
        self.write_register(slave, TMC_REG_IHOLD_IRUN, ihold_irun)

        chopconf, _ = self.read_register(slave, TMC_REG_CHOPCONF)
        if chopconf is None:
            chopconf = 0x10000053
        if vsense:
            chopconf |= (1 << 17)
        else:
            chopconf &= ~(1 << 17)
        self.write_register(slave, TMC_REG_CHOPCONF, chopconf)

        print(f"    current={current_ma}mA, IRUN={irun}, IHOLD={ihold}, vsense={'ON' if vsense else 'OFF'}")

    def set_microsteps(self, slave, microsteps):
        mres_map = {256: 0, 128: 1, 64: 2, 32: 3, 16: 4, 8: 5, 4: 6, 2: 7, 1: 8}
        if microsteps not in mres_map:
            raise ValueError(f"unsupported microsteps: {microsteps}")

        chopconf, _ = self.read_register(slave, TMC_REG_CHOPCONF)
        if chopconf is None:
            chopconf = 0x10000053
        chopconf &= ~(0x0F << 24)
        chopconf |= (mres_map[microsteps] & 0x0F) << 24
        self.write_register(slave, TMC_REG_CHOPCONF, chopconf)
        print(f"    microsteps={microsteps}")

    def set_pwm_autoscale(self, slave, enable=True):
        pwmconf, _ = self.read_register(slave, TMC_REG_PWMCONF)
        if pwmconf is None:
            pwmconf = 0xC10D0024
        if enable:
            pwmconf |= (1 << 18)
        else:
            pwmconf &= ~(1 << 18)
        self.write_register(slave, TMC_REG_PWMCONF, pwmconf)
        print(f"    pwm_autoscale={'ON' if enable else 'OFF'}")

    def set_stallguard(self, slave, threshold):
        self.write_register(slave, TMC_REG_SGTHRS, threshold & 0xFF)
        print(f"    SGTHRS={threshold}")

    def configure_axis(self, name, slave, current_ma=600, microsteps=16, stall_threshold=64):
        print(f"  {name}: configuring TMC2209 (slave {slave})")
        self.write_register(slave, TMC_REG_GCONF, (1 << 0) | (1 << 6) | (1 << 7) | (1 << 8))
        self.set_current_rms(slave, current_ma)
        self.set_microsteps(slave, microsteps)
        self.set_pwm_autoscale(slave, True)
        self.set_stallguard(slave, stall_threshold)

    def info(self, name, slave):
        print(f"\n[{name}] TMC2209 info (slave {slave})")
        for reg_name, reg in [("GSTAT", TMC_REG_GSTAT), ("IOIN", TMC_REG_IOIN), ("IHOLD_IRUN", TMC_REG_IHOLD_IRUN), ("CHOPCONF", TMC_REG_CHOPCONF), ("PWMCONF", TMC_REG_PWMCONF)]:
            value, err = self.read_register(slave, reg)
            if err:
                print(f"  {reg_name}: ERROR ({err})")
                continue
            print(f"  {reg_name}: 0x{value:08X}")

        ioin, err = self.read_register(slave, TMC_REG_IOIN)
        if ioin is not None:
            version = (ioin >> 24) & 0xFF
            print(f"  version: 0x{version:02X}")
            print(
                f"  enn={bool(ioin & 0x01)}, ms1={bool(ioin & (1 << 2))}, ms2={bool(ioin & (1 << 3))}, "
                f"pdn_uart={bool(ioin & (1 << 6))}, step={bool(ioin & (1 << 7))}, dir={bool(ioin & (1 << 9))}"
            )


class StepperAxis:
    POSITIVE = 1
    NEGATIVE = 0

    def __init__(self, pi, step_pin, dir_pin, en_pin, name):
        self.pi = pi
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.en_pin = en_pin
        self.name = name
        self.enabled = False
        self.direction = self.POSITIVE
        self.current_speed = 1000

        for pin in (self.step_pin, self.dir_pin, self.en_pin):
            self.pi.set_mode(pin, pigpio.OUTPUT)
        self.pi.write(self.step_pin, 0)
        self.pi.write(self.dir_pin, 0)
        self.pi.write(self.en_pin, 1)

    def enable(self):
        self.pi.write(self.en_pin, 0)
        self.enabled = True
        print(f"[{self.name}] ENABLED")

    def disable(self):
        self.pi.write(self.en_pin, 1)
        self.enabled = False
        print(f"[{self.name}] DISABLED")

    def set_direction(self, direction):
        self.direction = self.POSITIVE if direction else self.NEGATIVE
        self.pi.write(self.dir_pin, self.direction)

    def step(self, direction, count):
        if not self.enabled:
            print(f"[{self.name}] motor disabled; press enable first")
            return

        self.set_direction(direction)
        direction_name = "FORWARD(+)" if direction == self.POSITIVE else "BACKWARD(-)"
        print(f"[{self.name}] DIR={direction_name} ({direction}), steps={count}")

        for _ in range(count):
            self.pi.write(self.step_pin, 1)
            time.sleep(0.000010)
            self.pi.write(self.step_pin, 0)
            time.sleep(0.000010)

    def run_continuous(self, steps):
        if not self.enabled:
            print(f"[{self.name}] motor disabled; press enable first")
            return

        delay_us = 1000000.0 / max(1, self.current_speed) / 2.0
        print(f"[{self.name}] running {steps} steps at {self.current_speed} steps/s")
        for i in range(steps):
            self.pi.write(self.step_pin, 1)
            time.sleep(delay_us / 1000000.0)
            self.pi.write(self.step_pin, 0)
            time.sleep(delay_us / 1000000.0)
            if (i + 1) % 100 == 0:
                print(f"  {i + 1} / {steps}")


def print_banner():
    print("=== ESP32 Analog Dual TMC2209 Test for Raspberry Pi 3B+ ===")
    print("Pin map (BCM numbering):")
    print(f"  X: STEP={STEP_PIN_X}, DIR={DIR_PIN_X}, EN={EN_PIN_X}")
    print(f"  Y: STEP={STEP_PIN_Y}, DIR={DIR_PIN_Y}, EN={EN_PIN_Y}")
    print(f"  Lasers: R={LASER_RED_PIN}, G={LASER_GREEN_PIN}, B={LASER_BLUE_PIN}")
    print("  UART: /dev/serial0 (GPIO14 TXD0, GPIO15 RXD0)")
    print()


def print_help():
    print("Commands:")
    print("  s   single step X")
    print("  S   single step Y")
    print("  r   run X continuously")
    print("  R   run Y continuously")
    print("  d   toggle X direction")
    print("  D   toggle Y direction")
    print("  1-5 speed tests on X: 500/1000/2000/4000/8000")
    print("  h   home motors (placeholder/manual)")
    print("  c   center motors (placeholder/manual)")
    print("  i   read TMC2209 info over UART")
    print("  e   enable both")
    print("  x   disable both")
    print("  E   enable X only")
    print("  X   disable X")
    print("  Y   enable Y only")
    print("  Z   disable Y")
    print("  ?   help")
    print("  q   quit")


def make_pi():
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpio daemon not running")
    return pi


def init_lasers(pi):
    for pin in (LASER_RED_PIN, LASER_GREEN_PIN, LASER_BLUE_PIN):
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.write(pin, 0)


def main():
    print_banner()

    pi = make_pi()
    init_lasers(pi)

    x_axis = StepperAxis(pi, STEP_PIN_X, DIR_PIN_X, EN_PIN_X, "X")
    y_axis = StepperAxis(pi, STEP_PIN_Y, DIR_PIN_Y, EN_PIN_Y, "Y")

    x_axis.direction = StepperAxis.NEGATIVE
    y_axis.direction = StepperAxis.NEGATIVE

    uart = None
    try:
        uart = TMC2209Bus()
        print(f"UART opened on {UART_PORT}")
        print("Configuring TMC2209 drivers...")
        uart.configure_axis("X", 0, current_ma=600, microsteps=16, stall_threshold=64)
        uart.configure_axis("Y", 1, current_ma=600, microsteps=16, stall_threshold=64)
        print("Configuration complete.")
    except Exception as exc:
        print(f"WARNING: UART unavailable or not wired: {exc}")
        print("Continuing with GPIO-only stepping.")

    print_help()

    try:
        while True:
            cmd = input("cmd> ").strip()
            if not cmd:
                continue

            ch = cmd[0]

            if ch == 'q':
                break
            elif ch == 's':
                x_axis.step(x_axis.POSITIVE, 1)
            elif ch == 'S':
                y_axis.step(y_axis.POSITIVE, 1)
            elif ch == 'r':
                x_axis.current_speed = 3000
                x_axis.run_continuous(3000)
            elif ch == 'R':
                y_axis.current_speed = 3000
                y_axis.run_continuous(3000)
            elif ch == 'd':
                x_axis.direction = StepperAxis.NEGATIVE if x_axis.direction == StepperAxis.POSITIVE else StepperAxis.POSITIVE
                x_axis.pi.write(x_axis.dir_pin, x_axis.direction)
                print(f"X Direction: {'CW' if x_axis.direction else 'CCW'}")
            elif ch == 'D':
                y_axis.direction = StepperAxis.NEGATIVE if y_axis.direction == StepperAxis.POSITIVE else StepperAxis.POSITIVE
                y_axis.pi.write(y_axis.dir_pin, y_axis.direction)
                print(f"Y Direction: {'CW' if y_axis.direction else 'CCW'}")
            elif ch == '1':
                x_axis.current_speed = 500
                x_axis.run_continuous(500)
            elif ch == '2':
                x_axis.current_speed = 1000
                x_axis.run_continuous(1000)
            elif ch == '3':
                x_axis.current_speed = 2000
                x_axis.run_continuous(2000)
            elif ch == '4':
                x_axis.current_speed = 4000
                x_axis.run_continuous(4000)
            elif ch == '5':
                x_axis.current_speed = 8000
                x_axis.run_continuous(8000)
            elif ch == 'h':
                print("Homing is not implemented in this analog. Use the UART probe + manual limit workflow.")
            elif ch == 'c':
                print("Centering is not implemented in this analog. Use your calibration workflow.")
            elif ch == 'i':
                if uart is None:
                    print("UART is not available.")
                else:
                    uart.info("X", 0)
                    uart.info("Y", 1)
            elif ch == 'e':
                x_axis.enable()
                y_axis.enable()
            elif ch == 'x':
                x_axis.disable()
                y_axis.disable()
            elif ch == 'E':
                x_axis.enable()
                y_axis.disable()
            elif ch == 'X':
                x_axis.disable()
            elif ch == 'Y':
                x_axis.disable()
                y_axis.enable()
            elif ch == 'Z':
                y_axis.disable()
            elif ch == '?':
                print_help()
            else:
                print(f"Unknown command: {cmd}")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        x_axis.disable()
        y_axis.disable()
        if uart is not None:
            uart.close()
        pi.stop()


if __name__ == "__main__":
    main()
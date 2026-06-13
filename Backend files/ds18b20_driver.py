"""
DS18B20 Temperature Sensor Driver
Uses the Linux kernel 1-Wire interface (no extra libraries needed).

Wiring:
    VCC  → 3.3V  (Pi Pin 1)
    GND  → GND   (Pi Pin 6)
    DATA → GPIO4 (Pi Pin 7)   ← MUST have a 4.7kΩ pull-up resistor between DATA and VCC

Enable 1-Wire before use:
    sudo nano /boot/firmware/config.txt
    Add line:  dtoverlay=w1-gpio
    Save, then: sudo reboot
"""

import glob
import os


W1_DEVICE_PATH = "/sys/bus/w1/devices/"
W1_GLOB        = W1_DEVICE_PATH + "28-*/w1_slave"   # DS18B20 family code = 0x28


class DS18B20:
    def __init__(self):
        self._device_file = self._find_device()

    def _find_device(self) -> str | None:
        devices = glob.glob(W1_GLOB)
        if not devices:
            print("[DS18B20] WARNING: No sensor found at /sys/bus/w1/devices/28-*")
            print("          Make sure dtoverlay=w1-gpio is in /boot/firmware/config.txt")
            print("          and you have rebooted after adding it.")
            return None
        print(f"[DS18B20] Found sensor: {devices[0]}")
        return devices[0]

    def read_celsius(self) -> float | None:
        """
        Read temperature in °C.
        Returns None if the sensor is not found or reading fails.
        The DS18B20 takes up to 750ms to convert; the kernel driver handles waiting.
        """
        if not self._device_file or not os.path.exists(self._device_file):
            # Try to re-detect in case it was reconnected
            self._device_file = self._find_device()
            if not self._device_file:
                return None

        try:
            with open(self._device_file, "r") as f:
                lines = f.readlines()

            # Line 1 must end with "YES" — CRC check passed
            if len(lines) < 2 or lines[0].strip()[-3:] != "YES":
                return None

            # Line 2 contains "t=<millidegrees>"
            t_pos = lines[1].find("t=")
            if t_pos == -1:
                return None

            temp_mc = float(lines[1][t_pos + 2:])
            temp_c  = round(temp_mc / 1000.0, 1)

            # Sanity check: DS18B20 range is -55°C to +125°C
            # 85.0°C is also the power-on reset value — treat as invalid
            if temp_c == 85.0 or not (-55 <= temp_c <= 125):
                return None

            return temp_c

        except (OSError, ValueError) as e:
            print(f"[DS18B20] Read error: {e}")
            return None

"""
MAX30102 Pulse Oximeter & Heart Rate Sensor Driver
Communicates via I2C on Raspberry Pi (default bus=1, addr=0x57)
Wiring: SDA -> GPIO2 (Pin 3), SCL -> GPIO3 (Pin 5), VCC -> 3.3V, GND -> GND
"""

import smbus2
import time

MAX30102_ADDR = 0x57

# --- Register Map ---
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01
REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03
REG_FIFO_WR_PTR   = 0x04
REG_OVF_COUNTER   = 0x05
REG_FIFO_RD_PTR   = 0x06
REG_FIFO_DATA     = 0x07
REG_FIFO_CONFIG   = 0x08
REG_MODE_CONFIG   = 0x09
REG_SPO2_CONFIG   = 0x0A
REG_LED1_PA       = 0x0C   # Red LED amplitude
REG_LED2_PA       = 0x0D   # IR LED amplitude
REG_PILOT_PA      = 0x10
REG_PART_ID       = 0xFF

EXPECTED_PART_ID  = 0x15


class MAX30102:
    def __init__(self, bus_number: int = 1):
        self.bus = smbus2.SMBus(bus_number)
        self.address = MAX30102_ADDR
        self._verify_device()
        self._init_sensor()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _write(self, reg: int, value: int):
        self.bus.write_byte_data(self.address, reg, value)

    def _read(self, reg: int) -> int:
        return self.bus.read_byte_data(self.address, reg)

    def _read_block(self, reg: int, length: int) -> list:
        return self.bus.read_i2c_block_data(self.address, reg, length)

    def _verify_device(self):
        part_id = self._read(REG_PART_ID)
        if part_id != EXPECTED_PART_ID:
            raise RuntimeError(
                f"MAX30102 not found! Part ID = 0x{part_id:02X} (expected 0x{EXPECTED_PART_ID:02X}). "
                "Check wiring and I2C address."
            )
        print(f"[MAX30102] Device found. Part ID: 0x{part_id:02X}")

    def _reset(self):
        """Soft-reset; bit 6 of MODE_CONFIG auto-clears after reset."""
        self._write(REG_MODE_CONFIG, 0x40)
        time.sleep(0.1)

    # ------------------------------------------------------------------ #
    #  Sensor initialisation                                               #
    # ------------------------------------------------------------------ #

    def _init_sensor(self):
        self._reset()

        # Clear FIFO pointers
        self._write(REG_FIFO_WR_PTR, 0x00)
        self._write(REG_OVF_COUNTER, 0x00)
        self._write(REG_FIFO_RD_PTR, 0x00)

        # FIFO config:
        #   Bits[7:5] SMP_AVE = 010  → 4-sample averaging  (effective rate = 100/4 = 25 Hz)
        #   Bit[4]    FIFO_ROLLOVER_EN = 0
        #   Bits[3:0] FIFO_A_FULL = 0xF (almost-full at 17 remaining)
        self._write(REG_FIFO_CONFIG, 0x4F)

        # Mode config: SpO2 mode (Red + IR channels both active)
        self._write(REG_MODE_CONFIG, 0x03)

        # SpO2 config:
        #   Bits[6:5] ADC_RGE  = 01  → 4096 nA full-scale
        #   Bits[4:2] SR       = 001 → 100 samples/sec
        #   Bits[1:0] LED_PW   = 11  → 411 µs pulse, 18-bit ADC resolution
        self._write(REG_SPO2_CONFIG, 0x27)

        # LED amplitude (~7.2 mA; 0x24 = 36 → 36 * 0.2 mA = 7.2 mA)
        self._write(REG_LED1_PA, 0x24)   # Red LED
        self._write(REG_LED2_PA, 0x24)   # IR LED
        self._write(REG_PILOT_PA, 0x7F)  # Proximity pilot LED

        # Enable FIFO-almost-full & new-data-ready interrupts
        self._write(REG_INTR_ENABLE_1, 0xC0)
        self._write(REG_INTR_ENABLE_2, 0x00)

        print("[MAX30102] Sensor initialised (SpO2 mode, 25 Hz effective).")

    # ------------------------------------------------------------------ #
    #  Data reading                                                        #
    # ------------------------------------------------------------------ #

    def samples_available(self) -> int:
        """Number of unread samples in the FIFO."""
        wr = self._read(REG_FIFO_WR_PTR)
        rd = self._read(REG_FIFO_RD_PTR)
        return (wr - rd) & 0x1F

    def read_fifo_sample(self) -> tuple[int, int]:
        """
        Read one sample from the FIFO.
        Returns (red, ir) as 18-bit integers (0 – 262143).
        """
        raw = self._read_block(REG_FIFO_DATA, 6)
        # Each channel: 3 bytes, top 2 bits masked to 18-bit value
        red = ((raw[0] & 0x03) << 16) | (raw[1] << 8) | raw[2]
        ir  = ((raw[3] & 0x03) << 16) | (raw[4] << 8) | raw[5]
        return red, ir

    def read_all_fifo_samples(self) -> list[tuple[int, int]]:
        """Drain the FIFO and return all available (red, ir) samples."""
        samples = []
        n = self.samples_available()
        for _ in range(n):
            samples.append(self.read_fifo_sample())
        return samples

    # ------------------------------------------------------------------ #
    #  Cleanup                                                             #
    # ------------------------------------------------------------------ #

    def close(self):
        self.bus.close()
        print("[MAX30102] I2C bus closed.")

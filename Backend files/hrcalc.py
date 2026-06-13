"""
Heart Rate & SpO2 Calculator for MAX30102
Implements peak-detection based HR and ratio-of-ratios SpO2 estimation.

Reference: Maxim Integrated Application Note AN6612
"""

import math
from typing import Sequence


# ─────────────────────────────────────────────────────────────────────────────
#  SpO2 empirical coefficients (curve fit against clinical data)
#  SpO2 ≈ A·R² + B·R + C  where R = (AC_red/DC_red) / (AC_ir/DC_ir)
# ─────────────────────────────────────────────────────────────────────────────
SPO2_A = -45.060
SPO2_B =  30.354
SPO2_C =  98.356

EFFECTIVE_SAMPLE_RATE = 25   # Hz (100 Hz hardware / 4-sample average)
MIN_HR = 30                  # bpm – below this we report -1
MAX_HR = 240                 # bpm – above this we report -1
MIN_PEAK_DISTANCE = 5        # samples (prevents double-counting the same peak)
PEAK_THRESHOLD_RATIO = 0.4   # fraction of max AC amplitude used as threshold


def _mean(data: Sequence[float]) -> float:
    return sum(data) / len(data)


def _remove_dc(data: Sequence[float]) -> list[float]:
    """Subtract the mean (DC component) from each sample."""
    mu = _mean(data)
    return [x - mu for x in data]


def _detect_peaks(ac_signal: list[float], threshold: float, min_distance: int) -> list[int]:
    """Return indices of local maxima above `threshold`, spaced >= min_distance apart."""
    peaks = []
    n = len(ac_signal)
    for i in range(1, n - 1):
        if (
            ac_signal[i] > threshold
            and ac_signal[i] > ac_signal[i - 1]
            and ac_signal[i] > ac_signal[i + 1]
        ):
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
    return peaks


def calc_hr_and_spo2(
    ir_data: Sequence[int],
    red_data: Sequence[int],
) -> tuple[int, float]:
    """
    Estimate heart rate (bpm) and SpO2 (%) from raw IR and Red buffers.

    Parameters
    ----------
    ir_data  : list of raw 18-bit IR ADC readings
    red_data : list of raw 18-bit Red ADC readings

    Returns
    -------
    (hr, spo2)  –  hr is int bpm (-1 if unavailable)
                   spo2 is float % (-1.0 if unavailable)
    """
    n = len(ir_data)
    if n < 10:
        return -1, -1.0

    ir  = list(ir_data)
    red = list(red_data)

    # ── DC / AC decomposition ────────────────────────────────────────────
    dc_ir  = _mean(ir)
    dc_red = _mean(red)

    ir_ac  = _remove_dc(ir)
    red_ac = _remove_dc(red)

    ac_ir  = max(abs(x) for x in ir_ac)
    ac_red = max(abs(x) for x in red_ac)

    # ── SpO2 (ratio-of-ratios) ────────────────────────────────────────────
    spo2 = -1.0
    if dc_ir > 0 and dc_red > 0 and ac_ir > 0:
        R = (ac_red / dc_red) / (ac_ir / dc_ir)
        raw_spo2 = SPO2_A * R * R + SPO2_B * R + SPO2_C
        spo2 = round(max(0.0, min(100.0, raw_spo2)), 1)

    # ── Heart Rate (peak detection on IR AC signal) ───────────────────────
    hr = -1
    if ac_ir > 0:
        threshold = PEAK_THRESHOLD_RATIO * ac_ir
        peaks = _detect_peaks(ir_ac, threshold, MIN_PEAK_DISTANCE)

        if len(peaks) >= 2:
            intervals = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
            avg_interval = _mean(intervals)
            bpm = (EFFECTIVE_SAMPLE_RATE * 60) / avg_interval
            if MIN_HR <= bpm <= MAX_HR:
                hr = round(bpm)

    return hr, spo2

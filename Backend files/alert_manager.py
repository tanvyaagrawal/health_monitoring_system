"""
Alert Manager
─────────────
Sends Telegram alerts when vitals are abnormal.

False-alarm prevention:
  1. PERSIST check  — value must be abnormal for N seconds continuously
  2. COOLDOWN check — same alert type won't repeat for M seconds
  3. Ready gate     — no alerts until the sensor buffer is fully warmed up
"""

import time
import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
    THRESHOLDS,
    ALERT_PERSIST_SECONDS,
    ALERT_COOLDOWN_SECONDS,
)

# Each alert type tracks:  { "since": float|None, "last_sent": float }
_ALERT_KEYS = ["hr_low", "hr_high", "spo2_low", "temp_high", "temp_low"]

ALERT_MESSAGES = {
    "hr_low":    "🔴 LOW HEART RATE (Bradycardia)\nHR = {value} bpm  (threshold < {thresh} bpm)\nPlease check on the patient immediately.",
    "hr_high":   "🔴 HIGH HEART RATE (Tachycardia)\nHR = {value} bpm  (threshold > {thresh} bpm)\nPlease check on the patient immediately.",
    "spo2_low":  "🔴 LOW BLOOD OXYGEN (Hypoxemia)\nSpO₂ = {value}%  (threshold < {thresh}%)\nUrgent attention may be required.",
    "temp_high": "🌡️ HIGH TEMPERATURE (Fever)\nTemp = {value}°C  (threshold > {thresh}°C)\nPatient may need medical evaluation.",
    "temp_low":  "🌡️ LOW TEMPERATURE (Hypothermia)\nTemp = {value}°C  (threshold < {thresh}°C)\nPatient may need medical evaluation.",
}

RECOVERY_MESSAGES = {
    "hr_low":    "✅ Heart rate has returned to normal range ({value} bpm).",
    "hr_high":   "✅ Heart rate has returned to normal range ({value} bpm).",
    "spo2_low":  "✅ SpO₂ has returned to normal range ({value}%).",
    "temp_high": "✅ Temperature has returned to normal range ({value}°C).",
    "temp_low":  "✅ Temperature has returned to normal range ({value}°C).",
}


def _tg_send(text: str):
    """Fire-and-forget Telegram message."""
    if not TELEGRAM_ENABLED:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"[TELEGRAM] Sent: {text[:60]}…")
        else:
            print(f"[TELEGRAM] Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[TELEGRAM] Failed to send: {e}")


class AlertManager:
    def __init__(self):
        self._state: dict[str, dict] = {
            key: {"since": None, "last_sent": 0.0, "active": False}
            for key in _ALERT_KEYS
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(self, hr: int, spo2: float, temp: float | None, ready: bool) -> list[str]:
        """
        Call this on every data update.
        Returns list of alert keys that fired this cycle (for broadcasting to frontend).
        """
        if not ready:
            return []

        now    = time.time()
        fired  = []

        checks = self._build_checks(hr, spo2, temp)

        for key, (is_abnormal, value) in checks.items():
            s = self._state[key]

            if is_abnormal:
                if s["since"] is None:
                    s["since"] = now   # start the persist timer

                elapsed    = now - s["since"]
                since_sent = now - s["last_sent"]
                thresh_met = elapsed >= ALERT_PERSIST_SECONDS
                cooldown_ok= since_sent >= ALERT_COOLDOWN_SECONDS

                if thresh_met and cooldown_ok:
                    self._send_alert(key, value)
                    s["last_sent"] = now
                    s["active"]    = True
                    fired.append(key)
            else:
                # Condition cleared — send recovery if it was active
                if s["active"]:
                    self._send_recovery(key, value)
                    s["active"] = False
                # Reset persist timer
                s["since"] = None

        return fired

    def active_alerts(self) -> list[str]:
        return [k for k, s in self._state.items() if s["active"]]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_checks(self, hr, spo2, temp) -> dict:
        t = THRESHOLDS
        checks = {}

        # Only check HR if it's a valid reading (not -1)
        if hr != -1:
            checks["hr_low"]  = (hr < t["hr_low"],   hr)
            checks["hr_high"] = (hr > t["hr_high"],  hr)

        # Only check SpO2 if valid
        if spo2 != -1:
            checks["spo2_low"] = (spo2 < t["spo2_low"], spo2)

        # Only check temperature if sensor returned a value
        if temp is not None:
            checks["temp_high"] = (temp > t["temp_high"], temp)
            checks["temp_low"]  = (temp < t["temp_low"],  temp)

        return checks

    def _send_alert(self, key: str, value):
        t = THRESHOLDS
        thresh_map = {
            "hr_low":    t["hr_low"],
            "hr_high":   t["hr_high"],
            "spo2_low":  t["spo2_low"],
            "temp_high": t["temp_high"],
            "temp_low":  t["temp_low"],
        }
        msg = ALERT_MESSAGES[key].format(value=value, thresh=thresh_map[key])
        header = "⚠️ PATIENT VITAL ALERT\n──────────────────────\n"
        _tg_send(header + msg)

    def _send_recovery(self, key: str, value):
        msg = RECOVERY_MESSAGES[key].format(value=value)
        _tg_send(msg)

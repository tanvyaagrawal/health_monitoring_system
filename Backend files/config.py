# ─────────────────────────────────────────────────────────────────────────────
#  config.py  –  Edit this file before running the server
# ─────────────────────────────────────────────────────────────────────────────

# ── Telegram ──────────────────────────────────────────────────────────────────
# Step 1: Message @BotFather on Telegram → /newbot → copy the token below
# Step 2: Message @userinfobot on Telegram → copy your chat_id below
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"       # e.g. "7312456789:AAF..."
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"          # e.g. "123456789"

# Set to False to disable Telegram alerts without removing the credentials
TELEGRAM_ENABLED = True

# ── Alert thresholds ──────────────────────────────────────────────────────────
#
#   These are conservative clinical thresholds.
#   An alert only fires after the value stays abnormal for ALERT_PERSIST_SECONDS
#   continuously, AND won't repeat for ALERT_COOLDOWN_SECONDS.
#   This eliminates motion-artifact false alarms.

THRESHOLDS = {
    "hr_low":    45,    # bpm  — below this = bradycardia alert
    "hr_high":  130,    # bpm  — above this = tachycardia alert
    "spo2_low":  92.0,  # %    — below this = hypoxemia alert  (94% is borderline, 92% is serious)
    "temp_high": 38.5,  # °C   — above this = fever alert
    "temp_low":  35.0,  # °C   — below this = hypothermia alert
}

# How many SECONDS a value must stay abnormal before an alert is sent
# (prevents motion-artifact spikes from triggering false alerts)
ALERT_PERSIST_SECONDS  = 15

# Minimum gap (seconds) between two alerts of the SAME type
# (prevents alert spam if condition persists)
ALERT_COOLDOWN_SECONDS = 600   # 10 minutes

# ── Hardware ──────────────────────────────────────────────────────────────────
I2C_BUS            = 1        # Raspberry Pi I2C bus number
WEBSOCKET_PORT     = 8765
DS18B20_READ_EVERY = 5        # seconds between temperature reads (sensor is slow)

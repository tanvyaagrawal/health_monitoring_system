"""
Vital Signs WebSocket Server
─────────────────────────────
Reads MAX30102 (HR + SpO2 + raw IR/Red) and DS18B20 (temperature),
broadcasts JSON to all connected WebSocket clients, and fires Telegram
alerts via AlertManager when readings are abnormal.

Run:  python sensor_server.py
URL:  ws://<pi_ip>:8765
"""

import asyncio
import json
import time
from collections import deque

import websockets

from max30102_driver import MAX30102
from ds18b20_driver  import DS18B20
from hrcalc          import calc_hr_and_spo2
from alert_manager   import AlertManager
from config          import (
    I2C_BUS,
    WEBSOCKET_PORT,
    DS18B20_READ_EVERY,
)

# ─── Tuning ────────────────────────────────────────────────────────────────
CALC_BUFFER   = 100     # samples for HR/SpO2 calculation
POLL_INTERVAL = 0.04    # seconds between FIFO polls (~25 Hz)

# ─── Connected clients ─────────────────────────────────────────────────────
CLIENTS: set = set()


# ────────────────────────────────────────────────────────────────────────────
#  WebSocket handlers
# ────────────────────────────────────────────────────────────────────────────

async def connection_handler(websocket):
    CLIENTS.add(websocket)
    addr = websocket.remote_address
    print(f"[WS] Client connected:    {addr}  (total: {len(CLIENTS)})")
    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.discard(websocket)
        print(f"[WS] Client disconnected: {addr}  (total: {len(CLIENTS)})")


async def broadcast(payload: dict):
    if not CLIENTS:
        return
    msg = json.dumps(payload)
    await asyncio.gather(
        *[ws.send(msg) for ws in CLIENTS],
        return_exceptions=True,
    )


# ────────────────────────────────────────────────────────────────────────────
#  Sensor loop
# ────────────────────────────────────────────────────────────────────────────

async def sensor_loop():
    # ── Init hardware ──────────────────────────────────────────────────────
    try:
        oximeter = MAX30102(bus_number=I2C_BUS)
    except Exception as e:
        print(f"[ERROR] MAX30102 init failed: {e}")
        raise

    thermometer = DS18B20()   # non-fatal if not connected
    alerts      = AlertManager()

    ir_buf  = deque(maxlen=CALC_BUFFER)
    red_buf = deque(maxlen=CALC_BUFFER)

    hr   = -1
    spo2 = -1.0
    temp = None

    last_temp_read = 0.0
    print("[SERVER] Streaming vitals…")

    try:
        while True:
            now = time.time()

            # ── Read MAX30102 FIFO ─────────────────────────────────────────
            try:
                for red_raw, ir_raw in oximeter.read_all_fifo_samples():
                    ir_buf.append(ir_raw)
                    red_buf.append(red_raw)
            except OSError as e:
                print(f"[WARN] MAX30102 read error: {e}")

            # ── Calculate HR / SpO2 once buffer is warm ────────────────────
            ready = len(ir_buf) == CALC_BUFFER
            if ready:
                hr, spo2 = calc_hr_and_spo2(list(ir_buf), list(red_buf))

            # ── Read DS18B20 (slow sensor — read every N seconds) ──────────
            if now - last_temp_read >= DS18B20_READ_EVERY:
                temp = thermometer.read_celsius()
                last_temp_read = now

            # ── Evaluate alerts ────────────────────────────────────────────
            fired_alerts = alerts.evaluate(hr, spo2, temp, ready)

            # ── Broadcast to dashboard ────────────────────────────────────
            if ir_buf:
                payload = {
                    "timestamp":    round(now * 1000),   # ms epoch
                    "ir":           ir_buf[-1],
                    "red":          red_buf[-1],
                    "hr":           hr,
                    "spo2":         spo2,
                    "temp":         temp,
                    "ready":        ready,
                    "active_alerts": alerts.active_alerts(),
                    "fired_alerts":  fired_alerts,
                }
                await broadcast(payload)

            await asyncio.sleep(POLL_INTERVAL)

    finally:
        oximeter.close()


# ────────────────────────────────────────────────────────────────────────────
#  Entry point
# ────────────────────────────────────────────────────────────────────────────

async def main():
    async with websockets.serve(connection_handler, "0.0.0.0", WEBSOCKET_PORT):
        print(f"[WS] Server listening on ws://0.0.0.0:{WEBSOCKET_PORT}")
        await sensor_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")

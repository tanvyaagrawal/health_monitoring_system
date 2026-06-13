# Real-Time Health Monitoring System

## Overview

A full-stack IoT Health Monitoring System that continuously acquires physiological data from wearable sensors, processes the data in real time, generates health alerts, and visualizes patient vitals through an interactive web dashboard.

The system integrates biomedical sensors with a Python backend and a React-based frontend to provide continuous monitoring of critical health parameters such as heart rate, blood oxygen saturation (SpO₂), and body temperature.

---

## Key Features

### Real-Time Vital Monitoring

* Heart Rate (BPM)
* Blood Oxygen Saturation (SpO₂)
* Body Temperature

### Intelligent Alert System

* Bradycardia Detection
* Tachycardia Detection
* Hypoxemia Detection
* Fever Detection
* Hypothermia Detection

### Live Dashboard

* Real-time sensor updates
* Interactive charts and visualizations
* Device connection monitoring
* Alert notifications
* Responsive user interface

### IoT Integration

* MAX30102 Pulse Oximeter Sensor
* DS18B20 Temperature Sensor
* WebSocket-based communication
* Continuous sensor data streaming

---

## System Architecture

```text
MAX30102 Sensor
        │
        ▼
Heart Rate & SpO₂ Processing
        │
        ▼
Python Backend Server
        │
        ├── Alert Manager
        ├── Sensor Drivers
        └── WebSocket Server
        │
        ▼
React Dashboard
        │
        ▼
Real-Time Visualization
```

---

## Technology Stack

### Frontend

* React
* Vite
* JavaScript
* Recharts

### Backend

* Python
* Async WebSockets

### Hardware

* MAX30102 Pulse Oximeter Sensor
* DS18B20 Temperature Sensor

### Communication

* WebSocket Protocol

---

## Project Structure

```text
health-monitoring-system/

├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── backend/
│   ├── sensor_server.py
│   ├── alert_manager.py
│   ├── config.py
│   ├── hrcalc.py
│   ├── max30102_driver.py
│   ├── ds18b20_driver.py
│   └── requirements.txt
│
└── README.md
```

---

## Hardware Requirements

### Sensors

* MAX30102 Pulse Oximeter Sensor
* DS18B20 Temperature Sensor

### Processing Unit

* Raspberry Pi (recommended)

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/health-monitoring-system.git
cd health-monitoring-system
```

---

## Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start backend server:

```bash
python sensor_server.py
```

---

## Frontend Setup

Navigate to frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## Health Alert Criteria

### Heart Rate

| Condition   | Threshold  |
| ----------- | ---------- |
| Bradycardia | < 45 BPM   |
| Normal      | 45–130 BPM |
| Tachycardia | > 130 BPM  |

### SpO₂

| Condition  | Threshold |
| ---------- | --------- |
| Normal     | ≥ 95%     |
| Low Oxygen | 90–94%    |
| Hypoxemia  | < 90%     |

### Temperature

| Condition   | Threshold     |
| ----------- | ------------- |
| Hypothermia | < 35°C        |
| Normal      | 35°C–37.5°C   |
| Elevated    | 37.5°C–38.5°C |
| Fever       | > 38.5°C      |

---

## Applications

* Remote Patient Monitoring
* Elderly Care Systems
* Home Health Monitoring
* Telemedicine Platforms
* Smart Healthcare Devices
* Clinical Research

---

## Future Enhancements

* Cloud Database Integration
* Historical Health Analytics
* Mobile Application Support
* Doctor Notification System
* AI-Based Health Risk Prediction
* Multi-Patient Monitoring
* Electronic Health Record Integration

---

## Authors

Developed as an IoT-based healthcare monitoring solution for real-time physiological data acquisition, processing, and visualization.

---

## License

This project is intended for educational, research, and healthcare technology development purposes.

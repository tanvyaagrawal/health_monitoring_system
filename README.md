# Health Monitoring System

## Overview

A real-time Health Monitoring System developed using React and Vite that continuously monitors vital health parameters and displays them through an interactive dashboard.

The system receives live sensor data through WebSocket communication and provides real-time visualization, status monitoring, and medical alerts.

---

## Features

### Real-Time Monitoring

* Heart Rate (BPM)
* Blood Oxygen Saturation (SpO₂)
* Body Temperature

### Intelligent Health Alerts

* Bradycardia Detection
* Tachycardia Detection
* Low SpO₂ Detection (Hypoxemia)
* Fever Detection
* Hypothermia Detection

### Dashboard Features

* Live sensor status indicators
* Automatic WebSocket reconnection
* Real-time health data visualization
* Responsive user interface
* Alert prioritization and color-coded notifications

---

## Technology Stack

### Frontend

* React
* Vite
* JavaScript (ES6+)

### Visualization

* Recharts

### Communication

* WebSocket

### Development Tools

* ESLint

---

## Project Structure

```text
health-monitoring-system/
├── public/
├── src/
│   ├── assets/
│   ├── App.jsx
│   ├── App.css
│   ├── main.jsx
│   └── index.css
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/<your-username>/health-monitoring-system.git
cd health-monitoring-system
```

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The application will be available at:

```text
http://localhost:5173
```

---

## Configuration

Update the WebSocket endpoint in `src/App.jsx`:

```javascript
const WS_URL = "ws://YOUR_SERVER_IP:8765";
```

Replace `YOUR_SERVER_IP` with the IP address of your Raspberry Pi, ESP32 gateway, or backend server.

---

## Health Status Logic

### Heart Rate

| Condition   | Range        |
| ----------- | ------------ |
| Normal      | 45 – 130 BPM |
| Bradycardia | < 45 BPM     |
| Tachycardia | > 130 BPM    |

### SpO₂

| Condition | Range  |
| --------- | ------ |
| Normal    | ≥ 95%  |
| Low       | 90–94% |
| Hypoxemia | < 90%  |

### Temperature

| Condition   | Range           |
| ----------- | --------------- |
| Normal      | 35.0°C – 37.5°C |
| Elevated    | 37.5°C – 38.5°C |
| Fever       | > 38.5°C        |
| Hypothermia | < 35.0°C        |

---

## Future Enhancements

* Cloud data storage
* Patient history tracking
* Mobile application support
* Doctor notification system
* AI-based health risk prediction
* Multi-patient monitoring

---

## Authors

Developed as part of a Health Monitoring System project for real-time vital sign monitoring and visualization.

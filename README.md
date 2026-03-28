# CyberGuard – SOC Analyst Simulation Dashboard

A fully functional Security Operations Center (SOC) simulation dashboard that monitors logs, detects threats, generates alerts, and produces PDF reports. Built with React, Flask, SQLite, and WebSockets.

## Features

- **Real-time log monitoring** with WebSocket updates
- **Threat detection** (brute force, port scan, DDoS, suspicious IP)
- **Alert system** with severity levels (Low, Medium, High, Critical)
- **Security level** auto-adjustment (Normal → Critical Emergency)
- **Dashboard** with charts (login success/failure, alerts by type, traffic over time)
- **PDF report** generation (ReportLab)
- **Dark mode** toggle
- **Search & filter** logs
- **Export logs** as CSV
- **Manual threat marking** and **IP blacklisting**
- **Real-time toast notifications**

## Tech Stack

- **Frontend**: React, Tailwind CSS, Recharts, Axios, Socket.IO-client
- **Backend**: Flask, Flask-SocketIO, SQLAlchemy, SQLite
- **Other**: ReportLab, Faker, Pandas

## Installation & Running

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
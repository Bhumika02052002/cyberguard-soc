from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import threading
import time
import json
import pandas as pd
import io
import platform
import subprocess
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta

from database import db, Log, Alert, Blacklist
from log_generator import generate_and_store_logs
from threat_engine import ThreatEngine
from alert_engine import AlertEngine
from report_generator import generate_pdf_report

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyberguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)

with app.app_context():
    db.create_all()

# ----------------------------------------------------------------------
# System log collection helpers
# ----------------------------------------------------------------------
def get_windows_security_logs():
    """Retrieve last 50 security events (failed logins) from Windows Event Log."""
    try:
        cmd = ['wevtutil', 'qe', 'Security', '/rd:true', '/c:50', '/f:xml']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        root = ET.fromstring(result.stdout)
        logs = []
        for event in root.findall('.//Event'):
            event_id_elem = event.find('.//EventID')
            if event_id_elem is None:
                continue
            event_id = int(event_id_elem.text)
            if event_id != 4625:
                continue
            system = event.find('System')
            if system is None:
                continue
            time_created = system.find('TimeCreated')
            if time_created is None:
                continue
            timestamp_str = time_created.get('SystemTime')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
            data_items = event.findall('.//Data')
            ip = None
            for data in data_items:
                name = data.get('Name')
                if name == 'IpAddress':
                    ip = data.text
                    break
            if ip is None:
                continue
            logs.append({
                'timestamp': timestamp.isoformat(),
                'ip_address': ip,
                'port': 0,
                'status': 'failed',
                'event_type': 'login',
                'country': None
            })
        return logs
    except Exception as e:
        print(f"Error reading Windows security logs: {e}")
        return []

def get_linux_auth_logs():
    """Read /var/log/auth.log and extract failed password attempts."""
    logs = []
    try:
        with open('/var/log/auth.log', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        pattern = re.compile(r'Failed password for .* from (?P<ip>\d+\.\d+\.\d+\.\d+) port \d+')
        for line in lines:
            match = pattern.search(line)
            if not match:
                continue
            ip = match.group('ip')
            parts = line.split()
            if len(parts) < 3:
                continue
            month = parts[0]
            day = parts[1]
            time_str = parts[2]
            try:
                dt_str = f"{datetime.now().year} {month} {day} {time_str}"
                timestamp = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
            except:
                timestamp = datetime.utcnow()
            logs.append({
                'timestamp': timestamp.isoformat(),
                'ip_address': ip,
                'port': 22,
                'status': 'failed',
                'event_type': 'login',
                'country': None
            })
        return logs
    except Exception as e:
        print(f"Error reading Linux auth logs: {e}")
        return []

# ----------------------------------------------------------------------
# Background log generator
# ----------------------------------------------------------------------
def auto_log_generator():
    while True:
        with app.app_context():
            new_logs = generate_and_store_logs(count=5)
            for log in new_logs:
                socketio.emit('new_log', log.to_dict())
        time.sleep(10)

threading.Thread(target=auto_log_generator, daemon=True).start()

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.route('/api/logs', methods=['GET'])
def get_logs():
    ip = request.args.get('ip')
    event_type = request.args.get('event_type')
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    query = Log.query
    if ip:
        query = query.filter(Log.ip_address == ip)
    if event_type:
        query = query.filter(Log.event_type == event_type)
    if status:
        query = query.filter(Log.status == status)
    logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
    return jsonify([log.to_dict() for log in logs])

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(100).all()
    return jsonify([alert.to_dict() for alert in alerts])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_logs = Log.query.count()
    total_alerts = Alert.query.count()
    failed_logins = Log.query.filter_by(status='failed', event_type='login').count()
    successful_logins = Log.query.filter_by(status='success', event_type='login').count()

    from sqlalchemy import func
    alerts_per_type = db.session.query(Alert.threat_type, func.count(Alert.id)).group_by(Alert.threat_type).all()
    alerts_per_type = {t: c for t, c in alerts_per_type}

    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    hourly_traffic = []
    for i in range(24):
        start = day_ago + timedelta(hours=i)
        end = start + timedelta(hours=1)
        count = Log.query.filter(Log.timestamp >= start, Log.timestamp < end).count()
        hourly_traffic.append(count)

    return jsonify({
        'total_logs': total_logs,
        'total_alerts': total_alerts,
        'failed_logins': failed_logins,
        'successful_logins': successful_logins,
        'alerts_per_type': alerts_per_type,
        'hourly_traffic': hourly_traffic
    })

@app.route('/api/security-level', methods=['GET'])
def get_security_level():
    now = datetime.utcnow()
    last_hour_alerts = Alert.query.filter(Alert.timestamp >= now - timedelta(hours=1)).all()
    critical_count = sum(1 for a in last_hour_alerts if a.severity == 'Critical')
    high_count = sum(1 for a in last_hour_alerts if a.severity == 'High')
    medium_count = sum(1 for a in last_hour_alerts if a.severity == 'Medium')
    low_count = sum(1 for a in last_hour_alerts if a.severity == 'Low')

    if critical_count >= 2 or high_count >= 5:
        level = "Critical Emergency"
    elif high_count >= 2 or medium_count >= 5:
        level = "Under Attack"
    elif medium_count >= 2 or low_count >= 5:
        level = "Suspicious"
    elif low_count >= 2:
        level = "Elevated"
    else:
        level = "Normal"
    return jsonify({'level': level})

@app.route('/api/blacklist', methods=['POST'])
def add_blacklist():
    data = request.json
    ip = data.get('ip')
    reason = data.get('reason', '')
    if not ip:
        return jsonify({'error': 'IP required'}), 400
    existing = Blacklist.query.filter_by(ip_address=ip).first()
    if existing:
        return jsonify({'message': 'IP already blacklisted'}), 200
    blacklist = Blacklist(ip_address=ip, reason=reason)
    db.session.add(blacklist)
    db.session.commit()
    return jsonify({'message': 'IP blacklisted'}), 201

@app.route('/api/blacklist', methods=['GET'])
def get_blacklist():
    blacklist = Blacklist.query.all()
    return jsonify([b.to_dict() for b in blacklist])

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    data = [log.to_dict() for log in logs]
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='logs_export.csv'
    )

@app.route('/api/report/pdf', methods=['GET'])
def export_pdf():
    pdf_buffer = generate_pdf_report()
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='cyberguard_report.pdf'
    )

@app.route('/upload-logs', methods=['POST'])
def upload_logs():
    """Upload a file (JSON, .log, .txt) containing logs."""
    file = request.files['file']
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    filename = file.filename
    logs_data = []
    try:
        if filename.endswith('.json'):
            logs_data = json.load(file)
        elif filename.endswith(('.log', '.txt')):
            content = file.read().decode('utf-8').splitlines()
            for line in content:
                try:
                    entry = json.loads(line)
                    logs_data.append(entry)
                except json.JSONDecodeError:
                    parts = line.split()
                    if len(parts) >= 4:
                        timestamp = parts[0] + " " + parts[1]
                        ip = parts[2] if len(parts) > 2 else "0.0.0.0"
                        status = "failed" if "failed" in line.lower() else "success"
                        event_type = "login" if "login" in line.lower() else "network"
                        logs_data.append({
                            "timestamp": timestamp,
                            "ip_address": ip,
                            "port": 0,
                            "status": status,
                            "event_type": event_type,
                            "country": None
                        })
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400

    count = 0
    for entry in logs_data:
        try:
            log = Log(
                timestamp=datetime.fromisoformat(entry['timestamp']),
                ip_address=entry['ip_address'],
                port=int(entry.get('port', 0)),
                status=entry['status'],
                event_type=entry['event_type'],
                country=entry.get('country')
            )
            db.session.add(log)
            db.session.flush()
            count += 1
            alerts = ThreatEngine.analyze_log(log)
            for alert_data in alerts:
                AlertEngine.create_alert(**alert_data)
        except Exception as e:
            print(f"Skipping entry {entry}: {e}")
            continue
    db.session.commit()
    return jsonify({'message': f'{count} logs uploaded'}), 201

@app.route('/analyze-system', methods=['GET'])
def analyze_system():
    """Collect system logs, analyze them, and return logs & alerts."""
    system = platform.system()
    logs = []
    if system == 'Windows':
        logs = get_windows_security_logs()
    elif system == 'Linux':
        logs = get_linux_auth_logs()
    else:
        return jsonify({'error': 'Unsupported OS'}), 400

    if not logs:
        return jsonify({'logs': [], 'alerts': []}), 200

    stored_logs = []
    alerts = []
    for log_data in logs:
        log = Log(
            timestamp=datetime.fromisoformat(log_data['timestamp']),
            ip_address=log_data['ip_address'],
            port=log_data['port'],
            status=log_data['status'],
            event_type=log_data['event_type'],
            country=log_data['country']
        )
        db.session.add(log)
        db.session.flush()
        stored_logs.append(log.to_dict())
        threat_alerts = ThreatEngine.analyze_log(log)
        for alert_data in threat_alerts:
            alert = AlertEngine.create_alert(**alert_data)
            alerts.append(alert.to_dict())
    db.session.commit()

    return jsonify({
        'logs': stored_logs,
        'alerts': alerts
    })

@app.route('/api/manual-threat', methods=['POST'])
def manual_threat():
    data = request.json
    log_id = data.get('log_id')
    log = Log.query.get(log_id)
    if not log:
        return jsonify({'error': 'Log not found'}), 404
    alert_data = {
        'threat_type': 'Manual Threat',
        'severity': 'High',
        'ip_address': log.ip_address,
        'description': f'Manually marked log ID {log_id} as threat'
    }
    AlertEngine.create_alert(**alert_data)
    return jsonify({'message': 'Alert created'}), 201

@app.route('/api/clear-logs', methods=['DELETE'])
def clear_logs():
    """Delete all logs and alerts from the database."""
    try:
        num_logs = Log.query.delete()
        num_alerts = Alert.query.delete()
        db.session.commit()
        return jsonify({
            'message': f'Cleared {num_logs} logs and {num_alerts} alerts'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ----------------------------------------------------------------------
# WebSocket
# ----------------------------------------------------------------------
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to CyberGuard backend'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
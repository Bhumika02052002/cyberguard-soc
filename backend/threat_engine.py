from datetime import datetime, timedelta
from collections import defaultdict
from database import db, Log, Alert, Blacklist
from sqlalchemy import func, and_

class ThreatEngine:
    @staticmethod
    def check_failed_logins(ip_address, window_minutes=5, threshold=5):
        """Detect brute force: more than threshold failed logins in time window."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        failed_count = Log.query.filter(
            Log.ip_address == ip_address,
            Log.status == 'failed',
            Log.event_type == 'login',
            Log.timestamp >= cutoff
        ).count()
        return failed_count >= threshold

    @staticmethod
    def check_port_scan(ip_address, window_seconds=30, threshold=10):
        """Detect port scan: same IP hitting many distinct ports in short time."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        distinct_ports = db.session.query(Log.port).filter(
            Log.ip_address == ip_address,
            Log.timestamp >= cutoff
        ).distinct().count()
        return distinct_ports >= threshold

    @staticmethod
    def check_ddos(ip_address, window_seconds=10, threshold=50):
        """Detect DDoS: high frequency of requests from same IP."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        request_count = Log.query.filter(
            Log.ip_address == ip_address,
            Log.timestamp >= cutoff
        ).count()
        return request_count >= threshold

    @staticmethod
    def check_suspicious_ip(ip_address):
        """Check if IP is in blacklist or from an unexpected country (simulated)."""
        blacklisted = Blacklist.query.filter_by(ip_address=ip_address).first() is not None
        # Simulate geo anomaly: if IP starts with '192.168' treat as internal (safe), else external suspicious
        # In real system, you'd check against known malicious IP lists.
        geo_suspicious = not ip_address.startswith('192.168.') and not ip_address.startswith('10.')
        return blacklisted or geo_suspicious

    @staticmethod
    def analyze_log(log_entry):
        """Run all checks on a log entry and return a list of alerts."""
        alerts = []
        ip = log_entry.ip_address

        # 1. Failed login detection
        if log_entry.status == 'failed' and log_entry.event_type == 'login':
            if ThreatEngine.check_failed_logins(ip):
                alerts.append({
                    'threat_type': 'Brute Force Attack',
                    'severity': 'High',
                    'ip_address': ip,
                    'description': f'Multiple failed logins from {ip}'
                })

        # 2. Port scanning detection (triggered by any log from IP that hits many ports)
        if ThreatEngine.check_port_scan(ip):
            alerts.append({
                'threat_type': 'Port Scan',
                'severity': 'Medium',
                'ip_address': ip,
                'description': f'Port scanning detected from {ip}'
            })

        # 3. DDoS detection (high frequency)
        if ThreatEngine.check_ddos(ip):
            alerts.append({
                'threat_type': 'DDoS Attempt',
                'severity': 'Critical',
                'ip_address': ip,
                'description': f'Possible DDoS from {ip}'
            })

        # 4. Suspicious IP detection
        if ThreatEngine.check_suspicious_ip(ip):
            alerts.append({
                'threat_type': 'Suspicious IP',
                'severity': 'Medium',
                'ip_address': ip,
                'description': f'IP {ip} is blacklisted or from suspicious location'
            })

        return alerts
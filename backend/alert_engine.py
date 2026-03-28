from database import db, Alert

class AlertEngine:
    @staticmethod
    def create_alert(threat_type, severity, ip_address, description):
        """Store an alert in the database."""
        alert = Alert(
            threat_type=threat_type,
            severity=severity,
            ip_address=ip_address,
            description=description
        )
        db.session.add(alert)
        db.session.commit()
        return alert
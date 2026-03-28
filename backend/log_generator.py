import random
import json
from faker import Faker
from datetime import datetime
from database import db, Log
from threat_engine import ThreatEngine
from alert_engine import AlertEngine

fake = Faker()

def generate_random_log():
    """Generate a single random log entry."""
    event_types = ['login', 'file_access', 'network']
    statuses = ['success', 'failed']
    ip = fake.ipv4()
    port = random.randint(1024, 65535)
    event_type = random.choice(event_types)
    status = random.choice(statuses)
    country = fake.country() if random.random() > 0.3 else None

    log = Log(
        timestamp=datetime.utcnow(),
        ip_address=ip,
        port=port,
        status=status,
        event_type=event_type,
        country=country
    )
    return log

def generate_and_store_logs(count=1):
    """Generate `count` logs, store in DB, run threat detection, and return created logs."""
    created_logs = []
    for _ in range(count):
        log = generate_random_log()
        db.session.add(log)
        db.session.flush()  # get ID
        created_logs.append(log)

        # Threat detection
        alerts = ThreatEngine.analyze_log(log)
        for alert_data in alerts:
            AlertEngine.create_alert(**alert_data)

    db.session.commit()
    return created_logs
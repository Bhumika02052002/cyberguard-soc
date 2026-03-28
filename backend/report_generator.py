from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
from database import db, Log, Alert
from sqlalchemy import func
from datetime import datetime

def generate_pdf_report():
    """Generate PDF report with summary, logs, alerts, and charts snapshot."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    story = []

    # Title
    story.append(Paragraph("CyberGuard SOC Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Summary
    total_logs = Log.query.count()
    total_alerts = Alert.query.count()
    failed_logins = Log.query.filter_by(status='failed', event_type='login').count()
    story.append(Paragraph("Summary", heading_style))
    story.append(Paragraph(f"Total logs: {total_logs}", normal_style))
    story.append(Paragraph(f"Total alerts: {total_alerts}", normal_style))
    story.append(Paragraph(f"Failed login attempts: {failed_logins}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Alerts breakdown
    alert_types = db.session.query(Alert.threat_type, func.count(Alert.id)).group_by(Alert.threat_type).all()
    if alert_types:
        story.append(Paragraph("Alerts by Type", heading_style))
        data = [["Threat Type", "Count"]] + [[t, c] for t, c in alert_types]
        table = Table(data, colWidths=[3*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    # Recent logs (last 20)
    recent_logs = Log.query.order_by(Log.timestamp.desc()).limit(20).all()
    if recent_logs:
        story.append(Paragraph("Recent Logs", heading_style))
        log_data = [["Timestamp", "IP", "Port", "Status", "Event Type", "Country"]]
        for log in recent_logs:
            log_data.append([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.ip_address,
                str(log.port),
                log.status,
                log.event_type,
                log.country or ""
            ])
        log_table = Table(log_data, colWidths=[1.2*inch, 1*inch, 0.6*inch, 0.8*inch, 1*inch, 1.2*inch])
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(log_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
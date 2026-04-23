from datetime import datetime, timezone
from flask import Blueprint, request, current_app

from database.db import db
from database.models import Alert
from services.alert_service import AlertService
from utils.response_utils import success_response, error_response, paginated_response

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/api/alerts', methods=['GET'])
def list_alerts():
    """Return a paginated list of alerts with optional filters."""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    status = request.args.get('status', None)
    severity = request.args.get('severity', None)

    query = Alert.query

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)

    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    items = [a.to_dict() for a in alerts]

    return paginated_response(items, total, limit, offset)


@alerts_bp.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged."""
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response('Alert not found.', 404)

    alert.status = 'acknowledged'
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(alert.to_dict(), 'Alert acknowledged.')


@alerts_bp.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response('Alert not found.', 404)

    alert.status = 'resolved'
    alert.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    return success_response(alert.to_dict(), 'Alert resolved.')


@alerts_bp.route('/api/alerts/send-test', methods=['POST'])
def send_test_alert():
    """Send a test alert email to verify email configuration."""
    try:
        import smtplib
        from email.mime.text import MIMEText

        from_addr = current_app.config.get('ALERT_EMAIL_FROM', '')
        password = current_app.config.get('ALERT_EMAIL_PASSWORD', '')
        to_addr = current_app.config.get('ALERT_EMAIL_TO', '')
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)

        if not all([from_addr, password, to_addr]):
            return success_response(
                {'email_configured': False},
                'Email config incomplete — test alert created as system notification only.'
            )

        msg = MIMEText('This is a test alert from GreenCity Waste Intelligence System.')
        msg['Subject'] = '[TEST] GreenCity Alert System'
        msg['From'] = from_addr
        msg['To'] = to_addr

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addr, msg.as_string())

        return success_response({'email_sent': True}, 'Test email sent successfully.')
    except Exception as exc:
        current_app.logger.error("Test alert failed: %s", exc)
        return success_response(
            {'email_sent': False, 'error': str(exc)},
            'Test email failed — system alert created instead.'
        )


@alerts_bp.route('/api/alerts/stats', methods=['GET'])
def alert_stats():
    """Return aggregated alert statistics."""
    total = Alert.query.count()
    pending = Alert.query.filter_by(status='pending').count()
    acknowledged = Alert.query.filter_by(status='acknowledged').count()
    resolved = Alert.query.filter_by(status='resolved').count()

    # Average resolution time (in minutes)
    resolved_alerts = Alert.query.filter(
        Alert.status == 'resolved',
        Alert.resolved_at.isnot(None),
    ).all()
    avg_resolution = 0
    if resolved_alerts:
        total_mins = 0
        count = 0
        for a in resolved_alerts:
            if a.resolved_at and a.created_at:
                delta = (a.resolved_at - a.created_at).total_seconds() / 60
                total_mins += delta
                count += 1
        if count > 0:
            avg_resolution = round(total_mins / count, 1)

    # Breakdown by severity
    by_severity = {}
    for sev in ('low', 'medium', 'high', 'critical'):
        by_severity[sev] = Alert.query.filter_by(severity=sev).count()

    return success_response({
        'total': total,
        'pending': pending,
        'acknowledged': acknowledged,
        'resolved': resolved,
        'avg_resolution_minutes': avg_resolution,
        'by_severity': by_severity,
    })

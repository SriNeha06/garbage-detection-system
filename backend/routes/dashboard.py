from datetime import datetime, timedelta, timezone
from flask import Blueprint

from database.db import db
from database.models import Detection, Alert
from services.analytics_service import AnalyticsService
from utils.response_utils import success_response, error_response

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Return comprehensive dashboard statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    # --- counts ---
    total_today = Detection.query.filter(
        Detection.timestamp >= today_start,
        Detection.is_deleted == False,
    ).count()

    total_week = Detection.query.filter(
        Detection.timestamp >= week_start,
        Detection.is_deleted == False,
    ).count()

    critical_today = Alert.query.filter(
        Alert.created_at >= today_start,
        Alert.severity == 'critical',
    ).count()

    active_alerts = Alert.query.filter(
        Alert.status.in_(['pending', 'sent', 'acknowledged']),
    ).count()

    resolved_today = Alert.query.filter(
        Alert.resolved_at >= today_start,
        Alert.status == 'resolved',
    ).count()

    bins_overflow = Detection.query.filter(
        Detection.timestamp >= today_start,
        Detection.bin_fill_level == 'overflow',
        Detection.is_deleted == False,
    ).count()

    # --- analytics ---
    analytics = AnalyticsService()
    cleanliness = analytics.calculate_cleanliness_score()
    most_polluted = analytics.get_most_polluted_zone()
    trend = analytics.get_detection_trend(7)
    severity_breakdown = analytics.get_severity_breakdown()
    zone_breakdown = analytics.get_zone_analytics()
    hourly = analytics.get_peak_hours()

    # Recent detections (last 5)
    recent = Detection.query.filter(
        Detection.is_deleted == False,
    ).order_by(Detection.timestamp.desc()).limit(5).all()
    recent_list = [d.to_dict() for d in recent]

    return success_response({
        'total_detections_today': total_today,
        'total_detections_week': total_week,
        'critical_alerts_today': critical_today,
        'active_alerts': active_alerts,
        'resolved_alerts_today': resolved_today,
        'bins_overflow': bins_overflow,
        'cleanliness_score': cleanliness,
        'most_polluted_zone': most_polluted,
        'detection_trend': trend,
        'severity_breakdown': severity_breakdown,
        'zone_breakdown': zone_breakdown,
        'recent_detections': recent_list,
        'hourly_distribution': hourly,
    })


@dashboard_bp.route('/api/dashboard/map-data', methods=['GET'])
def map_data():
    """Return detection markers from the last 7 days for the map."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    detections = Detection.query.filter(
        Detection.timestamp >= cutoff,
        Detection.is_deleted == False,
        Detection.latitude.isnot(None),
        Detection.longitude.isnot(None),
    ).order_by(Detection.timestamp.desc()).all()

    markers = []
    for d in detections:
        markers.append({
            'detection_id': d.id,
            'latitude': d.latitude,
            'longitude': d.longitude,
            'severity': d.severity,
            'location_name': d.location_name,
            'timestamp': d.timestamp.isoformat() if d.timestamp else None,
            'detection_count': d.detection_count,
            'bin_fill_level': d.bin_fill_level,
        })

    return success_response(markers)

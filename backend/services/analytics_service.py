import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case, extract

from database.db import db
from database.models import Detection, Alert

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    'critical': 15,
    'high': 8,
    'medium': 3,
    'low': 1,
}


class AnalyticsService:
    """Calculates cleanliness scores, trends, and zone analytics."""

    @staticmethod
    def calculate_cleanliness_score(zone: str = None) -> float:
        """
        Score 0-100 where 100 is perfectly clean.
        Penalised by recent detections weighted by severity.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        query = Detection.query.filter(
            Detection.timestamp >= cutoff,
            Detection.is_deleted == False,
        )
        if zone:
            query = query.filter(Detection.location_name.ilike(f'%{zone}%'))

        detections = query.all()
        penalty = 0
        for d in detections:
            penalty += SEVERITY_WEIGHTS.get(d.severity, 1)
        score = max(0.0, 100.0 - penalty)
        return round(score, 1)

    @staticmethod
    def get_detection_trend(days: int = 7) -> list:
        """Return daily detection counts for the last *days* days."""
        now = datetime.now(timezone.utc)
        trend = []
        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = Detection.query.filter(
                Detection.timestamp >= day_start,
                Detection.timestamp < day_end,
                Detection.is_deleted == False,
            ).count()
            trend.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'label': day_start.strftime('%a'),
                'count': count,
            })
        return trend

    @staticmethod
    def get_zone_analytics() -> list:
        """Per-zone breakdown of total and critical detections."""
        from database.models import Camera
        zones = {}
        cameras = Camera.query.all()
        for cam in cameras:
            z = cam.zone or 'unknown'
            if z not in zones:
                zones[z] = {'zone': z, 'count': 0, 'critical': 0}

        detections = Detection.query.filter(Detection.is_deleted == False).all()
        for d in detections:
            # Try to match by camera zone
            zone_key = 'unknown'
            if d.camera_id:
                cam = Camera.query.get(d.camera_id)
                if cam:
                    zone_key = cam.zone or 'unknown'
            if zone_key not in zones:
                zones[zone_key] = {'zone': zone_key, 'count': 0, 'critical': 0}
            zones[zone_key]['count'] += 1
            if d.severity in ('high', 'critical'):
                zones[zone_key]['critical'] += 1

        return list(zones.values())

    @staticmethod
    def get_peak_hours() -> list:
        """Return detection counts per hour (0-23) for today."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        detections = Detection.query.filter(
            Detection.timestamp >= today_start,
            Detection.is_deleted == False,
        ).all()

        hours = [0] * 24
        for d in detections:
            if d.timestamp:
                hours[d.timestamp.hour] += 1
        return hours

    @staticmethod
    def get_severity_breakdown() -> dict:
        """Return counts by severity level."""
        result = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        detections = Detection.query.filter(Detection.is_deleted == False).all()
        for d in detections:
            sev = d.severity or 'low'
            if sev in result:
                result[sev] += 1
        return result

    @staticmethod
    def get_most_polluted_zone() -> str:
        zones = AnalyticsService.get_zone_analytics()
        if not zones:
            return 'N/A'
        worst = max(zones, key=lambda z: z['count'])
        return worst['zone'].title()

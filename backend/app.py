import os
import sys
import json
import random
import logging
import uuid
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database.db import db, init_app
from database.models import Camera, Detection, Alert, Zone

# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.route('/', methods=['GET'])
    def frontend():
        return app.send_static_file('index.html')

    # Database
    init_app(app)

    # Register blueprints
    from routes.detection import detection_bp
    from routes.alerts import alerts_bp
    from routes.dashboard import dashboard_bp
    from routes.cameras import cameras_bp

    app.register_blueprint(detection_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cameras_bp)

    # Health endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        from models.detection_model import GarbageDetector
        detector = GarbageDetector(app.config.get('MODEL_PATH', 'models/best.pt'))
        total_detections = Detection.query.count()
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'database': 'connected',
                'detector': detector.detector_type,
                'total_detections': total_detections,
                'version': '1.0.0',
            },
            'message': '',
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'data': None, 'message': 'Resource not found.'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'data': None, 'message': 'Internal server error.'}), 500

    # Seed data
    with app.app_context():
        _seed_database()

    # Start camera scheduler (best effort)
    try:
        from services.camera_service import CameraService
        cam_svc = CameraService(app)
        cam_svc.start_scheduler()
    except Exception as exc:
        app.logger.warning("Could not start camera scheduler: %s", exc)

    return app


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

SAMPLE_CAMERAS = [
    {
        'name': 'Main Street Junction',
        'location_name': 'Main Street Junction',
        'latitude': 13.0827,
        'longitude': 80.2707,
        'zone': 'commercial',
        'stream_url': 'rtsp://city-cam-01.local/stream',
    },
    {
        'name': 'Central Park East Entrance',
        'location_name': 'Central Park East Entrance',
        'latitude': 13.0674,
        'longitude': 80.2376,
        'zone': 'park',
        'stream_url': 'rtsp://city-cam-02.local/stream',
    },
    {
        'name': 'Industrial Area Gate 3',
        'location_name': 'Industrial Area Gate 3',
        'latitude': 13.1067,
        'longitude': 80.2206,
        'zone': 'industrial',
        'stream_url': 'rtsp://city-cam-03.local/stream',
    },
    {
        'name': 'Residential Block B-12',
        'location_name': 'Residential Block B-12',
        'latitude': 13.0569,
        'longitude': 80.2425,
        'zone': 'residential',
        'stream_url': 'rtsp://city-cam-04.local/stream',
    },
    {
        'name': 'Bus Terminal Platform 5',
        'location_name': 'Bus Terminal Platform 5',
        'latitude': 13.0878,
        'longitude': 80.2785,
        'zone': 'commercial',
        'stream_url': 'rtsp://city-cam-05.local/stream',
    },
]

DETECTION_CLASSES = [
    'garbage_pile', 'bin_empty', 'bin_half', 'bin_full',
    'bin_overflow', 'litter_light', 'litter_heavy', 'plastic_waste',
]

SEVERITY_DISTRIBUTION = ['low'] * 4 + ['medium'] * 3 + ['high'] * 2 + ['critical'] * 1

FILL_LEVELS = ['empty', 'half', 'full', 'overflow']

WORKER_NAMES = [
    'Rajesh Kumar', 'Priya Sharma', 'Mohammed Ali',
    'Lakshmi Devi', 'Suresh Babu',
]


def _seed_database():
    """Idempotent seeding — skips if data already exists."""
    if Camera.query.first() is not None:
        return  # Already seeded

    now = datetime.now(timezone.utc)

    # ---- Cameras ----
    cam_ids = []
    for info in SAMPLE_CAMERAS:
        cam = Camera(
            id=str(uuid.uuid4()),
            name=info['name'],
            location_name=info['location_name'],
            latitude=info['latitude'],
            longitude=info['longitude'],
            stream_url=info['stream_url'],
            zone=info['zone'],
            is_active=True,
            last_checked=now - timedelta(minutes=random.randint(1, 120)),
        )
        db.session.add(cam)
        cam_ids.append(cam.id)
    db.session.flush()

    # ---- Zones ----
    for ztype in ('residential', 'commercial', 'industrial', 'park'):
        zone = Zone(
            id=str(uuid.uuid4()),
            name=ztype.title() + ' Zone',
            zone_type=ztype,
        )
        db.session.add(zone)
    db.session.flush()

    # ---- 30 Detections spread over last 7 days ----
    det_records = []
    for i in range(30):
        days_ago = random.randint(0, 6)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        ts = now - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)

        cam_id = random.choice(cam_ids)
        cam = Camera.query.get(cam_id)

        severity = random.choice(SEVERITY_DISTRIBUTION)
        fill = random.choice(FILL_LEVELS)
        num_classes = random.randint(1, 4)
        classes = random.sample(DETECTION_CLASSES, num_classes)
        scores = {c: round(random.uniform(0.45, 0.98), 2) for c in classes}
        critical_count = sum(1 for c in classes if c in ('bin_overflow', 'litter_heavy', 'garbage_pile'))

        det = Detection(
            id=str(uuid.uuid4()),
            camera_id=cam_id,
            detection_count=num_classes,
            critical_count=critical_count,
            bin_fill_level=fill,
            severity=severity,
            location_name=cam.location_name,
            latitude=cam.latitude + random.uniform(-0.002, 0.002),
            longitude=cam.longitude + random.uniform(-0.002, 0.002),
            timestamp=ts,
            alert_sent=severity in ('high', 'critical'),
        )
        det.set_detected_classes(classes)
        det.set_confidence_scores(scores)
        db.session.add(det)
        det_records.append(det)
    db.session.flush()

    # ---- 20 Alerts ----
    alert_dets = [d for d in det_records if d.severity in ('high', 'critical', 'medium')]
    if len(alert_dets) < 20:
        alert_dets = alert_dets + random.choices(det_records, k=20 - len(alert_dets))
    random.shuffle(alert_dets)
    alert_dets = alert_dets[:20]

    statuses = (['resolved'] * 5) + (['acknowledged'] * 8) + (['pending'] * 7)
    random.shuffle(statuses)

    for idx, status in enumerate(statuses):
        det = alert_dets[idx % len(alert_dets)]
        from services.alert_service import AlertService
        message = AlertService.get_alert_message(det)

        alert = Alert(
            id=str(uuid.uuid4()),
            detection_id=det.id,
            alert_type=random.choice(['system', 'email', 'system']),
            severity=det.severity,
            message=message,
            location_name=det.location_name,
            assigned_worker=random.choice(WORKER_NAMES) if status != 'pending' else None,
            status=status,
            created_at=det.timestamp + timedelta(seconds=random.randint(5, 120)),
        )
        if status == 'acknowledged':
            alert.acknowledged_at = alert.created_at + timedelta(minutes=random.randint(5, 60))
        if status == 'resolved':
            alert.acknowledged_at = alert.created_at + timedelta(minutes=random.randint(5, 30))
            alert.resolved_at = alert.acknowledged_at + timedelta(minutes=random.randint(10, 120))

        db.session.add(alert)

    db.session.commit()
    print(f"[SEED] Created {len(cam_ids)} cameras, {len(det_records)} detections, {len(statuses)} alerts.")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("  [GreenCity] Waste Intelligence System v1.0.0")
    print("=" * 60)
    print("\n  Available endpoints:\n")
    endpoints = [
        "GET    /api/health",
        "POST   /api/detect",
        "GET    /api/detections",
        "GET    /api/detections/<id>",
        "DELETE /api/detections/<id>",
        "GET    /api/alerts",
        "POST   /api/alerts/<id>/acknowledge",
        "POST   /api/alerts/<id>/resolve",
        "POST   /api/alerts/send-test",
        "GET    /api/alerts/stats",
        "GET    /api/dashboard/stats",
        "GET    /api/dashboard/map-data",
        "GET    /api/cameras",
        "POST   /api/cameras",
        "GET    /api/cameras/<id>",
        "PUT    /api/cameras/<id>",
        "DELETE /api/cameras/<id>",
        "POST   /api/cameras/<id>/capture",
    ]
    for ep in endpoints:
        print(f"    {ep}")
    print("\n" + "=" * 60 + "\n")

    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', '5000')),
        debug=Config.DEBUG,
        use_reloader=False,
    )

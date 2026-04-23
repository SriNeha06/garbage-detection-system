import json
from flask import Blueprint, request, current_app
from database.db import db
from database.models import Detection, Camera
from models.detection_model import GarbageDetector
from services.alert_service import AlertService
from utils.image_utils import validate_image_file, read_image_from_bytes, encode_image_to_base64, resize_image
from utils.response_utils import success_response, error_response, paginated_response

detection_bp = Blueprint('detection', __name__)

# Module-level detector instance (created once)
_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        model_path = current_app.config.get('MODEL_PATH', 'models/best.pt')
        _detector = GarbageDetector(model_path)
    return _detector


@detection_bp.route('/api/detect', methods=['POST'])
def detect_image():
    """Accept an image upload and run garbage detection on it."""
    if 'image' not in request.files:
        return error_response('No image file provided. Send a file with key "image".', 400)

    file = request.files['image']
    if file.filename == '':
        return error_response('Empty filename.', 400)

    if not validate_image_file(file.filename):
        return error_response('Invalid file type. Allowed: jpg, jpeg, png, webp', 400)

    # Optional metadata from form
    location_name = request.form.get('location', 'Unknown Location')
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    camera_id = request.form.get('camera_id', None)

    try:
        # Read and preprocess image
        file_bytes = file.read()
        image = read_image_from_bytes(file_bytes)
        image = resize_image(image, max_width=1280)

        # Run detection
        detector = _get_detector()
        detections = detector.detect(image)
        annotated = detector.annotate_image(image, detections)
        annotated_b64 = encode_image_to_base64(annotated)

        severity = GarbageDetector.calculate_severity(detections)
        fill_level = GarbageDetector.calculate_bin_fill_level(detections)
        critical_count = GarbageDetector.count_critical(detections)

        classes = [d['class_name'] for d in detections]
        scores = {d['class_name']: d['confidence'] for d in detections}

        # Save to database
        det_record = Detection(
            camera_id=camera_id,
            image_base64=annotated_b64,
            detection_count=len(detections),
            critical_count=critical_count,
            bin_fill_level=fill_level,
            severity=severity,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
        )
        det_record.set_detected_classes(classes)
        det_record.set_confidence_scores(scores)

        db.session.add(det_record)
        db.session.commit()

        # Send alert if needed
        alert_sent = False
        if GarbageDetector.is_alert_required(severity):
            alert_svc = AlertService(current_app._get_current_object())
            alert = alert_svc.send_alert(det_record)
            alert_sent = alert is not None

        return success_response({
            'detection_id': det_record.id,
            'detections': detections,
            'annotated_image_base64': annotated_b64,
            'severity': severity,
            'bin_fill_level': fill_level,
            'detection_count': len(detections),
            'critical_count': critical_count,
            'detected_classes': classes,
            'confidence_scores': scores,
            'alert_sent': alert_sent,
            'timestamp': det_record.timestamp.isoformat() if det_record.timestamp else None,
            'location_name': location_name,
        }, 'Detection completed successfully.')

    except Exception as exc:
        db.session.rollback()
        current_app.logger.error("Detection failed: %s", exc, exc_info=True)
        return error_response(f'Detection failed: {str(exc)}', 500)


@detection_bp.route('/api/detections', methods=['GET'])
def list_detections():
    """Return a paginated list of past detections."""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    severity = request.args.get('severity', None)
    location = request.args.get('location', None)
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)

    query = Detection.query.filter(Detection.is_deleted == False)

    if severity:
        query = query.filter(Detection.severity == severity)
    if location:
        query = query.filter(Detection.location_name.ilike(f'%{location}%'))
    if date_from:
        from datetime import datetime
        try:
            query = query.filter(Detection.timestamp >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        from datetime import datetime
        try:
            query = query.filter(Detection.timestamp <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    total = query.count()
    detections = query.order_by(Detection.timestamp.desc()).offset(offset).limit(limit).all()
    items = [d.to_dict() for d in detections]

    return paginated_response(items, total, limit, offset)


@detection_bp.route('/api/detections/<detection_id>', methods=['GET'])
def get_detection(detection_id):
    """Return a single detection with full details including base64 image."""
    det = Detection.query.get(detection_id)
    if not det or det.is_deleted:
        return error_response('Detection not found.', 404)
    return success_response(det.to_dict(include_image=True))


@detection_bp.route('/api/detections/<detection_id>', methods=['DELETE'])
def delete_detection(detection_id):
    """Soft-delete a detection record."""
    det = Detection.query.get(detection_id)
    if not det:
        return error_response('Detection not found.', 404)
    det.is_deleted = True
    db.session.commit()
    return success_response(None, 'Detection deleted.')

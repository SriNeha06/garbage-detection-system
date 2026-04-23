from flask import Blueprint, request, current_app
from datetime import datetime, timezone

from database.db import db
from database.models import Camera
from services.camera_service import CameraService
from utils.response_utils import success_response, error_response, paginated_response

cameras_bp = Blueprint('cameras', __name__)

_camera_service = None


def _get_camera_service():
    global _camera_service
    if _camera_service is None:
        _camera_service = CameraService(current_app._get_current_object())
    return _camera_service


@cameras_bp.route('/api/cameras', methods=['GET'])
def list_cameras():
    """Return all cameras."""
    cameras = Camera.query.order_by(Camera.created_at.desc()).all()
    return success_response([c.to_dict() for c in cameras])


@cameras_bp.route('/api/cameras', methods=['POST'])
def add_camera():
    """Register a new camera."""
    data = request.get_json(silent=True) or {}

    name = data.get('name')
    if not name:
        return error_response('Camera name is required.', 400)

    camera = Camera(
        name=name,
        location_name=data.get('location_name', ''),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        stream_url=data.get('stream_url', ''),
        zone=data.get('zone', 'residential'),
        is_active=data.get('is_active', True),
    )
    db.session.add(camera)
    db.session.commit()

    return success_response(camera.to_dict(), 'Camera added.', 201)


@cameras_bp.route('/api/cameras/<camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Get a single camera by ID."""
    camera = Camera.query.get(camera_id)
    if not camera:
        return error_response('Camera not found.', 404)
    return success_response(camera.to_dict())


@cameras_bp.route('/api/cameras/<camera_id>', methods=['PUT'])
def update_camera(camera_id):
    """Update an existing camera."""
    camera = Camera.query.get(camera_id)
    if not camera:
        return error_response('Camera not found.', 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        camera.name = data['name']
    if 'location_name' in data:
        camera.location_name = data['location_name']
    if 'latitude' in data:
        camera.latitude = data['latitude']
    if 'longitude' in data:
        camera.longitude = data['longitude']
    if 'stream_url' in data:
        camera.stream_url = data['stream_url']
    if 'zone' in data:
        camera.zone = data['zone']
    if 'is_active' in data:
        camera.is_active = data['is_active']

    db.session.commit()
    return success_response(camera.to_dict(), 'Camera updated.')


@cameras_bp.route('/api/cameras/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Delete a camera."""
    camera = Camera.query.get(camera_id)
    if not camera:
        return error_response('Camera not found.', 404)
    db.session.delete(camera)
    db.session.commit()
    return success_response(None, 'Camera deleted.')


@cameras_bp.route('/api/cameras/<camera_id>/capture', methods=['POST'])
def capture_from_camera(camera_id):
    """Simulate a capture from the specified camera and run detection."""
    camera = Camera.query.get(camera_id)
    if not camera:
        return error_response('Camera not found.', 404)

    try:
        svc = _get_camera_service()
        det = svc.capture_from_camera(camera)
        return success_response(det.to_dict(include_image=True), 'Capture and detection complete.')
    except Exception as exc:
        current_app.logger.error("Camera capture failed: %s", exc, exc_info=True)
        return error_response(f'Capture failed: {str(exc)}', 500)

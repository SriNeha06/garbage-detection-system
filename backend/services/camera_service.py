import logging
import random
import numpy as np
from datetime import datetime, timezone

from database.db import db
from database.models import Camera, Detection
from models.detection_model import GarbageDetector
from utils.image_utils import encode_image_to_base64

logger = logging.getLogger(__name__)

# Global scheduler reference (set in start_scheduler)
_scheduler = None


class CameraService:
    """Manages camera polling via APScheduler and on-demand captures."""

    def __init__(self, app=None, detector: GarbageDetector = None):
        self.app = app
        self.detector = detector or GarbageDetector()

    def init_app(self, app, detector=None):
        self.app = app
        if detector:
            self.detector = detector

    def start_scheduler(self):
        """Start the APScheduler background job to poll cameras every 5 minutes."""
        global _scheduler
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            _scheduler = BackgroundScheduler(daemon=True)
            _scheduler.add_job(self._poll_cameras_job, 'interval', minutes=5, id='camera_poll')
            _scheduler.start()
            logger.info("Camera polling scheduler started (every 5 min).")
        except Exception as exc:
            logger.warning("Could not start scheduler: %s", exc)

    def _poll_cameras_job(self):
        """Scheduler callback — polls all active cameras."""
        if self.app is None:
            return
        with self.app.app_context():
            self.poll_cameras()

    def poll_cameras(self):
        """Iterate active cameras and run detection on each."""
        cameras = Camera.query.filter_by(is_active=True).all()
        logger.info("Polling %d active camera(s)...", len(cameras))
        for cam in cameras:
            try:
                self.capture_from_camera(cam)
            except Exception as exc:
                logger.error("Error capturing from camera %s: %s", cam.name, exc)

    def capture_from_camera(self, camera: Camera) -> Detection:
        """
        Capture a frame from the camera (or generate a mock image) and
        run detection on it.  Returns the saved Detection record.
        """
        # Generate a random synthetic city-scene image
        image = self._generate_mock_image()

        detections = self.detector.detect(image)
        annotated = self.detector.annotate_image(image, detections)

        severity = GarbageDetector.calculate_severity(detections)
        fill_level = GarbageDetector.calculate_bin_fill_level(detections)
        critical_count = GarbageDetector.count_critical(detections)

        classes = [d['class_name'] for d in detections]
        scores = {d['class_name']: d['confidence'] for d in detections}

        det_record = Detection(
            camera_id=camera.id,
            image_base64=encode_image_to_base64(annotated),
            detection_count=len(detections),
            critical_count=critical_count,
            bin_fill_level=fill_level,
            severity=severity,
            location_name=camera.location_name or camera.name,
            latitude=camera.latitude,
            longitude=camera.longitude,
        )
        det_record.set_detected_classes(classes)
        det_record.set_confidence_scores(scores)

        camera.last_checked = datetime.now(timezone.utc)
        db.session.add(det_record)
        db.session.commit()

        # Trigger alert if needed
        if GarbageDetector.is_alert_required(severity):
            from services.alert_service import AlertService
            alert_svc = AlertService(self.app)
            alert_svc.send_alert(det_record)

        return det_record

    @staticmethod
    def _generate_mock_image() -> np.ndarray:
        """Create a random-coloured image to simulate a camera frame."""
        h, w = 480, 640
        # Dark-ish urban background
        base_color = [random.randint(30, 80) for _ in range(3)]
        img = np.full((h, w, 3), base_color, dtype=np.uint8)
        # Add some noise for realism
        noise = np.random.randint(0, 30, (h, w, 3), dtype=np.uint8)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return img

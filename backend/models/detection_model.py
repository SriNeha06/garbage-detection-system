import os
import logging
from .mock_detector import MockGarbageDetector

logger = logging.getLogger(__name__)

# Detection class categories
CRITICAL_CLASSES = {'bin_overflow', 'litter_heavy', 'garbage_pile'}
HIGH_CLASSES = {'bin_full', 'garbage_pile'}
MEDIUM_CLASSES = {'bin_half', 'litter_light'}

BIN_CLASSES_PRIORITY = ['bin_overflow', 'bin_full', 'bin_half', 'bin_empty']


class GarbageDetector:
    """
    Unified garbage detector.
    Attempts to load a real YOLOv8 model; falls back to MockGarbageDetector
    if the model file or ultralytics package is unavailable.
    """

    def __init__(self, model_path: str = 'models/best.pt'):
        self.detector = None
        self.detector_type = 'mock'

        # Try loading real YOLOv8 model
        try:
            if os.path.isfile(model_path):
                from ultralytics import YOLO
                self._yolo = YOLO(model_path)
                self.detector_type = 'yolov8'
                logger.info("Loaded YOLOv8 model from %s", model_path)
            else:
                raise FileNotFoundError(f"Model file not found: {model_path}")
        except Exception as exc:
            logger.warning("YOLOv8 unavailable (%s). Using MockGarbageDetector.", exc)
            self.detector = MockGarbageDetector()
            self.detector_type = 'mock'

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def detect(self, image_array):
        """Run detection and return list of detection dicts."""
        if self.detector_type == 'yolov8':
            return self._detect_yolo(image_array)
        return self.detector.detect(image_array)

    def annotate_image(self, image_array, detections):
        """Annotate image with detection results."""
        if self.detector_type == 'yolov8':
            # Re-use the mock annotator for consistent visual output
            mock = MockGarbageDetector()
            return mock.annotate_image(image_array, detections)
        return self.detector.annotate_image(image_array, detections)

    # ------------------------------------------------------------------ #
    # YOLOv8 specific
    # ------------------------------------------------------------------ #

    def _detect_yolo(self, image_array):
        results = self._yolo(image_array, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = r.names.get(cls_id, 'unknown')
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                detections.append({
                    'class_name': cls_name,
                    'confidence': round(conf, 2),
                    'bbox': [x1, y1, x2, y2],
                })
        return detections

    # ------------------------------------------------------------------ #
    # Severity & fill helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_severity(detections: list) -> str:
        classes = {d['class_name'] for d in detections}
        if classes & CRITICAL_CLASSES:
            return 'critical'
        if classes & HIGH_CLASSES:
            return 'high'
        if classes & MEDIUM_CLASSES:
            return 'medium'
        return 'low'

    @staticmethod
    def calculate_bin_fill_level(detections: list) -> str:
        classes = [d['class_name'] for d in detections]
        for level in BIN_CLASSES_PRIORITY:
            if level in classes:
                return level.replace('bin_', '')
        return 'empty'

    @staticmethod
    def is_alert_required(severity: str) -> bool:
        return severity in ('high', 'critical')

    @staticmethod
    def count_critical(detections: list) -> int:
        return sum(1 for d in detections if d['class_name'] in CRITICAL_CLASSES)

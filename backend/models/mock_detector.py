import random
import cv2
import numpy as np
from datetime import datetime


class MockGarbageDetector:
    """
    Simulates realistic garbage / waste detections when no YOLOv8 weights are available.
    Produces varied, convincing results on every call.
    """

    CLASSES = [
        'garbage_pile',
        'bin_empty',
        'bin_half',
        'bin_full',
        'bin_overflow',
        'litter_light',
        'litter_heavy',
        'plastic_waste',
    ]

    CRITICAL_CLASSES = {'bin_overflow', 'litter_heavy', 'garbage_pile'}

    # BGR colours for drawing
    CLASS_COLORS = {
        'garbage_pile': (0, 0, 220),       # red
        'bin_empty': (0, 200, 0),          # green
        'bin_half': (0, 220, 220),         # yellow
        'bin_full': (0, 140, 255),         # orange
        'bin_overflow': (0, 0, 255),       # bright red
        'litter_light': (0, 200, 200),     # yellow-ish
        'litter_heavy': (0, 50, 200),      # dark red
        'plastic_waste': (200, 150, 0),    # teal
    }

    def detect(self, image_array: np.ndarray):
        """
        Run mock detection on an image.

        Returns a list of dicts, each with:
            class_name, confidence, bbox (x1, y1, x2, y2)
        """
        h, w = image_array.shape[:2]
        num_detections = random.randint(1, 5)

        detections = []
        for _ in range(num_detections):
            cls = random.choice(self.CLASSES)
            confidence = round(random.uniform(0.45, 0.98), 2)

            # Generate a random bounding box within image bounds
            box_w = random.randint(int(w * 0.08), int(w * 0.35))
            box_h = random.randint(int(h * 0.08), int(h * 0.35))
            x1 = random.randint(0, max(0, w - box_w))
            y1 = random.randint(0, max(0, h - box_h))
            x2 = min(x1 + box_w, w)
            y2 = min(y1 + box_h, h)

            detections.append({
                'class_name': cls,
                'confidence': confidence,
                'bbox': [x1, y1, x2, y2],
            })

        return detections

    def annotate_image(self, image_array: np.ndarray, detections: list) -> np.ndarray:
        """
        Draw coloured bounding boxes, labels and overlays onto the image.
        Returns the annotated image as a numpy array.
        """
        annotated = image_array.copy()
        h, w = annotated.shape[:2]

        for det in detections:
            cls = det['class_name']
            conf = det['confidence']
            x1, y1, x2, y2 = det['bbox']
            color = self.CLASS_COLORS.get(cls, (200, 200, 200))

            # Draw bounding box
            thickness = max(2, int(min(w, h) / 300))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Label background
            label = f"{cls.replace('_', ' ').title()} {conf * 100:.0f}%"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.4, min(w, h) / 1200)
            text_thickness = max(1, int(font_scale * 2))
            (tw, th_text), baseline = cv2.getTextSize(label, font, font_scale, text_thickness)
            cv2.rectangle(annotated, (x1, y1 - th_text - baseline - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - baseline - 2), font, font_scale,
                        (255, 255, 255), text_thickness, cv2.LINE_AA)

        # Semi-transparent overlay with detection count at top-left
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, 40), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)

        count_text = f"Detections: {len(detections)}"
        critical = sum(1 for d in detections if d['class_name'] in self.CRITICAL_CLASSES)
        if critical:
            count_text += f"  |  Critical: {critical}"
        cv2.putText(annotated, count_text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 2, cv2.LINE_AA)

        # Timestamp watermark at bottom
        ts_overlay = annotated.copy()
        cv2.rectangle(ts_overlay, (0, h - 35), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(ts_overlay, 0.6, annotated, 0.4, 0, annotated)
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(annotated, f"GreenCity AI  |  {timestamp_str}", (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        return annotated

import base64
import io
import cv2
import numpy as np
from PIL import Image

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}


def validate_image_file(filename: str) -> bool:
    """Check whether the filename has an allowed image extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def read_image_from_bytes(file_bytes: bytes) -> np.ndarray:
    """Convert raw file bytes → PIL Image → OpenCV BGR numpy array."""
    pil_image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return cv_image


def encode_image_to_base64(image_array: np.ndarray, fmt: str = '.jpg') -> str:
    """Encode an OpenCV image array to a base64 string (JPEG by default)."""
    success, buffer = cv2.imencode(fmt, image_array, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise RuntimeError('Failed to encode image')
    return base64.b64encode(buffer).decode('utf-8')


def resize_image(image_array: np.ndarray, max_width: int = 1280) -> np.ndarray:
    """Resize an image so its width does not exceed *max_width*, preserving aspect ratio."""
    h, w = image_array.shape[:2]
    if w <= max_width:
        return image_array
    scale = max_width / w
    new_w = max_width
    new_h = int(h * scale)
    return cv2.resize(image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)


def draw_detection_overlay(image: np.ndarray, detections: list) -> np.ndarray:
    """
    Convenience wrapper — draws bounding boxes on a copy of the image.
    Delegates to MockGarbageDetector.annotate_image for consistent visuals.
    """
    from models.mock_detector import MockGarbageDetector
    mock = MockGarbageDetector()
    return mock.annotate_image(image, detections)

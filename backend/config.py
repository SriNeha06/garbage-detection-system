import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables with sensible defaults."""

    # Flask core
    SECRET_KEY = os.getenv('SECRET_KEY', 'greencity-garbage-detection-secret-key-2024')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///garbage_city.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Email alerts
    ALERT_EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM', 'alerts@greencity.local')
    ALERT_EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD', '')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', 'admin@greencity.local')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

    # Detection thresholds
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.45'))
    CRITICAL_CLASSES = ['bin_overflow', 'litter_heavy', 'garbage_pile']

    # Alert settings
    ALERT_COOLDOWN_MINUTES = int(os.getenv('ALERT_COOLDOWN_MINUTES', '30'))

    # Model settings
    MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'models/best.pt')
    USE_MOCK_DETECTOR = os.getenv('USE_MOCK_DETECTOR', 'True').lower() in ('true', '1', 'yes')

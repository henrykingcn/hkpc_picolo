"""
Configuration settings for HKPC PPE Detection System
"""
import os

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hkpc-ppe-detection-secret-key-2026'
    
    # Database settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # YOLO Model settings
    YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'yolo10s.pt')
    DETECTION_CONFIDENCE = 0.6
    
    # Camera settings
    CAMERA_INDEX = 1
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    
    # PPE Classes (17 classes for detection)
    PPE_CLASSES = [
        'Person',
        'Head',
        'Face',
        'Glasses',
        'Face-mask-medical',
        'Face-guard',
        'Ear',
        'Earmuffs',
        'Hands',
        'Gloves',
        'Foot',
        'Shoes',
        'Safety-vest',
        'Tools',
        'Helmet',
        'Medical-suit',
        'Safety-suit'
    ]
    
    # Default classes for access control (Head and Hands)
    DEFAULT_REQUIRED_CLASSES = ['Head', 'Hands']
    
    # Detection logic: 'ALL' or 'ANY'
    DEFAULT_DETECTION_LOGIC = 'ALL'
    
    # Face Recognition settings (InsightFace)
    FACE_RECOGNITION_SIMILARITY_THRESHOLD = 0.6  # Cosine similarity threshold (0.3-0.7)
    INSIGHTFACE_MODEL = "buffalo_s"  # or "buffalo_s" for smaller/faster model
    FACES_DIR = os.path.join(BASE_DIR, 'static', 'images', 'faces')
    FACE_RECOGNITION_ENABLED = True  # Can be toggled via admin interface
    
    # PIN Code settings
    PIN_CODE_LENGTH = 4
    MAX_PIN_ATTEMPTS = 3
    PIN_LOCKOUT_TIME = 30  # seconds
    
    # Access Control settings
    FACE_DETECTION_TIMEOUT = 5  # seconds
    PPE_DETECTION_DURATION = 3  # seconds
    ACCESS_GRANTED_DISPLAY_TIME = 5  # seconds
    
    # Performance settings
    DETECTION_FPS = 10  # Backend detection frame rate
    VIDEO_FPS = 15  # Video stream frame rate
    UPDATE_RATE = 100  # Frontend update rate (ms)
    
    # UI settings
    PORTRAIT_MODE = True
    SCREEN_WIDTH = 1080  # Adjust based on actual display
    SCREEN_HEIGHT = 1920


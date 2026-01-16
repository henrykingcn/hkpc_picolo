"""
Detection Processor
Runs YOLO and face recognition in background, sends results via WebSocket
"""
import cv2
import time
import threading
from detector import PPEDetector
from config import Config
from models import SystemSettings

# Try to import InsightFace, fall back to stub if not available
try:
    from face_manager_insightface import InsightFaceManager
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("⚠️ InsightFace not available, trying original face_recognition...")
    try:
        from face_manager import FaceRecognitionManager as InsightFaceManager
        FACE_RECOGNITION_AVAILABLE = True
    except ImportError:
        from face_manager_stub import FaceRecognitionManager as InsightFaceManager
        FACE_RECOGNITION_AVAILABLE = False


class DetectionProcessor:
    """Background detection processor"""
    
    def __init__(self, socketio, access_controller, app=None):
        """
        Initialize detection processor
        
        Args:
            socketio: Flask-SocketIO instance
            access_controller: AccessController instance
            app: Flask app instance (for application context)
        """
        self.socketio = socketio
        self.access_controller = access_controller
        self.app = app
        self.camera = None
        self.ppe_detector = None
        self.face_manager = None
        self.running = False
        self.thread = None
        self.face_enabled = self.load_face_config()
        
        print(f"✓ Detection Processor initialized (Face Recognition: {'ON' if self.face_enabled else 'OFF'})")
    
    def load_face_config(self):
        """Load face recognition enabled config from database"""
        try:
            setting = SystemSettings.query.filter_by(
                setting_key='face_recognition_enabled'
            ).first()
            return setting.setting_value == 'true' if setting else True
        except:
            # If database not available yet, default to True
            return True
    
    def reload_config(self):
        """Reload configuration from database"""
        self.face_enabled = self.load_face_config()
        print(f"Config reloaded: Face Recognition {'ON' if self.face_enabled else 'OFF'}")
        
        # If face recognition was just enabled and we don't have a face manager, initialize it
        if self.face_enabled and not self.face_manager and FACE_RECOGNITION_AVAILABLE:
            try:
                print("Initializing face recognition...")
                self.face_manager = InsightFaceManager(
                    similarity_threshold=Config.FACE_RECOGNITION_SIMILARITY_THRESHOLD
                )
            except Exception as e:
                print(f"Error initializing face recognition: {e}")
    
    def start(self):
        """Start the detection processor"""
        if self.running:
            print("Detection processor already running")
            return False
        
        try:
            # Initialize camera
            print("Initializing camera...")
            
            # Windows: Use DirectShow backend to avoid MSMF issues
            import platform
            if platform.system() == 'Windows':
                self.camera = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_DSHOW)
                print("Using DirectShow backend (Windows)")
            else:
                self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to 1 frame
            
            if not self.camera.isOpened():
                print("✗ Failed to open camera")
                return False
            
            # Initialize PPE detector
            print("Initializing PPE detector...")
            self.ppe_detector = PPEDetector(
                Config.YOLO_MODEL_PATH,
                Config.DETECTION_CONFIDENCE
            )
            
            # Initialize face manager (only if enabled)
            if self.face_enabled and FACE_RECOGNITION_AVAILABLE:
                print("Initializing InsightFace...")
                try:
                    self.face_manager = InsightFaceManager(
                        similarity_threshold=Config.FACE_RECOGNITION_SIMILARITY_THRESHOLD
                    )
                except Exception as e:
                    print(f"✗ Error initializing face recognition: {e}")
                    print("  Continuing without face recognition...")
                    self.face_manager = None
            else:
                if not self.face_enabled:
                    print("Face recognition disabled by configuration")
                elif not FACE_RECOGNITION_AVAILABLE:
                    print("Face recognition not available")
                self.face_manager = None
            
            # Start processing thread
            self.running = True
            self.thread = threading.Thread(target=self._process_loop, daemon=True)
            self.thread.start()
            
            print("✓ Detection processor started")
            return True
            
        except Exception as e:
            print(f"✗ Error starting detection processor: {e}")
            return False
    
    def stop(self):
        """Stop the detection processor"""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=2)
        
        # Properly release camera (especially important on Windows)
        if self.camera:
            try:
                self.camera.release()
                # Give OS time to fully release the camera (Windows issue)
                time.sleep(0.3)
                cv2.destroyAllWindows()
            except Exception as e:
                print(f"Warning during camera release: {e}")
        
        self.camera = None
        print("✓ Detection processor stopped")
    
    def _process_loop(self):
        """Main processing loop (runs in background thread)"""
        print("Detection loop started")
        
        frame_time = 1.0 / Config.DETECTION_FPS
        
        # Use app context for database access in background thread
        if self.app:
            with self.app.app_context():
                self._run_detection_loop(frame_time)
        else:
            self._run_detection_loop(frame_time)
        
        print("Detection loop stopped")
    
    def _run_detection_loop(self, frame_time):
        """Run the actual detection loop"""
        while self.running:
            try:
                start_time = time.time()
                
                # Read frame from camera
                success, frame = self.camera.read()
                if not success:
                    print("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Run face recognition (if enabled and available)
                if self.face_enabled and self.face_manager:
                    face_result = self.face_manager.identify_face(frame)
                else:
                    face_result = None
                
                # Run YOLO PPE detection (always runs)
                ppe_result = self.ppe_detector.detect(frame)
                
                # Update access controller
                self.access_controller.update(face_result, ppe_result)
                
                # Emit detection update via WebSocket
                self.emit_detection_update(face_result, ppe_result)
                
                # Emit face identification if changed
                if face_result and face_result.get('face_location'):
                    self.emit_face_identification(face_result)
                
                # Control frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in detection loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    def emit_detection_update(self, face_result, ppe_result):
        """
        Emit detection update via WebSocket
        
        Args:
            face_result: Face recognition results
            ppe_result: PPE detection results
        """
        if not self.socketio:
            return
        
        data = {
            'detected_classes': ppe_result.get('detected_classes', []),
            'confidence_scores': ppe_result.get('confidence_scores', {}),
            'detection_counts': ppe_result.get('detection_counts', {}),  # Include detection counts
            'face_detected': face_result is not None and face_result.get('face_location') is not None
        }
        
        self.socketio.emit('detection_update', data)
    
    def emit_face_identification(self, face_result):
        """
        Emit face identification result
        
        Args:
            face_result: Face recognition results
        """
        if not self.socketio:
            return
        
        data = {
            'matched': face_result.get('matched', False),
            'person_id': face_result.get('person_id'),
            'name': face_result.get('name'),
            'confidence': face_result.get('confidence')
        }
        
        self.socketio.emit('face_identified', data)
    
    def is_running(self):
        """Check if processor is running"""
        return self.running and self.thread and self.thread.is_alive()


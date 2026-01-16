"""
HKPC PPE Detection Access Control System
Main Flask Application
"""
from flask import Flask, render_template, Response, jsonify, request
from models import db, DetectionConfig, DetectionLog, SystemSettings
from config import Config
import json
from datetime import datetime
import cv2
import threading

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Global variables for camera and detector
camera = None
detector = None
current_status = {
    'access_granted': False,
    'detected_classes': [],
    'confidence_scores': {}
}
status_lock = threading.Lock()


def init_database():
    """Initialize database with default configuration"""
    with app.app_context():
        db.create_all()
        
        # Check if configuration already exists
        if DetectionConfig.query.count() == 0:
            # Initialize with all PPE classes
            for class_name in Config.PPE_CLASSES:
                enabled = class_name in Config.DEFAULT_REQUIRED_CLASSES
                config = DetectionConfig(class_name=class_name, enabled=enabled)
                db.session.add(config)
            
            # Initialize system settings
            logic_setting = SystemSettings(
                setting_key='detection_logic',
                setting_value=Config.DEFAULT_DETECTION_LOGIC
            )
            db.session.add(logic_setting)
            
            db.session.commit()
            print("✓ Database initialized with default configuration")


def get_camera():
    """Get or initialize camera"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
    return camera


def get_detector():
    """Get or initialize YOLO detector"""
    global detector
    if detector is None:
        from detector import PPEDetector
        detector = PPEDetector(Config.YOLO_MODEL_PATH, Config.DETECTION_CONFIDENCE)
    return detector


def generate_frames():
    """Generate frames for video streaming"""
    try:
        camera = get_camera()
        detector = get_detector()
        
        if not camera.isOpened():
            print("Error: Camera is not opened")
            return
        
        print("✓ Camera opened successfully, starting video stream...")
        frame_count = 0
        
        while True:
            success, frame = camera.read()
            if not success:
                print(f"Failed to read frame {frame_count}")
                break
            
            frame_count += 1
            
            # Run YOLO detection
            try:
                result = detector.detect(frame)
                annotated_frame = result['annotated_frame']
                detected_classes = result['detected_classes']
                confidence_scores = result['confidence_scores']
            except Exception as e:
                print(f"Detection error: {e}")
                annotated_frame = frame
                detected_classes = []
                confidence_scores = {}
            
            # Check access control
            access_granted = check_access_control(detected_classes)
            
            # Debug logging every 30 frames
            if frame_count % 30 == 0 and detected_classes:
                print(f"Detected: {detected_classes} | Access: {'GRANTED' if access_granted else 'DENIED'}")
            
            # Update global status
            with status_lock:
                current_status['access_granted'] = access_granted
                current_status['detected_classes'] = detected_classes
                current_status['confidence_scores'] = confidence_scores
            
            # Log detection event (every 30 frames to avoid too many logs)
            if frame_count % 30 == 0:
                log_detection(detected_classes, confidence_scores, access_granted)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                print("Failed to encode frame")
                continue
                
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    except Exception as e:
        print(f"Error in generate_frames: {e}")
        import traceback
        traceback.print_exc()


def check_access_control(detected_classes):
    """Check if detected classes meet access control requirements"""
    with app.app_context():
        # Get enabled classes from database
        enabled_configs = DetectionConfig.query.filter_by(enabled=True).all()
        required_classes = [config.class_name for config in enabled_configs]
        
        if not required_classes:
            return False
        
        # Convert detected classes to lowercase for case-insensitive comparison
        detected_classes_lower = [cls.lower() for cls in detected_classes]
        required_classes_lower = [cls.lower() for cls in required_classes]
        
        # Get detection logic
        logic_setting = SystemSettings.query.filter_by(setting_key='detection_logic').first()
        detection_logic = logic_setting.setting_value if logic_setting else 'ALL'
        
        if detection_logic == 'ALL':
            # All required classes must be detected
            return all(cls in detected_classes_lower for cls in required_classes_lower)
        else:  # ANY
            # At least one required class must be detected
            return any(cls in detected_classes_lower for cls in required_classes_lower)


def log_detection(detected_classes, confidence_scores, access_granted):
    """Log detection event to database"""
    with app.app_context():
        try:
            log_entry = DetectionLog(
                detected_classes=json.dumps(detected_classes),
                confidence_scores=json.dumps(confidence_scores),
                access_granted=access_granted
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"Error logging detection: {e}")
            db.session.rollback()


# Routes
@app.route('/')
def index():
    """Main detection interface"""
    return render_template('index.html')


@app.route('/admin')
def admin():
    """Admin configuration panel"""
    return render_template('admin.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/status')
def get_status():
    """Get current detection status"""
    with status_lock:
        return jsonify(current_status)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current detection configuration"""
    configs = DetectionConfig.query.all()
    logic_setting = SystemSettings.query.filter_by(setting_key='detection_logic').first()
    
    return jsonify({
        'classes': [config.to_dict() for config in configs],
        'detection_logic': logic_setting.setting_value if logic_setting else 'ALL'
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update detection configuration"""
    try:
        data = request.json
        
        # Update class configurations
        if 'classes' in data:
            for class_data in data['classes']:
                config = DetectionConfig.query.filter_by(
                    class_name=class_data['class_name']
                ).first()
                
                if config:
                    config.enabled = class_data['enabled']
        
        # Update detection logic
        if 'detection_logic' in data:
            logic_setting = SystemSettings.query.filter_by(
                setting_key='detection_logic'
            ).first()
            
            if logic_setting:
                logic_setting.setting_value = data['detection_logic']
            else:
                logic_setting = SystemSettings(
                    setting_key='detection_logic',
                    setting_value=data['detection_logic']
                )
                db.session.add(logic_setting)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/logs')
def get_logs():
    """Get detection logs"""
    limit = request.args.get('limit', 50, type=int)
    logs = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    })


@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all detection logs"""
    try:
        DetectionLog.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Logs cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    init_database()
    print("=" * 60)
    print("HKPC PPE Detection Access Control System")
    print("=" * 60)
    print(f"Starting server at http://localhost:5001")
    print(f"Main interface: http://localhost:5001/")
    print(f"Admin panel: http://localhost:5001/admin")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)


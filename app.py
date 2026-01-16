"""
HKPC PPE Detection Access Control System - Main Application
Upgraded with Face Recognition, WebSocket, and Portrait UI
"""
from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps
from models import db, DetectionConfig, SystemSettings, AuthorizedPerson, AccessLog, AdminAuth
from config import Config
from auth import PINAuthManager
import tempfile
# Try to import face recognition, fall back to stub if not available
try:
    from face_manager_insightface import InsightFaceManager as FaceRecognitionManager
    FACE_RECOGNITION_AVAILABLE = True
    print("✓ Using InsightFace for face recognition")
except ImportError:
    print("⚠ InsightFace not available, trying original face_recognition...")
    try:
        from face_manager import FaceRecognitionManager
        FACE_RECOGNITION_AVAILABLE = True
        print("✓ Using face_recognition library")
    except ImportError:
        from face_manager_stub import FaceRecognitionManager
        FACE_RECOGNITION_AVAILABLE = False
        print("⚠ Face recognition disabled - using stub version")
from access_controller import AccessController
from detection_processor import DetectionProcessor
import json
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY  # For session management

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
access_controller = None
detection_processor = None
face_manager = None


# Authentication decorator
def login_required(f):
    """Decorator to protect admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def init_database():
    """Initialize database with default configuration"""
    with app.app_context():
        db.create_all()
        
        # Initialize detection config
        if DetectionConfig.query.count() == 0:
            for class_name in Config.PPE_CLASSES:
                enabled = class_name in Config.DEFAULT_REQUIRED_CLASSES
                config = DetectionConfig(class_name=class_name, enabled=enabled)
                db.session.add(config)
            
            logic_setting = SystemSettings(
                setting_key='detection_logic',
                setting_value=Config.DEFAULT_DETECTION_LOGIC
            )
            db.session.add(logic_setting)
            db.session.commit()
            print("✓ Database initialized")
        
        # Initialize face recognition setting
        face_setting = SystemSettings.query.filter_by(
            setting_key='face_recognition_enabled'
        ).first()
        if not face_setting:
            face_setting = SystemSettings(
                setting_key='face_recognition_enabled',
                setting_value='true' if FACE_RECOGNITION_AVAILABLE else 'false'
            )
            db.session.add(face_setting)
            db.session.commit()
            print(f"✓ Face recognition setting initialized ({'enabled' if FACE_RECOGNITION_AVAILABLE else 'disabled'})")
        
        # Initialize PIN authentication
        PINAuthManager.initialize_default_pin()


def init_system():
    """Initialize access control system"""
    global access_controller, detection_processor, face_manager
    
    with app.app_context():
        # Initialize access controller
        access_controller = AccessController(socketio=socketio)
        
        # Initialize face manager with configured threshold
        face_manager = FaceRecognitionManager(
            similarity_threshold=Config.FACE_RECOGNITION_SIMILARITY_THRESHOLD
        )
        
        # Initialize detection processor (pass app for context)
        detection_processor = DetectionProcessor(socketio, access_controller, app=app)
        
        print("✓ System components initialized")


# Main Routes
@app.route('/')
def index():
    """Redirect to access control interface"""
    return redirect(url_for('access_control'))


@app.route('/access')
def access_control():
    """Main access control interface (modern)"""
    return render_template('modern_access.html')

@app.route('/access/old')
def access_control_old():
    """Old access control interface"""
    return render_template('access_control.html')


@app.route('/admin/login')
def admin_login():
    """Admin PIN login page"""
    return render_template('admin_login.html')


@app.route('/admin')
@login_required
def admin():
    """Admin dashboard (Protected)"""
    return render_template('admin.html')


@app.route('/admin/faces')
@login_required
def face_management():
    """Face management interface (Protected)"""
    return render_template('face_management.html')


@app.route('/admin/logout')
def admin_logout():
    """Logout from admin"""
    session.clear()
    return redirect(url_for('admin_login'))


# Authentication API
@app.route('/api/auth/pin', methods=['POST'])
def verify_pin():
    """Verify PIN code"""
    data = request.json
    pin = data.get('pin', '')
    
    success, message = PINAuthManager.verify_pin(pin)
    
    if success:
        # Create session token
        token = str(uuid.uuid4())
        session['admin_token'] = token
        session['authenticated'] = True
        return jsonify({'success': True, 'message': message, 'token': token})
    else:
        return jsonify({'success': False, 'message': message})


@app.route('/api/auth/lock-status')
def get_lock_status():
    """Get PIN lock status"""
    status = PINAuthManager.get_lock_status()
    return jsonify(status)


@app.route('/api/auth/change-pin', methods=['POST'])
def change_pin():
    """Change PIN code"""
    data = request.json
    old_pin = data.get('old_pin', '')
    new_pin = data.get('new_pin', '')
    
    success, message = PINAuthManager.change_pin(old_pin, new_pin)
    return jsonify({'success': success, 'message': message})


# Face Recognition API
@app.route('/api/faces')
def get_faces():
    """Get all authorized persons"""
    persons = AuthorizedPerson.query.all()
    return jsonify({'persons': [p.to_dict() for p in persons]})


@app.route('/api/faces/register', methods=['POST'])
def register_face():
    """Register new face"""
    try:
        name = request.form.get('name')
        employee_id = request.form.get('employee_id')
        photo = request.files.get('photo')
        
        if not all([name, employee_id, photo]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Check if employee_id already exists
        existing = AuthorizedPerson.query.filter_by(employee_id=employee_id).first()
        if existing:
            return jsonify({'success': False, 'message': f'Employee ID {employee_id} already exists'})
        
        # Save temporary photo (cross-platform: Windows, Mac, Linux)
        filename = secure_filename(photo.filename)
        temp_dir = tempfile.gettempdir()  # Windows: C:\Users\xxx\AppData\Local\Temp
        temp_path = os.path.join(temp_dir, filename)
        photo.save(temp_path)
        
        # Register face
        success, message, person_id = face_manager.register_face(temp_path, name, employee_id)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not delete temp file: {e}")
        
        if success:
            # Reload face manager
            face_manager.load_known_faces()
            return jsonify({'success': True, 'message': message, 'person_id': person_id})
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/faces/<int:person_id>', methods=['DELETE'])
def delete_face(person_id):
    """Delete authorized person"""
    success, message = face_manager.delete_person(person_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/faces/<int:person_id>/status', methods=['POST'])
def update_face_status(person_id):
    """Enable/disable authorized person"""
    data = request.json
    is_active = data.get('is_active', True)
    
    success, message = face_manager.update_person_status(person_id, is_active)
    return jsonify({'success': success, 'message': message})


# Configuration API
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
        
        if 'classes' in data:
            for class_data in data['classes']:
                config = DetectionConfig.query.filter_by(
                    class_name=class_data['class_name']
                ).first()
                
                if config:
                    config.enabled = class_data['enabled']
        
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
        
        # Emit config update via WebSocket
        emit_config_update()
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/config/face-recognition', methods=['GET'])
def get_face_recognition_config():
    """Get face recognition enabled status"""
    try:
        setting = SystemSettings.query.filter_by(
            setting_key='face_recognition_enabled'
        ).first()
        enabled = setting.setting_value == 'true' if setting else True
        
        return jsonify({
            'enabled': enabled,
            'available': FACE_RECOGNITION_AVAILABLE
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/config/face-recognition', methods=['POST'])
def update_face_recognition_config():
    """Toggle face recognition on/off"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        
        setting = SystemSettings.query.filter_by(
            setting_key='face_recognition_enabled'
        ).first()
        
        if setting:
            setting.setting_value = 'true' if enabled else 'false'
        else:
            setting = SystemSettings(
                setting_key='face_recognition_enabled',
                setting_value='true' if enabled else 'false'
            )
            db.session.add(setting)
        
        db.session.commit()
        
        # Reload configuration in access controller and detection processor
        if access_controller:
            access_controller.reload_config()
        if detection_processor:
            detection_processor.reload_config()
        
        # Emit config update via WebSocket
        socketio.emit('face_recognition_config_update', {'enabled': enabled})
        
        return jsonify({
            'success': True,
            'message': f"Face recognition {'enabled' if enabled else 'disabled'}",
            'enabled': enabled
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# Logs API
@app.route('/api/logs')
def get_logs():
    """Get access logs"""
    limit = request.args.get('limit', 50, type=int)
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    })


@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all logs"""
    try:
        AccessLog.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Logs cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# Status API
@app.route('/api/status')
def get_status():
    """Get current system status"""
    if access_controller:
        status = access_controller.get_status()
        return jsonify(status)
    else:
        return jsonify({'error': 'System not initialized'}), 500


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to HKPC Access Control System'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('request_config')
def handle_request_config():
    """Send current configuration to client"""
    emit_config_update()


@socketio.on('start_detection')
def handle_start_detection():
    """Start detection processor"""
    if detection_processor and not detection_processor.is_running():
        success = detection_processor.start()
        emit('detection_started', {'success': success})


@socketio.on('stop_detection')
def handle_stop_detection():
    """Stop detection processor"""
    if detection_processor:
        detection_processor.stop()
        emit('detection_stopped', {'success': True})


def emit_config_update():
    """Emit configuration update to all clients"""
    with app.app_context():
        enabled_configs = DetectionConfig.query.filter_by(enabled=True).all()
        required_classes = [config.class_name for config in enabled_configs]
        
        socketio.emit('config_update', {
            'required_classes': required_classes
        })


# Legacy video feed (for backward compatibility)
@app.route('/video_feed')
def video_feed():
    """Video streaming route (simple stream without YOLO annotations)"""
    def generate():
        import cv2
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    init_database()
    init_system()
    
    # Detection processor will be started when /access page is opened
    print("✓ Detection processor ready (will start when /access page is opened)")
    
    print("=" * 60)
    print("HKPC PPE Detection Access Control System v2.0")
    print("=" * 60)
    print(f"Main Interface: http://localhost:5001/access")
    print(f"Admin Login: http://localhost:5001/admin/login")
    print(f"Face Management: http://localhost:5001/admin/faces")
    print("=" * 60)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)


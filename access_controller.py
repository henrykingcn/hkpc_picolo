"""
Access Control State Machine
Manages the flow from face detection → recognition → PPE check → access decision
"""
from enum import Enum
from datetime import datetime, timedelta
import json
from models import db, AccessLog, DetectionConfig, SystemSettings


class AccessState(Enum):
    """Access control states"""
    IDLE = "IDLE"
    FACE_DETECTING = "FACE_DETECTING"
    FACE_RECOGNIZED = "FACE_RECOGNIZED"
    PPE_CHECKING = "PPE_CHECKING"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"


class AccessController:
    """State machine for access control"""
    
    def __init__(self, socketio=None):
        """
        Initialize access controller
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.current_state = AccessState.IDLE
        self.current_person = None
        self.current_person_name = None
        self.current_employee_id = None  # Store employee ID
        self.face_confidence = None
        self.detected_classes = []
        self.state_start_time = datetime.now()
        self.access_granted_time = None
        
        # Timeouts (seconds)
        self.face_detection_timeout = 5
        self.ppe_checking_duration = 3
        self.access_display_duration = 5
        
        # Load face recognition config
        self.face_recognition_enabled = self.load_face_config()
        
        print(f"✓ Access Controller initialized (Face Recognition: {'ON' if self.face_recognition_enabled else 'OFF'})")
    
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
        self.face_recognition_enabled = self.load_face_config()
        print(f"Config reloaded: Face Recognition {'ON' if self.face_recognition_enabled else 'OFF'}")
    
    def reset(self):
        """Reset to IDLE state"""
        self.current_state = AccessState.IDLE
        self.current_person = None
        self.current_person_name = None
        self.current_employee_id = None
        self.face_confidence = None
        self.detected_classes = []
        self.state_start_time = datetime.now()
        self.access_granted_time = None
        self.emit_status_change()
    
    def update(self, face_result, ppe_result):
        """
        Update state machine with new detection results
        
        Args:
            face_result: Dict with face recognition results
            ppe_result: Dict with PPE detection results
        """
        current_time = datetime.now()
        time_in_state = (current_time - self.state_start_time).total_seconds()
        
        # Update detected classes
        self.detected_classes = ppe_result.get('detected_classes', [])
        
        # Check for multiple people (deny access if more than one person detected)
        detection_counts = ppe_result.get('detection_counts', {})
        person_count = detection_counts.get('Person', 0)
        
        if person_count > 1:
            print(f"⚠️ Multiple people detected: {person_count} persons")
            if self.current_state not in [AccessState.ACCESS_DENIED, AccessState.ACCESS_GRANTED]:
                self.transition_to(AccessState.ACCESS_DENIED, 
                                 message=f"Multiple people detected ({person_count}). Please enter one at a time.")
                self.log_access(False, False)
                return
        
        # State machine logic
        if self.current_state == AccessState.IDLE:
            if not self.face_recognition_enabled:
                # Face recognition disabled - skip directly to PPE checking
                print("🔓 Face recognition DISABLED - skipping face check")
                self.current_person_name = 'Anonymous User'
                self.transition_to(AccessState.PPE_CHECKING)
            else:
                # Face recognition enabled - check if face is present
                print("🔐 Face recognition ENABLED - waiting for face")
                if face_result and face_result.get('face_location'):
                    print(f"👤 Face detected, matched: {face_result.get('matched')}")
                    self.transition_to(AccessState.FACE_DETECTING)
        
        elif self.current_state == AccessState.FACE_DETECTING:
            # Check if face is recognized
            if face_result and face_result.get('matched'):
                # Face matched - proceed to PPE checking
                print(f"✅ Face MATCHED: {face_result.get('name')} (confidence: {face_result.get('confidence')})")
                self.current_person = face_result.get('person_id')
                self.current_person_name = face_result.get('name')
                self.current_employee_id = face_result.get('employee_id')  # Store employee ID
                self.face_confidence = face_result.get('confidence')
                self.transition_to(AccessState.FACE_RECOGNIZED)
            elif face_result and face_result.get('face_location') and not face_result.get('matched'):
                # Face detected but NOT matched - deny access
                print(f"⚠️ Face detected but NOT matched (time: {time_in_state:.1f}s / {self.face_detection_timeout}s)")
                if time_in_state > self.face_detection_timeout:
                    print("🚫 TIMEOUT: Unknown person - denying access")
                    self.transition_to(AccessState.ACCESS_DENIED, 
                                     message="Unknown person - Face not recognized")
                    self.log_access(False, False)
            elif not face_result or not face_result.get('face_location'):
                # No face detected - timeout and reset
                print(f"👻 No face detected (time: {time_in_state:.1f}s)")
                if time_in_state > self.face_detection_timeout:
                    print("⏱️ TIMEOUT: Resetting to IDLE")
                    self.reset()
        
        elif self.current_state == AccessState.FACE_RECOGNIZED:
            # Immediately start PPE checking
            self.transition_to(AccessState.PPE_CHECKING)
        
        elif self.current_state == AccessState.PPE_CHECKING:
            # If face recognition is enabled, verify person is authorized
            print(f"🔍 PPE_CHECKING: face_enabled={self.face_recognition_enabled}, current_person={self.current_person}")
            if self.face_recognition_enabled and not self.current_person:
                # Face recognition enabled but no authorized person - deny immediately
                print("🚫 DENIED: Face recognition enabled but no authorized person!")
                self.transition_to(AccessState.ACCESS_DENIED, 
                                 message="Unauthorized - Face recognition required")
                self.log_access(False, False)
                return
            
            # Check if PPE requirements are met
            ppe_complete = self.check_ppe_requirements(self.detected_classes)
            
            if ppe_complete:
                face_matched = self.current_person is not None if self.face_recognition_enabled else True
                self.transition_to(AccessState.ACCESS_GRANTED)
                self.log_access(face_matched, True)
            
            # Check timeout
            elif time_in_state > self.ppe_checking_duration:
                face_matched = self.current_person is not None if self.face_recognition_enabled else True
                self.transition_to(AccessState.ACCESS_DENIED, 
                                 message="PPE requirements not met")
                self.log_access(face_matched, False)
        
        elif self.current_state == AccessState.ACCESS_GRANTED:
            # Display access granted for a duration, then reset
            if time_in_state > self.access_display_duration:
                self.reset()
        
        elif self.current_state == AccessState.ACCESS_DENIED:
            # Display access denied for a duration, then reset
            if time_in_state > self.access_display_duration:
                self.reset()
    
    def transition_to(self, new_state, message=None):
        """
        Transition to a new state
        
        Args:
            new_state: AccessState to transition to
            message: Optional message for the state
        """
        print(f"State transition: {self.current_state.value} → {new_state.value}")
        
        self.current_state = new_state
        self.state_start_time = datetime.now()
        
        if new_state == AccessState.ACCESS_GRANTED:
            self.access_granted_time = datetime.now()
        
        # Emit status change via WebSocket
        self.emit_status_change(message)
    
    def check_ppe_requirements(self, detected_classes):
        """
        Check if detected PPE meets requirements
        
        Args:
            detected_classes: List of detected class names
            
        Returns:
            bool: True if requirements are met
        """
        # Get required classes from database
        enabled_configs = DetectionConfig.query.filter_by(enabled=True).all()
        required_classes = [config.class_name for config in enabled_configs]
        
        if not required_classes:
            print("⚠️ No PPE requirements configured - granting access")
            return True  # No requirements
        
        # Get detection logic
        logic_setting = SystemSettings.query.filter_by(setting_key='detection_logic').first()
        detection_logic = logic_setting.setting_value if logic_setting else 'ALL'
        
        # Convert to lowercase for comparison
        detected_lower = [cls.lower() for cls in detected_classes]
        required_lower = [cls.lower() for cls in required_classes]
        
        print(f"🔍 PPE Check:")
        print(f"   Required: {required_classes} (lower: {required_lower})")
        print(f"   Detected: {detected_classes} (lower: {detected_lower})")
        print(f"   Logic: {detection_logic}")
        
        if detection_logic == 'ALL':
            result = all(cls in detected_lower for cls in required_lower)
            if not result:
                missing = [cls for cls in required_lower if cls not in detected_lower]
                print(f"   ❌ Missing: {missing}")
            else:
                print(f"   ✅ All requirements met!")
            return result
        else:  # ANY
            result = any(cls in detected_lower for cls in required_lower)
            if result:
                matched = [cls for cls in required_lower if cls in detected_lower]
                print(f"   ✅ Matched: {matched}")
            else:
                print(f"   ❌ None matched")
            return result
    
    def log_access(self, face_matched, access_granted):
        """
        Log access attempt to database
        
        Args:
            face_matched: Whether face was successfully matched
            access_granted: Whether access was granted
        """
        try:
            log = AccessLog(
                person_id=self.current_person,
                person_name=self.current_person_name or 'Unknown',
                employee_id=self.current_employee_id,  # Store employee ID (can be None)
                face_matched=face_matched,
                face_confidence=self.face_confidence,
                detected_classes=json.dumps(self.detected_classes),
                ppe_complete=access_granted if face_matched else False,
                access_granted=access_granted
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Error logging access: {e}")
            db.session.rollback()
    
    def emit_status_change(self, message=None):
        """
        Emit status change event via WebSocket
        
        Args:
            message: Optional status message
        """
        if not self.socketio:
            return
        
        status_data = {
            'state': self.current_state.value,
            'person_id': self.current_person,
            'person_name': self.current_person_name,
            'face_confidence': self.face_confidence,
            'detected_classes': self.detected_classes,
            'message': message or self.get_default_message()
        }
        
        if self.current_state == AccessState.ACCESS_GRANTED:
            status_data['duration'] = self.access_display_duration
        
        self.socketio.emit('access_status_change', status_data)
    
    def get_default_message(self):
        """Get default message for current state"""
        messages = {
            AccessState.IDLE: "Please stand in front of camera",
            AccessState.FACE_DETECTING: "Detecting face...",
            AccessState.FACE_RECOGNIZED: f"Identity verified: {self.current_person_name}",
            AccessState.PPE_CHECKING: "Checking PPE equipment...",
            AccessState.ACCESS_GRANTED: "Welcome! Door opening...",
            AccessState.ACCESS_DENIED: "Access denied"
        }
        return messages.get(self.current_state, "")
    
    def get_status(self):
        """Get current status as dictionary"""
        return {
            'state': self.current_state.value,
            'person_id': self.current_person,
            'person_name': self.current_person_name,
            'face_confidence': self.face_confidence,
            'detected_classes': self.detected_classes,
            'time_in_state': (datetime.now() - self.state_start_time).total_seconds()
        }


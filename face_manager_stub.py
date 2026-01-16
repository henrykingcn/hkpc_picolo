"""
Face Recognition Manager Stub (No-op version)
Use this when face-recognition library is not available
"""
import json
import os


class FaceRecognitionManager:
    """Stub version - always returns no face detected"""
    
    def __init__(self, tolerance=None, model=None):
        """Initialize stub face manager"""
        self.tolerance = tolerance or 0.6
        self.model = model or "hog"
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        
        print("⚠ Face Recognition DISABLED (library not installed)")
        print("  PPE detection will work, but no face recognition")
        print("  To enable: pip install dlib face-recognition")
    
    def load_known_faces(self):
        """Stub - no faces to load"""
        pass
    
    def register_face(self, image_path, name, employee_id):
        """Stub - face registration disabled"""
        return False, "Face recognition not available. Install dlib and face-recognition.", None
    
    def identify_face(self, frame):
        """Stub - always returns no face detected"""
        return {
            'person_id': None,
            'name': None,
            'confidence': None,
            'face_location': None,
            'matched': False
        }
    
    def delete_person(self, person_id):
        """Stub - nothing to delete"""
        return False, "Face recognition not available"
    
    def update_person_status(self, person_id, is_active):
        """Stub - nothing to update"""
        return False, "Face recognition not available"
    
    def get_all_persons(self):
        """Stub - no persons"""
        return []




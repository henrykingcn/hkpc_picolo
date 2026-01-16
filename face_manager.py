"""
Face Recognition Manager for HKPC Access Control System
"""
import face_recognition
import numpy as np
import json
import os
from datetime import datetime
from PIL import Image
import cv2
from models import db, AuthorizedPerson
from config import Config


class FaceRecognitionManager:
    """Manages face recognition for access control"""
    
    def __init__(self, tolerance=None, model=None):
        """
        Initialize face recognition manager
        
        Args:
            tolerance: Recognition tolerance (lower = more strict)
            model: Detection model ('hog' or 'cnn')
        """
        self.tolerance = tolerance or Config.FACE_RECOGNITION_TOLERANCE
        self.model = model or Config.FACE_DETECTION_MODEL
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.load_known_faces()
        
        print(f"✓ Face Recognition initialized ({len(self.known_face_encodings)} faces loaded)")
    
    def load_known_faces(self):
        """Load all known faces from database"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        
        persons = AuthorizedPerson.query.filter_by(is_active=True).all()
        
        for person in persons:
            try:
                # Parse face encoding from JSON
                encoding = np.array(json.loads(person.face_encoding))
                self.known_face_encodings.append(encoding)
                self.known_face_ids.append(person.id)
                self.known_face_names.append(person.name)
            except Exception as e:
                print(f"Error loading face for {person.name}: {e}")
    
    def register_face(self, image_path, name, employee_id):
        """
        Register a new face
        
        Args:
            image_path: Path to face image
            name: Person's name
            employee_id: Employee ID
            
        Returns:
            tuple: (success: bool, message: str, person_id: int or None)
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Detect faces
            face_locations = face_recognition.face_locations(image, model=self.model)
            
            if len(face_locations) == 0:
                return False, "No face detected in image", None
            
            if len(face_locations) > 1:
                return False, "Multiple faces detected. Please use image with single face", None
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) == 0:
                return False, "Could not encode face", None
            
            face_encoding = face_encodings[0]
            
            # Check if face already exists
            if len(self.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(
                    self.known_face_encodings,
                    face_encoding,
                    tolerance=self.tolerance
                )
                if any(matches):
                    matched_idx = matches.index(True)
                    matched_name = self.known_face_names[matched_idx]
                    return False, f"Face already registered for {matched_name}", None
            
            # Save to database
            encoding_json = json.dumps(face_encoding.tolist())
            
            # Generate photo filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"{employee_id}_{timestamp}.jpg"
            photo_path = os.path.join(Config.FACES_DIR, photo_filename)
            
            # Copy/save photo
            os.makedirs(Config.FACES_DIR, exist_ok=True)
            img = Image.open(image_path)
            img.save(photo_path)
            
            # Create database record
            person = AuthorizedPerson(
                name=name,
                employee_id=employee_id,
                face_encoding=encoding_json,
                photo_path=photo_filename
            )
            db.session.add(person)
            db.session.commit()
            
            # Reload known faces
            self.load_known_faces()
            
            return True, f"Face registered successfully for {name}", person.id
            
        except Exception as e:
            return False, f"Error registering face: {str(e)}", None
    
    def identify_face(self, frame):
        """
        Identify face in a video frame
        
        Args:
            frame: OpenCV BGR image frame
            
        Returns:
            dict: {
                'person_id': int or None,
                'name': str or None,
                'confidence': float or None,
                'face_location': tuple or None,
                'matched': bool
            }
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
            
            if len(face_locations) == 0:
                return {
                    'person_id': None,
                    'name': None,
                    'confidence': None,
                    'face_location': None,
                    'matched': False
                }
            
            # Use the first face found
            face_location = face_locations[0]
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
            
            if len(face_encodings) == 0:
                return {
                    'person_id': None,
                    'name': None,
                    'confidence': None,
                    'face_location': face_location,
                    'matched': False
                }
            
            face_encoding = face_encodings[0]
            
            # No known faces
            if len(self.known_face_encodings) == 0:
                return {
                    'person_id': None,
                    'name': 'Unknown',
                    'confidence': 0.0,
                    'face_location': face_location,
                    'matched': False
                }
            
            # Compare with known faces
            face_distances = face_recognition.face_distance(
                self.known_face_encodings,
                face_encoding
            )
            
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            
            # Check if match is good enough
            if best_distance <= self.tolerance:
                person_id = self.known_face_ids[best_match_index]
                name = self.known_face_names[best_match_index]
                confidence = 1.0 - best_distance
                
                return {
                    'person_id': person_id,
                    'name': name,
                    'confidence': confidence,
                    'face_location': face_location,
                    'matched': True
                }
            else:
                return {
                    'person_id': None,
                    'name': 'Unknown',
                    'confidence': 1.0 - best_distance,
                    'face_location': face_location,
                    'matched': False
                }
                
        except Exception as e:
            print(f"Error in face identification: {e}")
            return {
                'person_id': None,
                'name': None,
                'confidence': None,
                'face_location': None,
                'matched': False
            }
    
    def delete_person(self, person_id):
        """
        Delete a person from database
        
        Args:
            person_id: Person's database ID
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            person = AuthorizedPerson.query.get(person_id)
            if not person:
                return False, "Person not found"
            
            # Delete photo file
            if person.photo_path:
                photo_path = os.path.join(Config.FACES_DIR, person.photo_path)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            # Delete from database
            db.session.delete(person)
            db.session.commit()
            
            # Reload known faces
            self.load_known_faces()
            
            return True, f"Deleted {person.name} successfully"
            
        except Exception as e:
            return False, f"Error deleting person: {str(e)}"
    
    def update_person_status(self, person_id, is_active):
        """
        Enable/disable a person
        
        Args:
            person_id: Person's database ID
            is_active: True to enable, False to disable
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            person = AuthorizedPerson.query.get(person_id)
            if not person:
                return False, "Person not found"
            
            person.is_active = is_active
            db.session.commit()
            
            # Reload known faces
            self.load_known_faces()
            
            status = "enabled" if is_active else "disabled"
            return True, f"{person.name} {status} successfully"
            
        except Exception as e:
            return False, f"Error updating person: {str(e)}"
    
    def get_all_persons(self):
        """Get list of all authorized persons"""
        persons = AuthorizedPerson.query.all()
        return [person.to_dict() for person in persons]


if __name__ == "__main__":
    """Test face recognition"""
    print("Testing Face Recognition Manager...")
    # This would need app context to actually run
    print("Face recognition module ready")




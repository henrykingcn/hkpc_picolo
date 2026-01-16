"""
InsightFace Manager for HKPC Access Control System
Replaces face_recognition library with InsightFace (ONNX Runtime)
"""
import insightface
from insightface.app import FaceAnalysis
import numpy as np
import json
import os
from datetime import datetime
from PIL import Image
import cv2
from models import db, AuthorizedPerson
from config import Config


class InsightFaceManager:
    """Manages face recognition using InsightFace"""
    
    def __init__(self, similarity_threshold=0.4):
        """
        Initialize InsightFace manager
        
        Args:
            similarity_threshold: Minimum cosine similarity for face match (0.3-0.5)
        """
        self.similarity_threshold = similarity_threshold
        self.known_face_encodings = []  # 512-dim vectors
        self.known_face_ids = []
        self.known_face_names = []
        
        # Initialize InsightFace app with CPU provider
        print("Loading InsightFace models...")
        try:
            self.app = FaceAnalysis(
                name='buffalo_l',  # or 'buffalo_s' for smaller model
                providers=['CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("✓ InsightFace initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing InsightFace: {e}")
            raise
        
        self.load_known_faces()
        print(f"✓ Face Recognition initialized ({len(self.known_face_encodings)} faces loaded)")
    
    def load_known_faces(self):
        """Load all known faces from database"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.known_face_employee_ids = []  # Store employee IDs
        
        persons = AuthorizedPerson.query.filter_by(is_active=True).all()
        
        for person in persons:
            try:
                # Parse face encoding from JSON (512-dim vector)
                encoding = np.array(json.loads(person.face_encoding))
                # Normalize the encoding for cosine similarity
                encoding = encoding / np.linalg.norm(encoding)
                
                self.known_face_encodings.append(encoding)
                self.known_face_ids.append(person.id)
                self.known_face_names.append(person.name)
                self.known_face_employee_ids.append(person.employee_id)  # Add employee ID
            except Exception as e:
                print(f"Error loading face for {person.name}: {e}")
        
        # Convert to numpy array for faster computation
        if self.known_face_encodings:
            self.known_face_encodings = np.array(self.known_face_encodings)
    
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
            img = cv2.imread(image_path)
            if img is None:
                return False, "Could not load image", None
            
            # Detect faces
            faces = self.app.get(img)
            
            if len(faces) == 0:
                return False, "No face detected in image", None
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please use image with single face", None
            
            # Get face embedding (512-dim)
            face_embedding = faces[0].embedding
            
            # Normalize for cosine similarity
            face_embedding_normalized = face_embedding / np.linalg.norm(face_embedding)
            
            # Check if face already exists
            if len(self.known_face_encodings) > 0:
                similarities = np.dot(self.known_face_encodings, face_embedding_normalized)
                max_similarity = np.max(similarities)
                
                if max_similarity > self.similarity_threshold:
                    matched_idx = np.argmax(similarities)
                    matched_name = self.known_face_names[matched_idx]
                    return False, f"Face already registered for {matched_name}", None
            
            # Save to database (store original unnormalized embedding)
            encoding_json = json.dumps(face_embedding.tolist())
            
            # Generate photo filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"{employee_id}_{timestamp}.jpg"
            photo_path = os.path.join(Config.FACES_DIR, photo_filename)
            
            # Copy/save photo
            os.makedirs(Config.FACES_DIR, exist_ok=True)
            img_pil = Image.open(image_path)
            img_pil.save(photo_path)
            
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
                'employee_id': str or None,
                'confidence': float or None,
                'face_location': tuple or None,
                'matched': bool
            }
        """
        try:
            # Detect faces using InsightFace
            faces = self.app.get(frame)
            
            # Debug: Log if multiple faces detected
            if len(faces) > 1:
                print(f"⚠️ 检测到 {len(faces)} 个人脸！")
                for i, face in enumerate(faces):
                    bbox = face.bbox.astype(int)
                    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    print(f"   人脸 {i+1}: 位置 [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}], 面积 {area}px²")
            
            if len(faces) == 0:
                return {
                    'person_id': None,
                    'name': None,
                    'employee_id': None,
                    'confidence': None,
                    'face_location': None,
                    'matched': False
                }
            
            # Use the first face found
            face = faces[0]
            
            # Get face bbox (converting InsightFace format to face_recognition format)
            # InsightFace: [x1, y1, x2, y2]
            # face_recognition: (top, right, bottom, left)
            bbox = face.bbox.astype(int)
            face_location = (bbox[1], bbox[2], bbox[3], bbox[0])  # (top, right, bottom, left)
            
            # Get face embedding (512-dim)
            face_embedding = face.embedding
            
            # Normalize for cosine similarity
            face_embedding_normalized = face_embedding / np.linalg.norm(face_embedding)
            
            # No known faces
            if len(self.known_face_encodings) == 0:
                return {
                    'person_id': None,
                    'name': 'Unknown',
                    'employee_id': None,
                    'confidence': 0.0,
                    'face_location': face_location,
                    'matched': False
                }
            
            # Compare with known faces using cosine similarity
            similarities = np.dot(self.known_face_encodings, face_embedding_normalized)
            
            best_match_index = np.argmax(similarities)
            best_similarity = similarities[best_match_index]
            best_match_name = self.known_face_names[best_match_index]
            
            # Debug: Print similarity score
            print(f"🎯 Face similarity: {best_similarity:.3f} vs threshold {self.similarity_threshold:.3f}")
            print(f"   Closest match: {best_match_name}")
            if best_similarity < self.similarity_threshold:
                print(f"   ❌ Below threshold! Consider lowering threshold to ~{best_similarity - 0.05:.2f}")
            
            # Check if match is good enough
            if best_similarity >= self.similarity_threshold:
                person_id = self.known_face_ids[best_match_index]
                name = self.known_face_names[best_match_index]
                employee_id = self.known_face_employee_ids[best_match_index]
                
                return {
                    'person_id': person_id,
                    'name': name,
                    'employee_id': employee_id,  # Include employee ID
                    'confidence': float(best_similarity),
                    'face_location': face_location,
                    'matched': True
                }
            else:
                return {
                    'person_id': None,
                    'name': 'Unknown',
                    'employee_id': None,  # No employee ID for unknown person
                    'confidence': float(best_similarity),
                    'face_location': face_location,
                    'matched': False
                }
                
        except Exception as e:
            print(f"Error in face identification: {e}")
            import traceback
            traceback.print_exc()
            return {
                'person_id': None,
                'name': None,
                'employee_id': None,
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
    """Test InsightFace recognition"""
    print("Testing InsightFace Manager...")
    print("InsightFace module ready")


"""
YOLO PPE Detector Module for HKPC Access Control System
"""
import cv2
import torch
from ultralytics import YOLO
import numpy as np

# Fix for PyTorch 2.6+ weights_only security
try:
    from ultralytics.nn.tasks import DetectionModel
    torch.serialization.add_safe_globals([DetectionModel])
except Exception:
    pass  # Fallback for older PyTorch/Ultralytics versions


class PPEDetector:
    """PPE Detection using YOLO model"""
    
    def __init__(self, model_path, confidence_threshold=0.5):
        """
        Initialize the PPE detector
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
        """
        print(f"Loading YOLO model from {model_path}...")
        try:
            self.model = YOLO(model_path)
            self.confidence_threshold = confidence_threshold
            print("✓ YOLO model loaded successfully")
        except Exception as e:
            print(f"✗ Error loading YOLO model: {e}")
            raise
    
    def detect(self, frame):
        """
        Run detection on a single frame
        
        Args:
            frame: OpenCV image frame (BGR format)
            
        Returns:
            dict with keys:
                - annotated_frame: Frame with detection boxes drawn
                - detected_classes: List of detected class names
                - confidence_scores: Dict mapping class names to confidence scores
                - detection_counts: Dict mapping class names to count (e.g., how many Person detected)
                - raw_results: Raw YOLO results
        """
        # Run YOLO inference
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        # Extract detection information
        detected_classes = []
        confidence_scores = {}
        detection_counts = {}  # Track count of each detected class
        
        for result in results:
            # Get class names and confidence scores
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    # Get class ID and confidence
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Get class name from model
                    class_name = self.model.names[class_id]
                    
                    # Count detections per class
                    detection_counts[class_name] = detection_counts.get(class_name, 0) + 1
                    
                    # Add to detected classes
                    if class_name not in detected_classes:
                        detected_classes.append(class_name)
                        confidence_scores[class_name] = confidence
                    else:
                        # Keep the highest confidence for each class
                        confidence_scores[class_name] = max(
                            confidence_scores[class_name],
                            confidence
                        )
            
            # Get annotated frame with boxes drawn
            annotated_frame = result.plot()
        
        # If no detections, return original frame
        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            annotated_frame = frame.copy()
        
        return {
            'annotated_frame': annotated_frame,
            'detected_classes': detected_classes,
            'confidence_scores': confidence_scores,
            'detection_counts': detection_counts,  # Number of each class detected
            'raw_results': results
        }
    
    def detect_batch(self, frames):
        """
        Run detection on multiple frames
        
        Args:
            frames: List of OpenCV image frames
            
        Returns:
            List of detection results (same format as detect())
        """
        results_list = []
        for frame in frames:
            results_list.append(self.detect(frame))
        return results_list
    
    def get_model_info(self):
        """Get information about the loaded model"""
        return {
            'model_name': str(self.model),
            'class_names': self.model.names,
            'confidence_threshold': self.confidence_threshold
        }


if __name__ == "__main__":
    """Test the detector with webcam"""
    print("Testing PPE Detector...")
    
    # Initialize detector
    detector = PPEDetector("yolo10s.pt", confidence_threshold=0.5)
    
    # Print model info
    info = detector.get_model_info()
    print(f"Model classes: {info['class_names']}")
    
    # Open webcam
    cap = cv2.VideoCapture(1)
    
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        exit()
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run detection
        result = detector.detect(frame)
        
        # Display results
        cv2.imshow("PPE Detection Test", result['annotated_frame'])
        
        # Print detected classes
        if result['detected_classes']:
            print(f"Detected: {result['detected_classes']}")
        
        # Quit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


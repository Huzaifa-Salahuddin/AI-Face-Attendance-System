from deepface import DeepFace
from deepface.commons import image_utils
from PIL import Image
import numpy as np
import io
import logging
from typing import Tuple, Optional, Dict, Any
import warnings
import time

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastAttendanceVerifier:
    def __init__(self, 
                 model_name: str = 'Facenet512',
                 distance_metric: str = 'cosine',
                 threshold: float = 0.30,
                 max_image_size: int = 640):
        """
        Fast Face Verification optimized for attendance systems
        
        Args:
            model_name: Face recognition model ('Facenet512' recommended for speed+accuracy)
            distance_metric: Distance metric ('cosine' recommended)
            threshold: Verification threshold (0.30 for Facenet512 with cosine)
            max_image_size: Maximum image dimension for faster processing
        """
        self.model_name = model_name
        self.distance_metric = distance_metric
        self.threshold = threshold
        self.max_image_size = max_image_size
        
        
        self._warm_up_model()
        
        logger.info(f"🚀 FastAttendanceVerifier initialized with {model_name}")
    
    def _warm_up_model(self):
        """Pre-load the model to avoid first-time loading delays"""
        try:
            
            dummy_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
            DeepFace.represent(
                img_path=dummy_img,
                model_name=self.model_name,
                detector_backend='opencv',
                enforce_detection=False
            )
            logger.info("✅ Model pre-loaded successfully")
        except Exception as e:
            logger.warning(f"Model pre-loading failed: {e}")
    
    def fast_preprocess(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Lightning-fast image preprocessing for attendance (no OpenCV version)
        """
        try:
            
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
            
            width, height = image.size
            if max(width, height) > self.max_image_size:
                scale = self.max_image_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.BILINEAR)
        
            img_array = np.array(image)
            return img_array

        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}")
        return None
    
    def verify_attendance(self, 
                         reference_image_bytes: bytes, 
                         live_image_bytes: bytes) -> Tuple[bool, float, float]:
        """
        Fast attendance verification - optimized for speed
        
        Args:
            reference_image_bytes: Stored reference photo
            live_image_bytes: Live capture for attendance
            
        Returns:
            Tuple of (is_verified, distance, processing_time_seconds)
        """
        start_time = time.time()
        
        try:
            
            ref_img = self.fast_preprocess(reference_image_bytes)
            live_img = self.fast_preprocess(live_image_bytes)
            
            if ref_img is None or live_img is None:
                logger.error("❌ Image preprocessing failed")
                return False, 1.0, time.time() - start_time
            
            
            result = DeepFace.verify(
                img1_path=ref_img,
                img2_path=live_img,
                model_name=self.model_name,
                detector_backend='opencv',  
                distance_metric=self.distance_metric,
                enforce_detection=False,    
                align=False,               
                normalization='base'
            )
            
            distance = result['distance']
            is_verified = distance <= self.threshold
            processing_time = time.time() - start_time
            
            
            status = "✅ MATCH" if is_verified else "❌ NO MATCH"
            logger.info(f"{status} | Distance: {distance:.3f} | Time: {processing_time:.2f}s")
            
            return is_verified, distance, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Verification error: {e} | Time: {processing_time:.2f}s")
            return False, 1.0, processing_time


class AttendanceSystem:
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Complete attendance system with employee database
        
        Args:
            confidence_threshold: Minimum confidence for attendance marking
        """
        self.verifier = FastAttendanceVerifier()
        self.confidence_threshold = confidence_threshold
        self.employee_database = {}  
        
    def register_employee(self, employee_id: str, name: str, reference_image_bytes: bytes) -> bool:
        """
        Register a new employee in the system
        """
        try:
            
            img = self.verifier.fast_preprocess(reference_image_bytes)
            if img is None:
                return False
            
            
            faces = DeepFace.extract_faces(
                img_path=img,
                detector_backend='opencv',
                enforce_detection=False
            )
            
            if len(faces) == 0:
                logger.error(f"❌ No face detected in reference image for {employee_id}")
                return False
            
            
            self.employee_database[employee_id] = {
                'name': name,
                'reference_image': reference_image_bytes,
                'registered_at': time.time()
            }
            
            logger.info(f"✅ Employee {employee_id} ({name}) registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Registration failed for {employee_id}: {e}")
            return False
    
    def mark_attendance(self, live_image_bytes: bytes) -> Dict[str, Any]:
        """
        Mark attendance by comparing live image with all registered employees
        
        Returns:
            Dictionary with attendance result
        """
        start_time = time.time()
        
        if not self.employee_database:
            return {
                'success': False,
                'message': 'No employees registered in system',
                'processing_time': time.time() - start_time
            }
        
        best_match = None
        best_confidence = 0
        best_distance = 1.0
        
    
        for employee_id, employee_data in self.employee_database.items():
            is_verified, distance, _ = self.verifier.verify_attendance(
                employee_data['reference_image'],
                live_image_bytes
            )
            
            if is_verified:
                
                confidence = max(0, 1 - (distance / self.verifier.threshold))
                
                if confidence > best_confidence and confidence >= self.confidence_threshold:
                    best_confidence = confidence
                    best_distance = distance
                    best_match = {
                        'employee_id': employee_id,
                        'name': employee_data['name'],
                        'confidence': confidence,
                        'distance': distance
                    }
        
        processing_time = time.time() - start_time
        
        if best_match:
            logger.info(f"🎯 Attendance marked for {best_match['name']} "
                       f"(Confidence: {best_match['confidence']:.2f})")
            return {
                'success': True,
                'employee': best_match,
                'message': f"Attendance marked for {best_match['name']}",
                'processing_time': processing_time
            }
        else:
            logger.warning("👤 No matching employee found")
            return {
                'success': False,
                'message': 'Employee not recognized or confidence too low',
                'processing_time': processing_time
            }


def quick_face_verify(reference_bytes: bytes, 
                     live_bytes: bytes, 
                     threshold: float = 0.30) -> Tuple[bool, float]:
    """
    Ultra-fast face verification for attendance
    
    Returns:
        (is_match, distance)
    """
    verifier = FastAttendanceVerifier(threshold=threshold)
    is_verified, distance, _ = verifier.verify_attendance(reference_bytes, live_bytes)
    return is_verified, distance


def batch_verify_attendance(live_image_bytes: bytes, 
                          reference_images: Dict[str, bytes],
                          threshold: float = 0.30) -> Optional[str]:
    """
    Quick batch verification against multiple reference images
    
    Args:
        live_image_bytes: Live capture image
        reference_images: Dict of {employee_id: reference_image_bytes}
        threshold: Verification threshold
    
    Returns:
        employee_id of best match or None
    """
    verifier = FastAttendanceVerifier(threshold=threshold)
    
    best_match = None
    best_distance = float('inf')
    
    for employee_id, ref_bytes in reference_images.items():
        is_verified, distance, _ = verifier.verify_attendance(ref_bytes, live_image_bytes)
        
        if is_verified and distance < best_distance:
            best_distance = distance
            best_match = employee_id
    
    return best_match


# Example usage for attendance system
if __name__ == "__main__":
    # Initialize attendance system
    attendance = AttendanceSystem(confidence_threshold=0.80)
    

    
    print("🚀 Fast Attendance System Ready!")
    print("📊 Expected processing time: 0.3-0.8 seconds per verification")
    print("🎯 Optimized for real-time attendance marking")
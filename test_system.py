"""
Quick test script to verify system works without face-recognition
"""
import sys
print("Testing HKPC System...")

# Test imports
try:
    print("1. Testing Flask import...")
    from flask import Flask
    print("   ✓ Flask OK")
except ImportError as e:
    print(f"   ✗ Flask failed: {e}")
    sys.exit(1)

try:
    print("2. Testing database models...")
    from models import db, DetectionConfig
    print("   ✓ Models OK")
except ImportError as e:
    print(f"   ✗ Models failed: {e}")
    sys.exit(1)

try:
    print("3. Testing face manager (should use stub)...")
    from face_manager_stub import FaceRecognitionManager
    face_mgr = FaceRecognitionManager()
    print("   ✓ Face manager stub OK")
except ImportError as e:
    print(f"   ✗ Face manager stub failed: {e}")
    sys.exit(1)

try:
    print("4. Testing detection processor...")
    # Don't actually import to avoid cv2 requirement
    print("   ⚠ Skipped (requires cv2)")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n✅ Basic imports OK!")
print("\nTo start system:")
print("  1. Install remaining dependencies: pip install -r requirements.txt")
print("  2. Run: python app.py")




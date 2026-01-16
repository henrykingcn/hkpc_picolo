"""
Test script to verify InsightFace installation and basic functionality
"""
import sys

def test_insightface_import():
    """Test if InsightFace can be imported"""
    print("1. Testing InsightFace import...")
    try:
        import insightface
        print("   ✓ InsightFace imported successfully")
        print(f"   Version: {insightface.__version__}")
        return True
    except ImportError as e:
        print(f"   ✗ Failed to import InsightFace: {e}")
        print("   Please install: pip install insightface")
        return False

def test_onnxruntime_import():
    """Test if ONNX Runtime can be imported"""
    print("\n2. Testing ONNX Runtime import...")
    try:
        import onnxruntime
        print("   ✓ ONNX Runtime imported successfully")
        print(f"   Version: {onnxruntime.__version__}")
        print(f"   Providers: {onnxruntime.get_available_providers()}")
        return True
    except ImportError as e:
        print(f"   ✗ Failed to import ONNX Runtime: {e}")
        print("   Please install: pip install onnxruntime")
        return False

def test_insightface_initialization():
    """Test if InsightFace can be initialized"""
    print("\n3. Testing InsightFace initialization...")
    try:
        from insightface.app import FaceAnalysis
        
        print("   Creating FaceAnalysis instance...")
        app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider']
        )
        
        print("   Preparing model (this may take a few minutes on first run)...")
        app.prepare(ctx_id=0, det_size=(640, 640))
        
        print("   ✓ InsightFace initialized successfully")
        print("   Model loaded and ready")
        return True
    except Exception as e:
        print(f"   ✗ Failed to initialize InsightFace: {e}")
        return False

def test_face_manager():
    """Test if our InsightFaceManager can be imported and initialized"""
    print("\n4. Testing InsightFaceManager...")
    try:
        # Need to be in app context for database access
        print("   Note: Full initialization requires app context")
        print("   Testing import only...")
        
        from face_manager_insightface import InsightFaceManager
        print("   ✓ InsightFaceManager module imported successfully")
        return True
    except Exception as e:
        print(f"   ✗ Failed to import InsightFaceManager: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("InsightFace Installation Test")
    print("=" * 60)
    
    results = []
    
    # Test imports
    results.append(("InsightFace Import", test_insightface_import()))
    results.append(("ONNX Runtime Import", test_onnxruntime_import()))
    
    # Only test initialization if imports succeeded
    if results[0][1] and results[1][1]:
        results.append(("InsightFace Initialization", test_insightface_initialization()))
        results.append(("InsightFaceManager Import", test_face_manager()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All tests passed! InsightFace is ready to use.")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Visit: http://localhost:5001/admin")
        print("3. Toggle face recognition on/off as needed")
        return 0
    else:
        print("\n❌ Some tests failed. Please install missing dependencies:")
        print("\npip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())




"""
Verification script to check if HKPC PPE Detection System is ready to run
"""
import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠ Warning: Python 3.8+ is recommended")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'flask': 'Flask',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'cv2': 'OpenCV (opencv-python)',
        'ultralytics': 'Ultralytics YOLO',
        'PIL': 'Pillow',
        'numpy': 'NumPy'
    }
    
    all_installed = True
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"✗ {name} is NOT installed")
            all_installed = False
    
    return all_installed

def check_files():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'detector.py',
        'models.py',
        'config.py',
        'yolo10s.pt',
        'static/css/style.css',
        'static/js/script.js',
        'static/images/logo-hkpc.png',
        'templates/base.html',
        'templates/index.html',
        'templates/admin.html'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist

def check_camera():
    """Check if camera is accessible"""
    try:
        import cv2
        cap = cv2.VideoCapture(1)
        if cap.isOpened():
            print("✓ Camera (index 1) is accessible")
            cap.release()
            return True
        else:
            print("✗ Camera (index 1) is NOT accessible")
            print("  Please check camera permissions in System Preferences")
            return False
    except Exception as e:
        print(f"✗ Error checking camera: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("HKPC PPE Detection System - Setup Verification")
    print("=" * 60)
    print()
    
    print("Checking Python version...")
    python_ok = check_python_version()
    print()
    
    print("Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("Checking required files...")
    files_ok = check_files()
    print()
    
    print("Checking camera access...")
    camera_ok = check_camera()
    print()
    
    print("=" * 60)
    if python_ok and deps_ok and files_ok and camera_ok:
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
        print()
        print("System is ready to run. Start the application with:")
        print("  python app.py")
        print()
        print("Or use the startup script:")
        print("  ./start.sh")
        print()
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("=" * 60)
        print()
        if not deps_ok:
            print("Install missing dependencies with:")
            print("  pip install -r requirements.txt")
            print()
        if not files_ok:
            print("Ensure all project files are present.")
            print()
        if not camera_ok:
            print("Check camera permissions in System Preferences.")
            print()
        return 1

if __name__ == "__main__":
    sys.exit(main())


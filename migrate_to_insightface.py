"""
Migration script to update system from face_recognition to InsightFace
"""
from app import app, db
from models import SystemSettings, AuthorizedPerson
import sys

def check_insightface():
    """Check if InsightFace is installed"""
    try:
        import insightface
        import onnxruntime
        print("✓ InsightFace and ONNX Runtime are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install insightface onnxruntime")
        return False

def add_face_recognition_setting():
    """Add face_recognition_enabled setting to database"""
    with app.app_context():
        setting = SystemSettings.query.filter_by(
            setting_key='face_recognition_enabled'
        ).first()
        
        if setting:
            print(f"✓ Face recognition setting already exists (value: {setting.setting_value})")
            return True
        
        # Add new setting
        setting = SystemSettings(
            setting_key='face_recognition_enabled',
            setting_value='true'
        )
        db.session.add(setting)
        db.session.commit()
        print("✓ Added face_recognition_enabled setting to database")
        return True

def check_registered_faces():
    """Check how many faces are registered"""
    with app.app_context():
        face_count = AuthorizedPerson.query.count()
        active_count = AuthorizedPerson.query.filter_by(is_active=True).count()
        
        print(f"\nRegistered faces: {face_count} total, {active_count} active")
        
        if face_count > 0:
            print("\n⚠️  IMPORTANT: Face encodings need to be updated!")
            print("   Old system: 128-dimensional vectors (face_recognition)")
            print("   New system: 512-dimensional vectors (InsightFace)")
            print("\n   You need to re-register all faces:")
            print("   1. Visit http://localhost:5001/admin/faces")
            print("   2. Delete old faces")
            print("   3. Re-register with new photos")
            
            response = input("\n   Type 'CLEAR' to delete all face data and start fresh: ")
            if response == 'CLEAR':
                AuthorizedPerson.query.delete()
                db.session.commit()
                print("   ✓ All face data cleared")
                return True
            else:
                print("   Keeping existing face data (you'll need to update manually)")
                return True
        else:
            print("✓ No faces registered yet - ready for InsightFace")
            return True

def test_insightface_manager():
    """Test if InsightFaceManager can be initialized"""
    print("\nTesting InsightFaceManager initialization...")
    try:
        with app.app_context():
            from face_manager_insightface import InsightFaceManager
            manager = InsightFaceManager()
            print("✓ InsightFaceManager initialized successfully")
            return True
    except Exception as e:
        print(f"✗ Error initializing InsightFaceManager: {e}")
        return False

def main():
    """Run migration"""
    print("=" * 70)
    print("Migration: face_recognition → InsightFace")
    print("=" * 70)
    
    # Step 1: Check dependencies
    print("\n[Step 1/4] Checking dependencies...")
    if not check_insightface():
        return 1
    
    # Step 2: Update database
    print("\n[Step 2/4] Updating database configuration...")
    if not add_face_recognition_setting():
        return 1
    
    # Step 3: Check registered faces
    print("\n[Step 3/4] Checking registered faces...")
    if not check_registered_faces():
        return 1
    
    # Step 4: Test InsightFace
    print("\n[Step 4/4] Testing InsightFace...")
    if not test_insightface_manager():
        print("\n⚠️  InsightFace test failed, but migration may still work.")
        print("   The model will download on first use.")
    
    # Summary
    print("\n" + "=" * 70)
    print("Migration Complete!")
    print("=" * 70)
    print("\nWhat changed:")
    print("  • Face recognition library: face_recognition → InsightFace")
    print("  • Face encoding dimension: 128 → 512")
    print("  • Installation: Requires compilation → pip install only")
    print("  • New feature: Toggle face recognition on/off in Admin")
    
    print("\nNext steps:")
    print("  1. Start the application: python app.py")
    print("  2. Visit admin panel: http://localhost:5001/admin")
    print("  3. Toggle 'Enable Face Recognition' as needed")
    print("  4. Re-register faces at: http://localhost:5001/admin/faces")
    
    print("\nDocumentation:")
    print("  • Setup guide: INSIGHTFACE_SETUP.md")
    print("  • Test installation: python test_insightface.py")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




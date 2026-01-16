"""
PIN Code Authentication System for Admin Access
"""
import bcrypt
from datetime import datetime, timedelta
from models import db, AdminAuth


class PINAuthManager:
    """Manages PIN code authentication for admin access"""
    
    DEFAULT_PIN = "123456"
    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 30  # seconds
    
    @staticmethod
    def initialize_default_pin():
        """Initialize default PIN if none exists"""
        auth = AdminAuth.query.first()
        if not auth:
            pin_hash = bcrypt.hashpw(
                PINAuthManager.DEFAULT_PIN.encode('utf-8'),
                bcrypt.gensalt()
            )
            auth = AdminAuth(pin_hash=pin_hash.decode('utf-8'))
            db.session.add(auth)
            db.session.commit()
            print("✓ Default PIN initialized: 123456")
            return True
        return False
    
    @staticmethod
    def verify_pin(pin):
        """
        Verify PIN code
        
        Returns:
            tuple: (success: bool, message: str)
        """
        auth = AdminAuth.query.first()
        if not auth:
            return False, "Authentication not initialized"
        
        # Check if locked
        if auth.locked_until and datetime.utcnow() < auth.locked_until:
            remaining = (auth.locked_until - datetime.utcnow()).seconds
            return False, f"Account locked. Try again in {remaining} seconds"
        
        # Clear lock if expired
        if auth.locked_until and datetime.utcnow() >= auth.locked_until:
            auth.locked_until = None
            auth.failed_attempts = 0
            db.session.commit()
        
        # Verify PIN
        if bcrypt.checkpw(pin.encode('utf-8'), auth.pin_hash.encode('utf-8')):
            # Success - reset failed attempts
            auth.failed_attempts = 0
            auth.locked_until = None
            db.session.commit()
            return True, "Authentication successful"
        else:
            # Failed attempt
            auth.failed_attempts += 1
            
            if auth.failed_attempts >= PINAuthManager.MAX_ATTEMPTS:
                auth.locked_until = datetime.utcnow() + timedelta(
                    seconds=PINAuthManager.LOCKOUT_DURATION
                )
                db.session.commit()
                return False, f"Too many failed attempts. Account locked for {PINAuthManager.LOCKOUT_DURATION} seconds"
            
            db.session.commit()
            remaining_attempts = PINAuthManager.MAX_ATTEMPTS - auth.failed_attempts
            return False, f"Invalid PIN. {remaining_attempts} attempts remaining"
    
    @staticmethod
    def change_pin(old_pin, new_pin):
        """
        Change PIN code
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Verify old PIN first
        success, message = PINAuthManager.verify_pin(old_pin)
        if not success:
            return False, "Current PIN is incorrect"
        
        # Validate new PIN
        if not new_pin.isdigit():
            return False, "PIN must contain only digits"
        
        if len(new_pin) < 4 or len(new_pin) > 6:
            return False, "PIN must be 4-6 digits long"
        
        # Update PIN
        auth = AdminAuth.query.first()
        pin_hash = bcrypt.hashpw(new_pin.encode('utf-8'), bcrypt.gensalt())
        auth.pin_hash = pin_hash.decode('utf-8')
        auth.failed_attempts = 0
        auth.locked_until = None
        db.session.commit()
        
        return True, "PIN changed successfully"
    
    @staticmethod
    def get_lock_status():
        """
        Get current lock status
        
        Returns:
            dict: Lock status information
        """
        auth = AdminAuth.query.first()
        if not auth:
            return {'locked': False, 'attempts': 0}
        
        is_locked = auth.locked_until and datetime.utcnow() < auth.locked_until
        remaining_time = 0
        
        if is_locked:
            remaining_time = (auth.locked_until - datetime.utcnow()).seconds
        
        return {
            'locked': is_locked,
            'attempts': auth.failed_attempts,
            'remaining_time': remaining_time
        }




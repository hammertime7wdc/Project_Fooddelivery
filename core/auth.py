# core/auth.py (Refactored with SQLAlchemy)
import bcrypt
from datetime import datetime, timedelta
from models.models import Session, User
from .database import log_action

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 1


# ========== PASSWORD FUNCTIONS ==========
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


import re

# Common weak passwords to block
COMMON_PASSWORDS = [
    'password', 'password123', '12345678', 'qwerty123', 'abc123456',
    'password1', '123456789', 'iloveyou', 'admin123', 'letmein'
]

def validate_email(email: str):
    """Validate email format"""
    if not email or len(email) < 3:
        return False, "Email is required"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 254:  # RFC 5321
        return False, "Email is too long"
    
    return True, ""


def validate_password(password: str):
    """Enhanced password validation with strength requirements"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    # Check for common weak passwords
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger password"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
    
    return True, ""


def validate_full_name(name: str):
    """Validate full name"""
    if not name or not name.strip():
        return False, "Full name is required"
    
    if len(name.strip()) < 2:
        return False, "Full name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Full name is too long"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        return False, "Full name can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, ""


def get_password_strength(password: str):
    """
    Calculate password strength
    Returns: ('weak', 'medium', 'strong', 'very strong'), score (0-100)
    """
    if not password:
        return 'weak', 0
    
    score = 0
    
    # Length scoring
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10
    
    # Character variety
    if re.search(r'[a-z]', password):
        score += 15
    if re.search(r'[A-Z]', password):
        score += 15
    if re.search(r'\d', password):
        score += 15
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 15
    
    # Penalty for common patterns
    if password.lower() in COMMON_PASSWORDS:
        score -= 30
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    # Categorize strength
    if score < 40:
        return 'weak', score
    elif score < 60:
        return 'medium', score
    elif score < 80:
        return 'strong', score
    else:
        return 'very strong', score

# ========== USER AUTHENTICATION WITH LOCKOUT ==========
def authenticate_user(email: str, password: str):
    session = Session()
    try:
        user = session.query(User).filter_by(
            email=email,
            is_active=1
        ).first()
        
        if not user:
            log_action(None, "LOGIN_FAILED", f"User not found: {email}")
            return None

        # ──────────────────────── LOCK CHECK & AUTO-UNLOCK ────────────────────────
        if user.locked_until:
            if datetime.now() >= user.locked_until:
                # TIME IS UP → automatically unlock and reset counter
                user.locked_until = None
                user.failed_login_attempts = 0
                session.commit()
            else:
                # Still locked
                return {"locked": True, "locked_until": user.locked_until.isoformat()}

        # ──────────────────────── PASSWORD CHECK ────────────────────────
        if not verify_password(password, user.password):
            new_attempts = user.failed_login_attempts + 1
            
            if new_attempts >= MAX_LOGIN_ATTEMPTS:
                locked_until_dt = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                user.failed_login_attempts = new_attempts
                user.locked_until = locked_until_dt
                session.commit()
                log_action(user.id, "ACCOUNT_LOCKED", f"Locked after {new_attempts} fails")
                return {"locked": True, "locked_until": locked_until_dt.isoformat()}
            else:
                user.failed_login_attempts = new_attempts
                session.commit()
                log_action(user.id, "LOGIN_FAILED", f"Wrong password (attempt {new_attempts})")
            return None

        # ──────────────────────── SUCCESSFUL LOGIN ────────────────────────
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        session.commit()
        
        log_action(user.id, "LOGIN_SUCCESS", f"Successful login: {email}")
        return user.to_dict()
    finally:
        session.close()


def register_user(email: str, password: str, full_name: str, role: str = "customer"):
    session = Session()
    try:
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            return False, "Email already exists"
        
        hashed_password = hash_password(password)
        user = User(
            email=email,
            password=hashed_password,
            full_name=full_name,
            role=role
        )
        session.add(user)
        session.commit()
        
        log_action(user.id, "USER_REGISTERED", f"New user registered: {email}")
        return True, "User registered successfully"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


# ========== USER MANAGEMENT ==========
def get_user_by_id(user_id: int):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        return user.to_dict() if user else None
    finally:
        session.close()


def get_all_users():
    session = Session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        return [user.to_dict() for user in users]
    finally:
        session.close()


def create_user_by_admin(email: str, password: str, full_name: str, role: str, admin_id: int):
    session = Session()
    try:
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            return False, "Email already exists"

        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        hashed_password = hash_password(password)
        user = User(
            email=email,
            password=hashed_password,
            full_name=full_name,
            role=role
        )
        session.add(user)
        session.commit()
        
        log_action(admin_id, "USER_CREATED", f"Admin created user: {email} (role: {role})")
        return True, f"User {email} created successfully"
    except Exception as e:
        session.rollback()
        return False, f"Error: {str(e)}"
    finally:
        session.close()


def delete_user(user_id: int, admin_id: int):
    from models.models import Order
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False, "User not found"
        
        # Check if user has orders
        order_count = session.query(Order).filter_by(customer_id=user_id).count()
        if order_count > 0:
            return False, f"Cannot delete user. User has {order_count} order(s). Please deactivate the account instead."
        
        user_email = user.email
        session.delete(user)
        session.commit()
        
        log_action(admin_id, "USER_DELETED", f"Admin deleted user: {user_email}")
        return True, f"User {user_email} deleted successfully"
    except Exception as e:
        session.rollback()
        return False, f"Error deleting user: {str(e)}"
    finally:
        session.close()


def disable_user(user_id: int, admin_id: int):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.is_active = 0
            session.commit()
            log_action(admin_id, "USER_DISABLED", f"Admin disabled user ID: {user_id}")
    finally:
        session.close()


def enable_user(user_id: int, admin_id: int):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.is_active = 1
            session.commit()
            log_action(admin_id, "USER_ENABLED", f"Admin enabled user ID: {user_id}")
    finally:
        session.close()


# ========== RBAC ==========
def has_permission(user_role: str, permission: str) -> bool:
    permissions = {
        "admin": ["user_management", "menu_management", "order_management", "view_audit_logs", "system_settings"],
        "owner": ["menu_management", "order_management", "view_orders"],
        "customer": ["browse_menu", "place_order", "view_own_orders", "manage_profile"]
    }
    return permission in permissions.get(user_role, [])


# ========== PROFILE & PASSWORD ==========
def update_user_profile(caller_id: int, user_id: int, new_name, new_email, address=None, contact=None, profile_pic=None, pic_type=None):
    session = Session()
    try:
        caller = session.query(User).filter_by(id=caller_id).first()
        if not caller:
            return False, "Caller not found"
        
        if caller_id != user_id and caller.role != "admin":
            return False, "Unauthorized: Can only update own profile or as admin"
        
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False, "User not found"
        
        user.full_name = new_name
        user.email = new_email
        
        if address is not None:
            user.address = address
        if contact is not None:
            user.contact = contact
        if profile_pic is not None and pic_type is not None:
            user.profile_picture = profile_pic
            user.pic_type = pic_type
        
        session.commit()
        log_action(user_id, "PROFILE_UPDATED", "User updated profile")
        return True, "Profile updated!"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def change_password(user_id: int, old_password: str, new_password: str):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            return False, "User not found"
        
        if not verify_password(old_password, user.password):
            return False, "Current password is incorrect"
        
        user.password = hash_password(new_password)
        session.commit()
        
        log_action(user_id, "PASSWORD_CHANGED", "User changed password")
        return True, "Password changed successfully!"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
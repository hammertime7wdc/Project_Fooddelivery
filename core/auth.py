# core/auth.py (Refactored with SQLAlchemy)
import bcrypt
from datetime import datetime, timedelta
from models.models import Session, User, PendingSignup
from .database import log_action
from .email_sender import get_email_sender
from .auth_login import authenticate_user_impl
import hashlib
import secrets
import math
from sqlalchemy import func

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 1
VERIFICATION_TOKEN_EXPIRY_MINUTES = 10
VERIFICATION_RESEND_COOLDOWN_SECONDS = 15
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 10
PASSWORD_RESET_RESEND_COOLDOWN_SECONDS = 60


# ========== PASSWORD FUNCTIONS ==========
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_otp_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


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
    return authenticate_user_impl(
        email=email,
        password=password,
        verify_password_func=verify_password,
        max_login_attempts=MAX_LOGIN_ATTEMPTS,
        lockout_duration_minutes=LOCKOUT_DURATION_MINUTES,
    )


def register_user(email: str, password: str, full_name: str, role: str = "customer", require_verification: bool = True):
    session = Session()
    try:
        email = (email or "").strip().lower()
        existing = session.query(User).filter(func.lower(func.trim(User.email)) == email).first()
        if existing:
            return False, "Email already registered"

        hashed_password = hash_password(password)

        if require_verification:
            email_sender = get_email_sender()
            if not email_sender.is_configured():
                return False, "Email service is not configured"

            now = datetime.now()
            token = _generate_otp_code()

            sent, send_msg = email_sender.send_verification_email(
                to_email=email,
                full_name=full_name,
                token=token,
                expiry_minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES,
            )
            if not sent:
                log_action(None, "SIGNUP_VERIFICATION_EMAIL_FAILED", f"Email: {email} | Reason: {send_msg}")
                return False, f"Failed to send verification email: {send_msg}"

            existing_pending = session.query(PendingSignup).filter(func.lower(func.trim(PendingSignup.email)) == email).first()
            if existing_pending:
                existing_pending.password_hash = hashed_password
                existing_pending.full_name = full_name
                existing_pending.role = role
                existing_pending.verification_token_hash = _hash_token(token)
                existing_pending.verification_token_expires_at = now + timedelta(minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES)
                existing_pending.verification_sent_at = now
                existing_pending.created_at = now
            else:
                pending = PendingSignup(
                    email=email,
                    password_hash=hashed_password,
                    full_name=full_name,
                    role=role,
                    verification_token_hash=_hash_token(token),
                    verification_token_expires_at=now + timedelta(minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES),
                    verification_sent_at=now,
                    created_at=now,
                )
                session.add(pending)

            session.commit()
            return True, "Verification code sent. Please check your email."

        user = User(
            email=email,
            password=hashed_password,
            email_verified=1,
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
            user.failed_login_attempts = 0
            user.locked_until = None
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


def verify_current_password(user_id: int, current_password: str):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id, is_active=1).first()
        if not user:
            return False, "User not found"
        if not verify_password((current_password or "").strip(), user.password):
            return False, "Current password is incorrect"
        return True, "Current password verified"
    finally:
        session.close()


def request_password_reset_code(email: str, is_resend: bool = False):
    session = Session()
    try:
        valid_email, msg = validate_email(email)
        if not valid_email:
            return False, msg

        user = session.query(User).filter_by(email=email, is_active=1).first()
        if not user:
            return False, "No account found with this email"

        email_sender = get_email_sender()
        if not email_sender.is_configured():
            return False, "Email service is not configured"

        now = datetime.now()
        resend_count = int(getattr(user, "reset_resend_count", 0) or 0)

        has_active_reset_flow = bool(
            user.reset_token_hash
            and user.reset_token_expires_at
            and now <= user.reset_token_expires_at
        )

        if not has_active_reset_flow:
            resend_count = 0

        if is_resend and has_active_reset_flow and resend_count > 0 and user.reset_sent_at:
            elapsed = (now - user.reset_sent_at).total_seconds()
            if elapsed < PASSWORD_RESET_RESEND_COOLDOWN_SECONDS:
                remaining = max(1, math.ceil(PASSWORD_RESET_RESEND_COOLDOWN_SECONDS - elapsed))
                return False, f"Please wait {remaining}s before requesting another code"

        token = _generate_otp_code()
        user.reset_token_hash = _hash_token(token)
        user.reset_token_expires_at = now + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
        user.reset_sent_at = now
        if is_resend:
            user.reset_resend_count = resend_count + 1 if has_active_reset_flow else 1
        else:
            user.reset_resend_count = 0
        session.commit()

        sent, send_msg = email_sender.send_password_reset_email(
            to_email=user.email,
            full_name=user.full_name,
            token=token,
            expiry_minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES,
        )
        if not sent:
            return False, f"Failed to send reset email: {send_msg}"

        return True, "Reset code sent. Please check your email."
    except Exception:
        session.rollback()
        return False, "Failed to request reset code"
    finally:
        session.close()


def reset_password_with_code(email: str, code: str, new_password: str):
    session = Session()
    try:
        valid_email, msg = validate_email(email)
        if not valid_email:
            return False, msg

        valid_password, pwd_msg = validate_password(new_password)
        if not valid_password:
            return False, pwd_msg

        user = session.query(User).filter_by(email=email, is_active=1).first()
        if not user:
            return False, "No account found with this email"

        if not user.reset_token_hash or not user.reset_token_expires_at:
            return False, "No code has been requested. Please request a new reset code."

        if datetime.now() > user.reset_token_expires_at:
            return False, "Verification code has expired. Please request a new code."

        if _hash_token(code.strip()) != user.reset_token_hash:
            return False, "Incorrect verification code. Please check and try again."

        user.password = hash_password(new_password)
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        user.reset_sent_at = None
        user.reset_resend_count = 0
        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()

        log_action(user.id, "PASSWORD_RESET", "User reset password using OTP")
        return True, "Password reset successful. You can now log in."
    except Exception:
        session.rollback()
        return False, "Failed to reset password"
    finally:
        session.close()


def verify_signup_code(email: str, code: str):
    session = Session()
    try:
        email = (email or "").strip().lower()
        pending = session.query(PendingSignup).filter(func.lower(func.trim(PendingSignup.email)) == email).first()

        if pending:
            if datetime.now() > pending.verification_token_expires_at:
                return False, "Verification code has expired. Please request a new code."

            if _hash_token(code.strip()) != pending.verification_token_hash:
                return False, "Incorrect verification code. Please check and try again."

            existing_user = session.query(User).filter(func.lower(func.trim(User.email)) == email, User.is_active == 1).first()
            if existing_user:
                session.delete(pending)
                session.commit()
                return True, "Email already verified"

            user = User(
                email=email,
                password=pending.password_hash,
                email_verified=1,
                full_name=pending.full_name,
                role=pending.role,
            )
            session.add(user)
            session.delete(pending)
            session.commit()

            log_action(user.id, "EMAIL_VERIFIED", f"Email verified and account created: {email}")
            return True, "Email verified successfully."

        user = session.query(User).filter_by(email=email, is_active=1).first()
        if not user:
            return False, "No signup request found for this email"

        if getattr(user, "email_verified", 1) == 1:
            return True, "Email already verified"

        if not user.verification_token_hash or not user.verification_token_expires_at:
            return False, "No verification code has been sent."

        if datetime.now() > user.verification_token_expires_at:
            return False, "Verification code has expired. Please request a new code."

        if _hash_token(code.strip()) != user.verification_token_hash:
            return False, "Incorrect verification code. Please check and try again."

        user.email_verified = 1
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        user.verification_sent_at = None
        session.commit()

        log_action(user.id, "EMAIL_VERIFIED", f"Email verified: {email}")
        return True, "Email verified successfully."
    except Exception:
        session.rollback()
        return False, "Failed to verify code"
    finally:
        session.close()


def resend_signup_code(email: str):
    session = Session()
    try:
        email = (email or "").strip().lower()
        pending = session.query(PendingSignup).filter(func.lower(func.trim(PendingSignup.email)) == email).first()

        if pending:
            email_sender = get_email_sender()
            if not email_sender.is_configured():
                log_action(None, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: Email service not configured")
                return False, "Email service is not configured"

            now = datetime.now()
            # Allow first resend immediately after signup; enforce cooldown only between resend attempts.
            # register_user sets created_at and verification_sent_at to the same timestamp for initial send.
            if pending.verification_sent_at and pending.created_at and pending.verification_sent_at > pending.created_at:
                elapsed = (now - pending.verification_sent_at).total_seconds()
                if elapsed < VERIFICATION_RESEND_COOLDOWN_SECONDS:
                    remaining = max(1, math.ceil(VERIFICATION_RESEND_COOLDOWN_SECONDS - elapsed))
                    log_action(None, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: Cooldown active ({remaining}s remaining)")
                    return False, f"Please wait {remaining}s before requesting another code"

            token = _generate_otp_code()
            pending.verification_token_hash = _hash_token(token)
            pending.verification_token_expires_at = now + timedelta(minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES)
            pending.verification_sent_at = now
            session.commit()

            sent, send_msg = email_sender.send_verification_email(
                to_email=pending.email,
                full_name=pending.full_name,
                token=token,
                expiry_minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES,
            )
            if not sent:
                log_action(None, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: {send_msg}")
                return False, f"Failed to resend verification email: {send_msg}"

            log_action(None, "SIGNUP_VERIFICATION_RESENT", f"Verification code resent: {email}")
            return True, "Verification code resent. Please check your email."

        user = session.query(User).filter_by(email=email, is_active=1).first()
        if not user:
            log_action(None, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: No signup request found")
            return False, "No signup request found for this email"

        if getattr(user, "email_verified", 1) == 1:
            return True, "Email already verified"

        email_sender = get_email_sender()
        if not email_sender.is_configured():
            log_action(user.id, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: Email service not configured")
            return False, "Email service is not configured"

        now = datetime.now()
        if user.verification_sent_at:
            elapsed = (now - user.verification_sent_at).total_seconds()
            if elapsed < VERIFICATION_RESEND_COOLDOWN_SECONDS:
                remaining = max(1, math.ceil(VERIFICATION_RESEND_COOLDOWN_SECONDS - elapsed))
                log_action(user.id, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: Cooldown active ({remaining}s remaining)")
                return False, f"Please wait {remaining}s before requesting another code"

        token = _generate_otp_code()
        user.verification_token_hash = _hash_token(token)
        user.verification_token_expires_at = now + timedelta(minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES)
        user.verification_sent_at = now
        session.commit()

        sent, send_msg = email_sender.send_verification_email(
            to_email=user.email,
            full_name=user.full_name,
            token=token,
            expiry_minutes=VERIFICATION_TOKEN_EXPIRY_MINUTES,
        )
        if not sent:
            log_action(user.id, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: {send_msg}")
            return False, f"Failed to resend verification email: {send_msg}"

        log_action(user.id, "SIGNUP_VERIFICATION_RESENT", f"Verification code resent: {email}")
        return True, "Verification code resent. Please check your email."
    except Exception:
        session.rollback()
        log_action(None, "SIGNUP_VERIFICATION_RESEND_FAILED", f"Email: {email} | Reason: Unexpected error")
        return False, "Failed to resend verification code"
    finally:
        session.close()
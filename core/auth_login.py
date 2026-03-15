from datetime import datetime, timedelta

from sqlalchemy import func

from models.models import Session, User
from .database import log_action


def authenticate_user_impl(
    email: str,
    password: str,
    verify_password_func,
    max_login_attempts: int,
    lockout_duration_minutes: int,
):
    """Authenticate user with lockout and disabled-account handling.

    Security behavior:
    - Unknown email and wrong password both return None (generic failure)
    - Disabled account is only revealed after successful password verification
    """
    session = Session()
    try:
        normalized_email = (email or "").strip().lower()
        user = session.query(User).filter(func.lower(func.trim(User.email)) == normalized_email).first()

        if not user:
            log_action(None, "LOGIN_FAILED", f"User not found: {normalized_email}")
            return None

        # Disabled accounts should never surface as locked. To avoid user enumeration,
        # still verify the password first; only a correct password reveals disabled state.
        if not bool(user.is_active):
            if not verify_password_func(password, user.password):
                log_action(user.id, "LOGIN_FAILED", "Wrong password on disabled account")
                return None

            log_action(user.id, "LOGIN_BLOCKED_DISABLED", f"Disabled account login blocked: {normalized_email}")
            return {"disabled": True}

        if user.locked_until:
            if datetime.now() >= user.locked_until:
                user.locked_until = None
                user.failed_login_attempts = 0
                session.commit()
            else:
                return {"locked": True, "locked_until": user.locked_until.isoformat()}

        if not verify_password_func(password, user.password):
            new_attempts = (user.failed_login_attempts or 0) + 1

            if new_attempts >= max_login_attempts:
                locked_until_dt = datetime.now() + timedelta(minutes=lockout_duration_minutes)
                user.failed_login_attempts = new_attempts
                user.locked_until = locked_until_dt
                session.commit()
                log_action(user.id, "ACCOUNT_LOCKED", f"Locked after {new_attempts} fails")
                return {"locked": True, "locked_until": locked_until_dt.isoformat()}

            user.failed_login_attempts = new_attempts
            session.commit()
            log_action(user.id, "LOGIN_FAILED", f"Wrong password (attempt {new_attempts})")
            return None

        if getattr(user, "email_verified", 1) == 0:
            return {"unverified": True, "email": user.email}

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
        session.commit()

        log_action(user.id, "LOGIN_SUCCESS", f"Successful login: {normalized_email}")
        return user.to_dict()
    finally:
        session.close()

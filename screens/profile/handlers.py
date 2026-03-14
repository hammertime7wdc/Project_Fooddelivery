"""Profile handlers for profile updates, password changes, and file uploads"""
import flet as ft
import uuid
import os
import imghdr
import time
from core.phone_utils import normalize_ph_to_e164
from core.auth import (
    get_user_by_id,
    update_user_profile,
    change_password,
    validate_password,
    validate_full_name,
    validate_email,
    get_password_strength,
    request_password_reset_code,
    reset_password_with_code,
    verify_current_password,
)
from core.cloudinary_storage import upload_profile_image
from utils import show_snackbar
from .loading_screen import show_loading, hide_loading


PROFILE_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "uploads",
)


def _set_profile_preview(profile_pic_preview, image_data, image_type):
    if image_type == "url":
        profile_pic_preview.content = ft.Image(
            src=image_data,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(75),
        )
    elif image_type == "base64":
        profile_pic_preview.content = ft.Image(
            src_base64=image_data,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(75),
        )
    else:
        profile_pic_preview.content = ft.Icon(ft.Icons.PERSON, size=120, color="grey")


def _resolve_pending_upload_path(file_name, pending_uploads):
    file_path = pending_uploads.pop(file_name, None)
    if file_path:
        return file_path

    if len(pending_uploads) == 1:
        _, only_path = pending_uploads.popitem()
        return only_path

    fallback_path = os.path.join(PROFILE_UPLOAD_DIR, file_name.replace("/", os.sep))
    if os.path.exists(fallback_path):
        return fallback_path

    return None


def finalize_profile_upload(file_path, profile_pic_preview, uploaded_pic, page, upload_state):
    detected_type = imghdr.what(file_path)
    if detected_type not in ("jpeg", "png", "gif"):
        upload_state["in_progress"] = False
        show_snackbar(page, "Invalid image file", error=True)
        return

    success, image_url, error_message = upload_profile_image(file_path)
    if not success:
        upload_state["in_progress"] = False
        print(error_message)
        show_snackbar(page, f"Cloud upload failed: {error_message}", error=True)
        return

    uploaded_pic["data"] = image_url
    uploaded_pic["type"] = "url"
    upload_state["in_progress"] = False
    _set_profile_preview(profile_pic_preview, image_url, "url")
    show_snackbar(page, "Profile picture uploaded!", success=True)
    page.update()


def handle_pic_upload_progress(e, profile_pic_preview, uploaded_pic, page, upload_state, pending_uploads):
    if e.error:
        file_path = _resolve_pending_upload_path(e.file_name, pending_uploads)
        upload_state["in_progress"] = False
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        show_snackbar(page, f"Upload failed: {e.error}", error=True)
        return

    if e.progress is None or e.progress < 1.0:
        return

    file_path = _resolve_pending_upload_path(e.file_name, pending_uploads)
    if not file_path or not os.path.exists(file_path):
        upload_state["in_progress"] = False
        show_snackbar(page, "Uploaded file could not be found on server.", error=True)
        return

    try:
        finalize_profile_upload(file_path, profile_pic_preview, uploaded_pic, page, upload_state)
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


def update_password_strength(password, password_strength_bar, password_strength_text, page, new_password_field=None, password_error=None):
    """Update password strength indicator"""
    # Validate password field first (like signup.py)
    if new_password_field and password_error:
        from core.auth import validate_password
        from utils import FIELD_BORDER
        if not password:
            password_error.visible = False
            new_password_field.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                password_error.value = error_msg
                password_error.visible = True
                new_password_field.border_color = "red"
            else:
                password_error.visible = False
                new_password_field.border_color = "green"
    
    if not password:
        password_strength_bar.value = 0
        password_strength_bar.color = "grey"
        password_strength_bar.visible = False
        password_strength_text.value = ""
        password_strength_text.color = "grey"
        password_strength_text.visible = False
    else:
        password_strength_bar.visible = True
        password_strength_text.visible = True
        strength, score = get_password_strength(password)
        password_strength_bar.value = score / 100
        
        # Color coding
        if strength == 'weak':
            password_strength_bar.color = "red"
            password_strength_text.color = "red"
        elif strength == 'medium':
            password_strength_bar.color = "orange"
            password_strength_text.color = "orange"
        elif strength == 'strong':
            password_strength_bar.color = "yellow"
            password_strength_text.color = "yellow"
        else:  # very strong
            password_strength_bar.color = "green"
            password_strength_text.color = "green"
        
        password_strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
    
    page.update()


def save_profile_picture(page, current_user, uploaded_pic, upload_state=None):
    """Save only the profile picture"""
    from core.auth import update_user_profile

    if upload_state and upload_state.get("in_progress"):
        show_snackbar(page, "Please wait for the upload to finish before saving.", error=True)
        return
    
    if not uploaded_pic["data"]:
        show_snackbar(page, "Please select a picture first", error=True)
        return
    
    loading = show_loading(page, "Saving picture...")
    
    async def _save_task():
        try:
            # Get current user data
            user = get_user_by_id(current_user["user"]["id"])
            if not user:
                hide_loading(page, loading)
                show_snackbar(page, "User not found", error=True)
                return
            
            # Update only the profile picture
            success, msg = update_user_profile(
                caller_id=current_user["user"]["id"],
                user_id=current_user["user"]["id"],
                new_name=user["full_name"],
                new_email=user["email"],
                address=user.get("address"),
                contact=user.get("contact"),
                profile_pic=uploaded_pic["data"],
                pic_type=uploaded_pic["type"]
            )
            
            hide_loading(page, loading)
            
            if success:
                # Update current user session
                current_user["user"]["profile_picture"] = uploaded_pic["data"]
                current_user["user"]["pic_type"] = uploaded_pic["type"]
                show_snackbar(page, "Profile picture saved successfully!", success=True)
            else:
                show_snackbar(page, f"Error: {msg}", error=True)
        except Exception as e:
            hide_loading(page, loading)
            show_snackbar(page, f"Error saving picture: {str(e)}", error=True)
    
    # Run task asynchronously
    page.run_task(_save_task)


def handle_pic_pick(e, current_user, profile_pic_preview, uploaded_pic, page, file_picker=None, upload_state=None, pending_uploads=None):
    """Handle profile picture file selection and upload"""
    if not e.files:
        return

    file = e.files[0]

    if file.size > 3145728:
        show_snackbar(page, "Image size must be under 3MB", error=True)
        return
    if not file.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        show_snackbar(page, "Only JPG, PNG, GIF allowed", error=True)
        return

    if not getattr(file, "path", None):
        if file_picker is None or upload_state is None or pending_uploads is None:
            show_snackbar(page, "Browser upload is not available right now.", error=True)
            return

        file_extension = os.path.splitext(file.name)[1].lower()
        server_name = f"profile_{current_user['user']['id']}_{uuid.uuid4().hex}{file_extension}"
        server_path = os.path.join(PROFILE_UPLOAD_DIR, server_name)
        pending_uploads[file.name] = server_path
        pending_uploads[server_name] = server_path
        upload_state["in_progress"] = True
        upload_url = page.get_upload_url(server_name, 600)
        file_picker.upload([
            ft.FilePickerUploadFile(name=file.name, upload_url=upload_url)
        ])
        show_snackbar(page, "Uploading profile picture to Cloudinary...")
        return

    if not os.path.exists(file.path):
        show_snackbar(page, "Selected file is not accessible.", error=True)
        return

    finalize_profile_upload(file.path, profile_pic_preview, uploaded_pic, page, upload_state or {"in_progress": False})


def save_profile(page, current_user, name_field, email_field, address_field, contact_field, 
                 name_error, uploaded_pic, back_callback, upload_state=None):
    """Save profile changes"""
    if upload_state and upload_state.get("in_progress"):
        show_snackbar(page, "Please wait for the upload to finish before saving.", error=True)
        return

    has_error = False
    
    valid, msg = validate_full_name(name_field.value)
    if not valid:
        name_error.value = msg
        name_error.visible = True
        name_field.border_color = "red"
        has_error = True
    else:
        name_error.visible = False
        name_field.border_color = "green"
    
    if has_error:
        page.update()
        return
    
    normalized_contact = None
    if contact_field.value and len(contact_field.value.strip()) > 0:
        normalized_contact = normalize_ph_to_e164(contact_field.value)
        if not normalized_contact:
            show_snackbar(page, "Invalid PH mobile number. Use 9XXXXXXXXX.")
            return
    
    loading = show_loading(page, "Saving profile...")
    
    async def _save_task():
        user = get_user_by_id(current_user["user"]["id"])
        if not user:
            hide_loading(page, loading)
            show_snackbar(page, "User not found", error=True)
            return

        success, msg = update_user_profile(
            current_user["user"]["id"],
            current_user["user"]["id"],
            name_field.value.strip(),
            user["email"],
            address=address_field.value.strip() if address_field.value else None,
            contact=normalized_contact,
            profile_pic=uploaded_pic["data"],
            pic_type=uploaded_pic["type"]
        )
        
        hide_loading(page, loading)
        show_snackbar(page, msg)
        
        if success:
            current_user["user"]["full_name"] = name_field.value.strip()
            current_user["user"]["email"] = user["email"]
            current_user["user"]["address"] = address_field.value.strip() if address_field.value else None
            current_user["user"]["contact"] = normalized_contact
            current_user["user"]["profile_picture"] = uploaded_pic["data"]
            current_user["user"]["pic_type"] = uploaded_pic["type"]
            
            name_error.value = ""
            name_error.visible = False
            page.update()
    
    # Run save operation asynchronously
    page.run_task(_save_task)

def change_password_handler(page, current_user, current_password, new_password, confirm_password,
                           password_strength_bar, password_strength_text):
    """Handle password change"""
    if not current_password.value or not new_password.value or not confirm_password.value:
        show_snackbar(page, "Fill all password fields")
        return
    
    valid, msg = validate_password(new_password.value)
    if not valid:
        show_snackbar(page, msg)
        return
    
    if new_password.value != confirm_password.value:
        show_snackbar(page, "New passwords don't match")
        return
    
    if current_password.value == new_password.value:
        show_snackbar(page, "New password must be different from current password")
        return
    
    loading = show_loading(page, "Updating password...")
    
    async def _change_task():
        success, msg = change_password(
            current_user["user"]["id"],
            current_password.value,
            new_password.value
        )
        
        hide_loading(page, loading)
        show_snackbar(page, msg)
        
        if success:
            current_password.value = ""
            new_password.value = ""
            confirm_password.value = ""
            password_strength_bar.value = 0
            password_strength_bar.color = "grey"
            password_strength_text.value = ""
            password_strength_text.color = "grey"
            page.update()
    
    # Run password change asynchronously
    page.run_task(_change_task)


def send_profile_reset_code_handler(
    page,
    current_user,
    current_password,
    new_password,
    confirm_password,
    code_field,
    code_info_text,
    verify_button,
    resend_button,
    is_resend=False,
):
    """Send OTP reset code after validating current password and new password fields."""
    validation_error_message = "Please complete all required fields with valid data before sending a code."

    def clear_field_error(field):
        field.error_text = None
        field.border_color = "#b5a89a"
        field.border_width = 1

    def set_field_error(field, message: str):
        field.error_text = message
        field.border_color = "#FF0000"
        field.border_width = 2

    user_id = current_user.get("user", {}).get("id")
    email_value = (current_user.get("user", {}).get("email") or "").strip().lower()
    current_password_value = (current_password.value or "").strip()
    new_password_value = (new_password.value or "").strip()
    confirm_password_value = (confirm_password.value or "").strip()

    for field in (current_password, new_password, confirm_password):
        clear_field_error(field)
    page.update()

    if not user_id:
        show_snackbar(page, "User not found", error=True)
        return False, "User not found"

    if not email_value:
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    if not current_password_value:
        set_field_error(current_password, "Please enter your current password")
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    if not new_password_value or not confirm_password_value:
        if not new_password_value:
            set_field_error(new_password, "Please enter a new password")
        if not confirm_password_value:
            set_field_error(confirm_password, "Please confirm your new password")
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    valid_password, pwd_msg = validate_password(new_password_value)
    if not valid_password:
        set_field_error(new_password, pwd_msg)
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    if new_password_value != confirm_password_value:
        set_field_error(confirm_password, "Passwords do not match")
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    if current_password_value == new_password_value:
        set_field_error(new_password, "Must be different from current password")
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    verified, verify_msg = verify_current_password(user_id, current_password_value)
    if not verified:
        set_field_error(current_password, verify_msg)
        page.update()
        show_snackbar(page, validation_error_message, error=True)
        return False, validation_error_message

    success, msg = request_password_reset_code(email_value, is_resend=is_resend)
    if success:
        clear_field_error(current_password)
        clear_field_error(new_password)
        clear_field_error(confirm_password)
        code_field.visible = True
        code_info_text.value = f"Code sent to {email_value}. Expires in 10 minutes."
        code_info_text.visible = True
        verify_button.visible = True
        resend_button.visible = True
        show_snackbar(page, msg, success=True)
    else:
        show_snackbar(page, msg, error=True)

    page.update()
    return success, msg


def reset_password_with_profile_code_handler(
    page,
    current_user,
    current_password,
    code_field,
    new_password,
    confirm_password,
    password_strength_bar,
    password_strength_text,
    code_info_text,
    verify_button,
    resend_button,
):
    """Reset password from profile screen using current password + OTP flow."""
    user_id = current_user.get("user", {}).get("id")
    email_value = (current_user.get("user", {}).get("email") or "").strip().lower()
    current_password_value = (current_password.value or "").strip()
    code_value = (code_field.value or "").strip()
    new_password_value = (new_password.value or "").strip()
    confirm_password_value = (confirm_password.value or "").strip()

    if not user_id:
        show_snackbar(page, "User not found", error=True)
        return

    if not email_value:
        show_snackbar(page, "No email found for this account", error=True)
        return

    if not current_password_value:
        show_snackbar(page, "Please enter your current password", error=True)
        return

    if len(code_value) != 6 or not code_value.isdigit():
        show_snackbar(page, "Please enter a valid 6-digit code", error=True)
        return

    valid_password, pwd_msg = validate_password(new_password_value)
    if not valid_password:
        show_snackbar(page, pwd_msg, error=True)
        return

    if new_password_value != confirm_password_value:
        show_snackbar(page, "Passwords do not match", error=True)
        return

    if current_password_value == new_password_value:
        show_snackbar(page, "New password must be different from current password", error=True)
        return

    verified, verify_msg = verify_current_password(user_id, current_password_value)
    if not verified:
        show_snackbar(page, verify_msg, error=True)
        return

    success, msg = reset_password_with_code(email_value, code_value, new_password_value)
    if success:
        show_snackbar(page, "Password reset successful!", success=True)
        code_field.error_text = None
        code_field.border_color = "green"
        code_field.border_width = 1
        code_field.value = ""
        new_password.value = ""
        confirm_password.value = ""
        code_info_text.visible = False
        code_info_text.value = ""
        code_field.visible = False
        verify_button.visible = False
        resend_button.visible = False
        password_strength_bar.value = 0
        password_strength_bar.color = "grey"
        password_strength_bar.visible = False
        password_strength_text.value = ""
        password_strength_text.color = "grey"
        password_strength_text.visible = False
    else:
        short_msg = msg
        if "No account found" in msg:
            short_msg = "Account not found"
        elif "No code has been requested" in msg:
            short_msg = "No code sent"
        elif "expired" in msg.lower():
            short_msg = "Code expired"
        elif "Incorrect" in msg:
            short_msg = "Wrong code"

        code_field.error_text = short_msg
        code_field.border_color = "red"
        code_field.border_width = 2
        show_snackbar(page, msg, error=True)

    page.update()

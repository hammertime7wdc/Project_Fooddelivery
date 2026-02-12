"""Profile handlers for profile updates, password changes, and file uploads"""
import re
import uuid
import shutil
import os
import imghdr
import time
from core.auth import get_user_by_id, update_user_profile, change_password, validate_password, validate_full_name, validate_email, get_password_strength
from utils import show_snackbar
from .loading_screen import show_loading, hide_loading


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


def save_profile_picture(page, current_user, uploaded_pic):
    """Save only the profile picture"""
    from core.auth import update_user_profile
    
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
                show_snackbar(page, "Profile picture saved successfully!", bgcolor="green")
            else:
                show_snackbar(page, f"Error: {msg}", error=True)
        except Exception as e:
            hide_loading(page, loading)
            show_snackbar(page, f"Error saving picture: {str(e)}", error=True)
    
    # Run task asynchronously
    page.run_task(_save_task)


def handle_pic_pick(e, current_user, profile_pic_preview, uploaded_pic, page):
    """Handle profile picture file selection and upload"""
    from flet import FilePickerResultEvent
    
    if e.files:
        file = e.files[0]
        
        # Check if file path exists
        if not file or not file.path:
            show_snackbar(page, "File not found")
            return
            
        if file.size > 1048576:
            show_snackbar(page, "Image size must be under 1MB")
            return
        if not file.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            show_snackbar(page, "Only JPG, PNG, GIF allowed")
            return

        # Check file type
        try:
            detected_type = imghdr.what(file.path)
            if detected_type not in ("jpeg", "png", "gif"):
                show_snackbar(page, "Invalid image file")
                return
        except:
            show_snackbar(page, "Could not verify image file")
            return
            
        try:
            import flet as ft
            # Generate unique filename for profile picture
            user_id = current_user["user"]["id"]
            file_ext = os.path.splitext(file.name)[1].lower()
            unique_filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
            
            # Copy file to assets/profiles/
            profiles_dir = "assets/profiles"
            os.makedirs(profiles_dir, exist_ok=True)
            dest_path = os.path.join(profiles_dir, unique_filename)
            shutil.copy(file.path, dest_path)
            
            # Store only filename in database (file-based approach)
            uploaded_pic["data"] = unique_filename
            uploaded_pic["type"] = "path"
            
            # Update preview to show file path
            profile_pic_preview.content = ft.Image(
                src=dest_path,
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(75)
            )
            show_snackbar(page, "Profile picture uploaded!")
            page.update()
        except Exception as ex:
            print(f"Profile upload error: {ex}")
            show_snackbar(page, "Upload failed. Please try another image.")


def save_profile(page, current_user, name_field, email_field, address_field, contact_field, 
                 name_error, email_error, uploaded_pic, back_callback):
    """Save profile changes"""
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
    
    valid, msg = validate_email(email_field.value)
    if not valid:
        email_error.value = msg
        email_error.visible = True
        email_field.border_color = "red"
        has_error = True
    else:
        email_error.visible = False
        email_field.border_color = "green"
    
    if has_error:
        page.update()
        return
    
    if contact_field.value and len(contact_field.value) > 0:
        if not re.match(r'^[\d\s\-\+\(\)]+$', contact_field.value):
            show_snackbar(page, "Invalid contact number format")
            return
    
    loading = show_loading(page, "Saving profile...")
    
    async def _save_task():
        success, msg = update_user_profile(
            current_user["user"]["id"],
            current_user["user"]["id"],
            name_field.value.strip(),
            email_field.value.strip(),
            address=address_field.value.strip() if address_field.value else None,
            contact=contact_field.value.strip() if contact_field.value else None,
            profile_pic=uploaded_pic["data"],
            pic_type=uploaded_pic["type"]
        )
        
        hide_loading(page, loading)
        show_snackbar(page, msg)
        
        if success:
            current_user["user"]["full_name"] = name_field.value.strip()
            current_user["user"]["email"] = email_field.value.strip()
            current_user["user"]["address"] = address_field.value.strip() if address_field.value else None
            current_user["user"]["contact"] = contact_field.value.strip() if contact_field.value else None
            current_user["user"]["profile_picture"] = uploaded_pic["data"]
            current_user["user"]["pic_type"] = uploaded_pic["type"]
            
            name_error.value = ""
            name_error.visible = False
            email_error.value = ""
            email_error.visible = False
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

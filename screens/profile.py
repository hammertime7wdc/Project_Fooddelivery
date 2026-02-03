import flet as ft
import re
import uuid
import shutil
import os
import imghdr
from core.auth import get_user_by_id, update_user_profile, change_password, validate_email, validate_password, validate_full_name, get_password_strength
from utils import show_snackbar, create_profile_pic_widget, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def profile_screen(page: ft.Page, current_user: dict, cart: list, back_callback):
    user = get_user_by_id(current_user["user"]["id"])
    if not user:
        show_snackbar(page, "User not found")
        back_callback(None)
        return ft.Container()

    name_field = ft.TextField(
        label="Full Name", 
        value=user["full_name"], 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        max_length=100,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000"),
        on_change=lambda e: validate_name_field()
    )
    
    name_error = ft.Text("", size=11, color="red", visible=False)
    
    email_field = ft.TextField(
        label="Email", 
        value=user["email"], 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        max_length=254,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000"),
        on_change=lambda e: validate_email_field()
    )
    
    email_error = ft.Text("", size=11, color="red", visible=False)
    
    address_field = ft.TextField(
        label="Address", 
        value=user["address"] or "", 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000")
    )
    contact_field = ft.TextField(
        label="Contact", 
        value=user["contact"] or "", 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000")
    )

    current_password = ft.TextField(
        label="Current Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000")
    )
    
    password_strength_text = ft.Text("", size=12, color="grey")
    password_strength_bar = ft.ProgressBar(width=300, value=0, color="grey", bgcolor="#333")
    
    password_requirements = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.SECURITY, color="#000000", size=20),
            ft.Text(
                "Password Requirements:",
                size=12,
                weight=ft.FontWeight.BOLD,
                color="#000000"
            ),
            ft.Text(
                "• At least 8 characters\n"
                "• One uppercase letter (A-Z)\n"
                "• One lowercase letter (a-z)\n"
                "• One number (0-9)\n"
                "• One special character (!@#$%...)",
                size=10,
                color="#000000"
            )
        ]),
        padding=10,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        bgcolor="#EBE1D1",
        width=300
    )

    def update_password_strength(password):
        validate_password_field(password)
        
        if not password:
            password_strength_bar.value = 0
            password_strength_bar.color = "grey"
            password_strength_text.value = ""
            password_strength_text.color = "grey"
        else:
            strength, score = get_password_strength(password)
            password_strength_bar.value = score / 100
            
            if strength == 'weak':
                password_strength_bar.color = "red"
                password_strength_text.color = "red"
            elif strength == 'medium':
                password_strength_bar.color = "orange"
                password_strength_text.color = "orange"
            elif strength == 'strong':
                password_strength_bar.color = "yellow"
                password_strength_text.color = "yellow"
            else:
                password_strength_bar.color = "green"
                password_strength_text.color = "green"
            
            password_strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
        
        page.update()
    
    new_password = ft.TextField(
        label="New Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        max_length=128,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000"),
        on_change=lambda e: update_password_strength(e.control.value)
    )
    
    password_error = ft.Text("", size=11, color="red", visible=False)
    
    confirm_password = ft.TextField(
        label="Confirm New Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor="#EBE1D1",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        max_length=128,
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000")
    )
    
    # Real-time validation functions
    def validate_name_field():
        if not name_field.value or name_field.value.strip() == "":
            name_error.visible = False
            name_field.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_full_name(name_field.value)
            if not is_valid:
                name_error.value = error_msg
                name_error.visible = True
                name_field.border_color = "red"
            else:
                name_error.visible = False
                name_field.border_color = "green"
        page.update()
    
    def validate_email_field():
        if not email_field.value or email_field.value.strip() == "":
            email_error.visible = False
            email_field.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_email(email_field.value)
            if not is_valid:
                email_error.value = error_msg
                email_error.visible = True
                email_field.border_color = "red"
            else:
                email_error.visible = False
                email_field.border_color = "green"
        page.update()
    
    def validate_password_field(password):
        if not password:
            password_error.visible = False
            new_password.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                password_error.value = error_msg
                password_error.visible = True
                new_password.border_color = "red"
            else:
                password_error.visible = False
                new_password.border_color = "green"
        page.update()

    profile_pic_preview = ft.Container(
        content=create_profile_pic_widget(user, 150, 150),
        width=150,
        height=150,
        border=ft.border.all(2, FIELD_BORDER),
        border_radius=ft.border_radius.all(75),
        alignment=ft.alignment.center
    )

    uploaded_pic = {"data": user.get("profile_picture"), "type": user.get("pic_type") or "emoji"}

    def handle_pic_pick(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            if file.size > 1048576:
                show_snackbar(page, "Image size must be under 1MB")
                return
            if not file.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                show_snackbar(page, "Only JPG, PNG, GIF allowed")
                return

            detected_type = imghdr.what(file.path)
            if detected_type not in ("jpeg", "png", "gif"):
                show_snackbar(page, "Invalid image file")
                return
            try:
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

    file_picker = ft.FilePicker(on_result=handle_pic_pick)
    page.overlay.append(file_picker)

    def save_profile(e):
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
            
            back_callback(e)

    def change_pass(e):
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
        
        success, msg = change_password(
            current_user["user"]["id"],
            current_password.value,
            new_password.value
        )
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

    return ft.Container(
        content=ft.Column(
            [
                ft.TextButton("← Back", on_click=back_callback, style=ft.ButtonStyle(color=TEXT_DARK)),
                ft.Text("Profile Settings", size=24, weight=ft.FontWeight.BOLD, color=TEXT_DARK),

                profile_pic_preview,
                ft.ElevatedButton(
                    "Upload Profile Picture",
                    icon=ft.Icons.UPLOAD_FILE,
                    bgcolor=ACCENT_DARK,
                    color="#EBE1D1",
                    on_click=lambda _: file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "gif"],
                        dialog_title="Select Profile Picture"
                    )
                ),

                ft.Divider(color=FIELD_BORDER, height=20),

                ft.Text("Personal Information", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                name_field,
                name_error,
                ft.Container(height=5),
                email_field,
                email_error,
                ft.Container(height=5),
                address_field,
                contact_field,

                ft.ElevatedButton("Save Profile", bgcolor=ACCENT_DARK, color="#EBE1D1", on_click=save_profile),

                ft.Divider(color=FIELD_BORDER),

                ft.Text("Change Password", size=20, color=TEXT_DARK),
                password_requirements,
                current_password,
                new_password,
                password_error,
                password_strength_bar,
                password_strength_text,
                confirm_password,
                ft.ElevatedButton("Update Password", bgcolor=ACCENT_DARK, color="#EBE1D1", on_click=change_pass)
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True,
        padding=20,
        bgcolor="#EBE1D1"
    )
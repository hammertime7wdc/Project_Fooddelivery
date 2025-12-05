import flet as ft
import base64
from core.auth import get_user_by_id, update_user_profile, change_password
from utils import show_snackbar, create_profile_pic_widget, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def profile_screen(page: ft.Page, current_user: dict, cart: list, back_callback):
    user = get_user_by_id(current_user["user"]["id"])  # Refresh user data
    if not user:
        show_snackbar(page, "User not found")
        back_callback(None)

    name_field = ft.TextField(
        label="Full Name", 
        value=user["full_name"], 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    email_field = ft.TextField(
        label="Email", 
        value=user["email"], 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    address_field = ft.TextField(
        label="Address", 
        value=user["address"] or "", 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    contact_field = ft.TextField(
        label="Contact", 
        value=user["contact"] or "", 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )

    current_password = ft.TextField(
        label="Current Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    new_password = ft.TextField(
        label="New Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    confirm_password = ft.TextField(
        label="Confirm New Password", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )

    profile_pic_preview = ft.Container(
        content=create_profile_pic_widget(user, 150, 150),
        width=150,
        height=150,
        border=ft.border.all(2, "grey"),
        border_radius=ft.border_radius.all(75),
        alignment=ft.alignment.center
    )

    uploaded_pic = {"data": user.get("profile_picture"), "type": user.get("pic_type") or "emoji"}

    file_picker = ft.FilePicker(on_result=lambda e: handle_pic_pick(e))
    page.overlay.append(file_picker)

    def handle_pic_pick(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            if file.size > 1048576:  # 1MB limit
                show_snackbar(page, "Image size must be under 1MB")
                return
            if not file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                show_snackbar(page, "Only JPG, PNG, GIF allowed")
                return
            try:
                with open(file.path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                uploaded_pic["data"] = image_data
                uploaded_pic["type"] = "base64"
                profile_pic_preview.content = ft.Image(
                    src_base64=image_data,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(75)
                )
                show_snackbar(page, "Profile picture uploaded!")
                page.update()
            except Exception as ex:
                show_snackbar(page, f"Error: {str(ex)}")

    def save_profile(e):
        if not name_field.value or not email_field.value:
            show_snackbar(page, "Name and email required")
            return
        success, msg = update_user_profile(
            current_user["user"]["id"],
            current_user["user"]["id"],
            name_field.value,
            email_field.value,
            address=address_field.value,
            contact=contact_field.value,
            profile_pic=uploaded_pic["data"],
            pic_type=uploaded_pic["type"]
        )
        show_snackbar(page, msg)
        if success:
            # Update the current_user dictionary with new values
            current_user["user"]["full_name"] = name_field.value
            current_user["user"]["email"] = email_field.value
            current_user["user"]["address"] = address_field.value
            current_user["user"]["contact"] = contact_field.value
            current_user["user"]["profile_picture"] = uploaded_pic["data"]
            current_user["user"]["pic_type"] = uploaded_pic["type"]
            
            back_callback(e)

    def change_pass(e):
        if not current_password.value or not new_password.value or not confirm_password.value:
            show_snackbar(page, "Fill all password fields")
            return
        if new_password.value != confirm_password.value:
            show_snackbar(page, "New passwords don't match")
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
            page.update()

    return ft.Container(
        content=ft.Column(
            [
                ft.TextButton("← Back", on_click=back_callback, style=ft.ButtonStyle(color=TEXT_LIGHT)),
                ft.Text("Profile Settings", size=24, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),

                profile_pic_preview,
                ft.ElevatedButton(
                    "Upload Profile Picture",
                    icon=ft.Icons.UPLOAD_FILE,
                    bgcolor=ACCENT_DARK,
                    color=TEXT_LIGHT,
                    on_click=lambda _: file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "gif"],
                        dialog_title="Select Profile Picture"
                    )
                ),

                name_field,
                email_field,
                address_field,
                contact_field,

                ft.ElevatedButton("Save Profile", bgcolor=ACCENT_DARK, color=TEXT_LIGHT, on_click=save_profile),

                ft.Divider(color="grey"),

                ft.Text("Change Password", size=20, color=TEXT_LIGHT),
                current_password,
                new_password,
                confirm_password,
                ft.ElevatedButton("Update Password", bgcolor=ACCENT_DARK, color=TEXT_LIGHT, on_click=change_pass)
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True,
        padding=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
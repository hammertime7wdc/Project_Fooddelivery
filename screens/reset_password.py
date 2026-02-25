import flet as ft
from core.auth import request_password_reset_code, reset_password_with_code, validate_password, get_password_strength, validate_email
from core.image_utils import get_base64_image
from utils import show_snackbar, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE

def reset_password_screen(page: ft.Page, current_user: dict, cart: list, goto_login):
    state = {"code_sent": False}

    email_field = ft.TextField(
        label="Enter your email",
        prefix_icon=ft.Icons.EMAIL,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        error_style=ft.TextStyle(color="#FF0000", size=12),
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK)
    )

    email_error = ft.Text("", size=11, color="red", visible=False)

    code_field = ft.TextField(
        label="Verification code",
        hint_text="Enter 6-digit code",
        prefix_icon=ft.Icons.VERIFIED_USER,
        width=300,
        max_length=6,
        text_align=ft.TextAlign.CENTER,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        error_style=ft.TextStyle(color="#FF0000", size=12),
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        visible=False,
    )

    new_password_field = ft.TextField(
        label="New password",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        error_style=ft.TextStyle(color="#FF0000", size=12),
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        visible=False,
    )

    password_strength_bar = ft.ProgressBar(width=300, value=0, color="grey", bgcolor="white", visible=False)
    password_strength_text = ft.Text("", size=12, color="grey", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)

    confirm_password_field = ft.TextField(
        label="Confirm new password",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        error_style=ft.TextStyle(color="#FF0000", size=12),
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        visible=False,
    )

    code_info_text = ft.Text("", size=12, color=DARK_GREEN, text_align=ft.TextAlign.CENTER, visible=False)

    send_code_button = ft.ElevatedButton(
        "Send reset code",
        width=300,
        height=46,
        bgcolor=ACCENT_DARK,
        color=CREAM,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=None,
    )

    reset_button = ft.ElevatedButton(
        "Verify code & reset password",
        width=300,
        height=46,
        bgcolor=ORANGE,
        color=CREAM,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        visible=False,
        on_click=None,
    )

    resend_button = ft.TextButton(
        "Resend code",
        visible=False,
        style=ft.ButtonStyle(color=DARK_GREEN),
        on_click=None,
    )

    def clear_field_error(field):
        field.border_color = FIELD_BORDER
        field.error_text = None
        field.border_width = 1

    def reset_field_errors():
        for field in (email_field, code_field, new_password_field, confirm_password_field):
            clear_field_error(field)
        page.update()

    def set_field_error(field, message: str):
        field.border_color = "#FF0000"
        field.error_text = message
        field.border_width = 2
        page.update()

    def update_strength(password):
        """Update password strength indicator and validation"""
        if not password:
            password_error.visible = False
            new_password_field.border_color = FIELD_BORDER
            password_strength_bar.value = 0
            password_strength_bar.color = "grey"
            password_strength_bar.visible = False
            password_strength_text.value = ""
            password_strength_text.visible = False
        else:
            # Validate password requirements
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                password_error.value = error_msg
                password_error.visible = True
                new_password_field.border_color = "red"
                password_strength_bar.visible = False
                password_strength_text.visible = False
            else:
                password_error.visible = False
                new_password_field.border_color = "green"
                password_strength_bar.visible = True
                password_strength_text.visible = True
                strength, score = get_password_strength(password)
                password_strength_bar.value = score / 100
                
                # Color coding - matching signup.py
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

    def validate_email_field():
        """Validate email format"""
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

    email_field.on_change = lambda e: validate_email_field()
    code_field.on_change = lambda e: clear_field_error(code_field)
    new_password_field.on_change = lambda e: (clear_field_error(new_password_field), update_strength(new_password_field.value))
    confirm_password_field.on_change = lambda e: clear_field_error(confirm_password_field)

    def show_code_step(email_value: str):
        state["code_sent"] = True
        code_field.visible = True
        new_password_field.visible = True
        confirm_password_field.visible = True
        code_info_text.value = f"Code sent to {email_value}. Expires in 10 minutes."
        code_info_text.visible = True
        reset_button.visible = True
        resend_button.visible = True
        page.update()

    def send_code_click(e):
        reset_field_errors()
        email_value = (email_field.value or "").strip().lower()
        if not email_value:
            set_field_error(email_field, "Please enter your email")
            show_snackbar(page, "Please enter your email")
            return

        success, msg = request_password_reset_code(email_value)
        if success:
            show_snackbar(page, msg, success=True)
            show_code_step(email_value)
        else:
            show_snackbar(page, msg, error=True)

    def do_reset_click(e):
        reset_field_errors()
        email_value = (email_field.value or "").strip().lower()
        code_value = (code_field.value or "").strip()
        new_password = (new_password_field.value or "").strip()
        confirm_password = (confirm_password_field.value or "").strip()

        if not email_value:
            set_field_error(email_field, "Please enter your email")
            show_snackbar(page, "Please enter your email", error=True)
            return

        if len(code_value) != 6 or not code_value.isdigit():
            set_field_error(code_field, "Enter a valid 6-digit code")
            show_snackbar(page, "Please enter a valid 6-digit code", error=True)
            return

        if not new_password:
            set_field_error(new_password_field, "Please enter a new password")
            show_snackbar(page, "Please enter a new password", error=True)
            return

        valid_password, pwd_msg = validate_password(new_password)
        if not valid_password:
            set_field_error(new_password_field, pwd_msg)
            show_snackbar(page, pwd_msg, error=True)
            return

        if new_password != confirm_password:
            set_field_error(confirm_password_field, "Passwords do not match")
            show_snackbar(page, "Passwords do not match", error=True)
            return

        success, msg = reset_password_with_code(email_value, code_value, new_password)
        if success:
            # Show simple success message
            success_text = ft.SnackBar(
                content=ft.Text("Password reset successful!", color="white"),
                bgcolor="#1a1a1a",
                duration=1000,
                open=True,
            )
            page.overlay.append(success_text)
            page.update()
            
            # Redirect after brief delay
            import threading
            import time
            def redirect():
                time.sleep(1)
                goto_login()
            threading.Thread(target=redirect, daemon=True).start()
        else:
            # Shorten error messages for field display
            short_msg = msg
            if "No account found" in msg:
                short_msg = "Account not found"
            elif "No code has been requested" in msg:
                short_msg = "No code sent"
            elif "expired" in msg.lower():
                short_msg = "Code expired"
            elif "Incorrect" in msg:
                short_msg = "Wrong code"
            set_field_error(code_field, short_msg)
            show_snackbar(page, msg, error=True)

    send_code_button.on_click = send_code_click
    reset_button.on_click = do_reset_click
    resend_button.on_click = send_code_click

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=24),
                ft.Image(
                    src_base64=get_base64_image("assets/login.png"),
                    width=95,
                    height=95,
                    fit=ft.ImageFit.CONTAIN
                ),
                ft.Container(height=10),
                ft.Text("RESET PASSWORD", size=30, weight=ft.FontWeight.BOLD, color=CREAM),
                ft.Text("Secure your account with OTP verification", size=13, color=CREAM),
                ft.Container(height=18),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Reset your password", size=22, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                            ft.Container(height=4),
                            ft.Text("Enter your email to receive a 6-digit reset code", size=12, color=DARK_GREEN, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=14),
                            email_field,
                            email_error,
                            ft.Container(height=8),
                            code_info_text,
                            code_field,
                            ft.Container(height=8),
                            new_password_field,
                            password_strength_bar,
                            password_strength_text,
                            password_error,
                            ft.Container(height=8),
                            confirm_password_field,
                            ft.Container(height=14),
                            send_code_button,
                            ft.Container(height=8),
                            reset_button,
                            resend_button,
                            ft.TextButton(
                                "← Back to login",
                                on_click=goto_login,
                                style=ft.ButtonStyle(color=DARK_GREEN)
                            )
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=370,
                    padding=26,
                    bgcolor=CREAM,
                    border=ft.border.all(1, FIELD_BORDER),
                    border_radius=20,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=16, color="black12", offset=ft.Offset(0, 6)),
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        bgcolor=ACCENT_PRIMARY,
        expand=True,
        padding=20
    )
import flet as ft
import re
import threading
import time
from core.auth import verify_signup_code, resend_signup_code
from core.image_utils import get_base64_image
from utils import show_snackbar, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN


def email_verification_screen(page: ft.Page, current_user: dict, cart: list, email: str, goto_login):
    resend_cooldown = {"active": False}

    masked_email = email
    if "@" in email:
        local, domain = email.split("@", 1)
        if len(local) > 2:
            masked_email = f"{local[:2]}***@{domain}"

    token_field = ft.TextField(
        label="Verification code",
        hint_text="Enter 6-digit code",
        prefix_icon=ft.Icons.VERIFIED_USER,
        width=310,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        error_style=ft.TextStyle(color="#FF0000", size=12),
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        max_length=6,
        text_align=ft.TextAlign.CENTER,
    )

    def clear_code_error():
        token_field.border_color = FIELD_BORDER
        token_field.error_text = None
        token_field.border_width = 1

    def set_code_error(message: str):
        token_field.border_color = "#FF0000"
        token_field.error_text = message
        token_field.border_width = 2
        page.update()

    resend_status_text = ft.Text("", size=11, color="#666666", visible=False, text_align=ft.TextAlign.CENTER)

    resend_status_container = ft.Container(
        content=resend_status_text,
        width=300,
        height=18,
        alignment=ft.alignment.center,
    )

    def _set_resend_state(enabled: bool):
        resend_button.disabled = not enabled
        page.update()

    def start_resend_countdown(seconds: int):
        seconds = max(1, int(seconds))

        if resend_cooldown["active"]:
            return

        resend_cooldown["active"] = True

        def _timer():
            _set_resend_state(False)
            remaining = seconds
            while remaining > 0:
                resend_status_text.value = f"Resend in {remaining}s"
                resend_status_text.visible = True
                page.update()
                time.sleep(1)
                remaining -= 1

            resend_status_text.visible = False
            resend_status_text.value = ""
            resend_cooldown["active"] = False
            _set_resend_state(True)

        threading.Thread(target=_timer, daemon=True).start()

    def verify_click(e):
        clear_code_error()
        code = (token_field.value or "").strip()
        if len(code) != 6 or not code.isdigit():
            set_code_error("Enter valid 6-digit code")
            return

        success, msg = verify_signup_code(email, code)
        if success:
            # Show simple success message
            success_text = ft.SnackBar(
                content=ft.Text("Sign up successful!", color="white"),
                bgcolor="#1a1a1a",
                duration=1000,
                open=True,
            )
            page.overlay.append(success_text)
            page.update()
            
            # Redirect after brief delay
            def redirect():
                time.sleep(1)
                goto_login()
            threading.Thread(target=redirect, daemon=True).start()
        else:
            # Shorten error messages for field display
            short_msg = msg
            if "No signup request" in msg:
                short_msg = "No signup request found"
            elif "No verification code" in msg:
                short_msg = "No code sent"
            elif "expired" in msg.lower():
                short_msg = "Code expired"
            elif "Incorrect" in msg:
                short_msg = "Wrong code"
            set_code_error(short_msg)
            show_snackbar(page, msg, error=True)

    def resend_click(e):
        if resend_cooldown["active"]:
            return

        _set_resend_state(False)
        resend_status_text.value = "Sending code..."
        resend_status_text.visible = True
        page.update()

        success, msg = resend_signup_code(email)
        if success:
            show_snackbar(page, msg, success=True)
            start_resend_countdown(15)
        else:
            show_snackbar(page, msg, error=True)
            cooldown_match = re.search(r"Please wait\s+(\d+)s", msg or "")
            if cooldown_match:
                start_resend_countdown(int(cooldown_match.group(1)))
            else:
                resend_status_text.visible = False
                resend_status_text.value = ""
                _set_resend_state(True)

    resend_button = ft.TextButton(
        "Didn’t receive it? Resend code",
        on_click=resend_click,
        style=ft.ButtonStyle(color=DARK_GREEN)
    )

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
                ft.Text("VERIFY YOUR EMAIL", size=30, weight=ft.FontWeight.BOLD, color=CREAM),
                ft.Text("One last step to secure your account", size=13, color=CREAM),
                ft.Container(height=18),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Enter Verification Code", size=22, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                            ft.Container(height=4),
                            ft.Text(f"We sent a 6-digit code to {masked_email}", size=12, color=DARK_GREEN, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=14),
                            token_field,
                            ft.Container(height=8),
                            ft.Text("Code expires in 10 minutes", size=11, color="#666666"),
                            ft.Container(height=14),
                            ft.ElevatedButton(
                                "Verify Code",
                                width=300,
                                height=46,
                                bgcolor=ACCENT_DARK,
                                color=CREAM,
                                on_click=verify_click,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                            ),
                            ft.Container(height=6),
                            resend_button,
                            resend_status_container,
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
        expand=True,
        bgcolor=ACCENT_PRIMARY,
        padding=20,
    )

import flet as ft
from datetime import datetime
import threading
import time
from core.auth import authenticate_user, validate_email
from utils import show_snackbar, ACCENT_PRIMARY, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_DARK

def login_screen(page: ft.Page, current_user: dict, cart: list, goto_signup, goto_reset, goto_dashboard):
    email_field = ft.TextField(
        label="Email",
        prefix_icon=ft.Icons.PERSON,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )

    password_field = ft.TextField(
        label="Password",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )

    role_selection = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="customer", label="Customer"),
            ft.Radio(value="owner", label="Restaurant Owner"),
            ft.Radio(value="admin", label="Administrator")
        ]),
        value="customer"
    )

    lockout_text_ref = ft.Ref[ft.Text]()
    lockout_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_CLOCK, color="red", size=40),
            ft.Text("", ref=lockout_text_ref, color="red", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        padding=10,
        border=ft.border.all(2, "red"),
        border_radius=10,
        visible=False
    )

    def countdown_timer(locked_until):
        while datetime.now() < locked_until:
            delta = locked_until - datetime.now()
            total_seconds = int(delta.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            lockout_text_ref.current.value = f"Account locked\nTry again in {minutes:02d}:{seconds:02d}"
            page.update()
            time.sleep(1)
        lockout_text_ref.current.value = ""
        lockout_container.visible = False
        page.update()

    def login_click(e):
        # Validate email format first
        valid, msg = validate_email(email_field.value)
        if not valid:
            show_snackbar(page, msg)
            return
        
        if not password_field.value:
            show_snackbar(page, "Please enter your password")
            return

        user = authenticate_user(email_field.value, password_field.value, role_selection.value)

        if user is None:
            # Generic error message for security (don't reveal if email exists)
            show_snackbar(page, "Invalid email or password")
            return

        if isinstance(user, dict) and "locked" in user:
            if not lockout_container.visible:
                locked_until = datetime.fromisoformat(user["locked_until"])
                lockout_container.visible = True
                threading.Thread(target=countdown_timer, args=(locked_until,), daemon=True).start()
            show_snackbar(page, f"Account locked due to too many failed attempts")
            return

        current_user["user"] = user
        cart.clear()  # Clear cart on login
        show_snackbar(page, f"Welcome back, {user['full_name']}!")
        goto_dashboard(user["role"])

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=25),

                ft.Image(
                    src="assets/burger.PNG",
                    width=110,
                    height=110,
                    fit=ft.ImageFit.CONTAIN
                ),

                ft.Text("FOOD DELIVERY", size=30, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                ft.Text("WELCOME BACK!", size=16, color=TEXT_LIGHT),

                ft.Container(height=20),

                email_field,
                password_field,
                lockout_container,

                ft.Container(
                    content=ft.Column([
                        ft.Text("Role Selection", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                        role_selection
                    ]),
                    padding=10,
                    border=ft.border.all(1, "black"),
                    border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#9A031E", "#6B0113"]
                    ),
                    width=300
                ),

                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SECURITY, color="yellow", size=20),
                        ft.Text(
                            "Account locks after 5 failed attempts",
                            size=11,
                            color=TEXT_LIGHT
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    width=300
                ),

                ft.Container(height=15),

                ft.ElevatedButton(
                    "Log in",
                    width=280,
                    height=45,
                    bgcolor=ACCENT_PRIMARY,
                    color=TEXT_LIGHT,
                    on_click=login_click
                ),

                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("Don't have an account? ", color=TEXT_LIGHT),
                            ft.Text("Sign Up", color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    on_click=goto_signup
                ),

                ft.TextButton(
                    "Reset Password",
                    on_click=goto_reset,
                    style=ft.ButtonStyle(color=TEXT_LIGHT)
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        ),
        expand=True,
        padding=20
    )
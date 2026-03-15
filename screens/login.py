import flet as ft
from datetime import datetime
import threading
import time
import json
import webbrowser
from core.auth import authenticate_user, validate_email, register_user
from core.database import log_action
from core.image_utils import get_base64_image
from utils import show_snackbar, ACCENT_PRIMARY, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE
from screens.login_loading import show_login_loading, hide_login_loading
from screens.login_side_help import create_login_side_help_widget

def login_screen(page: ft.Page, current_user: dict, cart: list, goto_signup, goto_reset, goto_dashboard, goto_verify=None, oauth_handler=None, logout_message=None, session_timed_out=None, cause=None):
    logo_base64 = get_base64_image("assets/burger.png")

    # Determine what message to show
    message_to_show = None
    if logout_message:
        message_to_show = logout_message
    elif cause == "timeout" and session_timed_out and session_timed_out.get("flag") is True:
        message_to_show = "Looks like you wandered off! Your session has ended."
        session_timed_out["flag"] = False
    
    # If we have a message, add snackbar to page overlay immediately
    if message_to_show:
        snackbar = ft.SnackBar(
            content=ft.Text(message_to_show, color="white", size=14),
            bgcolor="#1a1a1a",
            duration=8000,
            open=True,
        )
        page.overlay.append(snackbar)
        page.update()
    
    # Load welcome messages from JSON
    try:
        with open("assets/login_messages.json", "r") as f:
            messages_data = json.load(f)
            welcome_messages = messages_data["messages"]
    except:
        welcome_messages = ["WELCOME BACK!"]
    
    # Create welcome text component
    welcome_text = ft.Text(welcome_messages[0], size=14, color=DARK_GREEN, weight=ft.FontWeight.BOLD, opacity=1)
    
    # Rotating message function with fade effect
    message_index = [0]
    stop_rotation = [False]  # Flag to stop the rotation thread
    
    def rotate_message():
        while not stop_rotation[0]:
            time.sleep(3.5)
            if stop_rotation[0]:
                break
            # Fade out
            for i in range(10):
                if stop_rotation[0]:
                    break
                try:
                    welcome_text.opacity = 1 - (i / 10)
                    page.update()
                except (RuntimeError, Exception):
                    # Event loop closed or page no longer available
                    stop_rotation[0] = True
                    break
                time.sleep(0.05)
            
            if stop_rotation[0]:
                break
                
            # Change message
            message_index[0] = (message_index[0] + 1) % len(welcome_messages)
            welcome_text.value = welcome_messages[message_index[0]]
            
            # Fade in
            for i in range(10):
                if stop_rotation[0]:
                    break
                try:
                    welcome_text.opacity = i / 10
                    page.update()
                except (RuntimeError, Exception):
                    # Event loop closed or page no longer available
                    stop_rotation[0] = True
                    break
                time.sleep(0.05)
    
    # Start rotation thread
    threading.Thread(target=rotate_message, daemon=True).start()
    
    # Email field with error state
    email_field = ft.TextField(
        label="Email",
        prefix_icon=ft.Icons.PERSON,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ORANGE,
        border_radius=10,
        label_style=ft.TextStyle(color=DARK_GREEN),
        error_style=ft.TextStyle(color="#FF0000", size=12)
    )

    # Password field with error state
    password_field = ft.TextField(
        label="Password",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ORANGE,
        border_radius=10,
        label_style=ft.TextStyle(color=DARK_GREEN),
        error_style=ft.TextStyle(color="#FF0000", size=12)
    )
    
    # Wrap fields in containers with shadows for depth
    email_container = ft.Container(
        content=email_field,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="black12",
            offset=ft.Offset(0, 2)
        )
    )
    
    password_container = ft.Container(
        content=password_field,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="black12",
            offset=ft.Offset(0, 2)
        )
    )

    # Role selection with icons
    role_selection = ft.RadioGroup(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SHOPPING_BAG, color=DARK_GREEN, size=20),
                ft.Radio(value="customer", label="Customer", label_style=ft.TextStyle(color=TEXT_DARK), fill_color=DARK_GREEN)
            ], spacing=10),
            ft.Row([
                ft.Icon(ft.Icons.RESTAURANT, color=DARK_GREEN, size=20),
                ft.Radio(value="owner", label="Restaurant Owner", label_style=ft.TextStyle(color=TEXT_DARK), fill_color=DARK_GREEN)
            ], spacing=10),
            ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=DARK_GREEN, size=20),
                ft.Radio(value="admin", label="Administrator", label_style=ft.TextStyle(color=TEXT_DARK), fill_color=DARK_GREEN)
            ], spacing=10)
        ], spacing=8),
        value="customer"
    )

    lockout_text_ref = ft.Ref[ft.Text]()
    lockout_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_CLOCK, color=DARK_GREEN, size=40),
            ft.Text("", ref=lockout_text_ref, color=DARK_GREEN, size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        padding=10,
        border=ft.border.all(2, DARK_GREEN),
        border_radius=10,
        width=300,
        visible=False
    )

    login_status_text = ft.Text("", size=12, visible=False, text_align=ft.TextAlign.CENTER, width=300)
    google_status_text = ft.Text("", size=12, visible=False, text_align=ft.TextAlign.CENTER, width=300)
    oauth_state = {"in_progress": False}
    support_widget_container_ref = {"control": None}

    def set_support_widget_visible(visible: bool):
        container = support_widget_container_ref.get("control")
        if container is None:
            return
        if container.visible != visible:
            container.visible = visible
            page.update()

    def set_login_status(message: str = "", error: bool = False):
        login_status_text.value = message
        login_status_text.color = "#8B0000" if error else DARK_GREEN
        login_status_text.visible = bool(message)

    def set_google_status(message: str = "", error: bool = False):
        google_status_text.value = message
        google_status_text.color = "#8B0000" if error else DARK_GREEN
        google_status_text.visible = bool(message)

    def clear_auth_statuses():
        set_login_status()
        set_google_status()
        set_support_widget_visible(False)
        page.update()

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

    def reset_field_errors():
        """Reset all field error states"""
        email_field.border_color = FIELD_BORDER
        email_field.error_text = None
        email_field.border_width = 1
        password_field.border_color = FIELD_BORDER
        password_field.error_text = None
        password_field.border_width = 1
        clear_auth_statuses()
        page.update()

    def set_field_error(field, error_message):
        """Set error state on a field with red border"""
        field.border_color = "#FF0000"
        field.error_text = error_message
        field.border_width = 2
        page.update()

    def clear_field_error(field):
        field.border_color = FIELD_BORDER
        field.error_text = None
        field.border_width = 1
        page.update()

    def on_email_change(e):
        # Only re-validate while typing if an email error is currently shown
        if not email_field.error_text:
            return

        value = (email_field.value or "").strip()
        if not value:
            set_field_error(email_field, "Email is required")
            return

        valid, msg = validate_email(value)
        if valid:
            clear_field_error(email_field)
        else:
            set_field_error(email_field, msg)

    def on_password_change(e):
        # Clear password error as soon as user types a non-empty value
        if password_field.error_text and (password_field.value or "").strip():
            clear_field_error(password_field)

    email_field.on_change = on_email_change
    password_field.on_change = on_password_change

    def login_click(e):
        # Reset all errors first
        reset_field_errors()
        
        # Validate inputs and show field-specific errors together
        has_validation_error = False

        email_value = (email_field.value or "").strip()
        if not email_value:
            set_field_error(email_field, "Email is required")
            has_validation_error = True
        else:
            valid, msg = validate_email(email_value)
            if not valid:
                set_field_error(email_field, msg)
                has_validation_error = True

        if not password_field.value:
            set_field_error(password_field, "Please enter your password")
            has_validation_error = True

        if has_validation_error:
            show_snackbar(page, "Please fix the highlighted fields")
            return

        # Show loading screen only after validation passes
        loading = show_login_loading(page, "Logging in...")

        try:
            user = authenticate_user(email_field.value, password_field.value)

            if user is None:
                # Only highlight password field for security (don't reveal if email exists)
                hide_login_loading(page, loading)
                set_field_error(password_field, "Invalid email or password")
                show_snackbar(page, "Invalid email or password")
                return

            if isinstance(user, dict) and "locked" in user:
                hide_login_loading(page, loading)
                if not lockout_container.visible:
                    locked_until = datetime.fromisoformat(user["locked_until"])
                    lockout_container.visible = True
                    threading.Thread(target=countdown_timer, args=(locked_until,), daemon=True).start()
                set_login_status("Account locked due to too many failed attempts", error=True)
                set_support_widget_visible(True)
                show_snackbar(page, f"Account locked due to too many failed attempts")
                return

            if isinstance(user, dict) and user.get("unverified"):
                hide_login_loading(page, loading)
                set_login_status("Please verify your email before logging in", error=True)
                show_snackbar(page, "Please verify your email before logging in")
                if goto_verify:
                    goto_verify(user.get("email") or email_field.value)
                return

            if isinstance(user, dict) and user.get("disabled"):
                hide_login_loading(page, loading)
                set_login_status("Your account has been disabled. Please contact admin or owner.", error=True)
                set_support_widget_visible(True)
                show_snackbar(page, "Your account has been disabled. Please contact admin or owner.", error=True)
                return

            current_user["user"] = user
            cart.clear()  # Clear cart on login
            hide_login_loading(page, loading)
            clear_auth_statuses()
            show_snackbar(page, f"Welcome back, {user['full_name']}!")
            goto_dashboard(user["role"])
        except Exception as ex:
            hide_login_loading(page, loading)
            show_snackbar(page, f"Login error: {str(ex)}", error=True)

    def google_login_click(e):
        """Handle Google OAuth login by redirecting to Google"""
        if oauth_state["in_progress"]:
            show_snackbar(page, "Google sign-in is already in progress. Please finish the current login.", error=True)
            return

        oauth_state["in_progress"] = True
        google_btn = e.control
        google_btn.disabled = True
        google_btn.text = "Google (Signing in...)"
        page.update()

        set_google_status()

        def perform_google_login():
            try:
                # Start callback server
                if oauth_handler:
                    oauth_handler.start_callback_server()
                
                # Show loading dialog
                status_dialog = ft.AlertDialog(
                    title=ft.Text("Signing in with Google..."),
                    content=ft.Column([
                        ft.ProgressRing(),
                        ft.Text("Waiting for authorization. A browser window should have opened.", size=12),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=300),
                )
                page.dialog = status_dialog
                status_dialog.open = True
                page.update()
                
                # Get authorization URL with state
                auth_url, state = oauth_handler.get_authorization_url()
                
                # Open browser to Google OAuth
                page.launch_url(auth_url)
                
                # Wait for auth code from callback server (max 5 minutes)
                import time
                max_wait = 300
                start_time = time.time()
                
                while state not in oauth_handler.auth_codes and (time.time() - start_time) < max_wait:
                    time.sleep(1)
                
                # Close dialog
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                
                if state not in oauth_handler.auth_codes:
                    show_snackbar(page, "Authorization timeout. Please try again.", error=True)
                    return
                
                # Exchange code for token and get user info
                if not oauth_handler.exchange_code_for_token(state):
                    show_snackbar(page, "Failed to authenticate with Google.", error=True)
                    return
                
                user_info = oauth_handler.get_user_info(state)
                if not user_info:
                    show_snackbar(page, "Failed to get user info from Google.", error=True)
                    return
                
                # Get user info
                email = (user_info.get('email') or '').strip().lower()
                name = user_info.get('name', 'Google User')

                log_action(None, "GOOGLE_OAUTH_LOGIN_ATTEMPT", f"Google login attempt: {email}")
                
                # Check if user exists
                from models.models import Session, User
                from sqlalchemy import func
                session = Session()
                try:
                    user = session.query(User).filter(func.lower(func.trim(User.email)) == email).first()

                    if user and not bool(getattr(user, "is_active", 1)):
                        log_action(user.id, "GOOGLE_OAUTH_LOGIN_BLOCKED_DISABLED", f"Disabled Google login blocked: {email}")
                        set_google_status("Your account has been disabled. Please contact support/admin.", error=True)
                        set_support_widget_visible(True)
                        show_snackbar(page, "Your account has been disabled. Please contact support/admin.", error=True)
                        return

                    if user and getattr(user, "email_verified", 1) == 0:
                        user.email_verified = 1
                        session.commit()
                    
                    if not user:
                        # Auto-register
                        success, msg = register_user(email, "", name, "customer", require_verification=False)
                        if not success:
                            log_action(None, "GOOGLE_OAUTH_LOGIN_FAILED", f"Auto-register failed for {email}: {msg}")
                            show_snackbar(page, f"Registration failed: {msg}")
                            return
                        user = session.query(User).filter(func.lower(func.trim(User.email)) == email).first()
                    
                    if user:
                        clear_auth_statuses()
                        current_user["user"] = {
                            "id": user.id,
                            "full_name": user.full_name,
                            "email": user.email,
                            "role": user.role if hasattr(user, 'role') else "customer"
                        }
                        cart.clear()
                        log_action(user.id, "GOOGLE_OAUTH_LOGIN_SUCCESS", f"Google login success: {email}")
                        show_snackbar(page, f"Welcome, {name}!")
                        goto_dashboard(current_user["user"]["role"])
                finally:
                    session.close()
                        
            except Exception as ex:
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                show_snackbar(page, f"Error: {str(ex)}", error=True)
                import traceback
                traceback.print_exc()
            finally:
                oauth_state["in_progress"] = False
                try:
                    google_btn.disabled = False
                    google_btn.text = "Google"
                    page.update()
                except Exception:
                    pass
        
        threading.Thread(target=perform_google_login, daemon=True).start()

    support_email = "joborac@my.cspc.edu.ph"
    side_help_widget = create_login_side_help_widget(page, support_email=support_email)
    support_widget_container = ft.Container(
        content=side_help_widget,
        width=300,
        alignment=ft.alignment.center_right,
        visible=False,
    )
    support_widget_container_ref["control"] = support_widget_container

    login_container = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=24),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(
                                src_base64=logo_base64,
                                width=92,
                                height=92,
                                fit=ft.ImageFit.CONTAIN
                            ) if logo_base64 else ft.Icon(ft.Icons.FASTFOOD, color=CREAM, size=76),
                            ft.Container(height=8),
                            ft.Text(
                                "LK MARTIN FOOD SYSTEM",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=CREAM,
                                text_align=ft.TextAlign.CENTER,
                                width=320,
                                max_lines=2
                            ),
                            ft.Text(
                                "Fresh meals, fast delivery",
                                size=13,
                                color=CREAM,
                                text_align=ft.TextAlign.CENTER
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                ),
                ft.Container(height=18),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Welcome Back", size=22, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                            ft.Container(height=4),
                            welcome_text,
                            ft.Container(height=18),
                            email_container,
                            ft.Container(height=12),
                            password_container,
                            ft.Container(height=10),
                            lockout_container,
                            ft.Container(height=8),
                            login_status_text,
                            ft.Container(height=18),
                            ft.ElevatedButton(
                                "Log in",
                                width=300,
                                height=48,
                                bgcolor=ACCENT_DARK,
                                color=CREAM,
                                on_click=login_click,
                                elevation=4,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                )
                            ),
                            ft.Container(height=14),
                            ft.Text(
                                "— OR CONTINUE WITH —",
                                size=12,
                                color=DARK_GREEN,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                "Google",
                                width=300,
                                height=46,
                                bgcolor=CREAM,
                                color=DARK_GREEN,
                                on_click=lambda e: google_login_click(e),
                                elevation=2,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    side=ft.BorderSide(1, FIELD_BORDER)
                                )
                            ),
                            ft.Container(height=8),
                            google_status_text,
                            ft.Container(height=14),
                            ft.TextButton(
                                "Reset Password",
                                on_click=goto_reset,
                                style=ft.ButtonStyle(color=DARK_GREEN)
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text("Don't have an account? ", color=TEXT_DARK),
                                        ft.Text("Sign Up", color=ACCENT_DARK, weight=ft.FontWeight.BOLD)
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=0
                                ),
                                on_click=goto_signup
                            ),
                            ft.Container(height=10),
                            support_widget_container
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                    bgcolor=CREAM,
                    border_radius=20,
                    border=ft.border.all(1, FIELD_BORDER),
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=16,
                        color="black12",
                        offset=ft.Offset(0, 6)
                    ),
                    padding=28,
                    width=380,
                    on_click=None,
                    ink=False
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        bgcolor=ORANGE,
        expand=True,
        padding=20
    )
    
    return login_container
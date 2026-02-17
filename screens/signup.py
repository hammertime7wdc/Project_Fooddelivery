import flet as ft
from datetime import datetime
import threading
import time
import json
import webbrowser
from core.auth import register_user, validate_password, validate_email, validate_full_name, get_password_strength
from core.image_utils import get_base64_image
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE

def signup_screen(page: ft.Page, current_user: dict, cart: list, goto_login, oauth_handler=None):
    # Load welcome messages from JSON
    try:
        with open("assets/welcome_messages.json", "r") as f:
            messages_data = json.load(f)
            welcome_messages = messages_data["messages"]
    except:
        welcome_messages = ["Join us today!"]
    
    # Create welcome text component
    welcome_text = ft.Text("Join us today!", size=14, color=DARK_GREEN, weight=ft.FontWeight.BOLD, opacity=1)
    
    # Rotating message function with fade effect
    message_index = [0]
    def rotate_message():
        while True:
            time.sleep(3.5)
            # Fade out
            for i in range(10):
                welcome_text.opacity = 1 - (i / 10)
                page.update()
                time.sleep(0.05)
            # Change message
            message_index[0] = (message_index[0] + 1) % len(welcome_messages)
            welcome_text.value = welcome_messages[message_index[0]]
            # Fade in
            for i in range(10):
                welcome_text.opacity = i / 10
                page.update()
                time.sleep(0.05)
    
    # Start rotation thread
    threading.Thread(target=rotate_message, daemon=True).start()
    
    name_field = ft.TextField(
        label="Full Name",
        prefix_icon=ft.Icons.PERSON,
        width=300, 
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_name_field()
    )
    email_field = ft.TextField(
        label="Email",
        prefix_icon=ft.Icons.EMAIL,
        width=300, 
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_email_field()
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
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: update_password_strength(e.control.value)
    )
    confirm_password_field = ft.TextField(
        label="Confirm Password",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_confirm_password()
    )
    
    # Validation error texts (hidden by default)
    name_error = ft.Text("", size=11, color="red", visible=False)
    email_error = ft.Text("", size=11, color="red", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)
    confirm_password_error = ft.Text("", size=11, color="red", visible=False)
    
    # Password strength indicator
    strength_bar = ft.ProgressBar(width=300, value=0, color=DARK_GREEN, bgcolor=FIELD_BG)
    strength_text = ft.Text("", size=12, color=TEXT_DARK)
    
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
            password_field.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                password_error.value = error_msg
                password_error.visible = True
                password_field.border_color = "red"
            else:
                password_error.visible = False
                password_field.border_color = "green"
        page.update()
    
    def validate_confirm_password():
        if not confirm_password_field.value or confirm_password_field.value.strip() == "":
            confirm_password_error.visible = False
            confirm_password_field.border_color = FIELD_BORDER
        elif password_field.value != confirm_password_field.value:
            confirm_password_error.value = "Passwords do not match"
            confirm_password_error.visible = True
            confirm_password_field.border_color = "red"
        else:
            confirm_password_error.visible = False
            confirm_password_field.border_color = "green"
        page.update()
    
    def update_password_strength(password):
        validate_password_field(password)
        
        if not password:
            strength_bar.value = 0
            strength_bar.color = "grey"
            strength_text.value = ""
            strength_text.color = "grey"
        else:
            strength, score = get_password_strength(password)
            strength_bar.value = score / 100
            
            # Color coding
            if strength == 'weak':
                strength_bar.color = "red"
                strength_text.color = "red"
            elif strength == 'medium':
                strength_bar.color = "orange"
                strength_text.color = "orange"
            elif strength == 'strong':
                strength_bar.color = "yellow"
                strength_text.color = "yellow"
            else:  # very strong
                strength_bar.color = "green"
                strength_text.color = "green"
            
            strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
        
        page.update()

    def signup_click(e):
        # Validate full name
        valid, msg = validate_full_name(name_field.value)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Validate email
        valid, msg = validate_email(email_field.value)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Validate password
        valid, msg = validate_password(password_field.value)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Validate passwords match
        if password_field.value != confirm_password_field.value:
            show_snackbar(page, "Passwords do not match")
            return

        success, msg = register_user(email_field.value, password_field.value, name_field.value, "customer")
        if success:
            show_snackbar(page, "Account created successfully!")
            goto_login(e)
        else:
            show_snackbar(page, msg)

    def google_signup_click(e):
        """Handle Google OAuth signup by redirecting to Google"""
        def perform_google_signup():
            try:
                # Show loading dialog
                status_dialog = ft.AlertDialog(
                    title=ft.Text("Signing up with Google..."),
                    content=ft.Column([
                        ft.ProgressRing(),
                        ft.Text("Waiting for authorization. A browser window should have opened.", size=12),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=300),
                )
                page.dialog = status_dialog
                status_dialog.open = True
                page.update()
                
                # Build Google OAuth URL from config or environment
                import os
                import json
                
                with open('client_secret.json', 'r') as f:
                    config = json.load(f)['web']
                
                client_id = config['client_id']
                
                # Use environment variable for ngrok, fallback to localhost
                redirect_uri = os.getenv('OAUTH_CALLBACK_URL', 'http://localhost:9000')
                
                scope = "openid email profile"
                
                # Generate unique state for this signup attempt
                import uuid
                state = str(uuid.uuid4())
                
                # Force fresh consent each time to get a new authorization code
                auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent&state={state}"
                
                # Redirect the page to Google OAuth
                page.launch_url(auth_url)
                
                # Wait for auth code from callback server (max 5 minutes)
                import time
                max_wait = 300
                start_time = time.time()
                
                # Wait for this specific state's code
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
                email = user_info.get('email')
                name = user_info.get('name', 'Google User')
                
                # Register user
                success, msg = register_user(email, "", name, "customer")
                if success:
                    show_snackbar(page, "Account created successfully!")
                    goto_login(e)
                else:
                    show_snackbar(page, f"Registration failed: {msg}")
                        
            except Exception as ex:
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                show_snackbar(page, f"Error: {str(ex)}", error=True)
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=perform_google_signup, daemon=True).start()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=20),

                ft.Image(
                    src_base64=get_base64_image("assets/login.png"),
                    width=110,
                    height=110,
                    fit=ft.ImageFit.CONTAIN
                ),

                ft.Container(height=15),
                ft.Text("CREATE ACCOUNT", size=28, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                welcome_text,

                ft.Container(height=20),

                ft.Container(
                    content=ft.Column(
                        [
                            name_field,
                            name_error,
                            ft.Container(height=5),
                            email_field,
                            email_error,
                            ft.Container(height=5),
                            password_field,
                            password_error,
                            ft.Container(height=5),
                            strength_bar,
                            strength_text,
                            ft.Container(height=10),
                            confirm_password_field,
                            confirm_password_error,

                            ft.Container(height=20),

                            ft.ElevatedButton(
                                "Sign Up",
                                width=280,
                                height=45,
                                bgcolor=ACCENT_DARK,
                                color=CREAM,
                                on_click=signup_click,
                                elevation=4,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),

                            ft.Container(height=15),

                            ft.Text(
                                "— OR CONTINUE WITH —",
                                size=12,
                                color=DARK_GREEN,
                                weight=ft.FontWeight.BOLD
                            ),

                            ft.Container(height=10),

                            ft.ElevatedButton(
                                "  Google",
                                width=280,
                                height=45,
                                bgcolor=CREAM,
                                color=DARK_GREEN,
                                on_click=lambda e: google_signup_click(e),
                                elevation=2,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0
                    ),
                    bgcolor=CREAM,
                    border_radius=16,
                    padding=30,
                    width=350
                ),

                ft.Container(height=20),

                ft.TextButton(
                    "← Back to login",
                    on_click=goto_login,
                    style=ft.ButtonStyle(color=DARK_GREEN)
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=ORANGE,
        expand=True,
        padding=20
    )
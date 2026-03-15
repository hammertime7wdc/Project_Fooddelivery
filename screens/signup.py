import flet as ft
from datetime import datetime
import threading
import time
import json
import webbrowser
from core.auth import register_user, validate_password, validate_email, validate_full_name, get_password_strength
from core.database import log_action
from core.image_utils import get_base64_image
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE

def signup_screen(page: ft.Page, current_user: dict, cart: list, goto_login, goto_verify=None, oauth_handler=None):
    logo_base64 = get_base64_image("assets/login.png")

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
    email_exists_error = ft.Text("", size=11, color="red", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)
    confirm_password_error = ft.Text("", size=11, color="red", visible=False)
    
    # Validation timers for debouncing
    email_validation_timer = [None]
    name_validation_timer = [None]
    
    # Password strength indicator
    strength_bar = ft.ProgressBar(width=300, value=0, color=DARK_GREEN, bgcolor=FIELD_BG)
    strength_text = ft.Text("", size=12, color=TEXT_DARK)
    
    def check_email_exists():
        """Check if email is already registered in database"""
        if not email_field.value or email_field.value.strip() == "":
            email_exists_error.visible = False
            return
        
        try:
            from models.models import Session, User
            from sqlalchemy import func
            session = Session()
            try:
                email_value = email_field.value.strip().lower()
                existing_user = session.query(User).filter(func.lower(func.trim(User.email)) == email_value).first()
                if existing_user:
                    email_exists_error.value = "Email already registered"
                    email_exists_error.visible = True
                    email_field.border_color = "red"
                else:
                    email_exists_error.visible = False
            finally:
                session.close()
        except Exception as e:
            print(f"Error checking email: {e}")
        
        page.update()
    
    def validate_name_field():
        """Debounced name validation"""
        if name_validation_timer[0]:
            name_validation_timer[0].cancel()
        
        def delayed_validate():
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
        
        name_validation_timer[0] = threading.Timer(0.5, delayed_validate)
        name_validation_timer[0].start()
    
    def validate_email_field():
        """Debounced email validation with existence check"""
        if email_validation_timer[0]:
            email_validation_timer[0].cancel()
        
        def delayed_validate():
            if not email_field.value or email_field.value.strip() == "":
                email_error.visible = False
                email_field.border_color = FIELD_BORDER
                email_exists_error.visible = False
            else:
                is_valid, error_msg = validate_email(email_field.value)
                if not is_valid:
                    email_error.value = error_msg
                    email_error.visible = True
                    email_field.border_color = "red"
                    email_exists_error.visible = False
                else:
                    email_error.visible = False
                    email_field.border_color = "green"
                    check_email_exists()
            page.update()
        
        email_validation_timer[0] = threading.Timer(0.5, delayed_validate)
        email_validation_timer[0].start()
    
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
        """Handle signup with loading state and input trimming"""
        # Trim inputs
        name = name_field.value.strip() if name_field.value else ""
        email = email_field.value.strip().lower() if email_field.value else ""
        password = password_field.value if password_field.value else ""
        confirm_password = confirm_password_field.value if confirm_password_field.value else ""
        
        # Validate full name
        valid, msg = validate_full_name(name)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Validate email
        valid, msg = validate_email(email)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Check if email already exists
        from models.models import Session, User as UserModel
        from sqlalchemy import func
        session = Session()
        try:
            existing_user = session.query(UserModel).filter(func.lower(func.trim(UserModel.email)) == email).first()
            if existing_user:
                show_snackbar(page, "Email already registered")
                return
        finally:
            session.close()
        
        # Validate password
        valid, msg = validate_password(password)
        if not valid:
            show_snackbar(page, msg)
            return
        
        # Validate passwords match
        if password != confirm_password:
            show_snackbar(page, "Passwords do not match")
            return

        # Show loading state
        signup_button.disabled = True
        signup_button.content = ft.Row([
            ft.ProgressRing(width=20, height=20, color=CREAM),
            ft.Text("Creating account...", color=CREAM)
        ], spacing=10)
        page.update()
        
        try:
            success, msg = register_user(email, password, name, "customer")
            if success:
                show_snackbar(page, msg, success=True)
                if goto_verify:
                    goto_verify(email)
                else:
                    goto_login()
                
                # Clear fields
                name_field.value = ""
                email_field.value = ""
                password_field.value = ""
                confirm_password_field.value = ""
                
                # Reset password strength indicator
                strength_bar.value = 0
                strength_bar.color = "grey"
                strength_text.value = ""
                strength_text.color = "grey"
                
                # Reset field borders
                name_field.border_color = FIELD_BORDER
                email_field.border_color = FIELD_BORDER
                password_field.border_color = FIELD_BORDER
                confirm_password_field.border_color = FIELD_BORDER
                
                # Hide all error messages
                name_error.visible = False
                email_error.visible = False
                email_exists_error.visible = False
                password_error.visible = False
                confirm_password_error.visible = False
                
                page.update()
            else:
                show_snackbar(page, msg)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            show_snackbar(page, f"Error creating account: {str(ex)}")
        finally:
            # Restore button state
            signup_button.disabled = False
            signup_button.content = ft.Text("Sign Up")
            page.update()

    # Create signup button as variable so we can update it during loading
    signup_button = ft.ElevatedButton(
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
    )

    def google_signup_click(e):
        """Handle Google OAuth signup by redirecting to Google"""
        def perform_google_signup():
            max_retries = 3
            attempt = 0
            
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
                
                # Exchange code for token with retry logic
                for attempt in range(max_retries):
                    try:
                        if oauth_handler.exchange_code_for_token(state):
                            break
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Wait before retry
                    except Exception as retry_ex:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        show_snackbar(page, f"Authentication failed: {str(retry_ex)}", error=True)
                        return
                else:
                    if attempt == max_retries - 1:
                        show_snackbar(page, "Failed to exchange authorization code. Please try again.", error=True)
                        return
                
                # Get user info with error handling
                try:
                    user_info = oauth_handler.get_user_info(state)
                    if not user_info:
                        show_snackbar(page, "Failed to get user info from Google.", error=True)
                        return
                except Exception as info_ex:
                    show_snackbar(page, f"Error getting user info: {str(info_ex)}", error=True)
                    return
                
                # Get user info and register
                email = user_info.get('email', '').strip()
                name = user_info.get('name', 'Google User').strip()

                log_action(None, "GOOGLE_OAUTH_SIGNUP_ATTEMPT", f"Google signup attempt: {email}")
                
                if not email:
                    log_action(None, "GOOGLE_OAUTH_SIGNUP_FAILED", "Google signup failed: missing email from provider")
                    show_snackbar(page, "Could not retrieve email from Google account.", error=True)
                    return
                
                # Register user (password empty for OAuth users)
                try:
                    success, msg = register_user(email, "", name, "customer", require_verification=False)
                    if success:
                        # register_user already logs USER_REGISTERED; add explicit OAuth event too
                        from models.models import Session, User
                        from sqlalchemy import func
                        session = Session()
                        try:
                            created_user = session.query(User).filter(func.lower(func.trim(User.email)) == email.lower()).first()
                            if created_user:
                                log_action(created_user.id, "GOOGLE_OAUTH_SIGNUP_SUCCESS", f"Google signup success: {email}")
                            else:
                                log_action(None, "GOOGLE_OAUTH_SIGNUP_SUCCESS", f"Google signup success: {email}")
                        finally:
                            session.close()
                        show_snackbar(page, "Account created successfully!")
                        threading.Timer(1.0, lambda: goto_login(e)).start()
                    else:
                        log_action(None, "GOOGLE_OAUTH_SIGNUP_FAILED", f"Google signup failed for {email}: {msg}")
                        show_snackbar(page, f"Registration failed: {msg}")
                except Exception as reg_ex:
                    log_action(None, "GOOGLE_OAUTH_SIGNUP_FAILED", f"Google signup exception for {email}: {str(reg_ex)}")
                    show_snackbar(page, f"Error creating account: {str(reg_ex)}", error=True)
                        
            except FileNotFoundError:
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                show_snackbar(page, "Google configuration file not found.", error=True)
            except json.JSONDecodeError:
                if page.dialog:
                    page.dialog.open = False
                    page.update()
                show_snackbar(page, "Invalid Google configuration file.", error=True)
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
                ft.Container(height=24),
                ft.Column(
                    [
                        ft.Image(
                            src_base64=logo_base64,
                            width=92,
                            height=92,
                            fit=ft.ImageFit.CONTAIN
                        ) if logo_base64 else ft.Icon(ft.Icons.FASTFOOD, size=92, color=CREAM),
                        ft.Container(height=8),
                        ft.Text(
                            "CREATE ACCOUNT",
                            size=30,
                            weight=ft.FontWeight.BOLD,
                            color=CREAM,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Create your profile and start ordering",
                            size=13,
                            color=CREAM,
                            text_align=ft.TextAlign.CENTER
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0
                ),
                ft.Container(height=18),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Let’s Get Started", size=22, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                            ft.Container(height=4),
                            welcome_text,
                            ft.Container(height=18),

                            name_field,
                            name_error,
                            ft.Container(height=6),

                            email_field,
                            email_error,
                            email_exists_error,
                            ft.Container(height=6),

                            password_field,
                            password_error,
                            ft.Container(height=6),

                            strength_bar,
                            strength_text,
                            ft.Container(height=10),

                            confirm_password_field,
                            confirm_password_error,

                            ft.Container(height=20),

                            signup_button,

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
                                on_click=lambda e: google_signup_click(e),
                                elevation=2,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    side=ft.BorderSide(1, FIELD_BORDER)
                                )
                            ),

                            ft.Container(height=14),

                            ft.TextButton(
                                "← Back to login",
                                on_click=goto_login,
                                style=ft.ButtonStyle(color=DARK_GREEN)
                            )
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
                    width=380
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
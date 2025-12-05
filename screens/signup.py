import flet as ft
from core.auth import register_user, validate_password, validate_email, validate_full_name, get_password_strength
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def signup_screen(page: ft.Page, current_user: dict, cart: list, goto_login):
    name_field = ft.TextField(
        label="Full Name", 
        width=300, 
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )
    email_field = ft.TextField(
        label="Email", 
        width=300, 
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        on_change=lambda e: update_password_strength(e.control.value)
    )
    
    # Password strength indicator
    strength_bar = ft.ProgressBar(width=300, value=0, color="grey", bgcolor="#333")
    strength_text = ft.Text("", size=12, color="grey")
    
    def update_password_strength(password):
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

        success, msg = register_user(email_field.value, password_field.value, name_field.value, "customer")
        if success:
            show_snackbar(page, "Account created successfully!")
            goto_login(e)
        else:
            show_snackbar(page, msg)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=25),

                ft.Image(
                    src="assets/login.png",
                    width=120,
                    height=120,
                    fit=ft.ImageFit.CONTAIN
                ),

                ft.Text("CREATE ACCOUNT", size=28, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                ft.Text("Register as Customer", size=14, color=TEXT_LIGHT),
                ft.Container(height=15),

                name_field,
                email_field,
                password_field,
                strength_bar,
                strength_text,

                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SECURITY, color=TEXT_LIGHT, size=20),
                        ft.Text(
                            "Password Requirements:",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_LIGHT
                        ),
                        ft.Text(
                            "• At least 8 characters\n"
                            "• One uppercase letter (A-Z)\n"
                            "• One lowercase letter (a-z)\n"
                            "• One number (0-9)\n"
                            "• One special character (!@#$%...)",
                            size=10,
                            color=TEXT_LIGHT
                        )
                    ]),
                    padding=10,
                    border=ft.border.all(1, "white"),
                    border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#6B0113", ACCENT_DARK]
                    ),
                    width=300
                ),

                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=TEXT_LIGHT, size=20),
                        ft.Text(
                            "Note: Only customers can self-register.\nRestaurant owners are created by administrators.",
                            size=11,
                            color=TEXT_LIGHT,
                            text_align=ft.TextAlign.CENTER
                        )
                    ]),
                    padding=10,
                    border=ft.border.all(1, "white"),
                    border_radius=10,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#6B0113", ACCENT_DARK]
                    ),
                    width=300
                ),

                ft.Container(height=15),

                ft.ElevatedButton(
                    "Sign Up as Customer",
                    width=250,
                    height=45,
                    bgcolor=ACCENT_DARK,
                    color=TEXT_LIGHT,
                    on_click=signup_click
                ),

                ft.TextButton(
                    "← Back to login",
                    on_click=goto_login,
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
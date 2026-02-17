import flet as ft
from core.image_utils import get_base64_image
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE

def reset_password_screen(page: ft.Page, current_user: dict, cart: list, goto_login):
    email_field = ft.TextField(
        label="Enter your email",
        prefix_icon=ft.Icons.EMAIL,
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK)
    )

    def reset_click(e):
        if not email_field.value:
            show_snackbar(page, "Please enter your email")
            return
        # TODO: Implement actual reset logic if needed (e.g., send email)
        show_snackbar(page, "Reset link sent! (Placeholder)")

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=25),

                ft.Image(
                    src_base64=get_base64_image("assets/login.png"),
                    width=120,
                    height=120,
                    fit=ft.ImageFit.CONTAIN
                ),

                ft.Text("RESET PASSWORD", size=28, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Text("Enter your email to reset password", size=14, color=DARK_GREEN),
                ft.Container(height=15),

                email_field,

                ft.Container(height=15),

                ft.ElevatedButton(
                    "Reset Password",
                    width=250,
                    height=45,
                    bgcolor=ACCENT_DARK,
                    color=CREAM,
                    on_click=reset_click
                ),

                ft.TextButton(
                    "← Back to login",
                    on_click=goto_login,
                    style=ft.ButtonStyle(color=DARK_GREEN)
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=CREAM,
        expand=True,
        padding=20
    )
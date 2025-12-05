import flet as ft
import base64

# Constants
ACCENT_DARK = "#3D000D"
ACCENT_PRIMARY = "#9A031E"
TEXT_LIGHT = "white"
TEXT_DARK = "white"
FIELD_BG = "black"
FIELD_BORDER = "#6B0113"

# Snackbar helper
def show_snackbar(page: ft.Page, message: str, error: bool = False, success: bool = False):
    color = "#8B0000"   # dark red
    if success:
        color = "#006400"  # dark green
    elif error:
        color = "#8B0000"  # dark red
    else:
        color = "#1a1a1a"  # default

    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="white"),
        bgcolor=color,
        duration=4000,
        action=ft.TextButton("OK", on_click=lambda _: page.close_snack_bar())
    )
    page.snack_bar.open = True
    page.update()

# Helper function to create image widget
def create_image_widget(item, width=100, height=100):
    """Create appropriate image widget based on image type"""
    if item.get("image_type") == "emoji":
        return ft.Text(item["image"], size=50)
    elif item.get("image_type") == "base64" and item.get("image"):
        return ft.Image(
            src_base64=item["image"],
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )
    elif item.get("image_type") == "path" and item.get("image"):
        return ft.Image(
            src=item["image"],
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )
    else:
        return ft.Icon(ft.Icons.RESTAURANT, size=50, color="grey")

# Helper for user profile picture
def create_profile_pic_widget(user, width=100, height=100):
    if user.get("pic_type") == "base64" and user.get("profile_picture"):
        return ft.Image(
            src_base64=user["profile_picture"],
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(75)
        )
    else:
        return ft.Icon(ft.Icons.PERSON, size=width, color="grey")
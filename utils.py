import flet as ft

# Constants
ACCENT_DARK = "#3D000D"
ACCENT_PRIMARY = "#9A031E"
TEXT_LIGHT = "white"
TEXT_DARK = "white"
FIELD_BG = "black"
FIELD_BORDER = "#6B0113"

# Snackbar helper
def show_snackbar(page: ft.Page, message: str, error: bool = False, success: bool = False, duration: int = 8000):
    color = "#8B0000"   # dark red
    if success:
        color = "#006400"  # dark green
    elif error:
        color = "#8B0000"  # dark red
    else:
        color = "#1a1a1a"  # default

    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="white", size=14),
        bgcolor=color,
        duration=duration,
        action=ft.TextButton("OK", on_click=lambda _: page.close_snack_bar())
    )
    page.snack_bar.open = True
    page.update()

# Helper function to create image widget
def create_image_widget(item, width=100, height=100):
    """Create appropriate image widget based on image type"""
    if item.get("image_type") == "emoji":
        return ft.Text(item["image"], size=50)
    elif item.get("image_type") == "path" and item.get("image"):
        # Construct path: "uuid.jpg" -> "assets/menu/uuid.jpg"
        img_path = f"assets/menu/{item['image']}"
        return ft.Image(
            src=img_path,
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )
    elif item.get("image_type") == "base64" and item.get("image"):
        # Fallback for legacy base64 data
        return ft.Image(
            src_base64=item["image"],
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=10
        )
    else:
        return ft.Icon(ft.Icons.RESTAURANT, size=50, color="grey")

# Helper for user profile picture
def create_profile_pic_widget(user, width=100, height=100):
    """Create profile picture widget - file-based storage"""
    if user.get("pic_type") == "path" and user.get("profile_picture"):
        # File-based approach
        img_path = f"assets/profiles/{user['profile_picture']}"
        return ft.Image(
            src=img_path,
            width=width,
            height=height,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(75)
        )
    else:
        return ft.Icon(ft.Icons.PERSON, size=width, color="grey")
import flet as ft
from datetime import datetime
from utils import (
    TEXT_LIGHT,
    ACCENT_DARK,
    FIELD_BG,
    TEXT_DARK,
    FIELD_BORDER,
    ACCENT_PRIMARY,
    CREAM,
)


def create_user_details_dialog(page, user, handlers):
    """Create a dialog to display full user details with actions."""
    
    def _close():
        if page.dialog:
            page.dialog.open = False
            page.update()
    
    # Format dates
    created_at = "N/A"
    if user.get("created_at"):
        try:
            created_dt = datetime.fromisoformat(user["created_at"])
            created_at = created_dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            created_at = user.get("created_at", "N/A")
    
    last_login = "Never"
    if user.get("last_login"):
        try:
            login_dt = datetime.fromisoformat(user["last_login"])
            last_login = login_dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            last_login = user.get("last_login", "Never")
    
    # Determine status
    is_active = user.get("is_active", 0)
    status_text = "ACTIVE" if is_active else "DISABLED"
    status_color = "#FFFFFF" if is_active else "#666666"
    status_bg = "#4CAF50" if is_active else "#E0E0E0"
    
    # User Info Section
    info_section = ft.Container(
        content=ft.Column([
            ft.Text("Account Information", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
            ft.Divider(height=1, color=FIELD_BORDER),
            ft.Row([
                ft.Text("Email:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Text(user.get("email", "N/A"), size=12, color=TEXT_DARK),
            ]),
            ft.Row([
                ft.Text("Full Name:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Text(user.get("full_name", "N/A"), size=12, color=TEXT_DARK),
            ]),
            ft.Row([
                ft.Text("Role:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Container(
                    content=ft.Text(
                        user.get("role", "Unknown").upper(),
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=CREAM,
                    ),
                    bgcolor=ACCENT_PRIMARY,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    border_radius=12,
                ),
            ]),
            ft.Row([
                ft.Text("Status:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Container(
                    content=ft.Text(
                        status_text,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=status_color,
                    ),
                    bgcolor=status_bg,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    border_radius=12,
                ),
            ]),
            ft.Row([
                ft.Text("Created:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Text(created_at, size=12, color=TEXT_DARK),
            ]),
            ft.Row([
                ft.Text("Last Login:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=120),
                ft.Text(last_login, size=12, color=TEXT_DARK),
            ]),
        ]),
        padding=12,
        bgcolor=FIELD_BG,
        border_radius=8,
    )
    
    # Actions Section
    action_buttons = []
    if not is_active:
        action_buttons.append(
            ft.ElevatedButton(
                "Activate",
                bgcolor=ACCENT_PRIMARY,
                color=CREAM,
                icon=ft.Icons.CHECK_CIRCLE,
                on_click=lambda e, uid=user.get("id"): handlers["enable_user"](uid),
            )
        )
    
    if is_active:
        action_buttons.append(
            ft.ElevatedButton(
                "Deactivate",
                bgcolor="#FFA726",
                color=CREAM,
                icon=ft.Icons.BLOCK,
                on_click=lambda e, uid=user.get("id"): handlers["disable_user"](uid),
            )
        )
    
    action_buttons.append(
        ft.ElevatedButton(
            "Delete",
            bgcolor="#EF5350",
            color=CREAM,
            icon=ft.Icons.DELETE,
            on_click=lambda e, uid=user.get("id"): handlers["delete_user"](uid),
        )
    )
    
    # Create the dialog with minimal parameters
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"User Details - {user.get('email', 'Unknown')}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
        content=ft.Container(
            content=ft.Column([
                info_section,
                ft.Container(height=10),
                ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
                ft.Divider(height=1, color=FIELD_BORDER),
                ft.Row(action_buttons, spacing=8, wrap=True),
            ]),
            width=450,
            padding=15,
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: _close()),
        ],
        bgcolor="#FFFFFF",
    )
    
    return dialog

import flet as ft
from utils import CREAM, FIELD_BORDER, ACCENT_DARK, TEXT_DARK


def create_login_side_help_widget(page: ft.Page, support_email: str = "joborac@my.cspc.edu.ph") -> ft.Container:
    state = {"expanded": False}

    button_text = ft.Text(
        "Contact Support",
        size=13,
        color=ACCENT_DARK,
        weight=ft.FontWeight.W_600,
        visible=True,
    )

    title_text = ft.Text(
        "Need help with account access?",
        size=13,
        color=ACCENT_DARK,
        weight=ft.FontWeight.BOLD,
        visible=False,
    )

    details_text = ft.Text(
        f"If your account is disabled, contact admin/support to restore access.",
        size=11,
        color=TEXT_DARK,
        visible=False,
        max_lines=3,
    )

    email_text = ft.Text(
        support_email,
        size=11,
        color=ACCENT_DARK,
        weight=ft.FontWeight.W_600,
        visible=False,
        selectable=True,
    )

    email_button = ft.TextButton(
        "Email Support",
        visible=False,
        style=ft.ButtonStyle(color=ACCENT_DARK),
    )

    def open_email(e):
        page.launch_url(f"mailto:{support_email}?subject=Account%20Access%20Support")

    email_button.on_click = open_email

    hint_text = ft.Text(
        "Tap again to close",
        size=10,
        color="#777777",
        visible=False,
    )

    panel = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SUPPORT_AGENT, size=18, color=ACCENT_DARK),
                button_text,
                ft.Column(
                    [title_text, details_text, email_text, email_button, hint_text],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=170,
        height=56,
        bgcolor=CREAM,
        border=ft.border.all(2, ACCENT_DARK),
        border_radius=14,
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black12", offset=ft.Offset(0, 2)),
        animate=ft.Animation(260, ft.AnimationCurve.EASE_IN_OUT),
        ink=True,
    )

    def toggle_panel(e):
        state["expanded"] = not state["expanded"]
        expanded = state["expanded"]

        panel.width = 300 if expanded else 170
        panel.height = 150 if expanded else 56
        button_text.visible = not expanded
        title_text.visible = expanded
        details_text.visible = expanded
        email_text.visible = expanded
        email_button.visible = expanded
        hint_text.visible = expanded

        page.update()

    panel.on_click = toggle_panel

    return panel

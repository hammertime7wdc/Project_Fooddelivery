import flet as ft
import asyncio
from core.image_utils import get_base64_image
from utils import ACCENT_DARK, DARK_GREEN, ORANGE


def splash_screen(page: ft.Page, current_user: dict, cart: list, goto_login, duration_seconds: float = 2.5):
    splash = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=40),
                ft.Image(
                    src_base64=get_base64_image("assets/burger.PNG"),
                    width=140,
                    height=140,
                    fit=ft.ImageFit.CONTAIN,
                ),
                ft.Container(height=20),
                ft.Text(
                    "FOOD DELIVERY",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ACCENT_DARK,
                ),
                ft.Text(
                    "Fresh. Fast. Tasty.",
                    size=14,
                    color=DARK_GREEN,
                ),
                ft.Container(height=30),
                ft.ProgressRing(color=ACCENT_DARK),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        bgcolor=ORANGE,
        expand=True,
        opacity=1,
        animate_opacity=500,
    )
    
    async def go_next():
        await asyncio.sleep(duration_seconds)
        splash.opacity = 0
        page.update()
        await asyncio.sleep(0.5)
        goto_login()

    page.run_task(go_next)

    return splash

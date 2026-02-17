"""Loading screen overlay for profile operations"""
import flet as ft
import asyncio
from utils import ORANGE


def create_loading_overlay(page: ft.Page, message: str = "Loading...") -> ft.Container:
    """Create a full-screen loading overlay
    
    Args:
        page: The Flet page
        message: Message to display
    
    Returns:
        ft.Container: The loading overlay container
    """
    loading_overlay = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(color="#FF8C00", width=60, height=60),
                ft.Text(message, size=16, color="white", weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        bgcolor=ORANGE,  # Orange background like splash screen
        expand=True,
        alignment=ft.alignment.center,
        opacity=1,
        animate_opacity=200
    )
    return loading_overlay


def show_loading(page: ft.Page, message: str = "Loading...") -> ft.Container:
    """Show full-screen loading overlay
    
    Args:
        page: The Flet page
        message: Message to display
    
    Returns:
        ft.Container: The loading overlay (for later closing)
    """
    loading_overlay = create_loading_overlay(page, message)
    page.overlay.append(loading_overlay)
    page.update()
    return loading_overlay


def hide_loading(page: ft.Page, overlay: ft.Container):
    """Hide loading overlay from page
    
    Args:
        page: The Flet page
        overlay: The loading overlay to hide
    """
    async def _remove():
        if overlay in page.overlay:
            overlay.opacity = 0
            page.update()
            await asyncio.sleep(0.3)  # Wait for opacity animation
            if overlay in page.overlay:
                page.overlay.remove(overlay)
                page.update()
    
    page.run_task(_remove)

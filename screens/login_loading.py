import flet as ft
from utils import ORANGE, CREAM

def show_login_loading(page: ft.Page, message: str = "Logging in..."):
    """Display a loading screen during login"""
    loading_overlay = ft.Container(
        content=ft.Column([
            ft.ProgressRing(color=CREAM, stroke_width=4),
            ft.Container(height=20),
            ft.Text(message, size=16, color=CREAM, weight=ft.FontWeight.BOLD),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
           alignment=ft.MainAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        bgcolor=ORANGE,
        expand=True,
    )
    page.overlay.append(loading_overlay)
    page.update()
    return loading_overlay

def hide_login_loading(page: ft.Page, loading_overlay):
    """Hide the loading screen"""
    try:
        if loading_overlay in page.overlay:
            page.overlay.remove(loading_overlay)
            page.update()
    except:
        pass

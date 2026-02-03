import flet as ft
from utils import TEXT_LIGHT, TEXT_DARK, ACCENT_DARK, ACCENT_PRIMARY, CREAM

def order_confirmation_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    def continue_shop(e):
        goto_menu(e)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=60),
                ft.Text(
                    "Order Confirmation",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ACCENT_DARK
                ),

                ft.Container(height=16),

                ft.Image(
                    src="assets/cart.png",
                    width=120,
                    height=120,
                    fit=ft.ImageFit.CONTAIN
                ),

                ft.Container(height=12),

                ft.Text(
                    "Your order is placed!",
                    size=18,
                    color=TEXT_DARK,
                    weight=ft.FontWeight.W_600
                ),

                ft.Container(height=28),

                ft.ElevatedButton(
                    "Continue Shopping",
                    width=250,
                    height=48,
                    bgcolor=ACCENT_DARK,
                    color=CREAM,
                    on_click=continue_shop,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                ),

                ft.Container(height=20),

                ft.Text(
                    "Thank you for ordering with us!",
                    size=14,
                    color=ACCENT_PRIMARY,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        bgcolor=CREAM,
        padding=20
    )
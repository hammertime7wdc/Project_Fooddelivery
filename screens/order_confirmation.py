import flet as ft
from utils import TEXT_LIGHT, ACCENT_DARK

def order_confirmation_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    def continue_shop(e):
        goto_menu(e)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=80),
                ft.Text("Order Confirmation", size=24, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),

                ft.Container(height=20),

                ft.Image(src="assets/cart.png", width=120, height=120, fit=ft.ImageFit.CONTAIN),

                ft.Text("Your order is placed!", size=18, color=TEXT_LIGHT),

                ft.Container(height=30),

                ft.ElevatedButton(
                    "Continue Shopping",
                    width=250,
                    height=50,
                    bgcolor=ACCENT_DARK,
                    color=TEXT_LIGHT,
                    on_click=continue_shop
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
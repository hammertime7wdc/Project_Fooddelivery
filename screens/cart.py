import flet as ft
from core.database import create_order
from utils import show_snackbar, TEXT_LIGHT, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def cart_screen(page: ft.Page, current_user: dict, cart: list, goto_menu, goto_confirmation):
    cart_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    name_field = ft.TextField(
        hint_text="Full Name", 
        value=current_user["user"]["full_name"], 
        expand=True,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    address_field = ft.TextField(
        hint_text="Delivery Address", 
        value=current_user["user"].get("address", ""), 
        expand=True,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    contact_field = ft.TextField(
        hint_text="Contact Number", 
        value=current_user["user"].get("contact", ""), 
        expand=True,
        keyboard_type=ft.KeyboardType.PHONE,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )

    def load_cart():
        cart_list.controls.clear()
        total = 0

        for idx, item in enumerate(cart):
            total += item["price"] * item["quantity"]
            cart_list.controls.append(
                ft.Row([
                    ft.Text(f"{item['name']} x {item['quantity']}", expand=True, color=TEXT_LIGHT),
                    ft.Text(f"₱{item['price'] * item['quantity']:.2f}", color=TEXT_LIGHT),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, i=idx: remove_item(i))
                ])
            )

        return total

    def remove_item(idx):
        if 0 <= idx < len(cart):
            del cart[idx]
            load_cart()
            page.update()

    def place_order(e):
        if not cart:
            show_snackbar(page, "Cart is empty!")
            return
        if not name_field.value or not address_field.value or not contact_field.value:
            show_snackbar(page, "Please fill delivery details")
            return

        total = load_cart()
        create_order(
            current_user["user"]["id"],
            name_field.value,
            address_field.value,
            contact_field.value,
            cart,
            total
        )
        cart.clear()
        show_snackbar(page, "Order placed successfully!")
        goto_confirmation(e)

    total = load_cart()

    place_order_button = ft.ElevatedButton(
        "Place Order",
        expand=True,
        height=50,
        bgcolor=ACCENT_DARK,
        color=TEXT_LIGHT,
        on_click=place_order
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.TextButton("← back to menu", on_click=goto_menu, style=ft.ButtonStyle(color=TEXT_LIGHT)),

                ft.Text("Cart Items", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                cart_list,

                ft.Container(
                    content=ft.Column([
                        ft.Row([name_field], expand=True),
                        ft.Row([address_field], expand=True),
                        ft.Row([contact_field], expand=True)
                    ], spacing=10),
                    padding=20,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#9A031E", "#6B0113"]
                    ),
                    border_radius=10
                ),

                ft.Text(f"Total: ₱{total:.2f}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),

                ft.Row([place_order_button], expand=True)
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True,
        padding=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
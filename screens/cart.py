import flet as ft
from core.database import create_order
from utils import show_snackbar, TEXT_LIGHT, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def cart_screen(page: ft.Page, current_user: dict, cart: list, goto_menu, goto_confirmation):
    cart_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    name_field = ft.TextField(
        label="Full Name",
        prefix_icon=ft.Icons.PERSON,
        value=current_user["user"]["full_name"], 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )
    address_field = ft.TextField(
        label="Delivery Address",
        prefix_icon=ft.Icons.HOME,
        value=current_user["user"].get("address", ""), 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )
    contact_field = ft.TextField(
        label="Contact Number",
        prefix_icon=ft.Icons.PHONE,
        value=current_user["user"].get("contact", ""), 
        width=300,
        keyboard_type=ft.KeyboardType.PHONE,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10
    )
    
    # Wrap fields in containers with shadows for depth
    name_container = ft.Container(
        content=name_field,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="black12",
            offset=ft.Offset(0, 2)
        )
    )
    
    address_container = ft.Container(
        content=address_field,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="black12",
            offset=ft.Offset(0, 2)
        )
    )
    
    contact_container = ft.Container(
        content=contact_field,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=8,
            color="black12",
            offset=ft.Offset(0, 2)
        )
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
        width=280,
        height=45,
        bgcolor=ACCENT_PRIMARY,
        color=TEXT_LIGHT,
        on_click=place_order,
        elevation=8
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=10),
                
                ft.TextButton("← back to menu", on_click=goto_menu, style=ft.ButtonStyle(color=TEXT_LIGHT)),

                ft.Text("Cart Items", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                
                ft.Container(height=10),
                
                cart_list,

                ft.Container(height=20),
                
                ft.Text("Delivery Information", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                
                ft.Container(height=10),

                name_container,
                ft.Container(height=10),
                address_container,
                ft.Container(height=10),
                contact_container,

                ft.Container(height=20),

                ft.Text(f"Total: ₱{total:.2f}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),

                ft.Container(height=10),

                place_order_button
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        expand=True,
        padding=20,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
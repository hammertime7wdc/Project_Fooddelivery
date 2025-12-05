import flet as ft
from core.database import get_all_menu_items, get_categories
from utils import show_snackbar, create_image_widget, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

def browse_menu_screen(page: ft.Page, current_user: dict, cart: list, goto_cart, goto_profile, goto_history, goto_logout):
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)

    def add_to_cart(item, qty):
        try:
            qty = int(qty)
            if qty < 1:
                raise ValueError
        except:
            show_snackbar(page, "Invalid quantity")
            return

        # Check if item already exists in cart
        existing_item = None
        for cart_item in cart:
            if cart_item["id"] == item["id"]:
                existing_item = cart_item
                break
        
        if existing_item:
            # Update quantity of existing item
            existing_item["quantity"] += qty
            show_snackbar(page, f"Updated {item['name']} quantity to {existing_item['quantity']}")
        else:
            # Add new item to cart
            cart.append({"id": item["id"], "name": item["name"], "price": item["price"], "quantity": qty})
            show_snackbar(page, f"Added {qty} x {item['name']} to cart")

    def load_menu(category="All", search=""):
        menu_list.controls.clear()
        items = get_all_menu_items()

        if category != "All":
            items = [item for item in items if item.get("category") == category]

        if search:
            items = [item for item in items if search.lower() in item["name"].lower() or search.lower() in item["description"].lower()]

        for item in items:
            qty = ft.TextField(
                value="1", 
                width=50, 
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor=FIELD_BG,
                color=TEXT_DARK,
                border_color=FIELD_BORDER,
                focused_border_color=ACCENT_PRIMARY
            )

            menu_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        create_image_widget(item, 80, 80),
                        ft.Column([
                            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                            ft.Text(item["description"], size=12, color=TEXT_LIGHT),
                            ft.Text(f"₱{item['price']:.2f}", size=14, color=TEXT_LIGHT)
                        ], expand=True),
                        ft.Column([
                            qty,
                            ft.ElevatedButton(
                                "Add to Cart",
                                bgcolor=ACCENT_DARK,
                                color=TEXT_LIGHT,
                                on_click=lambda e, item=item, qty=qty: add_to_cart(item, qty.value)
                            )
                        ])
                    ]),
                    padding=10,
                    border=ft.border.all(1, "black"),
                    border_radius=10
                )
            )
        page.update()

    search_field = ft.TextField(
        hint_text="Search menu...", 
        width=300, 
        on_change=lambda e: load_menu(category=category_dropdown.value, search=e.control.value),
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )

    category_dropdown = ft.Dropdown(
        hint_text="Category",
        width=300,
        options=[ft.dropdown.Option(c) for c in get_categories()] + [ft.dropdown.Option("All")],
        value="All",
        on_change=lambda e: load_menu(category=e.control.value, search=search_field.value),
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )

    load_menu()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Menu", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.SHOPPING_CART, icon_color=TEXT_LIGHT, on_click=goto_cart),
                            ft.IconButton(icon=ft.Icons.HISTORY, icon_color=TEXT_LIGHT, on_click=goto_history),
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color=TEXT_LIGHT, on_click=goto_profile),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=TEXT_LIGHT, on_click=goto_logout)
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#6B0113", ACCENT_DARK]
                    ),
                    padding=15
                ),

                search_field,
                category_dropdown,
                menu_list
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        padding=10,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
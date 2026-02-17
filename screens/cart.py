import flet as ft
from core.database import create_order
from utils import show_snackbar, TEXT_LIGHT, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE
from screens.browse_menu.image_utils import load_image_from_binary

def cart_screen(page: ft.Page, current_user: dict, cart: list, goto_menu, goto_confirmation):
    
    # Create containers that will be updated
    cart_items_container = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    subtotal_text = ft.Text("₱0.00", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.RIGHT)
    total_text = ft.Text("₱0.00", size=16, weight=ft.FontWeight.BOLD, color=ORANGE, text_align=ft.TextAlign.RIGHT)
    
    def refresh_cart():
        """Refresh cart display and totals"""
        cart_items_container.controls.clear()
        total = 0

        if not cart:
            # Empty cart state
            empty_state = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(name=ft.Icons.SHOPPING_CART_OUTLINED, size=80, color=ORANGE),
                        ft.Container(height=10),
                        ft.Text("Your cart is empty", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                        ft.Text("Add items from the menu to get started", size=14, weight=ft.FontWeight.W_500, color=ACCENT_DARK),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8
                ),
                height=250,
                alignment=ft.alignment.center
            )
            cart_items_container.controls.append(empty_state)
            subtotal_text.value = "₱0.00"
            total_text.value = "₱0.00"
            page.update()
            return

        for idx, item in enumerate(cart):
            item_total = item["price"] * item["quantity"]
            total += item_total

            # Load image from binary data
            image_widget = load_image_from_binary(item) if item.get("image") else None

            # Remove item handler
            def remove_item(e, item_idx=idx):
                if 0 <= item_idx < len(cart):
                    del cart[item_idx]
                    refresh_cart()

            # Item card
            item_card = ft.Container(
                content=ft.Row(
                    [
                        # Product image or icon
                        ft.Container(
                            content=image_widget if image_widget else ft.Icon(
                                name=ft.Icons.FASTFOOD,
                                size=28,
                                color=ORANGE
                            ),
                            width=50,
                            height=50,
                            bgcolor="#FFF5E6",
                            border_radius=25,
                            alignment=ft.alignment.center,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE
                        ),
                        # Quantity and name
                        ft.Text(
                            f"{item['quantity']} ×",
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=TEXT_DARK,
                            width=35
                        ),
                        ft.Text(
                            item['name'],
                            size=12,
                            weight=ft.FontWeight.W_400,
                            color=TEXT_DARK,
                            expand=True,
                            max_lines=1
                        ),
                        # Price
                        ft.Text(
                            f"₱{item_total:.2f}",
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=ORANGE,
                            text_align=ft.TextAlign.RIGHT,
                            width=60
                        ),
                        # Remove button
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color="red700",
                            on_click=remove_item,
                            padding=2
                        ),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10,
                bgcolor=TEXT_LIGHT,
                border_radius=8,
                border=ft.border.all(1, FIELD_BORDER),
                width=400
            )
            
            cart_items_container.controls.append(item_card)

        # Update totals
        subtotal_text.value = f"₱{total:.2f}"
        total_text.value = f"₱{total:.2f}"
        page.update()
    
    # Payment method selection
    selected_payment = {"value": "Cash on Delivery"}
    
    def make_payment_chip(label, method, available=True):
        is_selected = method == selected_payment["value"]
        chip = ft.Container(
            content=ft.Column([
                ft.Text(
                    label,
                    size=13,
                    color="#FFFFFF" if (is_selected and available) else ("#9E9E9E" if not available else TEXT_DARK),
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    "Coming Soon" if not available else "",
                    size=10,
                    color="#9E9E9E",
                    italic=True,
                    visible=not available
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ACCENT_DARK if (is_selected and available) else ("#F5F5F5" if not available else TEXT_LIGHT),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=10,
            border=ft.border.all(1.5, ACCENT_DARK if (is_selected and available) else "#E0E0E0"),
            ink=available,
            data=method,
            opacity=0.6 if not available else 1.0
        )
        return chip
    
    cod_chip = make_payment_chip("💵 Cash on Delivery", "Cash on Delivery", available=True)
    gcash_chip = make_payment_chip("📱 GCash", "GCash", available=False)
    card_chip = make_payment_chip("💳 Card", "Credit/Debit Card", available=False)
    
    def on_payment_click(e):
        # Only Cash on Delivery is clickable
        if e.control.data == "Cash on Delivery":
            selected_payment["value"] = e.control.data
            page.update()
    
    cod_chip.on_click = on_payment_click
    
    payment_chips_row = ft.Row(
        [cod_chip, gcash_chip, card_chip],
        spacing=10,
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    # Delivery Information Fields - cleaner white background
    name_field = ft.TextField(
        label="Full Name",
        value=current_user["user"]["full_name"], 
        width=300,
        bgcolor=TEXT_LIGHT,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_DARK,
        border_radius=8,
        label_style=ft.TextStyle(color=ACCENT_DARK, size=13, weight=ft.FontWeight.W_500),
        text_style=ft.TextStyle(color=TEXT_DARK, size=13),
        height=50,
        content_padding=12
    )
    
    address_field = ft.TextField(
        label="Delivery Address",
        value=current_user["user"].get("address", ""), 
        width=300,
        bgcolor=TEXT_LIGHT,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_DARK,
        border_radius=8,
        label_style=ft.TextStyle(color=ACCENT_DARK, size=13, weight=ft.FontWeight.W_500),
        text_style=ft.TextStyle(color=TEXT_DARK, size=13),
        height=50,
        content_padding=12
    )
    
    contact_field = ft.TextField(
        label="Contact Number",
        value=current_user["user"].get("contact", ""), 
        width=300,
        keyboard_type=ft.KeyboardType.PHONE,
        bgcolor=TEXT_LIGHT,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_DARK,
        border_radius=8,
        label_style=ft.TextStyle(color=ACCENT_DARK, size=13, weight=ft.FontWeight.W_500),
        text_style=ft.TextStyle(color=TEXT_DARK, size=13),
        height=50,
        content_padding=12
    )

    # Order summary box - matching reference design with dynamic values
    summary_box = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Subtotal", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_400, width=80),
                        subtotal_text
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=10, color=FIELD_BORDER),
                ft.Row(
                    [
                        ft.Text("Total", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=80),
                        total_text
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ],
            spacing=0
        ),
        padding=12,
        bgcolor=TEXT_LIGHT,
        border_radius=12,
        border=ft.border.all(1.5, FIELD_BORDER),
        width=400
    )

    def place_order(e):
        if not cart:
            show_snackbar(page, "Cart is empty!")
            return
        if not name_field.value or not address_field.value or not contact_field.value:
            show_snackbar(page, "Please fill delivery details")
            return

        # Extract total from total_text (format: "₱123.45")
        total_amount = float(total_text.value.replace("₱", ""))
        
        create_order(
            current_user["user"]["id"],
            name_field.value,
            address_field.value,
            contact_field.value,
            cart,
            total_amount,
            selected_payment["value"]
        )
        cart.clear()
        refresh_cart()  # Update display to show empty cart
        show_snackbar(page, "Order placed successfully!")
        goto_confirmation(e)

    # Checkout button
    checkout_button = ft.Container(
        content=ft.ElevatedButton(
            "Checkout",
            width=280,
            height=50,
            bgcolor=ACCENT_DARK,
            color=TEXT_LIGHT,
            on_click=place_order,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_500)
            )
        ),
        alignment=ft.alignment.center
    )

    # Initialize cart display
    refresh_cart()

    # Main layout
    return ft.Container(
        content=ft.Column(
            [
                # Header
                ft.Container(height=12),
                
                ft.TextButton(
                    "← back to menu", 
                    on_click=goto_menu, 
                    style=ft.ButtonStyle(color=ACCENT_DARK)
                ),
                
                ft.Container(height=8),

                # Title
                ft.Text("My cart", size=20, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                
                ft.Container(height=16),
                
                # Cart items
                ft.Container(
                    content=cart_items_container,
                    height=300,
                    margin=ft.margin.only(bottom=10)
                ),

                ft.Container(height=20),
                
                # Order summary
                summary_box,
                
                ft.Container(height=16),
                
                # Checkout button
                checkout_button,
                
                ft.Container(height=20),
                
                # Payment Method section
                ft.Text("Payment Method", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Container(height=8),
                payment_chips_row,
                
                ft.Container(height=20),
                
                # Delivery Information section (initially hidden, can be shown on edit)
                ft.Text("Delivery Information", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                
                ft.Container(height=8),

                name_field,
                ft.Container(height=8),
                address_field,
                ft.Container(height=8),
                contact_field,
                
                ft.Container(height=20),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True,
        padding=20,
        bgcolor=FIELD_BG
    )
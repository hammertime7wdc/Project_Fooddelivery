import flet as ft
from core.database import create_order
from core.phone_utils import normalize_ph_to_e164, display_ph_local
from utils import show_snackbar, TEXT_LIGHT, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, DARK_GREEN, ORANGE
from screens.browse_menu.image_utils import load_image_from_binary
from screens.login_loading import show_login_loading, hide_login_loading

def cart_screen(page: ft.Page, current_user: dict, cart: list, goto_menu, goto_confirmation):
    viewport_width = page.width if page.width else 390
    content_width = min(max(viewport_width - 36, 280), 430)
    field_width = content_width - 28
    cart_list_height = 260 if viewport_width <= 420 else 300
    
    # Create containers that will be updated
    cart_items_container = ft.ListView(spacing=12, padding=0, auto_scroll=False, expand=True)
    subtotal_text = ft.Text("₱0.00", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.RIGHT)
    total_text = ft.Text("₱0.00", size=16, weight=ft.FontWeight.BOLD, color=ORANGE, text_align=ft.TextAlign.RIGHT)
    
    def refresh_cart():
        """Refresh cart display and totals"""
        cart_items_container.controls.clear()
        total = 0

        if not cart:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(name=ft.Icons.SHOPPING_CART_OUTLINED, size=80, color=ORANGE),
                    ft.Container(height=10),
                    ft.Text("Your cart is empty", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                    ft.Text("Add items from the menu to get started", size=14, weight=ft.FontWeight.W_500, color=ACCENT_DARK),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                height=220,
                alignment=ft.alignment.center,
                border_radius=16,
                bgcolor=FIELD_BG,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=16, color="black12", offset=ft.Offset(0, 6)),
            )
            cart_items_container.controls.append(empty_state)
            subtotal_text.value = "₱0.00"
            total_text.value = "₱0.00"
            page.update()
            return

        for idx, item in enumerate(cart):
            item_total = item["price"] * item["quantity"]
            total += item_total
            image_widget = load_image_from_binary(item) if item.get("image") else None

            def remove_item(e, item_idx=idx):
                if 0 <= item_idx < len(cart):
                    del cart[item_idx]
                    refresh_cart()

            item_card = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=image_widget if image_widget else ft.Icon(
                            name=ft.Icons.FASTFOOD,
                            size=32,
                            color=ORANGE
                        ),
                        width=56,
                        height=56,
                        bgcolor="#FFF5E6",
                        border_radius=28,
                        alignment=ft.alignment.center,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        margin=ft.margin.only(right=10)
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"{item['quantity']} ×", size=13, weight=ft.FontWeight.W_600, color=ACCENT_DARK),
                            ft.Text(item['name'], size=14, weight=ft.FontWeight.W_500, color=TEXT_DARK, expand=True, max_lines=1),
                        ], spacing=6, alignment=ft.MainAxisAlignment.START),
                        ft.Text(f"₱{item_total:.2f}", size=13, weight=ft.FontWeight.W_600, color=ORANGE),
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=18,
                        icon_color="red700",
                        on_click=remove_item,
                        padding=4
                    ),
                ], spacing=10, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=14,
                bgcolor=TEXT_LIGHT,
                border_radius=14,
                border=ft.border.all(1.5, FIELD_BORDER),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black12", offset=ft.Offset(0, 2)),
                margin=ft.margin.only(bottom=2),
                width=content_width
            )
            cart_items_container.controls.append(item_card)

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
        width=field_width,
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
        width=field_width,
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
        value=display_ph_local(current_user["user"].get("contact", "")),
        width=field_width,
        keyboard_type=ft.KeyboardType.PHONE,
        prefix_text="+63 ",
        max_length=10,
        input_filter=ft.NumbersOnlyInputFilter(),
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

    name_error = ft.Text("", size=11, color="red", visible=False)
    address_error = ft.Text("", size=11, color="red", visible=False)
    contact_error = ft.Text("", size=11, color="red", visible=False)

    def _clear_field_error(field, error_text):
        field.border_color = FIELD_BORDER
        error_text.visible = False
        error_text.value = ""
        page.update()

    def _show_field_error(field, error_text, msg):
        field.border_color = "red"
        error_text.value = msg
        error_text.visible = True

    name_field.on_change = lambda e: _clear_field_error(name_field, name_error)
    address_field.on_change = lambda e: _clear_field_error(address_field, address_error)
    contact_field.on_change = lambda e: _clear_field_error(contact_field, contact_error)

    # Order summary box - matching reference design with dynamic values
    summary_box = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Subtotal", size=13, color=TEXT_DARK, weight=ft.FontWeight.W_400),
                subtotal_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=10, color=FIELD_BORDER),
            ft.Row([
                ft.Text("Total", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                total_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=4),
        padding=16,
        bgcolor=TEXT_LIGHT,
        border_radius=14,
        border=ft.border.all(1.5, FIELD_BORDER),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color="black12", offset=ft.Offset(0, 2)),
        width=content_width
    )

    def place_order(e):
        if not cart:
            show_snackbar(page, "Cart is empty!")
            return

        has_error = False
        if not name_field.value or not name_field.value.strip():
            _show_field_error(name_field, name_error, "Full name is required.")
            has_error = True
        if not address_field.value or not address_field.value.strip():
            _show_field_error(address_field, address_error, "Delivery address is required.")
            has_error = True
        if not contact_field.value or not contact_field.value.strip():
            _show_field_error(contact_field, contact_error, "Contact number is required.")
            has_error = True
        if has_error:
            page.update()
            return

        checkout_btn.disabled = True
        loading_overlay = show_login_loading(page, "Placing your order...")
        page.update()

        # Extract total from total_text (format: "₱123.45")
        try:
            total_amount = float(total_text.value.replace("₱", ""))
            normalized_contact = normalize_ph_to_e164(contact_field.value)
            if not normalized_contact:
                hide_login_loading(page, loading_overlay)
                _show_field_error(contact_field, contact_error, "Enter a valid PH mobile number (e.g. 9XXXXXXXXX).")
                checkout_btn.disabled = False
                page.update()
                return

            create_order(
                current_user["user"]["id"],
                name_field.value,
                address_field.value,
                normalized_contact,
                cart,
                total_amount,
                selected_payment["value"]
            )
            cart.clear()
            refresh_cart()  # Update display to show empty cart
            hide_login_loading(page, loading_overlay)
            show_snackbar(page, "Order placed successfully!")
            goto_confirmation(e)
        except Exception:
            hide_login_loading(page, loading_overlay)
            show_snackbar(page, "Failed to place order. Please try again.")
        finally:
            checkout_btn.disabled = False
            hide_login_loading(page, loading_overlay)
            page.update()

    # Checkout button
    checkout_btn = ft.ElevatedButton(
        "Checkout",
        width=content_width,
        height=52,
        bgcolor=ACCENT_DARK,
        color=TEXT_LIGHT,
        on_click=place_order,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600),
            shadow_color=ACCENT_DARK,
        )
    )

    checkout_button = ft.Container(
        content=checkout_btn,
        alignment=ft.alignment.center,
        margin=ft.margin.only(top=8, bottom=8)
    )

    # Initialize cart display
    refresh_cart()

    # Main layout
    return ft.Container(
        content=ft.Column([
            ft.Container(height=10),
            ft.TextButton(
                "← back to menu",
                on_click=goto_menu,
                style=ft.ButtonStyle(color=ACCENT_DARK, text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500))
            ),
            ft.Container(height=6),
            ft.Text("My Cart", size=24, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
            ft.Container(height=10),
            ft.Container(
                content=cart_items_container,
                height=cart_list_height,
                bgcolor=FIELD_BG,
                border_radius=16,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black12", offset=ft.Offset(0, 2)),
                margin=ft.margin.only(bottom=10),
                width=content_width
            ),
            ft.Container(height=10),
            summary_box,
            checkout_button,
            ft.Container(height=10),
            ft.Divider(height=18, color=FIELD_BORDER),
            ft.Text("Payment Method", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
            ft.Container(height=8),
            ft.Container(
                content=payment_chips_row,
                bgcolor=FIELD_BG,
                border_radius=12,
                padding=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color="black12", offset=ft.Offset(0, 2)),
                margin=ft.margin.only(bottom=10),
                width=content_width
            ),
            ft.Divider(height=18, color=FIELD_BORDER),
            ft.Text("Delivery Information", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
            ft.Container(height=8),
            ft.Container(
                content=ft.Column([
                    name_field,
                    name_error,
                    ft.Container(height=6),
                    address_field,
                    address_error,
                    ft.Container(height=6),
                    contact_field,
                    contact_error,
                ], spacing=0),
                bgcolor=FIELD_BG,
                border_radius=12,
                padding=14,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color="black12", offset=ft.Offset(0, 2)),
                margin=ft.margin.only(bottom=10),
                width=content_width
            ),
            ft.Container(height=10),
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        padding=20,
        bgcolor=FIELD_BG
    )
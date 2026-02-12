"""Menu item handlers and cart operations"""
import threading
import time
import flet as ft
from core.database import add_favorite, remove_favorite
from utils import show_snackbar, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK


def create_add_to_cart_handler(page, cart, ui_update_lock):
    """Create add to cart handler with button animation"""
    def add_to_cart(item, qty, add_button=None):
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
            message = f"Updated {item['name']} quantity to {existing_item['quantity']}"
        else:
            # Add new item to cart
            cart.append({"id": item["id"], "name": item["name"], "price": item["price"], "quantity": qty})
            message = f"Added {qty} x {item['name']} to cart"
        
        # Show checkmark animation on button WITHOUT blocking UI
        if add_button:
            def animate_button():
                try:
                    original_icon = add_button.icon
                    original_color = add_button.icon_color
                    
                    # Change to checkmark
                    with ui_update_lock:
                        add_button.icon = ft.Icons.CHECK
                        add_button.icon_color = "#4CAF50"
                        page.update()
                    
                    # Non-blocking wait
                    time.sleep(0.8)
                    
                    # Restore original icon
                    with ui_update_lock:
                        add_button.icon = original_icon
                        add_button.icon_color = original_color
                        page.update()
                except Exception as e:
                    print(f"Error in button animation: {e}")
            
            # Run animation in background thread to avoid blocking UI
            threading.Thread(target=animate_button, daemon=True).start()
        
        show_snackbar(page, message)
    
    return add_to_cart


def create_quantity_handlers(page, ui_update_lock):
    """Create quantity increase/decrease handlers"""
    def make_decrease_qty(qty_state_ref, display):
        def decrease(e):
            if qty_state_ref["value"] > 1:
                qty_state_ref["value"] -= 1
                display.value = str(qty_state_ref["value"])
                with ui_update_lock:
                    page.update()
        return decrease
    
    def make_increase_qty(qty_state_ref, display):
        def increase(e):
            qty_state_ref["value"] += 1
            display.value = str(qty_state_ref["value"])
            with ui_update_lock:
                page.update()
        return increase
    
    return make_decrease_qty, make_increase_qty


def create_favorite_toggle_handler(page, user_id, favorites, ui_update_lock):
    """Create favorite toggle handler"""
    def make_toggle_favorite(item_id_ref, fav_btn_ref):
        def toggle(e):
            if item_id_ref in favorites:
                favorites.remove(item_id_ref)
                remove_favorite(user_id, item_id_ref)
                fav_btn_ref.icon = ft.Icons.FAVORITE_BORDER
                fav_btn_ref.icon_color = "#BDBDBD"
            else:
                favorites.add(item_id_ref)
                add_favorite(user_id, item_id_ref)
                fav_btn_ref.icon = ft.Icons.FAVORITE
                fav_btn_ref.icon_color = "#FF6B6B"
            with ui_update_lock:
                page.update()
        return toggle
    
    return make_toggle_favorite


def create_card_hover_handler(page, ui_update_lock):
    """Create card hover effect handler"""
    def card_hover(e, card):
        with ui_update_lock:
            if e.data == "true":
                # Elevated shadow on hover
                card.shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=12,
                    color="#33000000",
                    offset=ft.Offset(0, 4)
                )
                card.bgcolor = "#FFFFFF"
            else:
                # Normal shadow
                card.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color="#1A000000",
                    offset=ft.Offset(0, 2)
                )
                card.bgcolor = FIELD_BG
            page.update()
    
    return card_hover

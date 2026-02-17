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

        stock = item.get("stock", None)
        if stock is not None:
            try:
                stock = int(stock)
            except Exception:
                stock = None

        if stock is not None and stock <= 0:
            show_snackbar(page, "Out of stock")
            return

        # Check if item already exists in cart
        existing_item = None
        for cart_item in cart:
            if cart_item["id"] == item["id"]:
                existing_item = cart_item
                break
        
        if existing_item:
            # Update quantity of existing item
            if stock is not None and existing_item["quantity"] + qty > stock:
                show_snackbar(page, f"Only {stock} left in stock")
                return
            existing_item["quantity"] += qty
            message = f"Updated {item['name']} quantity to {existing_item['quantity']}"
        else:
            # Add new item to cart
            if stock is not None and qty > stock:
                show_snackbar(page, f"Only {stock} left in stock")
                return
            cart.append({
                "id": item["id"], 
                "name": item["name"], 
                "price": item["price"], 
                "quantity": qty,
                "image": item.get("image", ""),
                "image_type": item.get("image_type", ""),
                "restaurant": item.get("restaurant", "")
            })
            message = f"Added {qty} x {item['name']} to cart"
        
        # Show checkmark animation on button WITHOUT blocking UI
        if add_button:
            def animate_button():
                try:
                    original_icon = add_button.icon
                    original_color = add_button.icon_color
                    
                    # Change to checkmark
                    with ui_update_lock:
                        # Check if button still exists and is attached
                        if hasattr(add_button, 'icon') and add_button.page is not None:
                            add_button.icon = ft.Icons.CHECK
                            add_button.icon_color = "#4CAF50"
                            try:
                                page.update()
                            except:
                                pass
                    
                    # Non-blocking wait
                    time.sleep(0.8)
                    
                    # Restore original icon
                    with ui_update_lock:
                        # Check again before restoring
                        if hasattr(add_button, 'icon') and add_button.page is not None:
                            add_button.icon = original_icon
                            add_button.icon_color = original_color
                            try:
                                page.update()
                            except:
                                pass
                except Exception:
                    # Silently ignore errors during navigation
                    pass
            
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
                    try:
                        page.update()
                    except:
                        pass
        return decrease
    
    def make_increase_qty(qty_state_ref, display, max_qty=None):
        def increase(e):
            if max_qty is not None and qty_state_ref["value"] >= max_qty:
                show_snackbar(page, f"Only {max_qty} left in stock")
                return
            qty_state_ref["value"] += 1
            display.value = str(qty_state_ref["value"])
            with ui_update_lock:
                try:
                    page.update()
                except:
                    pass
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
                try:
                    page.update()
                except:
                    pass
        return toggle
    
    return make_toggle_favorite


def create_card_hover_handler(page, ui_update_lock):
    """Create card hover effect handler - lifts forward on hover"""
    def card_hover(e, card):
        with ui_update_lock:
            if e.data == "true":
                # Lift forward with scale and elevation
                card.scale = 1.03
                card.shadow = ft.BoxShadow(
                    spread_radius=3,
                    blur_radius=15,
                    color="#40000000",
                    offset=ft.Offset(0, 6)
                )
            else:
                # Return to normal
                card.scale = 1.0
                card.shadow = ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=4,
                    color="#1A000000",
                    offset=ft.Offset(0, 2)
                )
            try:
                page.update()
            except:
                pass
    
    return card_hover

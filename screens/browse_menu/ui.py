"""UI components for browse menu"""
import flet as ft
import threading
from core.database import get_menu_items_page, get_categories
from utils import TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, TEXT_LIGHT
from .image_utils import load_image_from_binary
from .handlers import create_add_to_cart_handler, create_quantity_handlers, create_favorite_toggle_handler, create_card_hover_handler


def create_menu_item_card(item, page, cart, user_id, favorites, ui_update_lock, add_to_cart):
    """Create a single menu item card"""
    # Quantity state for each item
    qty_state = {"value": 1}
    item_id = item["id"]
    is_favorited = item_id in favorites
    
    # Quantity display text
    qty_display = ft.Text(
        "1",
        size=13,
        color=TEXT_DARK,
        weight=ft.FontWeight.BOLD,
        width=20,
        text_align=ft.TextAlign.CENTER
    )
    
    # Get handlers
    make_decrease_qty, make_increase_qty = create_quantity_handlers(page, ui_update_lock)
    make_toggle_favorite = create_favorite_toggle_handler(page, user_id, favorites, ui_update_lock)
    
    # Heart button
    fav_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_favorited else ft.Icons.FAVORITE_BORDER,
        icon_color="#FF6B6B" if is_favorited else "#BDBDBD",
        icon_size=22
    )
    fav_btn.on_click = make_toggle_favorite(item_id, fav_btn)
    
    # Add to cart button with animation
    add_btn_icon = ft.IconButton(
        icon=ft.Icons.SHOPPING_BAG,
        icon_color="#EBE1D1",
        icon_size=20
    )
    
    def make_add_click(item_ref, qty_ref, btn_ref):
        def click(e):
            add_to_cart(item_ref, qty_ref["value"], btn_ref)
        return click
    
    add_btn_icon.on_click = make_add_click(item, qty_state, add_btn_icon)
    
    add_btn = ft.Container(
        content=add_btn_icon,
        bgcolor=ACCENT_DARK,
        border_radius=10,
        padding=2
    )
    
    # Image widget (loads in background)
    image_widget = ft.Container(
        content=ft.Icon(ft.Icons.RESTAURANT, size=50, color="grey"),
        width=80,
        height=80,
        alignment=ft.alignment.center
    )

    def load_binary_image(item_data=item, img_widget=image_widget):
        """Load image from file/base64 in background - THREAD SAFE"""
        try:
            real_img = load_image_from_binary(item_data)
            if real_img:
                # Use lock to safely update UI from background thread
                with ui_update_lock:
                    img_widget.content = real_img
                    page.update()
        except Exception as e:
            print(f"Error loading image in background: {e}")

    # Load image in background thread (non-blocking) - THREAD SAFE
    threading.Thread(target=load_binary_image, daemon=True).start()

    # Create card container reference for hover effect
    card_container = ft.Container(
        content=ft.Column([
            ft.Row([
                image_widget,
                ft.Column([
                    ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text(item["description"], size=12, color=TEXT_DARK),
                    ft.Text(f"₱{item['price']:.2f}", size=14, color=ACCENT_PRIMARY)
                ], expand=True, spacing=2)
            ], spacing=12),
            ft.Row([
                fav_btn,
                ft.Row([], expand=True),  # Spacer
                ft.Row([
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            icon_color=TEXT_DARK,
                            icon_size=18,
                            on_click=make_decrease_qty(qty_state, qty_display)
                        ),
                        border_radius=8,
                        border=ft.border.all(1, FIELD_BORDER)
                    ),
                    qty_display,
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_color=TEXT_DARK,
                            icon_size=18,
                            on_click=make_increase_qty(qty_state, qty_display)
                        ),
                        border_radius=8,
                        border=ft.border.all(1, FIELD_BORDER)
                    ),
                    add_btn
                ], spacing=8)
            ], spacing=10)
        ], spacing=8),
        padding=10,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        bgcolor=FIELD_BG,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=4,
            color="#1A000000",
            offset=ft.Offset(0, 2)
        )
    )

    card_hover = create_card_hover_handler(page, ui_update_lock)
    card_container.on_hover = lambda e: card_hover(e, card_container)

    return card_container


def create_category_chips(selected_category, load_menu_callback, page, ui_update_lock):
    """Create category filter chips"""
    categories = ["❤️ Favorites", "All"] + get_categories()
    chips = []
    
    def make_chip_click(cat):
        def on_click(e):
            selected_category["value"] = cat
            load_menu_callback(category=cat, search="", reset_page=True)
            # Update chip styles
            with ui_update_lock:
                for i, chip_cat in enumerate(categories):
                    chips[i].bgcolor = ACCENT_DARK if chip_cat == cat else "#E0E0E0"
                    chips[i].content.color = "#FFFFFF" if chip_cat == cat else TEXT_DARK
                page.update()
        return on_click
    
    for cat in categories:
        is_selected = cat == selected_category["value"]
        chip = ft.Container(
            content=ft.Text(cat, size=13, color="#FFFFFF" if is_selected else TEXT_DARK, weight=ft.FontWeight.W_500),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            on_click=make_chip_click(cat)
        )
        chips.append(chip)
    
    return ft.Row(chips, spacing=8, wrap=True, scroll=ft.ScrollMode.AUTO)


def create_search_field(load_menu_callback, selected_category):
    """Create search input field"""
    return ft.TextField(
        hint_text="Search menu...", 
        width=300, 
        on_change=lambda e: load_menu_callback(category=selected_category["value"], search=e.control.value, reset_page=True),
        bgcolor=FIELD_BG,
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        hint_style=ft.TextStyle(color="#000000"),
        text_style=ft.TextStyle(color="#000000")
    )


def create_pagination_controls(current_page, total_pages, selected_category, search_field, load_menu_callback, page_info_text):
    """Create pagination control buttons"""
    
    def goto_first_page(e):
        current_page["page"] = 1
        load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_prev_page(e):
        if current_page["page"] > 1:
            current_page["page"] -= 1
            load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_next_page(e):
        if current_page["page"] < total_pages["count"]:
            current_page["page"] += 1
            load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_last_page(e):
        current_page["page"] = total_pages["count"]
        load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)
    
    swipe_hint = ft.Text(
        "← Swipe to browse →",
        size=12,
        color="grey",
        text_align=ft.TextAlign.CENTER,
        italic=True
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
                    icon_color="#EBE1D1",
                    icon_size=20,
                    on_click=goto_first_page,
                    tooltip="First",
                    bgcolor=ACCENT_DARK,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_color="#EBE1D1",
                    icon_size=20,
                    on_click=goto_prev_page,
                    tooltip="Previous",
                    bgcolor=ACCENT_DARK,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.Container(
                    content=page_info_text,
                    bgcolor="#EBE1D1",
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=25, vertical=10),
                    border=ft.border.all(2, ACCENT_PRIMARY),
                    alignment=ft.alignment.center
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_color="#EBE1D1",
                    icon_size=20,
                    on_click=goto_next_page,
                    tooltip="Next",
                    bgcolor=ACCENT_DARK,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                ft.IconButton(
                    icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
                    icon_color="#EBE1D1",
                    icon_size=20,
                    on_click=goto_last_page,
                    tooltip="Last",
                    bgcolor=ACCENT_DARK,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
            ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
            swipe_hint
        ], spacing=8),
        padding=ft.padding.symmetric(vertical=12, horizontal=10)
    )

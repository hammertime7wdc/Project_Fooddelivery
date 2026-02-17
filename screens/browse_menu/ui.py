"""UI components for browse menu"""
import flet as ft
import threading
import json
import time
from pathlib import Path
from core.database import get_menu_items_page, get_categories, get_menu_item_stats
from utils import TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, TEXT_LIGHT
from .image_utils import load_image_from_binary
from .handlers import create_add_to_cart_handler, create_quantity_handlers, create_favorite_toggle_handler, create_card_hover_handler


def create_rotating_promo_banner(page):
    """Create auto-rotating promotional banner"""
    # Load messages from JSON
    messages_file = Path(__file__).parent.parent.parent / "assets" / "promo_messages.json"
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            messages = data.get("messages", ["Welcome to our restaurant!"])
    except Exception as e:
        print(f"Error loading promo messages: {e}")
        messages = ["Welcome to our restaurant!"]
    
    # Current message index
    current_index = {"value": 0}
    
    # Text display
    banner_text = ft.Text(
        messages[0],
        size=14,
        color=TEXT_LIGHT,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER
    )
    
    banner_container = ft.Container(
        content=banner_text,
        bgcolor="#E9762B",  # Orange background
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        border_radius=0,
        animate_opacity=300
    )
    
    def rotate_message():
        """Background thread to rotate messages"""
        while True:
            time.sleep(5)  # Change message every 5 seconds
            current_index["value"] = (current_index["value"] + 1) % len(messages)
            banner_text.value = messages[current_index["value"]]
            try:
                page.update()
            except:
                break  # Exit if page is closed
    
    # Start rotation in background
    threading.Thread(target=rotate_message, daemon=True).start()
    
    return banner_container


def create_feature_carousel(page):
    """Create auto-rotating feature carousel with deals, new items, and popular dishes"""
    # Load carousel items from JSON
    carousel_file = Path(__file__).parent.parent.parent / "assets" / "carousel_items.json"
    try:
        with open(carousel_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get("items", [])
    except Exception as e:
        print(f"Error loading carousel items: {e}")
        items = [{
            "title": "Welcome!",
            "description": "Check out our amazing menu",
            "image": None,
            "bg_color": "#0D4715"
        }]
    
    if not items:
        items = [{
            "title": "Welcome!",
            "description": "Check out our amazing menu",
            "image": None,
            "bg_color": "#0D4715"
        }]
    
    # Current item index
    current_index = {"value": 0}
    
    # Title text
    title_text = ft.Text(
        items[0]["title"],
        size=24,
        color=TEXT_LIGHT,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER
    )
    
    # Description text
    desc_text = ft.Text(
        items[0]["description"],
        size=16,
        color=TEXT_LIGHT,
        weight=ft.FontWeight.W_400,
        text_align=ft.TextAlign.CENTER
    )
    
    # Create navigation dots
    dots = []
    for i in range(len(items)):
        dot = ft.Container(
            width=8,
            height=8,
            border_radius=4,
            bgcolor=TEXT_LIGHT if i == 0 else "white30",
            data=i
        )
        dots.append(dot)
    
    dots_row = ft.Row(
        controls=dots,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8
    )
    
    # Main carousel content
    carousel_content = ft.Container(
        content=ft.Column([
            ft.Container(height=20),  # Top spacing
            title_text,
            ft.Container(height=10),
            desc_text,
            ft.Container(height=20),  # Bottom spacing before dots
            dots_row,
            ft.Container(height=10)
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=items[0]["bg_color"],
        height=200,
        border_radius=12,
        animate_opacity=300,
        padding=20
    )
    
    def update_carousel(index):
        """Update carousel to show item at given index"""
        try:
            item = items[index]
            # Check if controls still exist and are attached
            if hasattr(title_text, 'value') and title_text.page is not None:
                title_text.value = item["title"]
                desc_text.value = item["description"]
                carousel_content.bgcolor = item["bg_color"]
                
                # Update dots
                for i, dot in enumerate(dots):
                    if hasattr(dot, 'bgcolor') and dot.page is not None:
                        dot.bgcolor = TEXT_LIGHT if i == index else "white30"
                
                page.update()
        except:
            pass
    
    def rotate_carousel():
        """Background thread to auto-rotate carousel"""
        while True:
            time.sleep(6)  # Change every 6 seconds
            # Check if carousel still exists before updating
            if carousel_content.page is None or not hasattr(title_text, 'value'):
                break  # Stop rotation if controls are removed
            current_index["value"] = (current_index["value"] + 1) % len(items)
            update_carousel(current_index["value"])
    
    def make_dot_click(index):
        """Create click handler for navigation dot"""
        def click(e):
            current_index["value"] = index
            update_carousel(index)
        return click
    
    # Add click handlers to dots
    for i, dot in enumerate(dots):
        dot.on_click = make_dot_click(i)
        dot.ink = True
    
    # Start auto-rotation in background
    threading.Thread(target=rotate_carousel, daemon=True).start()
    
    return carousel_content


def create_menu_item_card(item, page, cart, user_id, favorites, ui_update_lock, add_to_cart):
    """Create a single menu item card"""
    stock_value = item.get("stock", None)
    try:
        stock_value = int(stock_value) if stock_value is not None else None
    except Exception:
        stock_value = None
    out_of_stock = stock_value is not None and stock_value <= 0
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
        icon_color="#EBE1D1" if not out_of_stock else "#FFFFFF",
        icon_size=20,
        disabled=out_of_stock
    )
    
    def make_add_click(item_ref, qty_ref, btn_ref):
        def click(e):
            # Create a modified item with sale price for cart
            item_for_cart = item_ref.copy()
            item_for_cart["price"] = display_price
            add_to_cart(item_for_cart, qty_ref["value"], btn_ref)
        return click
    
    add_btn_icon.on_click = make_add_click(item, qty_state, add_btn_icon)
    
    add_btn = ft.Container(
        content=add_btn_icon,
        bgcolor=ACCENT_DARK if not out_of_stock else "#BDBDBD",
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
            if real_img and img_widget:
                # Retry a few times until the widget is attached to the page
                for _ in range(10):
                    with ui_update_lock:
                        if hasattr(img_widget, "content") and img_widget.page is not None:
                            img_widget.content = real_img
                            try:
                                page.update()
                            except Exception:
                                # Ignore errors if page is being cleared/navigated
                                pass
                            return
                    time.sleep(0.1)
        except Exception:
            # Silently ignore errors during navigation
            pass

    # Load image in background thread (non-blocking) - THREAD SAFE
    threading.Thread(target=load_binary_image, daemon=True).start()

    # Create card container reference for hover effect
    minus_btn = ft.IconButton(
        icon=ft.Icons.REMOVE,
        icon_color=TEXT_DARK,
        icon_size=18,
        disabled=out_of_stock,
        on_click=make_decrease_qty(qty_state, qty_display)
    )

    plus_btn = ft.IconButton(
        icon=ft.Icons.ADD,
        icon_color=TEXT_DARK,
        icon_size=18,
        disabled=out_of_stock,
        on_click=make_increase_qty(qty_state, qty_display, stock_value)
    )

    stock_text = (
        f"Stock: {stock_value}" if stock_value is not None and stock_value > 0 else "Out of stock"
    )
    stock_color = "#000000" if not out_of_stock else "#C62828"
    
    # Calculate sale price if on sale
    is_on_sale = item.get('is_on_sale', 0)
    sale_percentage = item.get('sale_percentage', 0)
    original_price = item['price']
    display_price = original_price
    
    if is_on_sale and sale_percentage > 0:
        discount_multiplier = (100 - sale_percentage) / 100
        display_price = original_price * discount_multiplier

    # Click handler to show item details
    def show_item_details(e):
        stats = get_menu_item_stats(item_id)
        
        # Build nutrition info if available
        nutrition_info = []
        if item.get('calories') or item.get('allergens'):
            nutrition_rows = []
            if item.get('calories'):
                nutrition_rows.append(
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color="#FF5722", size=16),
                        ft.Text(f"{item['calories']} cal", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500)
                    ], spacing=6)
                )
            
            if item.get('allergens'):
                nutrition_rows.append(
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, color="#FF9800", size=16),
                        ft.Text(item['allergens'], size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500)
                    ], spacing=6)
                )
            
            nutrition_info.append(
                ft.Container(
                    content=ft.Row(nutrition_rows, spacing=15, wrap=True),
                    bgcolor="#FFF3E0",
                    padding=10,
                    border_radius=8
                )
            )
        
        # Build ingredients section
        ingredients_section = []
        if item.get('ingredients'):
            ingredients_section.append(ft.Container(height=5))
            ingredients_section.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("🥘 Ingredients", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                        ft.Container(height=5),
                        ft.Text(item['ingredients'], size=12, color=TEXT_DARK)
                    ], spacing=0),
                    bgcolor="#F5F5F5",
                    padding=12,
                    border_radius=8
                )
            )
        
        # Build recipe section
        recipe_section = []
        if item.get('recipe'):
            recipe_section.append(ft.Container(height=5))
            recipe_section.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("👨‍🍳 Recipe", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                        ft.Container(height=5),
                        ft.Text(item['recipe'], size=12, color=TEXT_DARK)
                    ], spacing=0),
                    bgcolor="#F5F5F5",
                    padding=12,
                    border_radius=8
                )
            )
        
        # Build stats section if available
        stats_section = []
        if stats:
            stats_section.extend([
                ft.Container(height=5),
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Sales Stats", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                        ft.Container(height=8),
                        ft.Row([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(str(stats['total_orders']), size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                                    ft.Text("Orders", size=11, color="#757575")
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                expand=True
                            ),
                            ft.Container(width=1, height=40, bgcolor=FIELD_BORDER),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(str(stats['total_quantity_sold']), size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                                    ft.Text("Sold", size=11, color="#757575")
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                expand=True
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=0),
                    bgcolor="#F5F5F5",
                    border_radius=10,
                    padding=15
                )
            ])
        
        detail_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Text(item['name'], size=20, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Container(
                    content=ft.Text(f"-{sale_percentage}% OFF", size=12, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    bgcolor="#E53935",
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=5,
                    visible=is_on_sale and sale_percentage > 0
                )
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(item['description'], size=13, color="#666666", italic=True),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Column([
                            ft.Text(
                                f"₱{original_price:.2f}",
                                size=14,
                                color="#999999",
                                weight=ft.FontWeight.W_400,
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                                visible=is_on_sale and sale_percentage > 0
                            ),
                            ft.Text(f"₱{display_price:.2f}", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY)
                        ], spacing=2),
                        ft.Container(width=15),
                        ft.Container(
                            content=ft.Text(f"Stock: {item['stock']}", size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500),
                            bgcolor="#E8F5E9" if item['stock'] > 0 else "#FFEBEE",
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=15
                        ),
                    ], spacing=0),
                    ft.Container(height=5),
                    *nutrition_info,
                    *ingredients_section,
                    *recipe_section,
                    *stats_section,
                ], spacing=5, scroll=ft.ScrollMode.AUTO),
                width=380,
                padding=15,
                bgcolor="white"
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.close(detail_dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor="white"
        )
        page.open(detail_dialog)
    
    card_container = ft.Container(
        content=ft.Column([
            ft.Row([
                image_widget,
                ft.Column([
                    ft.Row([
                        ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Container(
                            content=ft.Text(f"-{sale_percentage}%", size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            bgcolor="#E53935",
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4,
                            visible=is_on_sale and sale_percentage > 0
                        )
                    ], spacing=6),
                    ft.Text(item["description"], size=12, color=TEXT_DARK),
                    ft.Row([
                        ft.Text(
                            f"₱{original_price:.2f}",
                            size=12,
                            color="#999999",
                            weight=ft.FontWeight.W_400,
                            visible=is_on_sale and sale_percentage > 0,
                            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH)
                        ),
                        ft.Text(f"₱{display_price:.2f}", size=14, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD)
                    ], spacing=6),
                    ft.Text(stock_text, size=12, color=stock_color, weight=ft.FontWeight.W_500)
                ], expand=True, spacing=2)
            ], spacing=12),
            ft.Row([
                fav_btn,
                ft.Row([], expand=True),  # Spacer
                ft.Row([
                    ft.Container(
                        content=minus_btn,
                        border_radius=8,
                        border=ft.border.all(1, FIELD_BORDER)
                    ),
                    qty_display,
                    ft.Container(
                        content=plus_btn,
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
        bgcolor=TEXT_LIGHT,
        animate_scale=300,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=4,
            color="#1A000000",
            offset=ft.Offset(0, 2)
        ),
        ink=True,
        on_click=show_item_details
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
        border_radius=12,
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

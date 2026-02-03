import flet as ft
import threading
import time
from core.database import get_categories, get_menu_items_page, get_user_favorites, add_favorite, remove_favorite
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

# Image cache to avoid reloading
image_cache = {}
# Thread lock for UI updates
ui_update_lock = threading.Lock()

def load_image_from_binary(item):
    """Load image from file path - for fast binary transmission"""
    try:
        item_id = item.get("id")
        
        # Check cache first
        if item_id in image_cache:
            return image_cache[item_id]
        
        # Load from file path stored in database
        if item.get("image_type") == "path" and item.get("image"):
            # Path is relative: "uuid.jpg" -> full path: "assets/menu/uuid.jpg"
            img_path = f"assets/menu/{item['image']}"
            img = ft.Image(
                src=img_path,
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
            image_cache[item_id] = img
            return img
        elif item.get("image_type") == "base64" and item.get("image"):
            # Fallback for old base64 data
            img = ft.Image(
                src_base64=item["image"],
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
            image_cache[item_id] = img
            return img
        
        return None
    except Exception as e:
        print(f"Error loading image for item {item.get('id')}: {e}")
        return None

def browse_menu_screen(page: ft.Page, current_user: dict, cart: list, goto_cart, goto_profile, goto_history, goto_logout):
    # Pagination state
    current_page = {"page": 1}
    items_per_page = 10
    total_pages = {"count": 1}
    
    # Swipe gesture tracking
    swipe_start_x = {"value": 0}
    min_swipe_distance = 50  # Minimum pixels for swipe detection
    
    def on_pan(e):
        """Handle swipe gestures for pagination"""
        if e.state == "start":
            swipe_start_x["value"] = e.global_x
        elif e.state == "end":
            swipe_distance = e.global_x - swipe_start_x["value"]
            
            # Swipe right (previous page)
            if swipe_distance > min_swipe_distance and current_page["page"] > 1:
                current_page["page"] -= 1
                load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)
            
            # Swipe left (next page)
            elif swipe_distance < -min_swipe_distance and current_page["page"] < total_pages["count"]:
                current_page["page"] += 1
                load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)
    
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)
    menu_list.on_pan = on_pan
    
    # Selected category state for chips
    selected_category = {"value": "All"}
    
    # Load favorites from database
    user_id = current_user["user"]["id"]
    favorites = set(get_user_favorites(user_id))
    
    page_info_text = ft.Text("", size=13, color=TEXT_DARK, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_500)

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

    def load_menu(category="All", search="", reset_page=True):
        with ui_update_lock:
            if reset_page:
                current_page["page"] = 1
                
            menu_list.controls.clear()

            try:
                # Handle Favorites category
                if category == "❤️ Favorites":
                    if not favorites:
                        menu_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=80, color="grey"),
                                    ft.Text("No favorites yet", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Text("Add items to your favorites", size=14, color="grey"),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                                padding=50,
                                alignment=ft.alignment.center
                            )
                        )
                        page.update()
                        return
                    
                    # Get all items and filter by favorites
                    all_items = []
                    for fav_id in favorites:
                        for item in get_menu_items_page(limit=1000, offset=0).get("items", []):
                            if item["id"] == fav_id:
                                all_items.append(item)
                    
                    items = all_items[((current_page["page"]-1)*items_per_page):((current_page["page"])*items_per_page)]
                    total = len(all_items)
                    total_pages["count"] = max(1, (total + items_per_page - 1) // items_per_page)
                else:
                    offset = (current_page["page"] - 1) * items_per_page
                    result = get_menu_items_page(category=category, search=search, limit=items_per_page, offset=offset)
                    items = result.get("items", [])
                    total = result.get("total", 0)
                    
                    # Calculate total pages
                    total_pages["count"] = max(1, (total + items_per_page - 1) // items_per_page)
                
                # Ensure current page is within bounds
                if current_page["page"] > total_pages["count"]:
                    current_page["page"] = total_pages["count"]
                    offset = (current_page["page"] - 1) * items_per_page
                    result = get_menu_items_page(category=category, search=search, limit=items_per_page, offset=offset)
                    items = result.get("items", [])
                    total = result.get("total", 0)
                
                # Update page info
                page_info_text.value = f"{current_page['page']} / {total_pages['count']}"

                # Empty state when no items found
                if not items:
                    menu_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey"),
                                ft.Text("No items found", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Text("Try adjusting your search or filter", size=14, color="grey"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                            padding=50,
                            alignment=ft.alignment.center
                        )
                    )
                    page.update()
                    return

                for item in items:
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
                    
                    # Decrease quantity
                    def make_decrease_qty(qty_state_ref, display):
                        def decrease(e):
                            if qty_state_ref["value"] > 1:
                                qty_state_ref["value"] -= 1
                                display.value = str(qty_state_ref["value"])
                                with ui_update_lock:
                                    page.update()
                        return decrease
                    
                    # Increase quantity
                    def make_increase_qty(qty_state_ref, display):
                        def increase(e):
                            qty_state_ref["value"] += 1
                            display.value = str(qty_state_ref["value"])
                            with ui_update_lock:
                                page.update()
                        return increase
                    
                    # Favorite toggle
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
                    
                    # Image widget (loads in background - will be replaced by actual image in background thread)
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

                    def card_hover(e, card=card_container):
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

                    card_container.on_hover = card_hover

                    menu_list.controls.append(card_container)
                
                # Update once after all items added
                page.update()
                
            except Exception as e:
                print(f"Error loading menu: {e}")
                menu_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=80, color="#F44336"),
                            ft.Text("Error loading menu", size=20, weight=ft.FontWeight.BOLD, color="#F44336"),
                            ft.Text(str(e), size=12, color="grey"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        padding=50,
                        alignment=ft.alignment.center
                    )
                )
                page.update()

    def goto_first_page(e):
        current_page["page"] = 1
        load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_prev_page(e):
        if current_page["page"] > 1:
            current_page["page"] -= 1
            load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_next_page(e):
        if current_page["page"] < total_pages["count"]:
            current_page["page"] += 1
            load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)

    def goto_last_page(e):
        current_page["page"] = total_pages["count"]
        load_menu(category=selected_category["value"], search=search_field.value, reset_page=False)

    search_field = ft.TextField(
        hint_text="Search menu...", 
        width=300, 
        on_change=lambda e: load_menu(category=selected_category["value"], search=e.control.value, reset_page=True),
        bgcolor=FIELD_BG,
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        hint_style=ft.TextStyle(color="#000000"),
        text_style=ft.TextStyle(color="#000000")
    )

    # Category chips
    def create_category_chips():
        categories = ["❤️ Favorites", "All"] + get_categories()
        chips = []
        
        def make_chip_click(cat):
            def on_click(e):
                selected_category["value"] = cat
                load_menu(category=cat, search=search_field.value, reset_page=True)
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
    
    category_chips = create_category_chips()
    
    # Pagination controls - Simple clean design with swipe support
    swipe_hint = ft.Text(
        "← Swipe to browse →",
        size=12,
        color="grey",
        text_align=ft.TextAlign.CENTER,
        italic=True
    )
    
    pagination_controls = ft.Container(
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

    load_menu()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Menu", size=20, weight=ft.FontWeight.BOLD, color="#EBE1D1", expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.SHOPPING_CART, icon_color="#EBE1D1", on_click=goto_cart),
                            ft.IconButton(icon=ft.Icons.HISTORY, icon_color="#EBE1D1", on_click=goto_history),
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color="#EBE1D1", on_click=goto_profile),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color="#EBE1D1", on_click=goto_logout)
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=15,
                    border_radius=10
                ),

                search_field,
                ft.Container(content=category_chips, padding=ft.padding.symmetric(horizontal=10, vertical=5)),
                menu_list,
                pagination_controls
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        padding=10,
        bgcolor=FIELD_BG
    )
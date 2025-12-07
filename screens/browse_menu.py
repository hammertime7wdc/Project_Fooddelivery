import flet as ft
import threading
from core.database import get_all_menu_items, get_categories
from utils import show_snackbar, TEXT_LIGHT, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK

# Image cache to avoid reloading
image_cache = {}

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
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)
    
    # Pagination state
    current_page = {"page": 1}
    items_per_page = 10
    total_pages = {"count": 1}
    all_filtered_items = {"items": []}
    
    page_info_text = ft.Text("", size=13, color=TEXT_LIGHT, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_500)

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

    def load_menu(category="All", search="", reset_page=True):
        if reset_page:
            current_page["page"] = 1
            
        menu_list.controls.clear()
        items = get_all_menu_items()

        if category != "All":
            items = [item for item in items if item.get("category") == category]

        if search:
            items = [item for item in items if search.lower() in item["name"].lower() or search.lower() in item["description"].lower()]

        # Store all filtered items for pagination
        all_filtered_items["items"] = items
        
        # Calculate total pages
        total_pages["count"] = max(1, (len(items) + items_per_page - 1) // items_per_page)
        
        # Ensure current page is within bounds
        if current_page["page"] > total_pages["count"]:
            current_page["page"] = total_pages["count"]
        
        # Calculate pagination slice
        start_idx = (current_page["page"] - 1) * items_per_page
        end_idx = start_idx + items_per_page
        items = items[start_idx:end_idx]
        
        # Update page info
        page_info_text.value = f"{current_page['page']} / {total_pages['count']}"

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

            # Image widget (loads in background)
            image_widget = ft.Container(
                content=ft.Icon(ft.Icons.RESTAURANT, size=50, color="grey"),
                width=80,
                height=80,
                alignment=ft.alignment.center
            )

            def load_binary_image(item_data=item, img_widget=image_widget):
                """Load image from file/base64 in background"""
                try:
                    real_img = load_image_from_binary(item_data)
                    if real_img:
                        img_widget.content = real_img
                        # Small delay before update to batch changes
                        import time
                        time.sleep(0.05)
                        page.update()
                except:
                    pass

            # Load image in background thread (non-blocking)
            threading.Thread(target=load_binary_image, daemon=True).start()

            menu_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        image_widget,
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
        # Update once after all items added
        page.update()

    def goto_first_page(e):
        current_page["page"] = 1
        load_menu(category=category_dropdown.value, search=search_field.value, reset_page=False)

    def goto_prev_page(e):
        if current_page["page"] > 1:
            current_page["page"] -= 1
            load_menu(category=category_dropdown.value, search=search_field.value, reset_page=False)

    def goto_next_page(e):
        if current_page["page"] < total_pages["count"]:
            current_page["page"] += 1
            load_menu(category=category_dropdown.value, search=search_field.value, reset_page=False)

    def goto_last_page(e):
        current_page["page"] = total_pages["count"]
        load_menu(category=category_dropdown.value, search=search_field.value, reset_page=False)

    search_field = ft.TextField(
        hint_text="Search menu...", 
        width=300, 
        on_change=lambda e: load_menu(category=category_dropdown.value, search=e.control.value, reset_page=True),
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
        on_change=lambda e: load_menu(category=e.control.value, search=search_field.value, reset_page=True),
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    
    # Pagination controls - Modern clean design with responsive layout
    pagination_controls = ft.Container(
        content=ft.ResponsiveRow(
            [
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
                        icon_color=TEXT_LIGHT,
                        icon_size=20,
                        on_click=goto_first_page,
                        tooltip="First Page"
                    ),
                    bgcolor="#1a1a1a",
                    border_radius=8,
                    padding=5,
                    col={"xs": 2, "sm": 1, "md": 1}
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT,
                        icon_color=TEXT_LIGHT,
                        icon_size=20,
                        on_click=goto_prev_page,
                        tooltip="Previous"
                    ),
                    bgcolor="#1a1a1a",
                    border_radius=8,
                    padding=5,
                    col={"xs": 2, "sm": 1, "md": 1}
                ),
                ft.Container(
                    content=page_info_text,
                    bgcolor=ACCENT_DARK,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=15, vertical=8),
                    border=ft.border.all(1, ACCENT_PRIMARY),
                    alignment=ft.alignment.center,
                    col={"xs": 4, "sm": 4, "md": 2, "lg": 2, "xl": 1}
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        icon_color=TEXT_LIGHT,
                        icon_size=20,
                        on_click=goto_next_page,
                        tooltip="Next"
                    ),
                    bgcolor="#1a1a1a",
                    border_radius=8,
                    padding=5,
                    col={"xs": 2, "sm": 1, "md": 1}
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
                        icon_color=TEXT_LIGHT,
                        icon_size=20,
                        on_click=goto_last_page,
                        tooltip="Last Page"
                    ),
                    bgcolor="#1a1a1a",
                    border_radius=8,
                    padding=5,
                    col={"xs": 2, "sm": 1, "md": 1}
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=15, horizontal=10),
        border_radius=10
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
                menu_list,
                pagination_controls
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
import flet as ft
import shutil
import os
import uuid
import imghdr
from core.database import (
    get_all_menu_items, 
    create_menu_item, 
    update_menu_item, 
    delete_menu_item, 
    get_all_orders, 
    update_order_status
)
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, create_image_widget, TEXT_DARK, ACCENT_PRIMARY, FIELD_BG, FIELD_BORDER, CREAM, ACCENT_DARK
from datetime import datetime, timedelta
from screens.admin_dashboard.order_details import create_order_details_dialog


def _create_timeline_strip(order):
    """Compact timeline strip with dots and a progress line."""
    status_order = ["placed", "preparing", "out for delivery", "delivered"]
    current_status = order.get("status", "placed").lower()

    if current_status == "cancelled":
        return ft.Row(
            [
                ft.Text("Cancelled", size=11, color="#C62828", weight=ft.FontWeight.W_600),
                ft.Container(width=8),
                ft.Container(width=8, height=8, bgcolor="#C62828", border_radius=50),
                ft.Container(width=24, height=2, bgcolor="#C62828"),
                ft.Container(width=8, height=8, bgcolor="#C62828", border_radius=50),
            ],
            spacing=6,
        )

    try:
        current_index = status_order.index(current_status)
    except ValueError:
        current_index = 0

    dots = []
    for i, _ in enumerate(status_order):
        is_done = i <= current_index
        dot_color = ACCENT_PRIMARY if is_done else "#CFCFCF"
        line_color = ACCENT_PRIMARY if i < current_index else "#E5E5E5"
        dots.append(ft.Container(width=8, height=8, bgcolor=dot_color, border_radius=50))
        if i < len(status_order) - 1:
            dots.append(ft.Container(width=26, height=2, bgcolor=line_color))

    return ft.Row(dots, spacing=6)


def _create_order_timeline(order):
    """Render status timeline for admin order cards."""
    timeline_events = [
        ("placed", order.get("placed_at"), "✓ Placed"),
        ("preparing", order.get("preparing_at"), "👨‍🍳 Preparing"),
        ("out for delivery", order.get("out_for_delivery_at"), "🚚 Out for Delivery"),
        ("delivered", order.get("delivered_at"), "✅ Delivered"),
        ("cancelled", order.get("cancelled_at"), "✗ Cancelled"),
    ]

    timeline_items = []
    current_status = order.get("status", "placed").lower()

    for status_name, timestamp, display_label in timeline_events:
        if status_name == "cancelled" and current_status != "cancelled":
            continue

        is_completed = False
        is_current = False

        status_order = ["placed", "preparing", "out for delivery", "delivered"]
        cancelled_order = ["placed", "cancelled"]

        if current_status == "cancelled":
            is_completed = status_name in cancelled_order and cancelled_order.index(status_name) <= cancelled_order.index(
                current_status
            )
            is_current = status_name == current_status
        else:
            is_completed = status_name in status_order and status_order.index(status_name) <= status_order.index(
                current_status
            )
            is_current = status_name == current_status

        time_text = ""
        if timestamp:
            try:
                time_text = f" - {format_datetime_philippine(timestamp)}"
            except Exception:
                time_text = f" - {timestamp}"

        text_color = ACCENT_PRIMARY if is_completed else "#999999"
        font_weight = ft.FontWeight.BOLD if is_current else ft.FontWeight.W_600

        timeline_items.append(
            ft.Row(
                [
                    ft.Text(display_label, size=13, color=text_color, weight=font_weight),
                    ft.Text(time_text, size=11, color="#555555", weight=ft.FontWeight.W_500),
                ],
                spacing=4,
            )
        )

    return timeline_items


def create_menu_handlers(page, current_user, menu_list, form_container, fields, uploaded_image, menu_filter_buttons):
    """Create all menu-related handlers"""
    
    current_menu_filter = {"value": "All"}
    edit_mode = {"active": False, "item_id": None}
    
    def update_menu_filter_buttons(active_filter):
        """Update menu chip colors to show active filter"""
        button_map = {
            "All": menu_filter_buttons["all"],
            "Appetizers": menu_filter_buttons["appetizers"],
            "Mains": menu_filter_buttons["mains"],
            "Desserts": menu_filter_buttons["desserts"],
            "Drinks": menu_filter_buttons["drinks"],
            "Other": menu_filter_buttons["other"]
        }
        
        for filter_name, chip in button_map.items():
            if filter_name == active_filter:
                chip.bgcolor = ACCENT_DARK
                chip.content.color = "#FFFFFF"
            else:
                chip.bgcolor = "#E0E0E0"
                chip.content.color = TEXT_DARK
        
        page.update()
    
    def load_menu(filter_category="All"):
        current_menu_filter["value"] = filter_category
        update_menu_filter_buttons(filter_category)
        
        menu_list.controls.clear()
        all_items = get_all_menu_items()
        
        if filter_category == "All":
            items = all_items
        else:
            items = [item for item in all_items if item.get("category") == filter_category]
        
        count_text = ft.Text(
            f"Showing {len(items)} item(s)" + (f" in category '{filter_category}'" if filter_category != "All" else ""),
            size=15,
            color="#000000",
            weight=ft.FontWeight.BOLD
        )
        menu_list.controls.append(count_text)
        
        if not items:
            menu_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No items found in this category.",
                        size=16,
                        color="#000000",
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=30,
                    alignment=ft.alignment.center,
                    bgcolor="#F5F5F5",
                    border_radius=10
                )
            )
        
        for item in items:
            # Category badge color mapping
            category_colors = {
                "Appetizers": {"bg": "#FFE5B4", "text": "#8B4513"},
                "Mains": {"bg": "#FFD4D4", "text": "#8B0000"},
                "Desserts": {"bg": "#FFB6C1", "text": "#C71585"},
                "Drinks": {"bg": "#B0E0E6", "text": "#00688B"},
                "Other": {"bg": "#E0E0E0", "text": "#505050"}
            }
            
            category = item.get('category', 'Other')
            cat_color = category_colors.get(category, category_colors["Other"])
            
            # Calculate sale price if applicable
            is_on_sale = item.get('is_on_sale', 0)
            sale_percentage = item.get('sale_percentage', 0)
            original_price = item['price']
            display_price = original_price
            
            if is_on_sale and sale_percentage > 0:
                discount_multiplier = (100 - sale_percentage) / 100
                display_price = original_price * discount_multiplier
            
            # Build price display
            price_row_items = []
            if is_on_sale and sale_percentage > 0:
                price_row_items.append(
                    ft.Text(
                        f"₱{original_price:.2f}",
                        size=13,
                        color="#999999",
                        weight=ft.FontWeight.W_400,
                        style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH)
                    )
                )
            price_row_items.append(
                ft.Text(f"₱{display_price:.2f}", size=15, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD)
            )
            
            # Create the card
            card = ft.Container(
                content=ft.Row([
                    create_image_widget(item, 85, 85),
                    ft.Column([
                        ft.Row([
                            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color="#000000"),
                            ft.Container(
                                content=ft.Text(category, size=10, weight=ft.FontWeight.BOLD, color=cat_color["text"]),
                                bgcolor=cat_color["bg"],
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=10
                            ),
                            ft.Container(
                                content=ft.Text(f"-{sale_percentage}% OFF", size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                bgcolor="#E53935",
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=10,
                                visible=is_on_sale and sale_percentage > 0
                            )
                        ], spacing=8),
                        ft.Text(item["description"], size=13, color="#000000", weight=ft.FontWeight.W_500),
                        ft.Row(price_row_items, spacing=6),
                        ft.Text(f"Stock: {item.get('stock', 0)}", size=12, color="#000000", weight=ft.FontWeight.W_500)
                    ], expand=True, spacing=5),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_ROUNDED,
                        icon_color="white",
                        bgcolor="#0D4715",
                        icon_size=20,
                        on_click=lambda e, item=item: edit_item(item),
                        tooltip="Edit"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_ROUNDED,
                        icon_color="white",
                        bgcolor="#D32F2F",
                        icon_size=20,
                        on_click=lambda e, id=item["id"]: delete_item(id),
                        tooltip="Delete"
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=12,
                border=ft.border.all(1.5, FIELD_BORDER),
                border_radius=12,
                bgcolor=FIELD_BG
            )
            
            menu_list.controls.append(card)
        
        page.update()
    
    def delete_item(item_id):
        user_id = current_user["user"]["id"]
        delete_menu_item(item_id, user_id)
        show_snackbar(page, "Item deleted!")
        load_menu(current_menu_filter["value"])
    
    def edit_item(item):
        edit_mode["active"] = True
        edit_mode["item_id"] = item["id"]
        fields["name"].value = item["name"]
        fields["desc"].value = item["description"]
        fields["price"].value = str(item["price"])
        fields["stock"].value = str(item.get("stock", 0))
        fields["category"].value = item.get("category", "Other")
        fields["calories"].value = str(item.get("calories", 0)) if item.get("calories") else ""
        fields["ingredients"].value = item.get("ingredients", "")
        fields["recipe"].value = item.get("recipe", "")
        fields["allergens"].value = item.get("allergens", "")
        fields["is_on_sale"].value = bool(item.get("is_on_sale", 0))
        fields["sale_percentage"].value = str(item.get("sale_percentage", 0))
        
        if item.get("image"):
            uploaded_image["data"] = item["image"]
            uploaded_image["type"] = item.get("image_type", "emoji")
            fields["image_preview"].content = create_image_widget(item, 150, 150)
        
        form_container.visible = True
        page.update()
    
    def handle_file_pick(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            if file.size > 3145728:
                show_snackbar(page, "Image size must be under 3MB")
                return
            if not file.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                show_snackbar(page, "Only JPG, PNG, GIF allowed")
                return
            
            detected_type = imghdr.what(file.path)
            if detected_type not in ("jpeg", "png", "gif"):
                show_snackbar(page, "Invalid image file")
                return
            
            try:
                file_ext = os.path.splitext(file.name)[1]
                filename = f"{uuid.uuid4()}{file_ext}"
                assets_path = "assets/menu"
                dest_path = os.path.join(assets_path, filename)
                
                os.makedirs(assets_path, exist_ok=True)
                shutil.copy(file.path, dest_path)
                
                uploaded_image["data"] = filename
                uploaded_image["type"] = "path"
                
                fields["image_preview"].content = ft.Image(
                    src=dest_path,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.COVER,
                    border_radius=10
                )
                show_snackbar(page, "Image uploaded successfully!")
                page.update()
            except Exception as ex:
                print(f"Upload error: {ex}")
                show_snackbar(page, "Upload failed. Please try another image.")
    
    def save_item(e):
        if not fields["name"].value or not fields["desc"].value or not fields["price"].value:
            show_snackbar(page, "Please fill all fields!")
            return

        stock_value = fields["stock"].value.strip() if fields["stock"].value else "0"
        try:
            stock = int(stock_value)
            if stock < 0:
                raise ValueError()
        except Exception:
            show_snackbar(page, "Stock must be a non-negative whole number")
            return
        
        user_id = current_user["user"]["id"]
        image_data = uploaded_image["data"] if uploaded_image["data"] else "🍽️"
        image_type = uploaded_image["type"]
        category = fields["category"].value
        
        # Get nutrition and recipe fields
        calories = int(fields["calories"].value) if fields["calories"].value and fields["calories"].value.isdigit() else 0
        ingredients = fields["ingredients"].value if fields["ingredients"].value else ""
        recipe = fields["recipe"].value if fields["recipe"].value else ""
        allergens = fields["allergens"].value if fields["allergens"].value else ""
        
        # Get sale fields
        is_on_sale = 1 if fields["is_on_sale"].value else 0
        sale_percentage_value = fields["sale_percentage"].value if fields["sale_percentage"].value else "0"
        sale_percentage = int(sale_percentage_value) if sale_percentage_value.strip().isdigit() else 0
        # Clamp sale percentage between 0 and 100
        sale_percentage = max(0, min(100, sale_percentage))
        
        # If sale percentage is set, automatically enable sale
        if sale_percentage > 0:
            is_on_sale = 1
        
        if edit_mode["active"]:
            update_menu_item(
                edit_mode["item_id"],
                fields["name"].value,
                fields["desc"].value,
                float(fields["price"].value),
                stock,
                image_data,
                image_type,
                category,
                user_id,
                calories,
                ingredients,
                recipe,
                allergens,
                is_on_sale,
                sale_percentage
            )
            show_snackbar(page, "Item updated!")
            edit_mode["active"] = False
        else:
            create_menu_item(
                fields["name"].value,
                fields["desc"].value,
                float(fields["price"].value),
                stock,
                image_data,
                image_type,
                category,
                user_id,
                calories,
                ingredients,
                recipe,
                allergens,
                is_on_sale,
                sale_percentage
            )
            show_snackbar(page, "Item added!")
        
        fields["name"].value = ""
        fields["desc"].value = ""
        fields["price"].value = ""
        fields["stock"].value = "0"
        fields["category"].value = "Other"
        fields["calories"].value = ""
        fields["ingredients"].value = ""
        fields["recipe"].value = ""
        fields["allergens"].value = ""
        fields["is_on_sale"].value = False
        fields["sale_percentage"].value = "0"
        uploaded_image["data"] = None
        uploaded_image["type"] = "emoji"
        fields["image_preview"].content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")
        form_container.visible = False
        load_menu(current_menu_filter["value"])
    
    def show_form(e):
        edit_mode["active"] = False
        fields["name"].value = ""
        fields["desc"].value = ""
        fields["price"].value = ""
        fields["stock"].value = "0"
        fields["category"].value = "Other"
        fields["calories"].value = ""
        fields["ingredients"].value = ""
        fields["recipe"].value = ""
        fields["allergens"].value = ""
        fields["is_on_sale"].value = False
        fields["sale_percentage"].value = "0"
        uploaded_image["data"] = None
        uploaded_image["type"] = "emoji"
        fields["image_preview"].content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")
        
        form_container.visible = True
        page.update()
    
    return {
        "load_menu": load_menu,
        "handle_file_pick": handle_file_pick,
        "save_item": save_item,
        "show_form": show_form
    }


def create_order_handlers(page, current_user, orders_list, order_filter_buttons, order_search_field, date_range_dropdown):
    """Create all order-related handlers"""
    
    current_order_filter = {"value": "all"}
    order_search_query = {"value": ""}
    date_range_days = {"value": "30"}

    def update_order_filter_buttons(active_filter):
        for filter_name, button in order_filter_buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
                if hasattr(button, "content") and button.content:
                    button.content.color = "#FFFFFF"
            else:
                button.bgcolor = "#E0E0E0"
                if hasattr(button, "content") and button.content:
                    button.content.color = "#000000"
        page.update()

    def open_order_details(order):
        def handle_status_change(e):
            new_status = e.control.value
            if not new_status or new_status == order.get("status"):
                return
            try:
                update_order_status(order.get("id"), new_status, current_user["user"]["id"])
                show_snackbar(page, f"Order status updated to {new_status}")
                load_orders(current_order_filter["value"])
                
                # Fetch updated order data from database
                from core.database import get_all_orders
                all_orders = get_all_orders()
                updated_order = next((o for o in all_orders if o.get("id") == order.get("id")), None)
                
                if updated_order:
                    # Recreate dialog with updated order data and timeline
                    new_dialog = create_order_details_dialog(
                        page,
                        updated_order,
                        handle_status_change,
                        _create_order_timeline(updated_order),
                    )
                    page.dialog = new_dialog
                    new_dialog.open = True
                    page.update()
            except Exception as handler_err:
                show_snackbar(page, f"Error: {str(handler_err)[:50]}")
                page.update()

        dialog = create_order_details_dialog(
            page,
            order,
            handle_status_change,
            _create_order_timeline(order),
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        page.dialog = dialog
        dialog.open = True
        page.update()

    def on_order_search_change(e):
        order_search_query["value"] = e.control.value.lower().strip()
        load_orders(current_order_filter["value"])

    def on_date_range_change(e):
        date_range_days["value"] = e.control.value
        load_orders(current_order_filter["value"])

    
    def load_orders(filter_status="all"):
        current_order_filter["value"] = filter_status
        update_order_filter_buttons(filter_status)

        temp_controls = []

        try:
            all_orders = get_all_orders()
        except Exception as db_error:
            temp_controls.append(ft.Text(f"DB Error: {db_error}", color="red"))
            orders_list.controls = temp_controls
            page.update()
            return

        if not all_orders:
            temp_controls.append(ft.Text("No orders in database", size=12, color=TEXT_DARK))
            orders_list.controls = temp_controls
            page.update()
            return

        if filter_status == "all":
            orders = all_orders
        else:
            orders = [order for order in all_orders if order["status"] == filter_status]

        if order_search_query["value"]:
            query = order_search_query["value"]
            filtered = []
            for order in orders:
                customer_name = (order.get("customer_name") or "").lower()
                order_number = str(order.get("customer_order_number", ""))
                items_list = order.get("items", []) if isinstance(order.get("items"), list) else []
                item_names = " ".join([(item.get("name") or "") for item in items_list]).lower()
                if query in customer_name or query in order_number or query in item_names:
                    filtered.append(order)
            orders = filtered

        if date_range_days["value"] != "all":
            try:
                days = int(date_range_days["value"])
                cutoff = datetime.now() - timedelta(days=days)
                date_filtered = []
                for order in orders:
                    created_at = order.get("created_at")
                    if not created_at:
                        continue
                    try:
                        created_dt = datetime.fromisoformat(created_at)
                    except Exception:
                        created_dt = None
                    if created_dt and created_dt >= cutoff:
                        date_filtered.append(order)
                orders = date_filtered
            except Exception:
                pass

        count_text = ft.Text(f"{len(orders)} order(s)", size=13, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
        temp_controls.append(count_text)
        if not orders:
            temp_controls.append(ft.Text("No matching orders", size=12, color="#666666", italic=True))
            orders_list.controls = temp_controls
            page.update()
            return

        for order in orders:
            status_colors = {
                "placed": {"bg": "#E8F5E9", "text": "#2E7D32"},
                "preparing": {"bg": "#FFF3E0", "text": "#E65100"},
                "out for delivery": {"bg": "#E3F2FD", "text": "#1565C0"},
                "delivered": {"bg": "#E8F5E9", "text": "#2E7D32"},
                "cancelled": {"bg": "#FFEBEE", "text": "#C62828"},
            }
            status_text = order.get("status", "unknown").upper()
            status_style = status_colors.get(order.get("status", "unknown"), {"bg": "#E0E0E0", "text": "#505050"})

            def make_status_change_handler(oid, old_status):
                def handler(e):
                    new_status = e.control.value
                    if not new_status or new_status == old_status:
                        return

                    try:
                        update_order_status(oid, new_status, current_user["user"]["id"])
                        show_snackbar(page, f"Order status updated to {new_status}")
                        load_orders(current_order_filter["value"])
                        page.update()
                    except Exception as handler_err:
                        show_snackbar(page, f"Error: {str(handler_err)[:50]}")
                        page.update()
                return handler

            try:
                formatted_date = format_datetime_philippine(order.get("created_at"))
            except Exception:
                formatted_date = order.get("created_at", "N/A")

            items_list = order.get("items", [])
            items_text = ""
            if isinstance(items_list, list):
                item_descriptions = []
                for item in items_list:
                    if isinstance(item, dict):
                        item_name = item.get("name", "Unknown")
                        item_qty = item.get("quantity", 1)
                        item_descriptions.append(f"{item_name} (x{item_qty})")
                items_text = ", ".join(item_descriptions) if item_descriptions else "No items"
            else:
                items_text = "No items"

            def on_card_hover(e):
                if e.data == "true":
                    card.scale = 1.02
                    card.shadow = ft.BoxShadow(
                        spread_radius=2,
                        blur_radius=8,
                        color="#00000033",
                    )
                else:
                    card.scale = 1
                    card.shadow = None
                page.update()

            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            f"Order #{order.get('customer_order_number', '?')}",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_DARK,
                                        ),
                                        ft.Text(order.get("customer_name", "Unknown"), size=12, color="#444444"),
                                        ft.Text(formatted_date, size=10, color="#888888"),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Text(
                                                status_text,
                                                size=10,
                                                weight=ft.FontWeight.BOLD,
                                                color=status_style["text"],
                                            ),
                                            bgcolor=status_style["bg"],
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            border_radius=12,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.ARROW_FORWARD,
                                            icon_size=18,
                                            icon_color=ACCENT_PRIMARY,
                                            tooltip="View order",
                                            on_click=lambda e, order=order: open_order_details(order),
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Text(items_text, size=11, color="#555555"),
                        _create_timeline_strip(order),
                        ft.Text(
                            f"{order.get('delivery_address', 'N/A')} • {order.get('contact_number', 'N/A')}",
                            size=10,
                            color="#666666",
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    f"\u20b1{order.get('total_amount', 0):.2f}",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ACCENT_PRIMARY,
                                ),
                                ft.Container(expand=True),
                                ft.Dropdown(
                                    width=170,
                                    value=order.get("status", "placed"),
                                    disabled=order.get("status", "placed") in ["delivered", "cancelled"],
                                    options=[
                                        ft.dropdown.Option(
                                            "placed",
                                            content=ft.Text("placed", color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                        ),
                                        ft.dropdown.Option(
                                            "preparing",
                                            content=ft.Text("preparing", color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                        ),
                                        ft.dropdown.Option(
                                            "out for delivery",
                                            content=ft.Text(
                                                "out for delivery",
                                                color=TEXT_DARK,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ),
                                        ft.dropdown.Option(
                                            "delivered",
                                            content=ft.Text("delivered", color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                        ),
                                        ft.dropdown.Option(
                                            "cancelled",
                                            content=ft.Text("cancelled", color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                        ),
                                    ],
                                    on_change=make_status_change_handler(
                                        order.get("id"),
                                        order.get("status", "placed"),
                                    ),
                                    bgcolor=FIELD_BG,
                                    border_color=FIELD_BORDER,
                                    text_style=ft.TextStyle(color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                                    color=TEXT_DARK,
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=6,
                ),
                padding=14,
                border=ft.border.all(1, "#E5E5E5"),
                border_radius=12,
                bgcolor=CREAM,
                height=220,
                on_hover=on_card_hover,
            )

            temp_controls.append(card)

        orders_list.controls = temp_controls
        page.update()

    def on_status_change(e, order_id):
        update_order_status(order_id, e.control.value, current_user["user"]["id"])
        show_snackbar(page, "Status updated!")
        load_orders(current_order_filter["value"])
    
    # Set up event handlers
    order_search_field.on_change = on_order_search_change
    date_range_dropdown.on_change = on_date_range_change

    return {
        "load_orders": load_orders,
        "on_status_change": on_status_change,
        "on_order_search_change": on_order_search_change,
        "on_date_range_change": on_date_range_change,
    }

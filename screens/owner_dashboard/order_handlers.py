from datetime import datetime, timedelta
import flet as ft
from core.database import get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, TEXT_DARK, ACCENT_PRIMARY, FIELD_BG, FIELD_BORDER, CREAM, ACCENT_DARK


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


def create_order_handlers(
    page,
    current_user,
    orders_list,
    order_filter_buttons,
    order_search_field,
    date_range_dropdown,
    order_details_panel=None,
    order_details_content=None,
):
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

    def hide_order_details(e=None):
        if order_details_panel is not None:
            order_details_panel.visible = False
        if order_details_content is not None:
            order_details_content.controls.clear()
        page.update()

    def open_order_details(order):
        if order_details_panel is None or order_details_content is None:
            show_snackbar(page, "Order details panel is unavailable")
            return

        def handle_status_change(e):
            new_status = e.control.value
            if not new_status or new_status == order.get("status"):
                return
            try:
                success, message = update_order_status(order.get("id"), new_status, current_user["user"]["id"])
                if not success:
                    show_snackbar(page, f"Error: {message[:50]}")
                    e.control.value = order.get("status", "placed")
                    page.update()
                    return

                refreshed_orders = get_all_orders()
                updated_order = next((o for o in refreshed_orders if o.get("id") == order.get("id")), None)
                show_snackbar(page, f"Order status updated to {new_status}")
                load_orders(current_order_filter["value"])
                if updated_order:
                    open_order_details(updated_order)
                else:
                    hide_order_details()
            except Exception as handler_err:
                show_snackbar(page, f"Error: {str(handler_err)[:50]}")

        try:
            formatted_date = format_datetime_philippine(order.get("created_at"))
        except Exception:
            formatted_date = order.get("created_at", "N/A")

        items_list = order.get("items", []) if isinstance(order.get("items"), list) else []
        item_rows = []
        for item in items_list:
            name = item.get("name", "Unknown")
            qty = item.get("quantity", 1)
            price = item.get("price", 0)
            item_rows.append(
                ft.Row(
                    [
                        ft.Text(f"{name} (x{qty})", size=12, color=TEXT_DARK),
                        ft.Container(expand=True),
                        ft.Text(f"₱{price * qty:.2f}", size=12, color=TEXT_DARK),
                    ],
                    spacing=6,
                )
            )
        if not item_rows:
            item_rows.append(ft.Text("No items", size=12, color=TEXT_DARK))

        status_dropdown = ft.Dropdown(
            width=220,
            value=order.get("status", "placed"),
            disabled=order.get("status", "placed") in ["delivered", "cancelled"],
            options=[
                ft.dropdown.Option("placed", content=ft.Text("Placed", color=TEXT_DARK, size=13)),
                ft.dropdown.Option("preparing", content=ft.Text("Preparing", color=TEXT_DARK, size=13)),
                ft.dropdown.Option("out for delivery", content=ft.Text("Out for Delivery", color=TEXT_DARK, size=13)),
                ft.dropdown.Option("delivered", content=ft.Text("Delivered", color=TEXT_DARK, size=13)),
                ft.dropdown.Option("cancelled", content=ft.Text("Cancelled", color=TEXT_DARK, size=13)),
            ],
            on_change=handle_status_change,
            bgcolor=FIELD_BG,
            border_color=FIELD_BORDER,
            text_style=ft.TextStyle(color=TEXT_DARK, weight=ft.FontWeight.BOLD),
            color=TEXT_DARK,
        )

        order_details_content.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Order #{order.get('customer_order_number', '?')}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(order.get("customer_name", "Unknown"), size=13, color=TEXT_DARK),
                        ft.Text(formatted_date, size=11, color="#666666"),
                    ],
                    spacing=4,
                ),
                padding=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, FIELD_BORDER),
                border_radius=10,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Status", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    status_dropdown,
                ], spacing=8),
                padding=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, FIELD_BORDER),
                border_radius=10,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Delivery", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text(order.get("delivery_address", "N/A"), size=12, color=TEXT_DARK),
                    ft.Text(order.get("contact_number", "N/A"), size=12, color=TEXT_DARK),
                    ft.Text(f"Total: ₱{order.get('total_amount', 0):.2f}", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
                ], spacing=6),
                padding=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, FIELD_BORDER),
                border_radius=10,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Items", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Column(item_rows, spacing=6),
                ], spacing=8),
                padding=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, FIELD_BORDER),
                border_radius=10,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Timeline", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Column(_create_order_timeline(order), spacing=4),
                ], spacing=8),
                padding=12,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, FIELD_BORDER),
                border_radius=10,
            ),
        ]
        order_details_panel.visible = True
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

                    allowed_transitions = {
                        "placed": ["preparing", "out for delivery", "cancelled"],
                        "preparing": ["out for delivery", "cancelled"],
                        "out for delivery": ["delivered", "cancelled"],
                        "delivered": [],
                        "cancelled": [],
                    }

                    allowed_next = allowed_transitions.get(old_status, [])
                    if new_status not in allowed_next:
                        show_snackbar(page, f"Invalid status change: {old_status} → {new_status}")
                        e.control.value = old_status
                        page.update()
                        return

                    try:
                        success, message = update_order_status(oid, new_status, current_user["user"]["id"])
                        if not success:
                            show_snackbar(page, f"Error: {message[:50]}")
                            e.control.value = old_status
                            page.update()
                            return
                        show_snackbar(page, f"Order status updated to {new_status}")
                        load_orders(current_order_filter["value"])
                    except Exception as handler_err:
                        show_snackbar(page, f"Error: {str(handler_err)[:50]}")
                        e.control.value = old_status
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
                                    f"₱{order.get('total_amount', 0):.2f}",
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
            )

            temp_controls.append(card)

        orders_list.controls = temp_controls
        page.update()

    def on_status_change(e, order_id):
        update_order_status(order_id, e.control.value, current_user["user"]["id"])
        show_snackbar(page, "Status updated!")
        load_orders(current_order_filter["value"])

    order_search_field.on_change = on_order_search_change
    date_range_dropdown.on_change = on_date_range_change

    return {
        "load_orders": load_orders,
        "on_status_change": on_status_change,
        "on_order_search_change": on_order_search_change,
        "on_date_range_change": on_date_range_change,
        "hide_order_details": hide_order_details,
    }

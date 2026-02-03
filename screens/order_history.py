import flet as ft
from datetime import datetime
import threading
import time
from core.database import get_orders_by_customer, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK, ACCENT_PRIMARY, FIELD_BG, TEXT_DARK, FIELD_BORDER, CREAM, DARK_GREEN, DARKER_GREEN, ORANGE

def order_history_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    orders_table_container = ft.Column(expand=True)
    running = True
    current_filter = "all"
    filter_label = ft.Text("Status: All Orders", size=12, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
    
    # Add a lock for thread safety
    update_lock = threading.Lock()
    
    # Filter button data
    filter_options = [
        {"label": "All Orders", "status": "all", "icon": ft.Icons.LIST},
        {"label": "Placed", "status": "placed", "icon": ft.Icons.SHOPPING_BAG},
        {"label": "Preparing", "status": "preparing", "icon": ft.Icons.RESTAURANT},
        {"label": "Out for Delivery", "status": "out for delivery", "icon": ft.Icons.LOCAL_SHIPPING},
        {"label": "Delivered", "status": "delivered", "icon": ft.Icons.CHECK_CIRCLE},
        {"label": "Cancelled", "status": "cancelled", "icon": ft.Icons.CANCEL},
    ]
    
    def create_menu_item(option):
        """Create a menu item for the filter dropdown"""
        return ft.MenuItemButton(
            content=ft.Row([
                ft.Icon(option["icon"], size=20, color=TEXT_DARK),
                ft.Text(option["label"], size=13, color=TEXT_DARK)
            ], spacing=12),
            on_click=lambda e, status=option["status"], label=option["label"]: on_filter_select(status, label)
        )
    
    def on_filter_select(status: str, label: str):
        """Handle filter selection"""
        filter_label.value = f"Status: {label}"
        load_orders(status)

    def create_status_badge(status: str, is_payment: bool = False):
        """Small badge matching the screenshot colors"""
        if is_payment:
            if status.lower() == "success":
                color = "#4CAF50"
                label = "Success"
            else:
                color = "#FF9800"
                label = "Pending"
        else:
            if status.lower() == "fulfilled":
                color = "#4CAF50"
                label = "Fulfilled"
            else:
                color = "#F44336"
                label = "Unfulfilled"

        return ft.Container(
            content=ft.Text(label, size=12, color=color, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            opacity=0.08,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=20,
            border=ft.border.all(1, color)
        )

    def create_order_card(order: dict):
        """Unified card layout for all screen sizes"""
        items_list = order.get('items', [])
        status = (order.get('status','') or '').lower()
        def can_cancel(s: str) -> bool:
            return s in {"placed", "preparing", "out for delivery"}

        return ft.Card(
            elevation=0,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Container(
                bgcolor=FIELD_BG,
                border_radius=12,
                border=ft.border.all(1, FIELD_BORDER),
                padding=14,
                content=ft.Column([
                    # Header row with order ID and cancel button
                    ft.Row([
                        ft.Column([
                            ft.Text(f"Order #{order['customer_order_number']}", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(format_datetime_philippine(order.get('created_at')), size=11, color="grey")
                        ], spacing=2, expand=True),
                        ft.ElevatedButton(
                            "Cancel",
                            visible=can_cancel(status),
                            bgcolor=ACCENT_DARK,
                            color=CREAM,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=10, vertical=6)),
                            on_click=lambda e, oid=order['id'], onum=order['customer_order_number']: cancel_order(oid, onum)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=10, color=FIELD_BORDER),
                    
                    # Customer name (full width)
                    ft.Row([
                        ft.Column([
                            ft.Text("CUSTOMER", size=10, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                order.get('customer_name', 'N/A'),
                                size=12,
                                color=TEXT_DARK,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=4, expand=True)
                    ]),
                    
                    # Second row: Total, Items, Status (3 columns - better spacing on small screens)
                    ft.Row([
                        ft.Column([
                            ft.Text("TOTAL", size=10, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"₱{order['total_amount']:.2f}",
                                size=12,
                                color=ACCENT_PRIMARY,
                                weight=ft.FontWeight.BOLD,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=4, expand=1),
                        ft.Column([
                            ft.Text("ITEMS", size=10, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{len(items_list)}", size=12, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
                        ], spacing=4, expand=1),
                        ft.Column([
                            ft.Text("STATUS", size=10, color=TEXT_DARK, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(
                                    (order.get('status','') or 'N/A').upper(),
                                    size=11,
                                    color=CREAM,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                bgcolor=ACCENT_DARK,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=16,
                                alignment=ft.alignment.center
                            )
                        ], spacing=4, expand=1)
                    ], spacing=12)
                ], spacing=8)
            )
        )

    def update_filter_buttons(active_filter):
        """Update filter label"""
        for option in filter_options:
            if option["status"] == active_filter:
                filter_label.value = f"Status: {option['label']}"
                break
        
        page.update()

    def cancel_order(order_id, order_number):
        """Cancel an order"""
        try:
            success, message = update_order_status(order_id, "cancelled", current_user["user"]["id"])
            if success:
                show_snackbar(page, f"Order #{order_number} cancelled successfully!")
                load_orders(current_filter)
            else:
                show_snackbar(page, f"Cannot cancel: {message}")
        except Exception as e:
            show_snackbar(page, f"Error cancelling order: {str(e)}")

    def load_orders(filter_status="all"):
        nonlocal current_filter
        
        # Prevent concurrent updates with thread lock
        with update_lock:
            current_filter = filter_status
            update_filter_buttons(filter_status)
            
            if current_user.get("user") is None:
                return
                
            orders_table_container.controls.clear()
            all_orders = get_orders_by_customer(current_user["user"]["id"])
            
            # Apply filter
            if filter_status == "all":
                orders = all_orders
            else:
                orders = [order for order in all_orders if order['status'] == filter_status]
            
            # Empty state styling
            if not orders:
                orders_table_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=72, color="#777"),
                            ft.Text(
                                "No orders found" if filter_status == "all" else f"No {filter_status} orders",
                                size=16,
                                color="#AAA",
                                text_align=ft.TextAlign.CENTER
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                           spacing=10),
                        alignment=ft.alignment.center,
                        expand=True,
                        padding=30
                    )
                )
            else:
                # Use the same card layout for all screen sizes
                orders_table_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [create_order_card(order) for order in orders],
                            spacing=12,
                            scroll=ft.ScrollMode.AUTO
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        expand=True
                    )
                )

            page.update()

    def poll_orders():
        while running:
            time.sleep(30)
            load_orders(current_filter)

    load_orders()
    threading.Thread(target=poll_orders, daemon=True).start()
    
    # Add resize handler to refresh layout when window size changes
    def on_resize(e):
        load_orders(current_filter)
    
    page.on_resize = on_resize

    def stop_polling(e):
        nonlocal running
        running = False
        page.on_resize = None  # Remove resize handler
        goto_menu(e)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Order History", size=22, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=CREAM, on_click=stop_polling, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=8))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=18,
                    border_radius=ft.border_radius.only(top_left=0, top_right=0, bottom_left=12, bottom_right=12),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Filter", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.MenuBar(
                                controls=[
                                    ft.SubmenuButton(
                                        content=filter_label,
                                        controls=[
                                            create_menu_item(option) for option in filter_options
                                        ]
                                    )
                                ]
                            )
                        ], alignment=ft.MainAxisAlignment.START, spacing=12)
                    ], spacing=10),
                    padding=15,
                    border=ft.border.all(1, FIELD_BORDER),
                    border_radius=12,
                    margin=ft.margin.symmetric(horizontal=12, vertical=10),
                    bgcolor=FIELD_BG,
                ),
                ft.Container(
                    content=orders_table_container,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    expand=True
                )
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        bgcolor=FIELD_BG
    )
import flet as ft
from datetime import datetime
import threading
import time
from core.database import get_orders_by_customer, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK, ACCENT_PRIMARY, FIELD_BG, TEXT_DARK, FIELD_BORDER, CREAM, DARK_GREEN, DARKER_GREEN, ORANGE
from screens.profile.loading_screen import show_loading, hide_loading

def order_history_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    orders_table_container = ft.Column(expand=True)
    running = True
    current_filter = "all"
    filter_label = {"value": "All Orders"}  # Store as dict to allow updates
    
    # Add a lock for thread safety
    update_lock = threading.Lock()
    
    # Store callback for real-time updates
    refresh_callback = None
    
    # Filter button data
    filter_options = [
        {"label": "All Orders", "status": "all", "icon": ft.Icons.LIST},
        {"label": "Placed", "status": "placed", "icon": ft.Icons.SHOPPING_BAG},
        {"label": "Preparing", "status": "preparing", "icon": ft.Icons.RESTAURANT},
        {"label": "Out for Delivery", "status": "out for delivery", "icon": ft.Icons.LOCAL_SHIPPING},
        {"label": "Delivered", "status": "delivered", "icon": ft.Icons.CHECK_CIRCLE},
        {"label": "Cancelled", "status": "cancelled", "icon": ft.Icons.CANCEL},
    ]
    
    def on_filter_select(status: str, label: str):
        """Handle filter selection"""
        filter_label["value"] = label
        load_orders(status)

    def create_order_card(order: dict):
        """Card layout matching app design system"""
        items_list = order.get('items', [])
        status = (order.get('status','') or '').lower()
        
        def can_cancel(s: str) -> bool:
            return s in {"placed", "preparing", "out for delivery"}
        
        # Status color mapping
        status_colors = {
            "placed": {"bg": "#E3F2FD", "text": "#1976D2"},
            "preparing": {"bg": "#FFF3E0", "text": "#F57C00"},
            "out for delivery": {"bg": "#F3E5F5", "text": "#7B1FA2"},
            "delivered": {"bg": "#E8F5E9", "text": "#388E3C"},
            "cancelled": {"bg": "#FFEBEE", "text": "#C62828"},
        }
        colors = status_colors.get(status, {"bg": "#F5F5F5", "text": "#666"})

        return ft.Container(
            content=ft.Column([
                # Header with Order ID and timestamp
                ft.Row([
                    ft.Column([
                        ft.Text(f"Order #{order['customer_order_number']}", 
                               size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(format_datetime_philippine(order.get('created_at')), 
                               size=10, color="#888"),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(status.upper(), 
                                      size=10, color=colors["text"], 
                                      weight=ft.FontWeight.BOLD),
                        bgcolor=colors["bg"],
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=1, thickness=1, color=FIELD_BORDER),
                
                # Customer info
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=16, color=ACCENT_PRIMARY),
                    ft.Text(order.get('customer_name') or 'N/A', 
                           size=13, color=TEXT_DARK)
                ], spacing=6),
                
                # Address
                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ACCENT_PRIMARY),
                    ft.Text(order.get('delivery_address') or 'No address', 
                           size=12, color=TEXT_DARK, expand=True)
                ], spacing=6),
                
                # Contact
                ft.Row([
                    ft.Icon(ft.Icons.PHONE, size=16, color=ACCENT_PRIMARY),
                    ft.Text(order.get('contact_number') or 'No contact', 
                           size=12, color=TEXT_DARK)
                ], spacing=6),
                
                ft.Divider(height=1, thickness=1, color=FIELD_BORDER),
                
                # Total and Items row
                ft.Row([
                    ft.Text(f"₱{order['total_amount']:.2f}", 
                           size=16, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD),
                    
                    ft.Text(f"{len(items_list)} item{'s' if len(items_list) != 1 else ''}", 
                           size=12, color=TEXT_DARK),
                    
                    ft.ElevatedButton(
                        "CANCEL",
                        visible=can_cancel(status),
                        bgcolor=ACCENT_DARK,
                        color=CREAM,
                        height=32,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e, oid=order['id'], onum=order['customer_order_number']: cancel_order(oid, onum)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=6),
            bgcolor=FIELD_BG,
            border_radius=10,
            padding=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="black12",
                offset=ft.Offset(0, 2)
            )
        )

    def update_filter_buttons(active_filter):
        """Update filter label"""
        for option in filter_options:
            if option["status"] == active_filter:
                filter_label["value"] = option["label"]
                break
        
        page.update()

    def cancel_order(order_id, order_number):
        """Cancel an order with loading indicator"""
        loading = show_loading(page, "Cancelling order...")
        
        async def _cancel():
            try:
                success, message = update_order_status(order_id, "cancelled", current_user["user"]["id"])
                hide_loading(page, loading)
                
                if success:
                    show_snackbar(page, f"Order #{order_number} cancelled successfully!", bgcolor="green")
                    load_orders(current_filter)
                else:
                    show_snackbar(page, f"Cannot cancel: {message}", error=True)
            except Exception as e:
                hide_loading(page, loading)
                show_snackbar(page, f"Error cancelling order: {str(e)}", error=True)
        
        page.run_task(_cancel)

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
            
            # Empty state with better design and messaging
            if not orders:
                empty_messages = {
                    "all": ("No Orders Yet", "You haven't placed any orders. Start ordering delicious food now!"),
                    "placed": ("No Placed Orders", "You don't have any orders in this status"),
                    "preparing": ("No Orders Being Prepared", ""),
                    "out for delivery": ("No Orders Out for Delivery", ""),
                    "delivered": ("No Delivered Orders", "Come back after an order is delivered"),
                    "cancelled": ("No Cancelled Orders", ""),
                }
                title, subtitle = empty_messages.get(filter_status, ("No Orders", ""))
                
                orders_table_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Container(height=20),
                            ft.Icon(ft.Icons.SHOPPING_CART_CHECKOUT, size=80, color="#DDD"),
                            ft.Text(title, size=18, weight=ft.FontWeight.BOLD, 
                                   color=TEXT_DARK, text_align=ft.TextAlign.CENTER),
                            ft.Text(subtitle, size=12, color="#999", 
                                   text_align=ft.TextAlign.CENTER, width=250) if subtitle else ft.Container(),
                            ft.Container(height=20),
                        ], 
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12),
                        alignment=ft.alignment.center,
                        expand=True,
                        padding=30
                    )
                )
            else:
                # Display orders
                orders_table_container.controls.append(
                    ft.Column(
                        [create_order_card(order) for order in orders],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO
                    )
                )

            page.update()

    def poll_orders():
        while running:
            time.sleep(30)
            load_orders(current_filter)

    load_orders()
    
    # Remove polling - instead refresh when user manually filters or returns to screen
    # This is more efficient and doesn't drain battery
    def on_screen_focus(e):
        """Refresh when user returns to this screen"""
        load_orders(current_filter)
    
    page.on_focus = on_screen_focus
    
    def on_resize(e):
        """Refresh layout when window size changes"""
        load_orders(current_filter)
    
    page.on_resize = on_resize

    def stop_screen(e):
        """Clean up when leaving screen"""
        page.on_focus = None
        page.on_resize = None
        goto_menu(e)

    return ft.Container(
        content=ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Text("Order History", size=24, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK, 
                            icon_color=CREAM, 
                            on_click=stop_screen,
                            icon_size=24
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=20,
                ),
                
                # Filter dropdown
                ft.Container(
                    content=ft.PopupMenuButton(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Text(filter_label["value"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=22, color=TEXT_DARK)
                            ], spacing=5),
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            border=ft.border.all(2, ACCENT_PRIMARY),
                            border_radius=10,
                            bgcolor=FIELD_BG
                        ),
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Row([
                                    ft.Icon(option["icon"], size=20, color=ACCENT_PRIMARY),
                                    ft.Text(option["label"], size=14, color=TEXT_DARK)
                                ], spacing=12),
                                on_click=lambda e, status=option["status"], label=option["label"]: on_filter_select(status, label)
                            ) for option in filter_options
                        ]
                    ),
                    padding=15,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=8,
                        color="black12",
                        offset=ft.Offset(0, 2)
                    )
                ),
                
                # Orders list
                ft.Container(
                    content=orders_table_container,
                    padding=15,
                    expand=True
                )
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        bgcolor=CREAM
    )
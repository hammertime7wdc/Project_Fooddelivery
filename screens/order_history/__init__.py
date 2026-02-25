import flet as ft
from utils import TEXT_DARK, CREAM, ORANGE, FIELD_BORDER, ACCENT_DARK
from .timeline import create_customer_timeline
from .ui import build_order_card, build_empty_state
from .handlers import create_cancel_handler, create_load_orders_handler


def order_history_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    """Main order history screen"""
    
    # State
    orders_table_container = ft.Column(expand=True)
    
    current_filter_ref = {"value": "all"}
    filter_label_ref = {"value": "All Orders"}
    
    filter_options = [
        {"label": "All Orders", "status": "all", "icon": ft.Icons.LIST},
        {"label": "Placed", "status": "placed", "icon": ft.Icons.SHOPPING_BAG},
        {"label": "Preparing", "status": "preparing", "icon": ft.Icons.RESTAURANT},
        {"label": "Out for Delivery", "status": "out for delivery", "icon": ft.Icons.LOCAL_SHIPPING},
        {"label": "Delivered", "status": "delivered", "icon": ft.Icons.CHECK_CIRCLE},
        {"label": "Cancelled", "status": "cancelled", "icon": ft.Icons.CANCEL},
    ]
    
    status_colors = {
        "placed": {"bg": "#E3F2FD", "text": "#1976D2"},
        "preparing": {"bg": "#FFF3E0", "text": "#F57C00"},
        "out for delivery": {"bg": "#F3E5F5", "text": "#7B1FA2"},
        "delivered": {"bg": "#E8F5E9", "text": "#388E3C"},
        "cancelled": {"bg": "#FFEBEE", "text": "#C62828"},
    }
    
    # Create wrapper for order card builder with page context
    def create_order_card_with_handlers(order):
        """Create order card with proper handlers"""
        return build_order_card(order, status_colors, page, cancel_order)
    
    # Create handlers
    cancel_order = create_cancel_handler(
        page, current_user, orders_table_container, 
        create_order_card_with_handlers, current_filter_ref, status_colors
    )
    
    load_orders = create_load_orders_handler(
        page, current_user, orders_table_container,
        create_order_card_with_handlers, current_filter_ref, 
        filter_label_ref, filter_options, status_colors
    )
    
    def on_filter_select(status, label):
        """Handle filter selection"""
        filter_label_ref["value"] = label
        load_orders(status)
    
    # Load initial orders
    load_orders()
    
    # Refresh on screen focus
    def on_screen_focus(e):
        """Refresh when user returns to this screen"""
        load_orders(current_filter_ref["value"])
    
    page.on_focus = on_screen_focus
    page.on_resize = None
    
    def stop_screen(e):
        """Clean up when leaving screen"""
        page.on_focus = None
        page.on_resize = None
        goto_menu(e)
    
    # Build UI
    return ft.Container(
        content=ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK, 
                                icon_color=CREAM, 
                                on_click=stop_screen,
                                icon_size=24
                            ),
                            ft.Text("Order History", size=24, weight=ft.FontWeight.BOLD, color=CREAM),
                        ], alignment=ft.MainAxisAlignment.START, spacing=4),
                        ft.Text("Track and manage all your past orders", size=12, color=CREAM)
                    ], spacing=2),
                    bgcolor=ORANGE,
                    padding=ft.padding.only(left=12, right=18, top=14, bottom=16),
                ),
                
                # Filter dropdown
                ft.Container(
                    content=ft.PopupMenuButton(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Text(filter_label_ref["value"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=22, color=TEXT_DARK)
                            ], spacing=5),
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            border=ft.border.all(1, FIELD_BORDER),
                            border_radius=12,
                            bgcolor="#FFFFFF"
                        ),
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Row([
                                    ft.Icon(option["icon"], size=20, color=ORANGE),
                                    ft.Text(option["label"], size=14, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
                                ], spacing=12),
                                on_click=lambda e, status=option["status"], label=option["label"]: on_filter_select(status, label)
                            ) for option in filter_options
                        ],
                        menu_position=ft.PopupMenuPosition.UNDER,
                        bgcolor=CREAM
                    ),
                    padding=ft.padding.only(left=15, right=15, top=14, bottom=10)
                ),
                
                # Orders list
                ft.Container(
                    content=orders_table_container,
                    padding=ft.padding.only(left=15, right=15, bottom=15),
                    expand=True
                )
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        bgcolor=CREAM
    )

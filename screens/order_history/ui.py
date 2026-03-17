import flet as ft
from core.datetime_utils import format_datetime_philippine
from utils import ACCENT_DARK, ACCENT_PRIMARY, FIELD_BG, TEXT_DARK, FIELD_BORDER, CREAM
from .timeline import create_customer_timeline


def build_order_card(order, status_colors, page, cancel_handler):
    """Card layout matching app design system"""
    items_list = order.get('items', [])
    status = (order.get('status') or '').strip().lower()
    
    def can_cancel(s):
        return s in {"placed", "preparing"}
    
    colors = status_colors.get(status, {"bg": "#F5F5F5", "text": "#666"})
    
    # Create timeline content container
    timeline_content = ft.Container(
        content=ft.Column([], spacing=4),
        padding=ft.padding.only(left=8, right=6, top=2, bottom=2),
        bgcolor="#FFFFFF",
        visible=False
    )
    timeline_loaded = {"value": False}
    
    expand_button = ft.IconButton(
        icon=ft.Icons.EXPAND_MORE,
        icon_size=24,
        icon_color=ACCENT_PRIMARY,
        tooltip="View timeline"
    )
    
    def toggle_timeline(e):
        if not timeline_loaded["value"]:
            timeline_content.content.controls = create_customer_timeline(order)
            timeline_loaded["value"] = True
        timeline_content.visible = not timeline_content.visible
        expand_button.icon = ft.Icons.EXPAND_LESS if timeline_content.visible else ft.Icons.EXPAND_MORE
        page.update()

    expand_button.on_click = toggle_timeline

    status_text = ft.Text(
        status.upper(),
        size=10,
        color=colors["text"],
        weight=ft.FontWeight.BOLD,
    )

    status_chip = ft.Container(
        content=status_text,
        bgcolor=colors["bg"],
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=12,
    )

    cancel_button = ft.ElevatedButton(
        "Cancel",
        visible=can_cancel(status),
        bgcolor=ACCENT_DARK,
        color=CREAM,
        height=32,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=12),
        ),
        on_click=lambda e, oid=order['id'], onum=order['customer_order_number']: cancel_handler(oid, onum),
    )

    card = ft.Container(
        content=ft.Column([
            # Header with Order ID and timestamp
            ft.Row([
                ft.Column([
                    ft.Text(f"Order #{order['customer_order_number']}", 
                           size=15, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                    ft.Text(format_datetime_philippine(order.get('created_at')), 
                           size=11, color="#666666", weight=ft.FontWeight.W_500),
                ], spacing=2, expand=True),
                status_chip
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
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
            
            # Total and Items row
            ft.Row([
                ft.Text(f"₱{order['total_amount']:.2f}", 
                       size=16, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD),
                
                ft.Text(f"{len(items_list)} item{'s' if len(items_list) != 1 else ''}", 
                       size=12, color=TEXT_DARK),
                
                cancel_button
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            ft.Divider(height=10, thickness=0.7, color="#D8CDBB"),

            # Timeline info tab (collapsible header)
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TIMELINE, size=22, color=ACCENT_PRIMARY),
                    ft.Text("Order Timeline", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                    expand_button
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#FFF9F2",
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=8, vertical=7)
            ),
            
            # Timeline content (hidden by default)
            timeline_content
        ], spacing=8),
        bgcolor="#FFFFFF",
        border_radius=14,
        padding=13,
        border=ft.border.all(1, FIELD_BORDER),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color="black12",
            offset=ft.Offset(0, 4)
        )
    )

    return card, {
        "status_text": status_text,
        "status_chip": status_chip,
        "cancel_button": cancel_button,
        "timeline_content": timeline_content,
        "order": order,
    }


def build_empty_state(filter_status, TEXT_DARK, TEXT_LIGHT="#999"):
    """Build empty state container"""
    empty_messages = {
        "all": ("No Orders Yet", "You haven't placed any orders. Start ordering delicious food now!"),
        "placed": ("No Placed Orders", "You don't have any orders in this status"),
        "preparing": ("No Orders Being Prepared", ""),
        "out for delivery": ("No Orders Out for Delivery", ""),
        "delivered": ("No Delivered Orders", "Come back after an order is delivered"),
        "cancelled": ("No Cancelled Orders", ""),
    }
    title, subtitle = empty_messages.get(filter_status, ("No Orders", ""))
    
    return ft.Container(
        content=ft.Column([
            ft.Container(height=8),
            ft.Icon(ft.Icons.RECEIPT_LONG, size=76, color="#D7C8AF"),
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD, 
                   color=TEXT_DARK, text_align=ft.TextAlign.CENTER),
            ft.Text(subtitle, size=12, color=TEXT_LIGHT, 
                   text_align=ft.TextAlign.CENTER, width=250) if subtitle else ft.Container(),
            ft.Container(height=8),
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12),
        alignment=ft.alignment.center,
        expand=True,
        padding=20,
        bgcolor="#FFF9F2",
        border_radius=14,
        border=ft.border.all(1, "#E3D7C6")
    )

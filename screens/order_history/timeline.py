import flet as ft
from core.datetime_utils import format_datetime_philippine
from utils import ACCENT_PRIMARY, TEXT_DARK


def create_customer_timeline(order):
    """Creates a timeline for customer view showing status transitions with timestamps"""
    timeline_events = [
        ("placed", order.get("placed_at"), "✓ Placed"),
        ("preparing", order.get("preparing_at"), "👨‍🍳 Preparing"),
        ("out for delivery", order.get("out_for_delivery_at"), "🚚 Out for Delivery"),
        ("delivered", order.get("delivered_at"), "✅ Delivered"),
        ("cancelled", order.get("cancelled_at"), "✗ Cancelled"),
    ]
    
    timeline_data = []
    current_status = order.get("status", "placed").lower()
    
    for status_name, timestamp, display_label in timeline_events:
        # Skip cancelled if order is not cancelled
        if status_name == "cancelled" and current_status != "cancelled":
            continue
        
        # Check if this status has been reached
        is_completed = False
        is_current = False
        
        status_order = ["placed", "preparing", "out for delivery", "delivered"]
        cancelled_order = ["placed", "cancelled"]
        
        if current_status == "cancelled":
            is_completed = status_name in cancelled_order and cancelled_order.index(status_name) <= cancelled_order.index(current_status)
            is_current = status_name == current_status
        else:
            is_completed = status_name in status_order and status_order.index(status_name) <= status_order.index(current_status)
            is_current = status_name == current_status
        
        # Format timestamp if available
        time_text = ""
        if timestamp:
            try:
                time_text = f" • {format_datetime_philippine(timestamp)}"
            except:
                time_text = f" • {timestamp}"
        
        # Color based on completion status
        text_color = ACCENT_PRIMARY if is_completed else "#999999"
        font_weight = ft.FontWeight.BOLD if is_current else ft.FontWeight.W_600

        timeline_data.append({
            "display_label": display_label,
            "time_text": time_text,
            "is_completed": is_completed,
            "is_current": is_current,
            "text_color": text_color,
            "font_weight": font_weight,
        })

    timeline_items = []
    total_steps = len(timeline_data)

    for index, item in enumerate(timeline_data):
        line_color = ACCENT_PRIMARY if item["is_completed"] else "#D8D8D8"
        dot_color = ACCENT_PRIMARY if item["is_completed"] else "#CFCFCF"

        track = ft.Column(
            [
                ft.Container(width=1.5, height=10, bgcolor=line_color, visible=index > 0),
                ft.Container(width=8, height=8, border_radius=4, bgcolor=dot_color),
                ft.Container(width=1.5, height=22, bgcolor=line_color, visible=index < total_steps - 1),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        timeline_items.append(
            ft.Row(
                [
                    ft.Container(content=track, width=16, alignment=ft.alignment.top_center),
                    ft.Column(
                        [
                            ft.Text(item["display_label"], size=13, color=item["text_color"], weight=item["font_weight"]),
                            ft.Text(item["time_text"] if item["time_text"] else " ", size=11, color="#666666", weight=ft.FontWeight.W_500),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

    return timeline_items

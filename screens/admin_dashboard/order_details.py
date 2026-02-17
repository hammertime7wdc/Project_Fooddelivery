import flet as ft
from core.datetime_utils import format_datetime_philippine
from utils import TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, CREAM


def create_order_details_dialog(page, order, status_change_handler, timeline_items):
    """Create an order details dialog for the admin dashboard."""
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
                    ft.Text(f"\u20b1{price * qty:.2f}", size=12, color=TEXT_DARK),
                ],
                spacing=6,
            )
        )

    if not item_rows:
        item_rows.append(ft.Text("No items", size=12, color=TEXT_DARK))

    try:
        formatted_date = format_datetime_philippine(order.get("created_at"))
    except Exception:
        formatted_date = order.get("created_at", "N/A")

    status_dropdown = ft.Dropdown(
        width=200,
        value=order.get("status", "placed"),
        disabled=order.get("status", "placed") in ["delivered", "cancelled"],
        options=[
            ft.dropdown.Option(
                "placed",
                content=ft.Text("Placed", color=TEXT_DARK, size=13),
            ),
            ft.dropdown.Option(
                "preparing",
                content=ft.Text("Preparing", color=TEXT_DARK, size=13),
            ),
            ft.dropdown.Option(
                "out for delivery",
                content=ft.Text("Out for Delivery", color=TEXT_DARK, size=13),
            ),
            ft.dropdown.Option(
                "delivered",
                content=ft.Text("Delivered", color=TEXT_DARK, size=13),
            ),
            ft.dropdown.Option(
                "cancelled",
                content=ft.Text("Cancelled", color=TEXT_DARK, size=13),
            ),
        ],
        on_change=status_change_handler,
        bgcolor=FIELD_BG,
        border_color=FIELD_BORDER,
        text_style=ft.TextStyle(color=TEXT_DARK, weight=ft.FontWeight.BOLD),
        color=TEXT_DARK,
    )

    info_section = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Customer", size=11, color="#666666"),
                        ft.Text(
                            order.get("customer_name", "Unknown"),
                            size=14,
                            color=TEXT_DARK,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text("Date", size=11, color="#666666"),
                        ft.Text(formatted_date, size=12, color=TEXT_DARK),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Column(
                    [
                        ft.Text("Status", size=11, color="#666666"),
                        status_dropdown,
                        ft.Text("Total", size=11, color="#666666"),
                        ft.Text(
                            f"\u20b1{order.get('total_amount', 0):.2f}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ACCENT_PRIMARY,
                        ),
                    ],
                    spacing=6,
                ),
            ],
            spacing=16,
        ),
        padding=14,
        bgcolor="#FFFFFF",
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=12,
    )

    address_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Address", size=11, color="#666666"),
                ft.Text(order.get("delivery_address", "N/A"), size=12, color=TEXT_DARK),
                ft.Text("Contact", size=11, color="#666666"),
                ft.Text(order.get("contact_number", "N/A"), size=12, color=TEXT_DARK),
            ],
            spacing=4,
        ),
        padding=12,
        bgcolor="#FFFFFF",
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=12,
    )

    items_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Items", size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Column(item_rows, spacing=6),
            ],
            spacing=6,
        ),
        padding=12,
        bgcolor="#FFFFFF",
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=12,
    )

    timeline_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Timeline", size=13, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Column(timeline_items, spacing=4),
            ],
            spacing=6,
        ),
        padding=12,
        bgcolor="#FFFFFF",
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=12,
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            f"Order #{order.get('customer_order_number', '?')} Details",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=TEXT_DARK,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    info_section,
                    address_section,
                    items_section,
                    timeline_section,
                ],
                spacing=10,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=440,
            bgcolor=CREAM,
            padding=12,
            border_radius=12,
        ),
        actions=[
            ft.TextButton(
                "Close",
                on_click=lambda e: _close_dialog(page),
                style=ft.ButtonStyle(color=TEXT_DARK),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=CREAM,
        shape=ft.RoundedRectangleBorder(radius=12),
    )

    return dialog


def _close_dialog(page):
    if page.dialog:
        page.dialog.open = False
        page.update()

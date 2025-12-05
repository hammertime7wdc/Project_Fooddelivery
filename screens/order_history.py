import flet as ft
from datetime import datetime
import threading
import time
from core.database import get_orders_by_customer, update_order_status
from core.datetime_utils import format_datetime_philippine  # ← ADDED: Import datetime formatter
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK

def order_history_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    running = True

    def cancel_order(order_id, order_number):
        """Cancel an order"""
        try:
            success, message = update_order_status(order_id, "cancelled", current_user["user"]["id"])
            if success:
                show_snackbar(page, f"Order #{order_number} cancelled successfully!")
                load_orders()
            else:
                show_snackbar(page, f"Cannot cancel: {message}")
        except Exception as e:
            show_snackbar(page, f"Error cancelling order: {str(e)}")

    def load_orders():
        if current_user.get("user") is None:
            return
        orders_list.controls.clear()
        orders = get_orders_by_customer(current_user["user"]["id"])
        
        if not orders:
            orders_list.controls.append(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=100, color="grey"),
                        ft.Text("No orders yet", size=18, color="grey", text_align=ft.TextAlign.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                )
            )
        else:
            for order in orders:
                # ← CHANGED: Use the new formatting function
                formatted_date = format_datetime_philippine(order.get('created_at'))
                
                items_str = "\n".join([f"- {item['name']} (x{item['quantity']}) - ₱{item['price'] * item['quantity']:.2f}" for item in order["items"]])
                
                # Determine if order can be cancelled
                status = order['status'].lower()
                can_cancel = status in ['placed', 'preparing']
                
                # Status color
                status_color = TEXT_LIGHT
                if status == 'cancelled':
                    status_color = "red"
                elif status == 'delivered':
                    status_color = "green"
                
                # Build order card content
                card_content = [
                    ft.Row([
                        ft.Text(f"Order #{order['customer_order_number']}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT, expand=True),
                        ft.ElevatedButton(
                            "Cancel Order",
                            bgcolor="red" if can_cancel else "grey",
                            color="white" if can_cancel else "#CCCCCC",
                            disabled=not can_cancel,
                            on_click=lambda e, oid=order['id'], onum=order['customer_order_number']: cancel_order(oid, onum)
                        )
                    ]),
                    ft.Text(f"Date: {formatted_date}", size=14, color="grey"),
                    ft.Text(f"Status: {order['status'].capitalize()}", size=16, color=status_color, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text("Items:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                    ft.Text(items_str, size=13, color=TEXT_LIGHT),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(f"Total: ₱{order['total_amount']:.2f}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                    ft.Text(f"Delivery Address: {order['delivery_address']}", size=13, color="grey"),
                    ft.Text(f"Contact: {order['contact_number']}", size=13, color="grey")
                ]
                
                orders_list.controls.append(
                    ft.Card(
                        elevation=4,
                        content=ft.Container(
                            padding=15,
                            content=ft.Column(
                                card_content,
                                spacing=5,
                                horizontal_alignment=ft.CrossAxisAlignment.START
                            )
                        )
                    )
                )
        page.update()

    def poll_orders():
        while running:
            time.sleep(30)
            load_orders()

    load_orders()
    threading.Thread(target=poll_orders, daemon=True).start()

    def stop_polling(e):
        nonlocal running
        running = False
        goto_menu(e)

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Order History", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT, expand=True),
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_LIGHT, on_click=stop_polling)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#6B0113", ACCENT_DARK]
                    ),
                    padding=15
                ),
                orders_list
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
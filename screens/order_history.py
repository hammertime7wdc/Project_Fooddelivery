import flet as ft
from datetime import datetime
import threading
import time
from core.database import get_orders_by_customer, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK, FIELD_BG, TEXT_DARK, FIELD_BORDER

def order_history_screen(page: ft.Page, current_user: dict, cart: list, goto_menu):
    orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    running = True
    current_filter = "all"
    
    # Filter buttons
    filter_all_btn = ft.ElevatedButton(
        "All Orders",
        bgcolor=ACCENT_DARK,
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("all"),
        icon=ft.Icons.LIST
    )
    
    filter_placed_btn = ft.ElevatedButton(
        "Placed",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("placed"),
        icon=ft.Icons.SHOPPING_BAG
    )
    
    filter_preparing_btn = ft.ElevatedButton(
        "Preparing",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("preparing"),
        icon=ft.Icons.RESTAURANT
    )
    
    filter_delivery_btn = ft.ElevatedButton(
        "Out for Delivery",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("out for delivery"),
        icon=ft.Icons.LOCAL_SHIPPING
    )
    
    filter_delivered_btn = ft.ElevatedButton(
        "Delivered",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("delivered"),
        icon=ft.Icons.CHECK_CIRCLE
    )
    
    filter_cancelled_btn = ft.ElevatedButton(
        "Cancelled",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_orders("cancelled"),
        icon=ft.Icons.CANCEL
    )

    def update_filter_buttons(active_filter):
        buttons = {
            "all": filter_all_btn,
            "placed": filter_placed_btn,
            "preparing": filter_preparing_btn,
            "out for delivery": filter_delivery_btn,
            "delivered": filter_delivered_btn,
            "cancelled": filter_cancelled_btn
        }
        
        for filter_name, button in buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
            else:
                button.bgcolor = "#555"
        
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
        current_filter = filter_status
        update_filter_buttons(filter_status)
        
        if current_user.get("user") is None:
            return
            
        orders_list.controls.clear()
        all_orders = get_orders_by_customer(current_user["user"]["id"])
        
        # Apply filter
        if filter_status == "all":
            orders = all_orders
        else:
            orders = [order for order in all_orders if order['status'] == filter_status]
        
        # Add count text
        count_text = ft.Text(
            f"Showing {len(orders)} order(s)" + (f" with status '{filter_status}'" if filter_status != "all" else ""),
            size=14,
            color="grey",
            italic=True
        )
        orders_list.controls.append(count_text)
        
        if not orders:
            orders_list.controls.append(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=100, color="grey"),
                        ft.Text(
                            "No orders found" if filter_status == "all" else f"No {filter_status} orders",
                            size=18,
                            color="grey",
                            text_align=ft.TextAlign.CENTER
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                )
            )
        else:
            for order in orders:
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
                elif status == 'out for delivery':
                    status_color = "orange"
                
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
            load_orders(current_filter)

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
                ft.Container(
                    content=ft.Column([
                        ft.Text("Filter by Status:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                        ft.Row([
                            filter_all_btn,
                            filter_placed_btn,
                            filter_preparing_btn,
                        ], wrap=True, spacing=5),
                        ft.Row([
                            filter_delivery_btn,
                            filter_delivered_btn,
                            filter_cancelled_btn,
                        ], wrap=True, spacing=5)
                    ]),
                    padding=15,
                    border=ft.border.all(1, "white"),
                    border_radius=10,
                    margin=10
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
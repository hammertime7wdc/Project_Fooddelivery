import asyncio
import flet as ft
from core.database import get_orders_by_customer, update_order_status
from utils import show_snackbar, TEXT_DARK
from screens.profile.loading_screen import show_loading, hide_loading
from .ui import build_order_card, build_empty_state


def normalize_status(value):
    return (value or '').strip().lower()


def create_cancel_handler(page, current_user, orders_table_container, create_order_card_func, current_filter_ref, status_colors):
    """Create a cancel order handler"""
    def cancel_order(order_id, order_number):
        """Cancel an order - SYNCHRONOUS like the legacy code"""
        loading = show_loading(page, "Cancelling order...")
        
        try:
            user_id = current_user.get("user", {}).get("id")
            # Call synchronously - no async wrapper
            success, message = update_order_status(order_id, "cancelled", user_id)
            
            hide_loading(page, loading)

            if success:
                # Manually rebuild the orders list
                orders_table_container.controls.clear()
                all_orders = get_orders_by_customer(current_user["user"]["id"])
                
                # Apply current filter
                if current_filter_ref["value"] == "all":
                    filtered_orders = all_orders
                else:
                    filtered_orders = [order for order in all_orders 
                                     if normalize_status(order.get("status")) == current_filter_ref["value"]]
                
                # Rebuild order cards
                if filtered_orders:
                    orders_table_container.controls.append(
                        ft.Column(
                            [create_order_card_func(order)[0] for order in filtered_orders],
                            spacing=10,
                            scroll=ft.ScrollMode.AUTO
                        )
                    )
                else:
                    # Show empty state if no orders match filter
                    orders_table_container.controls.append(
                        build_empty_state(current_filter_ref["value"], TEXT_DARK)
                    )
                
                show_snackbar(page, f"Order #{order_number} cancelled successfully!", bgcolor="green")
                page.update()
            else:
                show_snackbar(page, f"Cannot cancel: {message}", error=True)
                page.update()
        except Exception as e:
            hide_loading(page, loading)
            show_snackbar(page, f"Error cancelling order: {str(e)}", error=True)
            page.update()

    return cancel_order


def create_load_orders_handler(page, current_user, orders_table_container, create_order_card_func, 
                               current_filter_ref, filter_label_ref, filter_options, status_colors):
    """Create a load orders handler"""
    def load_orders(filter_status="all"):
        """Load and display orders"""
        current_filter_ref["value"] = filter_status
        
        # Update filter label
        for option in filter_options:
            if option["status"] == filter_status:
                filter_label_ref["value"] = option["label"]
                break
        
        if current_user.get("user") is None:
            return

        orders_table_container.controls.clear()
        all_orders = get_orders_by_customer(current_user["user"]["id"])
        
        # Apply filter
        if filter_status == "all":
            orders = all_orders
        else:
            orders = [order for order in all_orders if normalize_status(order.get("status")) == filter_status]
        
        # Build controls
        if not orders:
            orders_table_container.controls.append(build_empty_state(filter_status, TEXT_DARK))
        else:
            orders_table_container.controls.append(
                ft.Column(
                    [create_order_card_func(order)[0] for order in orders],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO
                )
            )

        page.update()

    return load_orders

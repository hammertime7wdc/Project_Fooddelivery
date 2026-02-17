import flet as ft
from datetime import datetime, timedelta
from core.auth import (
    get_all_users,
    create_user_by_admin,
    delete_user,
    disable_user,
    enable_user,
    validate_email,
    validate_password,
    validate_full_name,
    get_password_strength,
)
from core.database import get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import (
    show_snackbar,
    TEXT_LIGHT,
    ACCENT_DARK,
    FIELD_BG,
    TEXT_DARK,
    FIELD_BORDER,
    ACCENT_PRIMARY,
    CREAM,
    DARK_GREEN,
)
from .order_details import create_order_details_dialog


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


def create_admin_handlers(
    page,
    current_user,
    users_list,
    orders_list,
    new_email,
    new_password,
    new_name,
    new_role,
    email_error,
    password_error,
    name_error,
    password_strength_text,
    password_strength_bar,
    user_search_field,
    role_filter_buttons,
    status_filter_buttons,
    role_filter_selected,
    status_filter_selected,
    order_filter_buttons,
    order_search_field,
    date_range_dropdown,
    form_container,
    user_details_panel,
    user_details_content,
):
    search_query = {"value": ""}
    current_order_filter = {"value": "all"}
    order_search_query = {"value": ""}
    date_range_days = {"value": "30"}

    def validate_email_field(e=None):
        if not new_email.value or new_email.value.strip() == "":
            email_error.visible = False
            new_email.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_email(new_email.value)
            if not is_valid:
                email_error.value = error_msg
                email_error.visible = True
                new_email.border_color = "red"
            else:
                email_error.visible = False
                new_email.border_color = "green"
        page.update()

    def validate_name_field(e=None):
        if not new_name.value or new_name.value.strip() == "":
            name_error.visible = False
            new_name.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_full_name(new_name.value)
            if not is_valid:
                name_error.value = error_msg
                name_error.visible = True
                new_name.border_color = "red"
            else:
                name_error.visible = False
                new_name.border_color = "green"
        page.update()

    def update_password_strength(e=None):
        password = new_password.value or ""
        if not password:
            password_strength_text.value = ""
            password_strength_bar.value = 0
            password_strength_bar.color = "grey"
            new_password.border_color = FIELD_BORDER
            password_error.visible = False
            page.update()
            return

        strength, score = get_password_strength(password)
        is_valid, error_msg = validate_password(password)

        password_strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
        password_strength_bar.value = score / 100

        if strength == "weak":
            password_strength_bar.color = "red"
            password_strength_text.color = "red"
        elif strength == "medium":
            password_strength_bar.color = "orange"
            password_strength_text.color = "orange"
        elif strength == "strong":
            password_strength_bar.color = "yellow"
            password_strength_text.color = "yellow"
        else:
            password_strength_bar.color = "green"
            password_strength_text.color = "green"

        if is_valid:
            new_password.border_color = "green"
            password_error.visible = False
        else:
            new_password.border_color = "red"
            password_error.value = error_msg
            password_error.visible = True

        page.update()

    def show_form(e):
        """Clear form fields and show the form container."""
        new_email.value = ""
        new_name.value = ""
        new_password.value = ""
        new_role.value = "customer"
        email_error.visible = False
        password_error.visible = False
        name_error.visible = False
        password_strength_text.value = ""
        password_strength_bar.value = 0
        new_email.border_color = FIELD_BORDER
        new_password.border_color = FIELD_BORDER
        new_name.border_color = FIELD_BORDER
        
        form_container.visible = True
        page.update()

    def hide_form(e):
        """Hide the form container."""
        form_container.visible = False
        page.update()

    def update_role_filter_chips(selected_role):
        for role, button in role_filter_buttons.items():
            is_selected = role == selected_role
            button.content.color = "#FFFFFF" if is_selected else "#000000"
            button.bgcolor = ACCENT_DARK if is_selected else "#E0E0E0"
        page.update()

    def update_status_filter_chips(selected_status):
        for status, button in status_filter_buttons.items():
            is_selected = status == selected_status
            button.content.color = "#FFFFFF" if is_selected else "#000000"
            button.bgcolor = ACCENT_DARK if is_selected else "#E0E0E0"
        page.update()

    def filter_users_by_role(role):
        role_filter_selected["value"] = role
        update_role_filter_chips(role)
        load_users()

    def filter_users_by_status(status):
        status_filter_selected["value"] = status
        update_status_filter_chips(status)
        load_users()

    def on_user_search_change(e):
        search_query["value"] = e.control.value.lower().strip()
        load_users()

    def handle_enable_user(user_id):
        """Enable a user and update UI"""
        enable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, "User enabled successfully!")
        user_details_panel.visible = False
        load_users()
        page.update()

    def handle_disable_user(user_id):
        """Disable a user and update UI"""
        disable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, "User disabled successfully!")
        user_details_panel.visible = False
        load_users()
        page.update()

    def handle_delete_user(user_id):
        """Delete a user and update UI"""
        success, msg = delete_user(user_id, current_user["user"]["id"])
        show_snackbar(page, msg)
        user_details_panel.visible = False
        if success:
            load_users()
        page.update()

    def hide_user_details(e):
        """Hide the user details panel"""
        user_details_panel.visible = False
        page.update()

    def open_user_details(user):
        """Show user details in the side panel"""
        from datetime import datetime
        
        # Clear previous content
        user_details_content.controls.clear()
        
        # Format dates
        created_at = "N/A"
        if user.get("created_at"):
            try:
                created_dt = datetime.fromisoformat(user["created_at"])
                created_at = created_dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                created_at = user.get("created_at", "N/A")
        
        last_login = "Never"
        if user.get("last_login"):
            try:
                login_dt = datetime.fromisoformat(user["last_login"])
                last_login = login_dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                last_login = user.get("last_login", "Never")
        
        # Determine status
        is_active = user.get("is_active", 0)
        status_text = "ACTIVE" if is_active else "DISABLED"
        status_color = "#FFFFFF" if is_active else "#666666"
        status_bg = "#4CAF50" if is_active else "#E0E0E0"
        
        # User info section
        user_details_content.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Account Information", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
                    ft.Divider(height=1, color=FIELD_BORDER),
                    ft.Row([
                        ft.Text("Email:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(user.get("email", "N/A"), size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Name:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(user.get("full_name", "N/A"), size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Role:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Container(
                            content=ft.Text(
                                user.get("role", "Unknown").upper(),
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=CREAM,
                            ),
                            bgcolor=ACCENT_PRIMARY,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=10,
                        ),
                    ]),
                    ft.Row([
                        ft.Text("Status:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Container(
                            content=ft.Text(
                                status_text,
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=status_color,
                            ),
                            bgcolor=status_bg,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=10,
                        ),
                    ]),
                    ft.Row([
                        ft.Text("Created:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(created_at, size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Last Login:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(last_login, size=11, color=TEXT_DARK),
                    ]),
                ], spacing=8),
                padding=12,
                bgcolor=FIELD_BG,
                border_radius=8,
            )
        )
        
        # Actions section
        user_details_content.controls.append(ft.Container(height=10))
        user_details_content.controls.append(
            ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY)
        )
        user_details_content.controls.append(ft.Divider(height=1, color=FIELD_BORDER))
        
        action_buttons = []
        if not is_active:
            action_buttons.append(
                ft.ElevatedButton(
                    "Activate",
                    bgcolor=ACCENT_PRIMARY,
                    color=CREAM,
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=lambda e, uid=user.get("id"): handle_enable_user(uid),
                )
            )
        
        if is_active:
            action_buttons.append(
                ft.ElevatedButton(
                    "Deactivate",
                    bgcolor="#FFA726",
                    color=CREAM,
                    icon=ft.Icons.BLOCK,
                    on_click=lambda e, uid=user.get("id"): handle_disable_user(uid),
                )
            )
        
        action_buttons.append(
            ft.ElevatedButton(
                "Delete",
                bgcolor="#EF5350",
                color=CREAM,
                icon=ft.Icons.DELETE,
                on_click=lambda e, uid=user.get("id"): handle_delete_user(uid),
            )
        )
        
        user_details_content.controls.append(
            ft.Row(action_buttons, spacing=8, wrap=True)
        )
        
        # Show the panel
        user_details_panel.visible = True
        page.update()

    def load_users():
        temp_controls = []
        all_users = get_all_users()

        filtered_users = all_users

        if role_filter_selected["value"] != "all":
            filtered_users = [u for u in filtered_users if u["role"] == role_filter_selected["value"]]

        if status_filter_selected["value"] != "all":
            if status_filter_selected["value"] == "active":
                filtered_users = [u for u in filtered_users if u["is_active"]]
            elif status_filter_selected["value"] == "disabled":
                filtered_users = [u for u in filtered_users if not u["is_active"]]
            elif status_filter_selected["value"] == "locked":
                locked_users = []
                for u in filtered_users:
                    if u.get("locked_until"):
                        try:
                            locked_until_dt = datetime.fromisoformat(u["locked_until"])
                            if datetime.now() < locked_until_dt:
                                locked_users.append(u)
                        except Exception:
                            pass
                filtered_users = locked_users

        if search_query["value"]:
            filtered_users = [
                u
                for u in filtered_users
                if search_query["value"] in u["full_name"].lower()
                or search_query["value"] in u["email"].lower()
            ]

        count_text = ft.Text(f"{len(filtered_users)} user(s)", size=13, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
        temp_controls.append(count_text)

        if not filtered_users:
            temp_controls.append(ft.Text("No users found", size=12, color="#666666", italic=True))
            users_list.controls = temp_controls
            page.update()
            return

        for user in filtered_users:
            status_badge_text = "ACTIVE" if user["is_active"] else "DISABLED"
            status_badge_color = "#4CAF50" if user["is_active"] else "#FFC107"
            status_badge_text_color = "#FFFFFF" if user["is_active"] else "#000000"

            def on_card_hover(e, card_ref=None):
                if card_ref is None:
                    return
                if e.data == "true":
                    card_ref.scale = 1.02
                    card_ref.shadow = ft.BoxShadow(
                        spread_radius=2,
                        blur_radius=8,
                        color="#00000033",
                    )
                else:
                    card_ref.scale = 1
                    card_ref.shadow = None
                page.update()

            # Create a unique button for this user
            user_id = user.get("id")
            
            def handle_arrow_click(e, u=user):
                open_user_details(u)
            
            arrow_btn = ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                icon_size=18,
                icon_color=ACCENT_PRIMARY,
                tooltip="View details",
                on_click=handle_arrow_click,
            )
            
            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            user.get("full_name", "Unknown"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_DARK,
                                        ),
                                        ft.Text(user.get("email", "N/A"), size=11, color="#666666"),
                                        ft.Text(
                                            user.get("role", "unknown").upper(),
                                            size=10,
                                            color=ACCENT_PRIMARY,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        status_badge_text,
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                        color=status_badge_text_color,
                                    ),
                                    bgcolor=status_badge_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=12,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=1, color="#E5E5E5"),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color="#999999"),
                                ft.Text(
                                    f"Created: {datetime.fromisoformat(user['created_at']).strftime('%b %d, %Y')}",
                                    size=10,
                                    color="#666666",
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LOGIN, size=12, color="#999999"),
                                ft.Text(
                                    f"Last Login: {datetime.fromisoformat(user['last_login']).strftime('%b %d, %Y') if user.get('last_login') else 'Never'}",
                                    size=10,
                                    color="#666666",
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.Container(expand=True),
                                arrow_btn,
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=8,
                ),
                padding=14,
                border=ft.border.all(1, "#E5E5E5"),
                border_radius=12,
                bgcolor=CREAM,
                height=200,
                ink=False,
            )
            
            # Attach hover handler
            card.on_hover = lambda e, card_ref=card: on_card_hover(e, card_ref)
            
            temp_controls.append(card)

        users_list.controls = temp_controls
        page.update()

    def add_user(e):
        has_error = False

        email_valid, email_msg = validate_email(new_email.value or "")
        if not email_valid:
            email_error.value = email_msg
            email_error.visible = True
            new_email.border_color = "red"
            has_error = True
        else:
            email_error.visible = False

        password_valid, password_msg = validate_password(new_password.value or "")
        if not password_valid:
            password_error.value = password_msg
            password_error.visible = True
            new_password.border_color = "red"
            has_error = True
        else:
            password_error.visible = False

        name_valid, name_msg = validate_full_name(new_name.value or "")
        if not name_valid:
            name_error.value = name_msg
            name_error.visible = True
            new_name.border_color = "red"
            has_error = True
        else:
            name_error.visible = False

        if has_error:
            page.update()
            return

        success, msg = create_user_by_admin(
            new_email.value,
            new_password.value,
            new_name.value,
            new_role.value,
            current_user["user"]["id"],
        )
        show_snackbar(page, msg)
        if success:
            new_email.value = ""
            new_password.value = ""
            new_name.value = ""
            new_role.value = "customer"
            new_email.border_color = FIELD_BORDER
            new_password.border_color = FIELD_BORDER
            new_name.border_color = FIELD_BORDER
            email_error.visible = False
            password_error.visible = False
            name_error.visible = False
            password_strength_text.value = ""
            password_strength_bar.value = 0
            page.update()
            load_users()

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

    def open_order_details(order):
        def handle_status_change(e):
            new_status = e.control.value
            if not new_status or new_status == order.get("status"):
                return
            try:
                update_order_status(order.get("id"), new_status, current_user["user"]["id"])
                show_snackbar(page, f"Order status updated to {new_status}")
                load_orders(current_order_filter["value"])
                
                # Fetch updated order data from database
                from core.database import get_all_orders
                all_orders = get_all_orders()
                updated_order = next((o for o in all_orders if o.get("id") == order.get("id")), None)
                
                if updated_order:
                    # Recreate dialog with updated order data and timeline
                    new_dialog = create_order_details_dialog(
                        page,
                        updated_order,
                        handle_status_change,
                        _create_order_timeline(updated_order),
                    )
                    page.dialog = new_dialog
                    new_dialog.open = True
                    page.update()
            except Exception as handler_err:
                show_snackbar(page, f"Error: {str(handler_err)[:50]}")
                page.update()

        dialog = create_order_details_dialog(
            page,
            order,
            handle_status_change,
            _create_order_timeline(order),
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        page.dialog = dialog
        dialog.open = True
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

                    try:
                        update_order_status(oid, new_status, current_user["user"]["id"])
                        show_snackbar(page, f"Order status updated to {new_status}")
                        load_orders(current_order_filter["value"])
                        page.update()
                    except Exception as handler_err:
                        show_snackbar(page, f"Error: {str(handler_err)[:50]}")
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

            def on_card_hover(e):
                if e.data == "true":
                    card.scale = 1.02
                    card.shadow = ft.BoxShadow(
                        spread_radius=2,
                        blur_radius=8,
                        color="#00000033",
                    )
                else:
                    card.scale = 1
                    card.shadow = None
                page.update()

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
                                    f"\u20b1{order.get('total_amount', 0):.2f}",
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
                on_hover=on_card_hover,
            )

            temp_controls.append(card)

        orders_list.controls = temp_controls
        page.update()

    def on_status_change(e, order_id):
        update_order_status(order_id, e.control.value, current_user["user"]["id"])
        show_snackbar(page, "Status updated!")
        load_orders(current_order_filter["value"])

    return {
        "validate_email_field": validate_email_field,
        "validate_name_field": validate_name_field,
        "update_password_strength": update_password_strength,
        "show_form": show_form,
        "hide_form": hide_form,
        "hide_user_details": hide_user_details,
        "filter_users_by_role": filter_users_by_role,
        "filter_users_by_status": filter_users_by_status,
        "on_search_change": on_user_search_change,
        "on_user_search_change": on_user_search_change,
        "load_users": load_users,
        "add_user": add_user,
        "load_orders": load_orders,
        "on_order_search_change": on_order_search_change,
        "on_date_range_change": on_date_range_change,
        "on_status_change": on_status_change,
    }

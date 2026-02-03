import flet as ft
from datetime import datetime
from core.auth import (
    get_all_users, create_user_by_admin, delete_user, 
    disable_user, enable_user, validate_email, 
    validate_password, validate_full_name, get_password_strength
)
from core.database import get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY, CREAM, DARK_GREEN

def admin_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    users_list = ft.ListView(spacing=10, padding=10, height=300)

    # User filtering state
    current_role_filter = "all"
    current_status_filter = "all"
    search_query = ""

    # Password strength indicator
    password_strength_text = ft.Text("", size=12, color=TEXT_DARK)
    password_strength_bar = ft.ProgressBar(width=250, value=0, color=DARK_GREEN, bgcolor=FIELD_BG)
    
    # Password requirements info box
    password_requirements = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.SECURITY, color=TEXT_DARK, size=20),
            ft.Text(
                "Password Requirements:",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=TEXT_DARK
            ),
            ft.Text(
                "• At least 8 characters\n"
                "• One uppercase letter (A-Z)\n"
                "• One lowercase letter (a-z)\n"
                "• One number (0-9)\n"
                "• One special character (!@#$%...)",
                size=10,
                color=TEXT_DARK
            )
        ]),
        padding=10,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=10,
        bgcolor=FIELD_BG,
        width=250
    )

    # Validation error texts (hidden by default)
    email_error = ft.Text("", size=11, color="red", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)
    name_error = ft.Text("", size=11, color="red", visible=False)

    def validate_email_field():
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

    def validate_name_field():
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

    def update_password_strength():
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

        # Update strength indicator
        password_strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
        password_strength_bar.value = score / 100

        # Color coding
        if strength == "weak":
            password_strength_bar.color = "red"
            password_strength_text.color = "red"
        elif strength == "medium":
            password_strength_bar.color = "orange"
            password_strength_text.color = "orange"
        elif strength == "strong":
            password_strength_bar.color = "yellow"
            password_strength_text.color = "yellow"
        else:  # very strong
            password_strength_bar.color = "green"
            password_strength_text.color = "green"

        # Validation border
        if is_valid:
            new_password.border_color = "green"
            password_error.visible = False
        else:
            new_password.border_color = "red"
            password_error.value = error_msg
            password_error.visible = True

        page.update()

    new_email = ft.TextField(
        hint_text="Email", 
        width=250,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        hint_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_email_field()
    )
    
    new_password = ft.TextField(
        hint_text="Password", 
        width=250, 
        password=True,
        can_reveal_password=True,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        hint_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: update_password_strength()
    )
    
    new_name = ft.TextField(
        hint_text="Full Name", 
        width=250,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        hint_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_name_field()
    )
    
    new_role = ft.Dropdown(
        width=250,
        options=[
            ft.dropdown.Option("customer"),
            ft.dropdown.Option("owner"),
            ft.dropdown.Option("admin")
        ],
        value="customer",
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK)
    )

    # User filter components
    search_field = ft.TextField(
        hint_text="Search by name or email...",
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        prefix_icon=ft.Icons.SEARCH,
        text_style=ft.TextStyle(color=TEXT_DARK),
        hint_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: on_search_change(e)
    )

    role_filter_all_btn = ft.ElevatedButton(
        "All Roles",
        bgcolor=ACCENT_DARK,
        color=CREAM,
        on_click=lambda e: filter_users_by_role("all"),
        icon=ft.Icons.PEOPLE
    )
    
    role_filter_customer_btn = ft.ElevatedButton(
        "Customers",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_role("customer"),
        icon=ft.Icons.PERSON
    )
    
    role_filter_owner_btn = ft.ElevatedButton(
        "Owners",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_role("owner"),
        icon=ft.Icons.STORE
    )
    
    role_filter_admin_btn = ft.ElevatedButton(
        "Admins",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_role("admin"),
        icon=ft.Icons.ADMIN_PANEL_SETTINGS
    )

    status_filter_all_btn = ft.ElevatedButton(
        "All Status",
        bgcolor=ACCENT_DARK,
        color=CREAM,
        on_click=lambda e: filter_users_by_status("all"),
        icon=ft.Icons.LIST
    )
    
    status_filter_active_btn = ft.ElevatedButton(
        "Active",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_status("active"),
        icon=ft.Icons.CHECK_CIRCLE
    )
    
    status_filter_disabled_btn = ft.ElevatedButton(
        "Disabled",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_status("disabled"),
        icon=ft.Icons.BLOCK
    )
    
    status_filter_locked_btn = ft.ElevatedButton(
        "Locked",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: filter_users_by_status("locked"),
        icon=ft.Icons.LOCK
    )

    def update_role_filter_buttons(active_filter):
        buttons = {
            "all": role_filter_all_btn,
            "customer": role_filter_customer_btn,
            "owner": role_filter_owner_btn,
            "admin": role_filter_admin_btn
        }
        
        for filter_name, button in buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
            else:
                button.bgcolor = "#555"
        
        page.update()

    def update_status_filter_buttons(active_filter):
        buttons = {
            "all": status_filter_all_btn,
            "active": status_filter_active_btn,
            "disabled": status_filter_disabled_btn,
            "locked": status_filter_locked_btn
        }
        
        for filter_name, button in buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
            else:
                button.bgcolor = "#555"
        
        page.update()

    def filter_users_by_role(role):
        nonlocal current_role_filter
        current_role_filter = role
        update_role_filter_buttons(role)
        load_users()

    def filter_users_by_status(status):
        nonlocal current_status_filter
        current_status_filter = status
        update_status_filter_buttons(status)
        load_users()

    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value.lower().strip()
        load_users()

    def load_users():
        users_list.controls.clear()
        all_users = get_all_users()
        
        # Apply filters
        filtered_users = all_users
        
        # Filter by role
        if current_role_filter != "all":
            filtered_users = [u for u in filtered_users if u["role"] == current_role_filter]
        
        # Filter by status
        if current_status_filter != "all":
            if current_status_filter == "active":
                filtered_users = [u for u in filtered_users if u["is_active"]]
            elif current_status_filter == "disabled":
                filtered_users = [u for u in filtered_users if not u["is_active"]]
            elif current_status_filter == "locked":
                locked_users = []
                for u in filtered_users:
                    if u.get("locked_until"):
                        try:
                            locked_until_dt = datetime.fromisoformat(u["locked_until"])
                            if datetime.now() < locked_until_dt:
                                locked_users.append(u)
                        except:
                            pass
                filtered_users = locked_users
        
        # Filter by search query
        if search_query:
            filtered_users = [
                u for u in filtered_users 
                if search_query in u["full_name"].lower() or search_query in u["email"].lower()
            ]
        
        # Show count
        count_text = ft.Text(
            f"Showing {len(filtered_users)} of {len(all_users)} user(s)",
            size=14,
            color=TEXT_DARK,
            italic=True
        )
        users_list.controls.append(count_text)
        
        if not filtered_users:
            users_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No users found matching the filters.",
                        size=16,
                        color=TEXT_DARK,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            page.update()
            return

        for user in filtered_users:
            # Format last login
            last_login = "Never"
            if user.get("last_login"):
                try:
                    last_login_dt = datetime.fromisoformat(user["last_login"])
                    last_login = last_login_dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    pass

            # Check if locked
            is_locked = False
            locked_until_str = ""
            if user.get("locked_until"):
                try:
                    locked_until_dt = datetime.fromisoformat(user["locked_until"])
                    if datetime.now() < locked_until_dt:
                        is_locked = True
                        locked_until_str = locked_until_dt.strftime("%I:%M %p")
                except:
                    pass

            def toggle_user(e, uid=user["id"], active=user["is_active"]):
                if active:
                    disable_user(uid, current_user["user"]["id"])
                else:
                    enable_user(uid, current_user["user"]["id"])
                load_users()

            def delete_user_click(e, uid=user["id"]):
                success, msg = delete_user(uid, current_user["user"]["id"])
                show_snackbar(page, msg)
                if success:
                    load_users()

            # Status text with more details
            status_parts = []
            if not user['is_active']:
                status_parts.append("Disabled")
            elif is_locked:
                status_parts.append(f"Locked until {locked_until_str}")
            else:
                status_parts.append("Active")
            
            if user.get("failed_login_attempts", 0) > 0 and not is_locked:
                status_parts.append(f"({user['failed_login_attempts']} failed attempts)")

            status_text = " - ".join(status_parts)
            status_color = "red" if not user['is_active'] or is_locked else TEXT_LIGHT

            users_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(user["full_name"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(f"{user['email']} ({user['role']})", size=12, color=TEXT_DARK),
                            ft.Text(f"Status: {status_text}", size=11, color=status_color if status_color != TEXT_LIGHT else TEXT_DARK),
                            ft.Text(f"Last login: {last_login}", size=10, color=TEXT_DARK),
                            ft.Text(f"Created: {datetime.fromisoformat(user['created_at']).strftime('%b %d, %Y')}", size=10, color=TEXT_DARK)
                        ], expand=True),
                        ft.IconButton(
                            icon=ft.Icons.BLOCK if user["is_active"] else ft.Icons.CHECK_CIRCLE,
                            icon_color=ACCENT_DARK,
                            on_click=toggle_user,
                            tooltip="Disable User" if user["is_active"] else "Enable User"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color="red",
                            on_click=delete_user_click,
                            tooltip="Delete User"
                        )
                    ]),
                    padding=10,
                    border=ft.border.all(1, FIELD_BORDER),
                    border_radius=10,
                    bgcolor=FIELD_BG
                )
            )
        page.update()

    def add_user(e):
        has_error = False
        
        # Validate email
        email_valid, email_msg = validate_email(new_email.value or "")
        if not email_valid:
            email_error.value = email_msg
            email_error.visible = True
            new_email.border_color = "red"
            has_error = True
        else:
            email_error.visible = False

        # Validate password
        password_valid, password_msg = validate_password(new_password.value or "")
        if not password_valid:
            password_error.value = password_msg
            password_error.visible = True
            new_password.border_color = "red"
            has_error = True
        else:
            password_error.visible = False

        # Validate name
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
            current_user["user"]["id"]
        )
        show_snackbar(page, msg)
        if success:
            # Clear fields and reset validation
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

    load_users()

    # Orders tab content for admin with filter functionality
    orders_list = ft.ListView(spacing=10, padding=10, height=300)
    current_filter = "all"
    
    # Filter buttons
    filter_all_btn = ft.ElevatedButton(
        "All Orders",
        bgcolor=ACCENT_DARK,
        color=CREAM,
        on_click=lambda e: load_orders("all"),
        icon=ft.Icons.LIST
    )
    
    filter_placed_btn = ft.ElevatedButton(
        "Placed",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: load_orders("placed"),
        icon=ft.Icons.SHOPPING_BAG
    )
    
    filter_preparing_btn = ft.ElevatedButton(
        "Preparing",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: load_orders("preparing"),
        icon=ft.Icons.RESTAURANT
    )
    
    filter_delivery_btn = ft.ElevatedButton(
        "Out for Delivery",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: load_orders("out for delivery"),
        icon=ft.Icons.LOCAL_SHIPPING
    )
    
    filter_delivered_btn = ft.ElevatedButton(
        "Delivered",
        bgcolor=DARK_GREEN,
        color=CREAM,
        on_click=lambda e: load_orders("delivered"),
        icon=ft.Icons.CHECK_CIRCLE
    )
    
    filter_cancelled_btn = ft.ElevatedButton(
        "Cancelled",
        bgcolor=DARK_GREEN,
        color=CREAM,
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

    def load_orders(filter_status="all"):
        nonlocal current_filter
        current_filter = filter_status
        update_filter_buttons(filter_status)
        
        orders_list.controls.clear()
        all_orders = get_all_orders()
        
        if filter_status == "all":
            orders = all_orders
        else:
            orders = [order for order in all_orders if order['status'] == filter_status]
        
        count_text = ft.Text(
            f"Showing {len(orders)} order(s)" + (f" with status '{filter_status}'" if filter_status != "all" else ""),
            size=14,
            color=TEXT_DARK,
            italic=True
        )
        orders_list.controls.append(count_text)
        
        if not orders:
            orders_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No orders found with this status.",
                        size=16,
                        color=TEXT_DARK,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
        
        for order in orders:
            formatted_date = format_datetime_philippine(order.get('created_at'))
            
            items_str = "\n".join([f"- {item['name']} (x{item['quantity']}) - ₱{item['price'] * item['quantity']:.2f}" for item in order["items"]])
            status_dropdown = ft.Dropdown(
                value=order['status'],
                options=[ft.dropdown.Option(s) for s in ["placed", "preparing", "out for delivery", "delivered", "cancelled"]],
                on_change=lambda e, oid=order['id']: on_status_change(e, oid),
                bgcolor=FIELD_BG,
                color=TEXT_DARK,
                border_color=FIELD_BORDER,
                focused_border_color=ACCENT_PRIMARY
            )
            orders_list.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=15,
                        bgcolor=FIELD_BG,
                        border=ft.border.all(1, FIELD_BORDER),
                        border_radius=8,
                        content=ft.Column(
                            [
                                ft.Text(f"Order #{order['customer_order_number']} - {order['customer_name']}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Text(f"System ID: {order['id']}", size=12, color=TEXT_DARK),
                                ft.Text(f"Customer: {order['customer_name']}", size=14, color=TEXT_DARK),
                                ft.Text(f"Date: {formatted_date}", size=14, color=TEXT_DARK),
                                ft.Text(f"Status: ", size=14, color=TEXT_DARK),
                                status_dropdown,
                                ft.Divider(height=10, color=FIELD_BORDER),
                                ft.Text("Items:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Text(items_str, size=13, color=TEXT_DARK),
                                ft.Divider(height=10, color=FIELD_BORDER),
                                ft.Text(f"Total: ₱{order['total_amount']:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
                                ft.Text(f"Delivery Address: {order['delivery_address']}", size=13, color=TEXT_DARK),
                                ft.Text(f"Contact: {order['contact_number']}", size=13, color=TEXT_DARK)
                            ],
                            spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.START
                        )
                    )
                )
            )
        page.update()

    def on_status_change(e, order_id):
        update_order_status(order_id, e.control.value, current_user["user"]["id"])
        show_snackbar(page, "Status updated!")
        load_orders(current_filter)

    load_orders()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Admin Dashboard", size=20, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color=CREAM, on_click=goto_profile, tooltip="Profile"),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=CREAM, on_click=goto_logout, tooltip="Logout")
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=15,
                    border_radius=8
                ),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    expand=True,
                    tabs=[
                        ft.Tab(
                            text="Users",
                            content=ft.Column(
                                [
                                    ft.Text("User Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Create New User", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                            new_email,
                                            email_error,
                                            ft.Container(height=5),
                                            password_requirements,
                                            ft.Container(height=5),
                                            new_password,
                                            password_error,
                                            password_strength_bar,
                                            password_strength_text,
                                            ft.Container(height=5),
                                            new_name,
                                            name_error,
                                            new_role,
                                            ft.ElevatedButton(
                                                "Add User", 
                                                bgcolor=ACCENT_DARK, 
                                                color=CREAM, 
                                                on_click=add_user,
                                                icon=ft.Icons.PERSON_ADD
                                            )
                                        ]),
                                        padding=15,
                                        bgcolor=FIELD_BG,
                                        border=ft.border.all(1, FIELD_BORDER),
                                        border_radius=10
                                    ),
                                    ft.Container(height=10),
                                    ft.Text("Filter Users", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Container(
                                        content=ft.Column([
                                            search_field,
                                            ft.Container(height=10),
                                            ft.Text("Filter by Role:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                            ft.Row([
                                                role_filter_all_btn,
                                                role_filter_customer_btn,
                                                role_filter_owner_btn,
                                                role_filter_admin_btn,
                                            ], wrap=True, spacing=5),
                                            ft.Container(height=10),
                                            ft.Text("Filter by Status:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                            ft.Row([
                                                status_filter_all_btn,
                                                status_filter_active_btn,
                                                status_filter_disabled_btn,
                                                status_filter_locked_btn,
                                            ], wrap=True, spacing=5)
                                        ]),
                                        padding=15,
                                        border=ft.border.all(1, FIELD_BORDER),
                                        border_radius=10,
                                        margin=ft.margin.only(bottom=10),
                                        bgcolor=FIELD_BG
                                    ),
                                    ft.Text("All Users", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    users_list
                                ],
                                scroll=ft.ScrollMode.AUTO
                            )
                        ),
                        ft.Tab(
                            text="Orders",
                            content=ft.Column(
                                [
                                    ft.Text("Order Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Filter by Status:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
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
                                        border=ft.border.all(1, FIELD_BORDER),
                                        border_radius=10,
                                        margin=ft.margin.only(bottom=10),
                                        bgcolor=FIELD_BG
                                    ),
                                    orders_list
                                ],
                                scroll=ft.ScrollMode.AUTO
                            )
                        )
                    ]
                )
            ],
        ),
        expand=True,
        padding=10,
        bgcolor=CREAM
    )
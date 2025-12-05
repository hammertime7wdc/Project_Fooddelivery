import flet as ft
from datetime import datetime
from core.auth import (
    get_all_users, create_user_by_admin, delete_user, 
    disable_user, enable_user, validate_email, 
    validate_password, validate_full_name, get_password_strength
)
from core.database import get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine  # ← ADDED: Import datetime formatter
from utils import show_snackbar, TEXT_LIGHT, ACCENT_DARK, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY

def admin_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    users_list = ft.ListView(expand=True, spacing=10, padding=10)

    # Password strength indicator
    password_strength_text = ft.Text("", size=12, color="grey")
    password_strength_bar = ft.ProgressBar(width=250, value=0, color="grey", bgcolor="#333")
    
    # Password requirements info box (consistent with signup screen)
    password_requirements = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.SECURITY, color=TEXT_LIGHT, size=20),
            ft.Text(
                "Password Requirements:",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=TEXT_LIGHT
            ),
            ft.Text(
                "• At least 8 characters\n"
                "• One uppercase letter (A-Z)\n"
                "• One lowercase letter (a-z)\n"
                "• One number (0-9)\n"
                "• One special character (!@#$%...)",
                size=10,
                color=TEXT_LIGHT
            )
        ]),
        padding=10,
        border=ft.border.all(1, "white"),
        border_radius=10,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#6B0113", ACCENT_DARK]
        ),
        width=250
    )

    new_email = ft.TextField(
        hint_text="Email", 
        width=250,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
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
        on_change=lambda e: update_password_strength()
    )
    
    new_name = ft.TextField(
        hint_text="Full Name", 
        width=250,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
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
        focused_border_color=ACCENT_PRIMARY
    )

    # Validation error texts
    email_error = ft.Text("", size=11, color="red", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)
    name_error = ft.Text("", size=11, color="red", visible=False)

    def validate_email_field():
        is_valid, error_msg = validate_email(new_email.value or "")
        if new_email.value:
            if is_valid:
                new_email.border_color = "green"
                email_error.visible = False
            else:
                new_email.border_color = "red"
                email_error.value = error_msg
                email_error.visible = True
        else:
            new_email.border_color = FIELD_BORDER
            email_error.visible = False
        page.update()

    def validate_name_field():
        is_valid, error_msg = validate_full_name(new_name.value or "")
        if new_name.value:
            if is_valid:
                new_name.border_color = "green"
                name_error.visible = False
            else:
                new_name.border_color = "red"
                name_error.value = error_msg
                name_error.visible = True
        else:
            new_name.border_color = FIELD_BORDER
            name_error.visible = False
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

        # Color coding (consistent with signup)
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

    def load_users():
        users_list.controls.clear()
        users = get_all_users()

        for user in users:
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
                            ft.Text(user["full_name"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                            ft.Text(f"{user['email']} ({user['role']})", size=12, color=TEXT_LIGHT),
                            ft.Text(f"Status: {status_text}", size=11, color=status_color),
                            ft.Text(f"Last login: {last_login}", size=10, color="grey"),
                            ft.Text(f"Created: {datetime.fromisoformat(user['created_at']).strftime('%b %d, %Y')}", size=10, color="grey")
                        ], expand=True),
                        ft.IconButton(
                            icon=ft.Icons.BLOCK if user["is_active"] else ft.Icons.CHECK_CIRCLE,
                            icon_color=TEXT_LIGHT,
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
                    border=ft.border.all(1, "black"),
                    border_radius=10
                )
            )
        page.update()

    def add_user(e):
        # Validate all fields
        email_valid, email_msg = validate_email(new_email.value or "")
        password_valid, password_msg = validate_password(new_password.value or "")
        name_valid, name_msg = validate_full_name(new_name.value or "")

        if not email_valid:
            email_error.value = email_msg
            email_error.visible = True
            new_email.border_color = "red"
            page.update()
            show_snackbar(page, email_msg)
            return

        if not password_valid:
            password_error.value = password_msg
            password_error.visible = True
            new_password.border_color = "red"
            page.update()
            show_snackbar(page, password_msg)
            return

        if not name_valid:
            name_error.value = name_msg
            name_error.visible = True
            new_name.border_color = "red"
            page.update()
            show_snackbar(page, name_msg)
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
            load_users()

    load_users()

    # Orders tab content for admin
    orders_list = ft.ListView(expand=True, spacing=10, padding=10)

    def load_orders():
        orders_list.controls.clear()
        orders = get_all_orders()
        
        for order in orders:
            # ← CHANGED: Use the new formatting function
            formatted_date = format_datetime_philippine(order.get('created_at'))
            
            items_str = "\n".join([f"- {item['name']} (x{item['quantity']}) - ₱{item['price'] * item['quantity']:.2f}" for item in order["items"]])
            status_dropdown = ft.Dropdown(
                value=order['status'],
                options=[ft.dropdown.Option(s) for s in ["placed", "preparing", "out for delivery", "delivered", "cancelled"]],
                on_change=lambda e, oid=order['id']: on_status_change(e, oid),
                bgcolor=FIELD_BG,
                color=TEXT_DARK,
                border_color=FIELD_BORDER
            )
            orders_list.controls.append(
                ft.Card(
                    elevation=4,
                    content=ft.Container(
                        padding=15,
                        content=ft.Column(
                            [
                                ft.Text(f"Order #{order['customer_order_number']} - {order['customer_name']}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                ft.Text(f"System ID: {order['id']}", size=12, color="grey"),
                                ft.Text(f"Customer: {order['customer_name']}", size=14, color="grey"),
                                ft.Text(f"Date: {formatted_date}", size=14, color="grey"),
                                ft.Text(f"Status: ", size=14, color="grey"),
                                status_dropdown,
                                ft.Divider(height=10, color="transparent"),
                                ft.Text("Items:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                ft.Text(items_str, size=13, color=TEXT_LIGHT),
                                ft.Divider(height=10, color="transparent"),
                                ft.Text(f"Total: ₱{order['total_amount']:.2f}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                ft.Text(f"Delivery Address: {order['delivery_address']}", size=13, color="grey"),
                                ft.Text(f"Contact: {order['contact_number']}", size=13, color="grey")
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
        load_orders()

    load_orders()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Admin Dashboard", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color=TEXT_LIGHT, on_click=goto_profile, tooltip="Profile"),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=TEXT_LIGHT, on_click=goto_logout, tooltip="Logout")
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=["#6B0113", ACCENT_DARK]
                    ),
                    padding=15
                ),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(
                            text="Users",
                            content=ft.Column(
                                [
                                    ft.Text("User Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Create New User", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
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
                                                color=TEXT_LIGHT, 
                                                on_click=add_user,
                                                icon=ft.Icons.PERSON_ADD
                                            )
                                        ]),
                                        padding=15,
                                        gradient=ft.LinearGradient(
                                            begin=ft.alignment.top_center,
                                            end=ft.alignment.bottom_center,
                                            colors=["#9A031E", "#6B0113"]
                                        ),
                                        border_radius=10
                                    ),
                                    ft.Container(height=10),
                                    ft.Text("All Users", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                    users_list
                                ],
                                scroll=ft.ScrollMode.AUTO
                            )
                        ),
                        ft.Tab(
                            text="Orders",
                            content=ft.Column(
                                [
                                    ft.Text("Order Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                    orders_list
                                ],
                                scroll=ft.ScrollMode.AUTO
                            )
                        )
                    ]
                )
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        padding=10,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#9A031E", "#6B0113"]
        )
    )
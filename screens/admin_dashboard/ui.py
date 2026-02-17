import flet as ft
from utils import (
    TEXT_LIGHT,
    ACCENT_DARK,
    FIELD_BG,
    TEXT_DARK,
    FIELD_BORDER,
    ACCENT_PRIMARY,
    CREAM,
    DARK_GREEN,
)
from .handlers import create_admin_handlers


def admin_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    users_list = ft.GridView(
        expand=True,
        max_extent=360,
        child_aspect_ratio=1.2,
        spacing=12,
        run_spacing=12,
        padding=10,
    )

    search_field = ft.TextField(
        hint_text="Search by name or email...",
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        prefix_icon=ft.Icons.SEARCH,
        text_style=ft.TextStyle(color=TEXT_DARK, size=12),
        hint_style=ft.TextStyle(color=TEXT_DARK, size=12),
    )
    password_strength_bar = ft.ProgressBar(width=250, value=0, color=DARK_GREEN, bgcolor=FIELD_BG)
    password_strength_text = ft.Text("", size=11, color=TEXT_DARK, visible=False)

    email_error = ft.Text("", size=11, color="red", visible=False)
    password_error = ft.Text("", size=11, color="red", visible=False)
    name_error = ft.Text("", size=11, color="red", visible=False)

    new_email = ft.TextField(
        hint_text="Email",
        width=250,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        hint_style=ft.TextStyle(color=TEXT_DARK),
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
    )

    new_role = ft.Dropdown(
        width=250,
        options=[
            ft.dropdown.Option("customer", content=ft.Text("Customer", color="#000000", size=13)),
            ft.dropdown.Option("owner", content=ft.Text("Owner", color="#000000", size=13)),
            ft.dropdown.Option("admin", content=ft.Text("Admin", color="#000000", size=13)),
        ],
        value="customer",
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
    )

    role_filter_selected = {"value": "all"}
    status_filter_selected = {"value": "all"}

    def make_role_filter_chip(label, role):
        is_selected = role == role_filter_selected["value"]
        return ft.Container(
            content=ft.Text(
                label,
                size=13,
                color="#FFFFFF" if is_selected else "#000000",
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
        )

    def make_status_filter_chip(label, status):
        is_selected = status == status_filter_selected["value"]
        return ft.Container(
            content=ft.Text(
                label,
                size=13,
                color="#FFFFFF" if is_selected else "#000000",
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
        )

    role_filter_all_btn = make_role_filter_chip("All Roles", "all")
    role_filter_customer_btn = make_role_filter_chip("Customers", "customer")
    role_filter_owner_btn = make_role_filter_chip("Owners", "owner")
    role_filter_admin_btn = make_role_filter_chip("Admins", "admin")

    status_filter_all_btn = make_status_filter_chip("All Status", "all")
    status_filter_active_btn = make_status_filter_chip("Active", "active")
    status_filter_disabled_btn = make_status_filter_chip("Disabled", "disabled")
    status_filter_locked_btn = make_status_filter_chip("Locked", "locked")

    orders_list = ft.GridView(
        expand=True,
        max_extent=360,
        child_aspect_ratio=1.2,
        spacing=12,
        run_spacing=12,
        padding=10,
    )

    order_search_field = ft.TextField(
        hint_text="Search order, customer, item...",
        width=280,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        prefix_icon=ft.Icons.SEARCH,
        text_style=ft.TextStyle(color=TEXT_DARK, size=12),
        hint_style=ft.TextStyle(color=TEXT_DARK, size=12),
    )

    date_range_dropdown = ft.Dropdown(
        width=180,
        options=[
            ft.dropdown.Option("all", text="All time", content=ft.Text("All time", color="#000000", size=13, weight=ft.FontWeight.BOLD)),
            ft.dropdown.Option("7", text="Last 7 days", content=ft.Text("Last 7 days", color="#000000", size=13, weight=ft.FontWeight.BOLD)),
            ft.dropdown.Option("30", text="Last 30 days", content=ft.Text("Last 30 days", color="#000000", size=13, weight=ft.FontWeight.BOLD)),
            ft.dropdown.Option("90", text="Last 90 days", content=ft.Text("Last 90 days", color="#000000", size=13, weight=ft.FontWeight.BOLD)),
        ],
        value="30",
        bgcolor=FIELD_BG,
        fill_color=FIELD_BG,
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        border_width=1,
        filled=True,
        text_style=ft.TextStyle(color="#000000", size=13, weight=ft.FontWeight.BOLD),
        label_style=ft.TextStyle(color="#000000", size=13, weight=ft.FontWeight.BOLD),
    )

    order_filter_selected = {"value": "all"}

    def make_order_filter_chip(label, status):
        is_selected = status == order_filter_selected["value"]
        return ft.Container(
            content=ft.Text(
                label,
                size=13,
                color="#FFFFFF" if is_selected else "#000000",
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
        )

    filter_all_btn = make_order_filter_chip("All Orders", "all")
    filter_placed_btn = make_order_filter_chip("Placed", "placed")
    filter_preparing_btn = make_order_filter_chip("Preparing", "preparing")
    filter_delivery_btn = make_order_filter_chip("Out for Delivery", "out for delivery")
    filter_delivered_btn = make_order_filter_chip("Delivered", "delivered")
    filter_cancelled_btn = make_order_filter_chip("Cancelled", "cancelled")

    order_filter_row = ft.Row(
        [
            filter_all_btn,
            filter_placed_btn,
            filter_preparing_btn,
            filter_delivery_btn,
            filter_delivered_btn,
            filter_cancelled_btn,
        ],
        spacing=8,
        wrap=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Build the form column
    form_column = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text("Create New User", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                
                # Basic Information Section
                ft.Text("Basic Information", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                new_email,
                email_error,
                new_name,
                name_error,
                new_role,
                ft.Container(height=10),
                
                # Password Section
                ft.Text("Password Setup", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                new_password,
                password_error,
                password_strength_bar,
                password_strength_text,
                ft.Container(height=10),
                
                # Form Actions (buttons will be stored for later handler assignment)
            ]),
            padding=20,
            bgcolor=CREAM,
            border=ft.border.all(1, FIELD_BORDER),
            border_radius=12,
        ),
    ])
    
    # Create the form action buttons separately
    add_user_btn = ft.ElevatedButton(
        "Add User",
        bgcolor=ACCENT_DARK,
        color=CREAM,
        on_click=lambda e: None,  # Will be set after handlers
        icon=ft.Icons.PERSON_ADD,
        width=150,
    )
    
    cancel_btn = ft.ElevatedButton(
        "Cancel",
        bgcolor="#999999",
        color=CREAM,
        on_click=lambda e: None,  # Will be set after handlers
        icon=ft.Icons.CLOSE,
        width=150,
    )
    
    # Add the buttons row to the form
    form_column.controls[0].content.controls.append(
        ft.Row([add_user_btn, cancel_btn], spacing=10)
    )
    
    # Create form container with the form column inside
    form_container = ft.Container(
        content=form_column,
        visible=False,
        width=350,
    )

    # Create user details panel (initially hidden)
    user_details_content = ft.Column([], spacing=10)
    user_details_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("User Details", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=20,
                    icon_color=TEXT_DARK,
                    tooltip="Close",
                    on_click=lambda e: None,  # Will be set after handlers
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=FIELD_BORDER),
            user_details_content,
        ], scroll=ft.ScrollMode.AUTO),
        visible=False,
        width=350,
        padding=20,
        bgcolor=CREAM,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=12,
    )

    handlers = create_admin_handlers(
        page=page,
        current_user=current_user,
        users_list=users_list,
        orders_list=orders_list,
        new_email=new_email,
        new_password=new_password,
        new_name=new_name,
        new_role=new_role,
        email_error=email_error,
        password_error=password_error,
        name_error=name_error,
        password_strength_text=password_strength_text,
        password_strength_bar=password_strength_bar,
        user_search_field=search_field,
        form_container=form_container,
        user_details_panel=user_details_panel,
        user_details_content=user_details_content,
        role_filter_buttons={
            "all": role_filter_all_btn,
            "customer": role_filter_customer_btn,
            "owner": role_filter_owner_btn,
            "admin": role_filter_admin_btn,
        },
        status_filter_buttons={
            "all": status_filter_all_btn,
            "active": status_filter_active_btn,
            "disabled": status_filter_disabled_btn,
            "locked": status_filter_locked_btn,
        },
        role_filter_selected=role_filter_selected,
        status_filter_selected=status_filter_selected,
        order_filter_buttons={
            "all": filter_all_btn,
            "placed": filter_placed_btn,
            "preparing": filter_preparing_btn,
            "out for delivery": filter_delivery_btn,
            "delivered": filter_delivered_btn,
            "cancelled": filter_cancelled_btn,
        },
        order_search_field=order_search_field,
        date_range_dropdown=date_range_dropdown,
    )

    new_email.on_change = handlers["validate_email_field"]
    new_password.on_change = handlers["update_password_strength"]
    new_name.on_change = handlers["validate_name_field"]
    search_field.on_change = handlers["on_user_search_change"]

    # Update form button handlers after handlers dict is created
    add_user_btn.on_click = handlers["add_user"]
    cancel_btn.on_click = handlers["hide_form"]
    
    # Update user details panel close button
    user_details_panel.content.controls[0].controls[1].on_click = handlers["hide_user_details"]

    role_filter_all_btn.on_click = lambda e: handlers["filter_users_by_role"]("all")
    role_filter_customer_btn.on_click = lambda e: handlers["filter_users_by_role"]("customer")
    role_filter_owner_btn.on_click = lambda e: handlers["filter_users_by_role"]("owner")
    role_filter_admin_btn.on_click = lambda e: handlers["filter_users_by_role"]("admin")

    status_filter_all_btn.on_click = lambda e: handlers["filter_users_by_status"]("all")
    status_filter_active_btn.on_click = lambda e: handlers["filter_users_by_status"]("active")
    status_filter_disabled_btn.on_click = lambda e: handlers["filter_users_by_status"]("disabled")
    status_filter_locked_btn.on_click = lambda e: handlers["filter_users_by_status"]("locked")

    filter_all_btn.on_click = lambda e: handlers["load_orders"]("all")
    filter_placed_btn.on_click = lambda e: handlers["load_orders"]("placed")
    filter_preparing_btn.on_click = lambda e: handlers["load_orders"]("preparing")
    filter_delivery_btn.on_click = lambda e: handlers["load_orders"]("out for delivery")
    filter_delivered_btn.on_click = lambda e: handlers["load_orders"]("delivered")
    filter_cancelled_btn.on_click = lambda e: handlers["load_orders"]("cancelled")

    order_search_field.on_change = handlers["on_order_search_change"]
    date_range_dropdown.on_change = handlers["on_date_range_change"]

    handlers["load_users"]()
    handlers["load_orders"]()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Admin Dashboard", size=20, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color=CREAM, on_click=goto_profile, tooltip="Profile"),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=CREAM, on_click=goto_logout, tooltip="Logout"),
                        ], tight=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=15,
                    border_radius=8,
                ),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    expand=True,
                    label_color="#000000",
                    unselected_label_color="#000000",
                    indicator_color=ACCENT_PRIMARY,
                    tabs=[
                        ft.Tab(
                            text="Users",
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("User Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                        ft.Text("View Users", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                        ft.Row(
                                            [
                                                search_field,
                                            ],
                                            wrap=True,
                                            spacing=10,
                                        ),
                                        ft.Row([
                                            role_filter_all_btn,
                                            role_filter_customer_btn,
                                            role_filter_owner_btn,
                                            role_filter_admin_btn,
                                        ], wrap=True, spacing=8),
                                        ft.Row([
                                            status_filter_all_btn,
                                            status_filter_active_btn,
                                            status_filter_disabled_btn,
                                            status_filter_locked_btn,
                                        ], wrap=True, spacing=8),
                                        ft.Row([
                                            ft.Container(
                                                content=users_list,
                                                padding=15,
                                                border_radius=10,
                                                border=ft.border.all(1, FIELD_BORDER),
                                                height=560,
                                                expand=True,
                                            ),
                                            user_details_panel,
                                        ], spacing=15),
                                        
                                        # Add New User Button
                                        ft.Container(
                                            content=ft.ElevatedButton(
                                                content=ft.Row([
                                                    ft.Icon(ft.Icons.ADD_CIRCLE_ROUNDED, size=20),
                                                    ft.Text("Add New User", size=15, weight=ft.FontWeight.BOLD)
                                                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                                                bgcolor=ACCENT_DARK,
                                                color=CREAM,
                                                height=50,
                                                on_click=lambda e: handlers["show_form"](e)
                                            ),
                                            width=350
                                        ),
                                        
                                        # Form Container (initially hidden)
                                        form_container
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=15,
                                ),
                                expand=True,
                                padding=10,
                                bgcolor="#FFFFFF",
                            ),
                        ),
                        ft.Tab(
                            text="Orders",
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Order Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                        ft.Row(
                                            [
                                                order_search_field,
                                                date_range_dropdown,
                                            ],
                                            wrap=True,
                                            spacing=10,
                                        ),
                                        order_filter_row,
                                        ft.Container(
                                            content=orders_list,
                                            padding=15,
                                            border_radius=10,
                                            border=ft.border.all(1, FIELD_BORDER),
                                            height=560,
                                        ),
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=15,
                                ),
                                expand=True,
                                padding=10,
                                bgcolor="#FFFFFF",
                            ),
                        ),
                    ],
                ),
            ],
        ),
        expand=True,
        padding=10,
        bgcolor=CREAM,
    )

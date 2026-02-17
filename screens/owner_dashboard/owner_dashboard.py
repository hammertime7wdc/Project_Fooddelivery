import flet as ft
from utils import CREAM, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY
from .ui import (
    create_menu_filter_buttons,
    create_order_filter_buttons,
    create_menu_form_fields,
    create_menu_form_container,
    create_header
)
from .handlers import create_menu_handlers, create_order_handlers


def owner_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    # Initialize menu list
    menu_list = ft.ListView(spacing=10, padding=10, height=300)
    
    # Initialize orders list
    orders_list = ft.GridView(
        expand=True,
        max_extent=360,
        child_aspect_ratio=1.2,
        spacing=12,
        run_spacing=12,
        padding=10,
    )
    
    # Create form fields
    form_fields = create_menu_form_fields()
    uploaded_image = {"data": None, "type": "emoji"}
    
    # Create file picker
    file_picker = ft.FilePicker(on_result=lambda e: menu_handlers["handle_file_pick"](e))
    page.overlay.append(file_picker)
    
    # Create form container
    form_container = ft.Container(visible=False)
    
    # Create menu filter buttons
    menu_filter_buttons = create_menu_filter_buttons(lambda cat: menu_handlers["load_menu"](cat))
    
    # Create order filter buttons (returns tuple of (row, buttons_dict))
    order_filter_buttons_row, order_filter_buttons = create_order_filter_buttons()
    
    # Create order search field
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
    
    # Create date range dropdown
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
    
    # Create menu form
    form_container = create_menu_form_container(
        file_picker,
        form_fields,
        lambda e: menu_handlers["save_item"](e)
    )
    
    # Create menu handlers
    menu_handlers = create_menu_handlers(page, current_user, menu_list, form_container, form_fields, uploaded_image, menu_filter_buttons)
    

    # Create order handlers
    order_handlers = create_order_handlers(page, current_user, orders_list, order_filter_buttons, order_search_field, date_range_dropdown)
    
    # Connect filter button callbacks now that handlers exist
    def update_filter_button_callbacks():
        for status, button in order_filter_buttons.items():
            button.on_click = lambda e, s=status: order_handlers["load_orders"](s)
    
    update_filter_button_callbacks()
    
    # Initial loads
    menu_handlers["load_menu"]()
    order_handlers["load_orders"]()
    
    # Create header
    header = create_header(goto_profile, goto_logout)
    
    # Return the main container
    return ft.Container(
        content=ft.Column(
            [
                header,
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    expand=True,
                    label_color="#000000",
                    unselected_label_color="#000000",
                    indicator_color=ACCENT_PRIMARY,
                    tabs=[
                        ft.Tab(
                            text="Menu",
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Menu Management", size=18, weight=ft.FontWeight.BOLD, color="#000000"),
                                        
                                        # Category filter chips
                                        ft.Row([
                                            menu_filter_buttons["all"],
                                            menu_filter_buttons["appetizers"],
                                            menu_filter_buttons["mains"],
                                            menu_filter_buttons["desserts"],
                                            menu_filter_buttons["drinks"],
                                            menu_filter_buttons["other"],
                                        ], wrap=True, spacing=8),
                                        
                                        # Menu items container
                                        ft.Container(
                                            content=menu_list,
                                            bgcolor="#FFFFFF",
                                            padding=15,
                                            border_radius=15,
                                            border=ft.border.all(1, FIELD_BORDER),
                                            height=350
                                        ),
                                        
                                        # Add new item button
                                        ft.Container(
                                            content=ft.ElevatedButton(
                                                content=ft.Row([
                                                    ft.Icon(ft.Icons.ADD_CIRCLE_ROUNDED, size=20),
                                                    ft.Text("Add New Item", size=15, weight=ft.FontWeight.BOLD)
                                                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                                                bgcolor=ACCENT_PRIMARY,
                                                color="white",
                                                height=50,
                                                on_click=lambda e: menu_handlers["show_form"](e)
                                            ),
                                            width=350
                                        ),
                                        form_container
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=10
                                ),
                                expand=True,
                                padding=10,
                                bgcolor=CREAM
                            )
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
                                        # Status filter chips
                                        order_filter_buttons_row,
                                        
                                        # Orders list container
                                        ft.Container(
                                            content=orders_list,
                                            padding=15,
                                            border_radius=10,
                                            border=ft.border.all(1, FIELD_BORDER),
                                            height=560,
                                        )
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=15
                                ),
                                expand=True,
                                padding=10,
                                bgcolor="#FFFFFF",
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

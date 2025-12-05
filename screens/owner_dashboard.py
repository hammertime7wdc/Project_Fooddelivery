import flet as ft
import base64
from datetime import datetime
from core.database import get_all_menu_items, create_menu_item, update_menu_item, delete_menu_item, get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine
from utils import show_snackbar, create_image_widget, TEXT_LIGHT, ACCENT_DARK, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY

def owner_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    # Menu filter functionality
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)
    current_menu_filter = "All"  # Track current menu filter
    
    # Menu filter buttons
    menu_filter_all_btn = ft.ElevatedButton(
        "All",
        bgcolor=ACCENT_DARK,
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("All"),
        icon=ft.Icons.RESTAURANT_MENU
    )
    
    menu_filter_appetizers_btn = ft.ElevatedButton(
        "Appetizers",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Appetizers"),
        icon=ft.Icons.RESTAURANT
    )
    
    menu_filter_mains_btn = ft.ElevatedButton(
        "Mains",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Mains"),
        icon=ft.Icons.DINNER_DINING
    )
    
    menu_filter_desserts_btn = ft.ElevatedButton(
        "Desserts",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Desserts"),
        icon=ft.Icons.CAKE
    )
    
    menu_filter_drinks_btn = ft.ElevatedButton(
        "Drinks",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Drinks"),
        icon=ft.Icons.LOCAL_BAR
    )
    
    menu_filter_other_btn = ft.ElevatedButton(
        "Other",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Other"),
        icon=ft.Icons.MORE_HORIZ
    )

    def update_menu_filter_buttons(active_filter):
        """Update menu button colors to show active filter"""
        buttons = {
            "All": menu_filter_all_btn,
            "Appetizers": menu_filter_appetizers_btn,
            "Mains": menu_filter_mains_btn,
            "Desserts": menu_filter_desserts_btn,
            "Drinks": menu_filter_drinks_btn,
            "Other": menu_filter_other_btn
        }
        
        for filter_name, button in buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
            else:
                button.bgcolor = "#555"
        
        page.update()


    name_field = ft.TextField(
        hint_text="Item name", 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    desc_field = ft.TextField(
        hint_text="Description", 
        width=300,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    price_field = ft.TextField(
        hint_text="Price", 
        width=300, 
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY
    )
    category_dropdown = ft.Dropdown(
        hint_text="Category",
        width=300,
        options=[ft.dropdown.Option(key) for key in ["Appetizers", "Mains", "Desserts", "Drinks", "Other"]],
        value="Other",
        bgcolor=FIELD_BG,
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        autofocus=False
    )
    
    # Image upload
    image_preview = ft.Container(
        content=ft.Icon(ft.Icons.IMAGE, size=100, color="grey"),
        width=150,
        height=150,
        border=ft.border.all(2, "grey"),
        border_radius=10,
        alignment=ft.alignment.center
    )
    
    uploaded_image = {"data": None, "type": "emoji"}

    file_picker = ft.FilePicker(on_result=lambda e: handle_file_pick(e))
    page.overlay.append(file_picker)

    form_container = ft.Container(visible=False)
    edit_mode = {"active": False, "item_id": None}

    def delete_item(item_id):
        nonlocal current_menu_filter
        user_id = current_user["user"]["id"]
        delete_menu_item(item_id, user_id)
        show_snackbar(page, "Item deleted!")
        load_menu(current_menu_filter)

    def edit_item(item):
        edit_mode["active"] = True
        edit_mode["item_id"] = item["id"]
        name_field.value = item["name"]
        desc_field.value = item["description"]
        price_field.value = str(item["price"])
        category_dropdown.value = item.get("category", "Other")
        
        # Load existing image
        if item.get("image"):
            uploaded_image["data"] = item["image"]
            uploaded_image["type"] = item.get("image_type", "emoji")
            image_preview.content = create_image_widget(item, 150, 150)
        
        form_container.visible = True
        page.update()

    def load_menu(filter_category="All"):
        nonlocal current_menu_filter
        current_menu_filter = filter_category
        update_menu_filter_buttons(filter_category)
        
        menu_list.controls.clear()
        all_items = get_all_menu_items()
        
        # Filter menu items based on category
        if filter_category == "All":
            items = all_items
        else:
            items = [item for item in all_items if item.get("category") == filter_category]
        
        # Show count
        count_text = ft.Text(
            f"Showing {len(items)} item(s)" + (f" in category '{filter_category}'" if filter_category != "All" else ""),
            size=14,
            color="grey",
            italic=True
        )
        menu_list.controls.append(count_text)
        
        if not items:
            menu_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No items found in this category.",
                        size=16,
                        color="grey",
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )

        for item in items:
            menu_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        create_image_widget(item, 70, 70),
                        ft.Column([
                            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                            ft.Text(item["description"], size=12, color=TEXT_LIGHT),
                            ft.Text(f"₱{item['price']:.2f}", size=14, color=TEXT_LIGHT),
                            ft.Text(f"Category: {item.get('category', 'Other')}", size=11, color="grey", italic=True)
                        ], expand=True),

                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=TEXT_LIGHT, on_click=lambda e, item=item: edit_item(item)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, id=item["id"]: delete_item(id))
                    ]),
                    padding=10,
                    border=ft.border.all(1, "black"),
                    border_radius=10
                )
            )
        page.update()

    def handle_file_pick(e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            if file.size > 3145728:  # 3MB limit
                show_snackbar(page, "Image size must be under 3MB")
                return
            if not file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                show_snackbar(page, "Only JPG, PNG, GIF allowed")
                return
            try:
                with open(file.path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                uploaded_image["data"] = image_data
                uploaded_image["type"] = "base64"
                
                # Update preview
                image_preview.content = ft.Image(
                    src_base64=image_data,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.COVER,
                    border_radius=10
                )
                show_snackbar(page, "Image uploaded successfully!")
                page.update()
            except Exception as ex:
                show_snackbar(page, f"Error uploading image: {str(ex)}")

    def save_item(e):
        nonlocal current_menu_filter
        if not name_field.value or not desc_field.value or not price_field.value:
            show_snackbar(page, "Please fill all fields!")
            return

        user_id = current_user["user"]["id"]
        image_data = uploaded_image["data"] if uploaded_image["data"] else "🍽️"
        image_type = uploaded_image["type"]
        category = category_dropdown.value

        if edit_mode["active"]:
            update_menu_item(
                edit_mode["item_id"],
                name_field.value,
                desc_field.value,
                float(price_field.value),
                image_data,
                image_type,
                category,
                user_id
            )
            show_snackbar(page, "Item updated!")
            edit_mode["active"] = False
        else:
            create_menu_item(
                name_field.value,
                desc_field.value,
                float(price_field.value),
                image_data,
                image_type,
                category,
                user_id
            )
            show_snackbar(page, "Item added!")

        # Reset form
        name_field.value = ""
        desc_field.value = ""
        price_field.value = ""
        category_dropdown.value = "Other"
        uploaded_image["data"] = None
        uploaded_image["type"] = "emoji"
        image_preview.content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")
        form_container.visible = False
        load_menu(current_menu_filter)

    def show_form(e):
        # Reset form
        edit_mode["active"] = False
        name_field.value = ""
        desc_field.value = ""
        price_field.value = ""
        category_dropdown.value = "Other"
        uploaded_image["data"] = None
        uploaded_image["type"] = "emoji"
        image_preview.content = ft.Icon(ft.Icons.IMAGE, size=100, color="grey")
        
        form_container.visible = True
        page.update()

    load_menu()

    form_container.content = ft.Column([
        ft.Text("Menu Item Form", size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
        name_field,
        desc_field,
        price_field,
        category_dropdown,
        ft.Container(height=10),
        ft.Text("Upload Image:", size=14, color=TEXT_LIGHT),
        image_preview,
        ft.ElevatedButton(
            "Choose Image",
            icon=ft.Icons.UPLOAD_FILE,
            bgcolor=ACCENT_DARK,
            color=TEXT_LIGHT,
            on_click=lambda _: file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "gif"],
                dialog_title="Select Food Image"
            )
        ),
        ft.Container(height=10),
        ft.ElevatedButton(
            "Save Item",
            width=300,
            bgcolor=ACCENT_DARK,
            color=TEXT_LIGHT,
            on_click=save_item
        )
    ])
    form_container.padding = 15
    form_container.border = ft.border.all(2, "black")
    form_container.border_radius = 10

    # Menu filter functionality
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)
    current_menu_filter = "All"  # Track current menu filter
    
    # Menu filter buttons
    menu_filter_all_btn = ft.ElevatedButton(
        "All",
        bgcolor=ACCENT_DARK,
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("All"),
        icon=ft.Icons.RESTAURANT_MENU
    )
    
    menu_filter_appetizers_btn = ft.ElevatedButton(
        "Appetizers",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Appetizers"),
        icon=ft.Icons.RESTAURANT
    )
    
    menu_filter_mains_btn = ft.ElevatedButton(
        "Mains",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Mains"),
        icon=ft.Icons.DINNER_DINING
    )
    
    menu_filter_desserts_btn = ft.ElevatedButton(
        "Desserts",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Desserts"),
        icon=ft.Icons.CAKE
    )
    
    menu_filter_drinks_btn = ft.ElevatedButton(
        "Drinks",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Drinks"),
        icon=ft.Icons.LOCAL_BAR
    )
    
    menu_filter_other_btn = ft.ElevatedButton(
        "Other",
        bgcolor="#555",
        color=TEXT_LIGHT,
        on_click=lambda e: load_menu("Other"),
        icon=ft.Icons.MORE_HORIZ
    )

    def update_menu_filter_buttons(active_filter):
        """Update menu button colors to show active filter"""
        buttons = {
            "All": menu_filter_all_btn,
            "Appetizers": menu_filter_appetizers_btn,
            "Mains": menu_filter_mains_btn,
            "Desserts": menu_filter_desserts_btn,
            "Drinks": menu_filter_drinks_btn,
            "Other": menu_filter_other_btn
        }
        
        for filter_name, button in buttons.items():
            if filter_name == active_filter:
                button.bgcolor = ACCENT_DARK
            else:
                button.bgcolor = "#555"
        
        page.update()

    # Orders tab content with filter functionality
    orders_list = ft.ListView(expand=True, spacing=10, padding=10)
    current_filter = "all"  # Track current filter
    
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
        """Update button colors to show active filter"""
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
        
        # Filter orders based on status
        if filter_status == "all":
            orders = all_orders
        else:
            orders = [order for order in all_orders if order['status'] == filter_status]
        
        # Show count
        count_text = ft.Text(
            f"Showing {len(orders)} order(s)" + (f" with status '{filter_status}'" if filter_status != "all" else ""),
            size=14,
            color="grey",
            italic=True
        )
        orders_list.controls.append(count_text)
        
        if not orders:
            orders_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No orders found with this status.",
                        size=16,
                        color="grey",
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
        load_orders(current_filter)  # Reload with current filter

    load_orders()  # Initial load

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Text("Restaurant Dashboard", size=20, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color=TEXT_LIGHT, on_click=goto_profile),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=TEXT_LIGHT, on_click=goto_logout)
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
                            text="Menu",
                            content=ft.Column(
                                [
                                    ft.Text("Menu Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Filter by Category:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                                            ft.Row([
                                                menu_filter_all_btn,
                                                menu_filter_appetizers_btn,
                                                menu_filter_mains_btn,
                                            ], wrap=True, spacing=5),
                                            ft.Row([
                                                menu_filter_desserts_btn,
                                                menu_filter_drinks_btn,
                                                menu_filter_other_btn,
                                            ], wrap=True, spacing=5)
                                        ]),
                                        padding=15,
                                        border=ft.border.all(1, "white"),
                                        border_radius=10,
                                        margin=ft.margin.only(bottom=10)
                                    ),
                                    menu_list,
                                    ft.ElevatedButton("Add New Item +", width=350, bgcolor=ACCENT_DARK, color=TEXT_LIGHT, on_click=show_form),
                                    form_container
                                ],
                                scroll=ft.ScrollMode.AUTO
                            )
                        ),
                        ft.Tab(
                            text="Orders",
                            content=ft.Column(
                                [
                                    ft.Text("Order Management", size=18, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
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
                                        margin=ft.margin.only(bottom=10)
                                    ),
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
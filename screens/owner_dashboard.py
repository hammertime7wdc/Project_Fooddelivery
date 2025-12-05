import flet as ft
import base64
from datetime import datetime
from core.database import get_all_menu_items, create_menu_item, update_menu_item, delete_menu_item, get_all_orders, update_order_status
from core.datetime_utils import format_datetime_philippine  # ← ADDED: Import datetime formatter
from utils import show_snackbar, create_image_widget, TEXT_LIGHT, ACCENT_DARK, FIELD_BG, TEXT_DARK, FIELD_BORDER, ACCENT_PRIMARY

def owner_dashboard_screen(page: ft.Page, current_user: dict, cart: list, goto_profile, goto_logout):
    menu_list = ft.ListView(expand=True, spacing=10, padding=10)

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
        focused_border_color=ACCENT_PRIMARY
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
        user_id = current_user["user"]["id"]
        delete_menu_item(item_id, user_id)
        show_snackbar(page, "Item deleted!")
        load_menu()

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

    def load_menu():
        menu_list.controls.clear()
        items = get_all_menu_items()

        for item in items:
            menu_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        create_image_widget(item, 70, 70),
                        ft.Column([
                            ft.Text(item["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_LIGHT),
                            ft.Text(item["description"], size=12, color=TEXT_LIGHT),
                            ft.Text(f"₱{item['price']:.2f}", size=14, color=TEXT_LIGHT)
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
            if file.size > 3145728:  # 1MB limit
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
        load_menu()

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

    # Orders tab content
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
                on_change=lambda e, oid=order['id']: on_status_change(e, oid)
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
import flet as ft
from utils import (
    ACCENT_DARK,
    FIELD_BG,
    TEXT_DARK,
    FIELD_BORDER,
    ACCENT_PRIMARY,
    CREAM,
    DARK_GREEN,
)


def create_menu_filter_buttons(load_menu_callback):
    """Create menu filter buttons with chip-style design"""
    categories = [
        {"name": "All", "key": "all"},
        {"name": "Appetizers", "key": "appetizers"},
        {"name": "Mains", "key": "mains"},
        {"name": "Desserts", "key": "desserts"},
        {"name": "Drinks", "key": "drinks"},
        {"name": "Other", "key": "other"}
    ]
    
    chips = {}
    for cat in categories:
        is_selected = cat["name"] == "All"
        chip = ft.Container(
            content=ft.Text(
                cat['name'],
                size=13,
                color="#FFFFFF" if is_selected else TEXT_DARK,
                weight=ft.FontWeight.W_500
            ),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            on_click=lambda e, name=cat["name"]: load_menu_callback(name)
        )
        chips[cat["key"]] = chip
    
    return chips


def create_order_filter_buttons():
    """Create order filter chip buttons - returns (row, buttons_dict) tuple"""
    statuses = ["all", "placed", "preparing", "out for delivery", "delivered", "cancelled"]
    status_labels = ["All Orders", "Placed", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
    buttons = {}
    
    for i, (status, label) in enumerate(zip(statuses, status_labels)):
        is_selected = status == "all"
        button = ft.Container(
            content=ft.Text(label, size=13, color="#FFFFFF" if is_selected else "#000000", weight=ft.FontWeight.W_500),
            bgcolor=ACCENT_DARK if is_selected else "#E0E0E0",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
        )
        buttons[status] = button
    
    # Return both the row and buttons dict
    buttons_row = ft.Row([buttons[s] for s in statuses], spacing=8, wrap=True, scroll=ft.ScrollMode.AUTO)
    return buttons_row, buttons


def create_menu_form_fields():
    """Create menu item form fields"""
    name_field = ft.TextField(
        hint_text="Item name", 
        label="Name",
        width=300,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    desc_field = ft.TextField(
        hint_text="Description",
        label="Description",
        width=300,
        multiline=True,
        min_lines=2,
        max_lines=3,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    price_field = ft.TextField(
        hint_text="0.00",
        label="Price (₱)",
        width=145,
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )

    stock_field = ft.TextField(
        hint_text="0",
        label="Stock",
        width=145,
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    
    # Create dropdown options with explicit text styling for visibility
    dropdown_options = []
    for cat in ["Appetizers", "Mains", "Desserts", "Drinks", "Other"]:
        dropdown_options.append(
            ft.dropdown.Option(
                key=cat,
                text=cat,
                text_style=ft.TextStyle(color="#000000", size=14, weight=ft.FontWeight.W_500)
            )
        )
    
    category_dropdown = ft.Dropdown(
        hint_text="Select category",
        label="Category",
        width=145,
        options=dropdown_options,
        value="Other",
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        autofocus=False,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD)
    )
    
    image_preview = ft.Container(
        content=ft.Icon(ft.Icons.IMAGE, size=100, color="#000000"),
        width=150,
        height=150,
        border=ft.border.all(2, FIELD_BORDER),
        border_radius=10,
        alignment=ft.alignment.center,
        bgcolor="#F5F5F5"
    )
    
    # Nutrition and recipe fields
    calories_field = ft.TextField(
        hint_text="0",
        label="Calories (optional)",
        width=145,
        keyboard_type=ft.KeyboardType.NUMBER,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    
    allergens_field = ft.TextField(
        hint_text="e.g., Nuts, Dairy",
        label="Allergens (optional)",
        width=300,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    
    ingredients_field = ft.TextField(
        hint_text="List ingredients...",
        label="Ingredients (optional)",
        width=300,
        multiline=True,
        min_lines=2,
        max_lines=4,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    
    recipe_field = ft.TextField(
        hint_text="Preparation steps...",
        label="Recipe (optional)",
        width=300,
        multiline=True,
        min_lines=3,
        max_lines=6,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666")
    )
    
    # Sale controls
    is_on_sale_checkbox = ft.Checkbox(
        label="On Sale",
        value=False,
        fill_color=ACCENT_PRIMARY,
        check_color="#FFFFFF"
    )
    
    sale_percentage_field = ft.TextField(
        hint_text="e.g., 10, 20, 50",
        label="Sale Discount %",
        value="0",
        width=300,
        bgcolor="#FFFFFF",
        color="#000000",
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.W_500, size=14),
        label_style=ft.TextStyle(color="#000000", weight=ft.FontWeight.BOLD),
        hint_style=ft.TextStyle(color="#666666"),
        keyboard_type=ft.KeyboardType.NUMBER
    )
    
    return {
        "name": name_field,
        "desc": desc_field,
        "price": price_field,
        "stock": stock_field,
        "category": category_dropdown,
        "image_preview": image_preview,
        "calories": calories_field,
        "allergens": allergens_field,
        "ingredients": ingredients_field,
        "recipe": recipe_field,
        "is_on_sale": is_on_sale_checkbox,
        "sale_percentage": sale_percentage_field
    }


def create_menu_form_container(file_picker, fields, save_callback):
    """Create the menu item form container"""
    form_container = ft.Container(visible=False)
    
    form_container.content = ft.Container(
        content=ft.Column([
            # Form header
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.RESTAURANT_MENU, color=ACCENT_PRIMARY, size=24),
                    ft.Text("Menu Item Form", size=18, weight=ft.FontWeight.BOLD, color="#000000")
                ], spacing=10),
                margin=ft.margin.only(bottom=15)
            ),
            
            # Form fields in better layout
            ft.Row([
                ft.Column([
                    ft.Text("Item Details", size=14, weight=ft.FontWeight.BOLD, color="#000000"),
                    fields["name"],
                    fields["desc"],
                    ft.Row([fields["price"], fields["category"], fields["stock"]], spacing=10),
                    ft.Container(height=5),
                    ft.Text("Nutrition & Recipe (Optional)", size=13, weight=ft.FontWeight.BOLD, color="#666666"),
                    ft.Row([fields["calories"], fields["allergens"]], spacing=10),
                    fields["ingredients"],
                    fields["recipe"],
                    ft.Container(height=5),
                    ft.Text("Sale Settings (Optional)", size=13, weight=ft.FontWeight.BOLD, color="#666666"),
                    ft.Row([
                        fields["is_on_sale"],
                        fields["sale_percentage"]
                    ], spacing=10)
                ], spacing=8, expand=True),
                
                ft.Container(width=20),
                
                # Image section
                ft.Column([
                    ft.Text("Item Image", size=14, weight=ft.FontWeight.BOLD, color="#000000"),
                    fields["image_preview"],
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.UPLOAD_FILE, size=18, color="#000000"),
                            ft.Text("Choose Image", size=13, color="#000000", weight=ft.FontWeight.W_500)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor="#E0E0E0",
                        color="#000000",
                        width=150,
                        on_click=lambda _: file_picker.pick_files(
                            allowed_extensions=["jpg", "jpeg", "png", "gif"],
                            dialog_title="Select Food Image"
                        )
                    )
                ], spacing=8)
            ], vertical_alignment=ft.CrossAxisAlignment.START),
            
            ft.Divider(height=20, color=FIELD_BORDER),
            
            # Action buttons
            ft.Row([
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE_ROUNDED, size=18, color="white"),
                            ft.Text("Save Item", size=14, weight=ft.FontWeight.BOLD, color="white")
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=ACCENT_DARK,
                        color=CREAM,
                        height=46,
                        width=170,
                        on_click=save_callback
                    )
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CANCEL_ROUNDED, size=18, color="white"),
                            ft.Text("Cancel", size=14, color="white", weight=ft.FontWeight.W_500)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor="#D32F2F",
                        color="white",
                        height=46,
                        width=170,
                        on_click=lambda e: setattr(form_container, 'visible', False) or fields["name"].page.update()
                    )
                )
            ], spacing=12, alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10),
        bgcolor="#FFFFFF",
        padding=20,
        border_radius=15,
        border=ft.border.all(2, ACCENT_PRIMARY)
    )
    
    return form_container


def create_header(goto_profile, goto_logout):
    """Create the dashboard header"""
    return ft.Container(
        content=ft.Row([
            ft.Text("Restaurant Dashboard", size=20, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
            ft.Row([
                ft.IconButton(icon=ft.Icons.PERSON, icon_color=CREAM, on_click=goto_profile),
                ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=CREAM, on_click=goto_logout)
            ], tight=True)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=ACCENT_PRIMARY,
        padding=15,
        border_radius=8
    )

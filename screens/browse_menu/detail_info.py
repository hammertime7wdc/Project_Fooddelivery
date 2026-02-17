"""Detailed food item information screen"""
import flet as ft
from utils import TEXT_LIGHT, FIELD_BG, ACCENT_PRIMARY, ACCENT_DARK, TEXT_DARK


def food_detail_screen(page: ft.Page, food_item: dict, goto_menu, current_user: dict):
    """
    Display detailed information about a food item with modern card design
    
    Args:
        page: Flet page object
        food_item: Dictionary containing food details (id, name, description, price, image, etc.)
        goto_menu: Callback to return to menu screen
        current_user: Current logged-in user data
    """
    
    # Extract food item details
    item_id = food_item.get("id")
    item_name = food_item.get("name", "Item")
    item_description = food_item.get("description", "")
    item_price = food_item.get("price", 0)
    item_category = food_item.get("category", "")
    item_restaurant = food_item.get("restaurant", "")
    
    # Image carousel state
    image_index = {"value": 0}
    
    # Create macro indicators (circles with percentages)
    def create_macro_indicator(label, percentage, color):
        """Create a circular macro indicator"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{percentage}%", size=18, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=80,
                    height=80,
                    border_radius=40,
                    bgcolor=color,
                ),
                ft.Text(label, size=12, color=TEXT_DARK, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    # Tab state
    current_tab = {"value": "Description"}
    
    # Tab content
    tab_content = ft.Column([
        ft.Text(item_description, size=13, color="#666666", height=150),
    ])
    
    def create_tab_button(label):
        """Create a tab button"""
        tab_btn = ft.Container(
            content=ft.Text(label, size=13, weight=ft.FontWeight.W_500, color=ACCENT_DARK),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            on_click=lambda e: switch_tab(label, tab_btn)
        )
        return tab_btn
    
    def switch_tab(tab_name, tab_btn):
        """Switch to a different tab"""
        current_tab["value"] = tab_name
        if tab_name == "Description":
            tab_content.controls[0].value = item_description
        elif tab_name == "Ingredients":
            tab_content.controls[0].value = "Coming soon..."
        elif tab_name == "Instructions":
            tab_content.controls[0].value = "Coming soon..."
        try:
            page.update()
        except:
            pass
    
    # Create tabs
    tabs = ft.Row([
        create_tab_button("Description"),
        create_tab_button("Ingredients"),
        create_tab_button("Instructions"),
    ], spacing=0)
    
    return ft.Container(
        content=ft.Column(
            [
                # Close button and back navigation
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_DARK, on_click=lambda e: goto_menu()),
                        ft.Text("Details", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.IconButton(icon=ft.Icons.BOOKMARK_BORDER, icon_color=TEXT_DARK),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="white"
                ),
                
                # Scrollable content
                ft.ListView([
                    # Image carousel with navigation
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Icon(ft.Icons.RESTAURANT, size=100, color="grey"),
                                width=ft.Page.width if hasattr(ft.Page, 'width') else 350,
                                height=250,
                                alignment=ft.alignment.center,
                                bgcolor="#E0E0E0",
                                border_radius=ft.border_radius.vertical(bottom=20),
                            ),
                            # Image navigation
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=24, on_click=lambda e: None),
                                ft.Row([], expand=True),
                                ft.IconButton(icon=ft.Icons.BOOKMARK, icon_color="#FF6B6B", icon_size=24),
                            ], spacing=0),
                        ], spacing=0),
                        margin=0,
                        padding=0
                    ),
                    
                    # Item name and price
                    ft.Container(
                        content=ft.Column([
                            ft.Text(item_name, size=22, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ft.Text(f"₱{item_price:.2f}", size=18, color=ACCENT_PRIMARY, weight=ft.FontWeight.BOLD),
                        ], spacing=5),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    ),
                    
                    # Info row: Calories, Time, Servings
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.FIRE_TRUCK, color=ACCENT_PRIMARY, size=16), ft.Text("273 kcal", size=12, color=TEXT_DARK)], spacing=5),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Divider(height=40, color="#DDD"),
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.SCHEDULE, color=ACCENT_PRIMARY, size=16), ft.Text("10 min", size=12, color=TEXT_DARK)], spacing=5),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Divider(height=40, color="#DDD"),
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.PEOPLE, color=ACCENT_PRIMARY, size=16), ft.Text("Serves 5", size=12, color=TEXT_DARK)], spacing=5),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], expand=True),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    ),
                    
                    # Macro indicators
                    ft.Container(
                        content=ft.Row([
                            create_macro_indicator("Protein", 9, "#E8A0BF"),
                            create_macro_indicator("Carbs", 13, "#B8E0B8"),
                            create_macro_indicator("Fat", 78, "#F5A35C"),
                        ], spacing=15, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        padding=15,
                    ),
                    
                    # Tab navigation
                    ft.Container(
                        content=ft.Column([
                            tabs,
                            ft.Divider(height=1, color="#DDD"),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        "Transform your culinary ~ments into a savory masterpiece",
                                        size=13,
                                        color="#666666",
                                        max_lines=5
                                    ),
                                ]),
                                padding=15,
                            )
                        ], spacing=0),
                        padding=0,
                    ),
                    
                    # Action buttons bar
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.FAVORITE_BORDER, size=24, color="#999"),
                                width=40,
                                height=40,
                                border_radius=20,
                                border=ft.border.all(1, "#DDD"),
                                alignment=ft.alignment.center
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.BOOKMARK_BORDER, size=24, color="#999"),
                                width=40,
                                height=40,
                                border_radius=20,
                                border=ft.border.all(1, "#DDD"),
                                alignment=ft.alignment.center
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.SHARE, size=24, color="#999"),
                                width=40,
                                height=40,
                                border_radius=20,
                                border=ft.border.all(1, "#DDD"),
                                alignment=ft.alignment.center
                            ),
                            ft.Row([], expand=True),
                            ft.Container(
                                content=ft.Icon(ft.Icons.ADD, size=28, color="white"),
                                width=50,
                                height=50,
                                border_radius=25,
                                bgcolor="#FF6B9D",
                                alignment=ft.alignment.center
                            ),
                        ], spacing=10),
                        padding=15,
                        margin=ft.margin.symmetric(horizontal=10, vertical=15),
                    ),
                    
                    # Add to cart button
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="Add to Cart",
                            width=300,
                            bgcolor=ACCENT_DARK,
                            color=TEXT_LIGHT,
                            height=50,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                        ),
                        alignment=ft.alignment.center,
                        padding=15,
                    ),
                    
                ], expand=True, spacing=0),
            ],
            expand=True,
            spacing=0
        ),
        expand=True,
        padding=0,
        bgcolor=FIELD_BG
    )


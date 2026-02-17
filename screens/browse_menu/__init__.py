"""Browse menu main screen"""
import flet as ft
import threading
from utils import TEXT_LIGHT, FIELD_BG, ACCENT_PRIMARY, ACCENT_DARK
from .handlers import create_add_to_cart_handler
from .ui import create_category_chips, create_search_field, create_pagination_controls, create_feature_carousel
from .pagination import create_menu_loader


def browse_menu_screen(page: ft.Page, current_user: dict, cart: list, goto_cart, goto_profile, goto_history, goto_logout):
    """Main browse menu screen"""
    # Thread lock for UI updates
    ui_update_lock = threading.Lock()
    
    # Pagination state
    current_page = {"page": 1}
    total_pages = {"count": 1}
    
    # Selected category state
    selected_category = {"value": "All"}
    
    # Menu list container - GridView like admin dashboard
    menu_list = ft.GridView(
        expand=True,
        max_extent=360,
        child_aspect_ratio=1.2,
        spacing=12,
        run_spacing=12,
        padding=10,
    )
    
    # Page info text
    page_info_text = ft.Text("", size=13, color="#000000", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_500)
    
    # Create handlers
    add_to_cart = create_add_to_cart_handler(page, cart, ui_update_lock)
    
    # Create menu loader
    load_menu = create_menu_loader(page, cart, current_user, menu_list, ui_update_lock, current_page, total_pages, selected_category, page_info_text, add_to_cart)
    
    # Create UI components
    search_field = create_search_field(load_menu, selected_category)
    category_chips = create_category_chips(selected_category, load_menu, page, ui_update_lock)
    pagination_controls = create_pagination_controls(current_page, total_pages, selected_category, search_field, load_menu, page_info_text)
    
    # Load initial menu
    load_menu()

    return ft.Container(
        content=ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Text("Menu", size=20, weight=ft.FontWeight.BOLD, color="#EBE1D1", expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.SHOPPING_CART, icon_color="#EBE1D1", on_click=goto_cart),
                            ft.IconButton(icon=ft.Icons.HISTORY, icon_color="#EBE1D1", on_click=goto_history),
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color="#EBE1D1", on_click=goto_profile),
                            ft.IconButton(icon=ft.Icons.LOGOUT, icon_color="#EBE1D1", on_click=goto_logout)
                        ], tight=True)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ACCENT_PRIMARY,
                    padding=15,
                    border_radius=10
                ),

                # Feature carousel
                ft.Container(
                    content=create_feature_carousel(page),
                    padding=ft.padding.symmetric(horizontal=10, vertical=10)
                ),

                # Search
                search_field,
                
                # Categories
                ft.Container(content=category_chips, padding=ft.padding.symmetric(horizontal=10, vertical=5)),
                
                # Menu items
                menu_list,
                
                # Pagination
                pagination_controls
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True,
        padding=10,
        bgcolor=FIELD_BG
    )

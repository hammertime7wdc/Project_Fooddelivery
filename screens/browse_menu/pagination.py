"""Pagination and menu loading logic"""
import flet as ft
import threading
from core.database import get_menu_items_page, get_user_favorites
from utils import TEXT_DARK, FIELD_BG, ACCENT_PRIMARY
from .ui import create_menu_item_card


def create_menu_loader(page, cart, current_user, menu_list, ui_update_lock, current_page, total_pages, selected_category, page_info_text, add_to_cart):
    """Create menu loading function"""
    user_id = current_user["user"]["id"]
    favorites = set(get_user_favorites(user_id))
    
    def load_menu(category="All", search="", reset_page=True):
        items_per_page = 10
        
        with ui_update_lock:
            if reset_page:
                current_page["page"] = 1
                
            menu_list.controls.clear()

            try:
                # Handle Favorites category
                if category == "❤️ Favorites":
                    if not favorites:
                        menu_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=80, color="grey"),
                                    ft.Text("No favorites yet", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                    ft.Text("Add items to your favorites", size=14, color="grey"),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                                padding=50,
                                alignment=ft.alignment.center
                            )
                        )
                        page.update()
                        return
                    
                    # Get all items and filter by favorites
                    all_items = []
                    for fav_id in favorites:
                        for item in get_menu_items_page(limit=1000, offset=0).get("items", []):
                            if item["id"] == fav_id:
                                all_items.append(item)
                    
                    items = all_items[((current_page["page"]-1)*items_per_page):((current_page["page"])*items_per_page)]
                    total = len(all_items)
                    total_pages["count"] = max(1, (total + items_per_page - 1) // items_per_page)
                else:
                    offset = (current_page["page"] - 1) * items_per_page
                    result = get_menu_items_page(category=category, search=search, limit=items_per_page, offset=offset)
                    items = result.get("items", [])
                    total = result.get("total", 0)
                    
                    # Calculate total pages
                    total_pages["count"] = max(1, (total + items_per_page - 1) // items_per_page)
                
                # Ensure current page is within bounds
                if current_page["page"] > total_pages["count"]:
                    current_page["page"] = total_pages["count"]
                    offset = (current_page["page"] - 1) * items_per_page
                    result = get_menu_items_page(category=category, search=search, limit=items_per_page, offset=offset)
                    items = result.get("items", [])
                    total = result.get("total", 0)
                
                # Update page info
                page_info_text.value = f"{current_page['page']} / {total_pages['count']}"

                # Empty state when no items found
                if not items:
                    menu_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey"),
                                ft.Text("No items found", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Text("Try adjusting your search or filter", size=14, color="grey"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                            padding=50,
                            alignment=ft.alignment.center
                        )
                    )
                    page.update()
                    return

                for item in items:
                    card = create_menu_item_card(item, page, cart, user_id, favorites, ui_update_lock, add_to_cart)
                    menu_list.controls.append(card)
                
                # Update once after all items added
                page.update()
                
            except Exception as e:
                print(f"Error loading menu: {e}")
                menu_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=80, color="#F44336"),
                            ft.Text("Error loading menu", size=20, weight=ft.FontWeight.BOLD, color="#F44336"),
                            ft.Text(str(e), size=12, color="grey"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        padding=50,
                        alignment=ft.alignment.center
                    )
                )
                page.update()
    
    return load_menu


def create_pan_handler(current_page, total_pages, selected_category, search_field, load_menu_callback):
    """Create swipe gesture handler for pagination"""
    swipe_start_x = {"value": 0}
    min_swipe_distance = 50  # Minimum pixels for swipe detection
    
    def on_pan(e):
        """Handle swipe gestures for pagination"""
        if e.state == "start":
            swipe_start_x["value"] = e.global_x
        elif e.state == "end":
            swipe_distance = e.global_x - swipe_start_x["value"]
            
            # Swipe right (previous page)
            if swipe_distance > min_swipe_distance and current_page["page"] > 1:
                current_page["page"] -= 1
                load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)
            
            # Swipe left (next page)
            elif swipe_distance < -min_swipe_distance and current_page["page"] < total_pages["count"]:
                current_page["page"] += 1
                load_menu_callback(category=selected_category["value"], search=search_field.value, reset_page=False)
    
    return on_pan

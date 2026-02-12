"""Image loading utilities for menu items"""
import flet as ft

# Image cache to avoid reloading
image_cache = {}


def load_image_from_binary(item):
    """Load image from file path - for fast binary transmission"""
    try:
        item_id = item.get("id")
        
        # Check cache first
        if item_id in image_cache:
            return image_cache[item_id]
        
        # Load from file path stored in database
        if item.get("image_type") == "path" and item.get("image"):
            # Path is relative: "uuid.jpg" -> full path: "assets/menu/uuid.jpg"
            img_path = f"assets/menu/{item['image']}"
            img = ft.Image(
                src=img_path,
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
            image_cache[item_id] = img
            return img
        elif item.get("image_type") == "base64" and item.get("image"):
            # Fallback for old base64 data
            img = ft.Image(
                src_base64=item["image"],
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
            image_cache[item_id] = img
            return img
        
        return None
    except Exception as e:
        print(f"Error loading image for item {item.get('id')}: {e}")
        return None

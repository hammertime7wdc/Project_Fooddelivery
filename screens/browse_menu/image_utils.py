"""Image loading utilities for menu items"""
import os
from pathlib import Path
import flet as ft

# Image cache to avoid reloading
# Map item_id -> {"key": (image_type, image_value), "img": Image}
image_cache = {}


def load_image_from_binary(item):
    """Load image from file path - for fast binary transmission"""
    try:
        item_id = item.get("id")
        
        # Check cache first (invalidate when image changes)
        cache_key = (item.get("image_type"), item.get("image"))
        cached = image_cache.get(item_id)
        if cached and cached.get("key") == cache_key:
            return cached.get("img")
        
        # Load from file path stored in database
        if item.get("image_type") == "path" and item.get("image"):
            # Path is relative: "uuid.jpg" -> full path: "assets/menu/uuid.jpg"
            root_dir = Path(__file__).resolve().parent.parent.parent
            img_path = root_dir / "assets" / "menu" / item["image"]
            img_path_str = str(img_path)
            try:
                mtime = os.path.getmtime(img_path_str)
            except Exception:
                mtime = None
            if mtime is not None:
                cache_key = (item.get("image_type"), item.get("image"), mtime)
            img = ft.Image(
                src=img_path_str,
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
            image_cache[item_id] = {"key": cache_key, "img": img}
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
            image_cache[item_id] = {"key": cache_key, "img": img}
            return img
        
        return None
    except Exception as e:
        print(f"Error loading image for item {item.get('id')}: {e}")
        return None

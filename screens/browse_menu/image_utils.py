"""Image loading utilities for menu items"""
import os
from pathlib import Path
import flet as ft

def load_image_from_binary(item):
    """Load image from file path - for fast binary transmission"""
    try:
        # Load from URL stored in database
        if item.get("image_type") == "url" and item.get("image"):
            return ft.Image(
                src=item["image"],
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )

        # Load from file path stored in database
        if item.get("image_type") == "path" and item.get("image"):
            # Path is relative: "uuid.jpg" -> full path: "assets/menu/uuid.jpg"
            image_name = Path(str(item["image"])).name
            root_dir = Path(__file__).resolve().parent.parent.parent
            img_path = root_dir / "assets" / "menu" / image_name
            img_path_str = str(img_path)
            return ft.Image(
                src=img_path_str,
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
        elif item.get("image_type") == "base64" and item.get("image"):
            # Fallback for old base64 data
            return ft.Image(
                src_base64=item["image"],
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=10
            )
        
        return None
    except Exception as e:
        print(f"Error loading image for item {item.get('id')}: {e}")
        return None

import base64
from pathlib import Path

def get_base64_image(image_path):
    """Convert image file to base64 string for web mode compatibility"""
    try:
        path = Path(image_path)
        if not path.is_absolute():
            root_dir = Path(__file__).resolve().parent.parent
            path = root_dir / path
        if path.exists():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
    return None

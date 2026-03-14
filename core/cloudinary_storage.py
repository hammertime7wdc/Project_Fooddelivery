import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv


load_dotenv()


_is_configured = False


def _ensure_configured():
    global _is_configured
    if _is_configured:
        return True

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not (cloud_name and api_key and api_secret):
        return False

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _is_configured = True
    return True


def upload_menu_image(file_path: str):
    """Upload a menu image to Cloudinary.

    Returns:
        tuple[bool, str, str]: (success, secure_url_or_empty, error_message_or_empty)
    """
    if not _ensure_configured():
        return False, "", "Cloudinary is not configured"

    folder = os.getenv("CLOUDINARY_FOLDER", "food_delivery/menu")

    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type="image",
            overwrite=False,
            use_filename=False,
            unique_filename=True,
        )
        secure_url = result.get("secure_url", "")
        if not secure_url:
            return False, "", "Cloudinary upload did not return a secure URL"
        return True, secure_url, ""
    except Exception as ex:
        return False, "", f"Cloudinary upload failed: {str(ex)}"


def upload_profile_image(file_path: str):
    """Upload a profile image to Cloudinary.

    Returns:
        tuple[bool, str, str]: (success, secure_url_or_empty, error_message_or_empty)
    """
    if not _ensure_configured():
        return False, "", "Cloudinary is not configured"

    folder = os.getenv("CLOUDINARY_PROFILE_FOLDER", "food_delivery/profiles")

    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type="image",
            overwrite=False,
            use_filename=False,
            unique_filename=True,
        )
        secure_url = result.get("secure_url", "")
        if not secure_url:
            return False, "", "Cloudinary upload did not return a secure URL"
        return True, secure_url, ""
    except Exception as ex:
        return False, "", f"Cloudinary upload failed: {str(ex)}"

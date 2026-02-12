"""Profile validation functions"""
from core.auth import validate_email, validate_password, validate_full_name


def validate_name_field(name_field, name_error, page):
    """Validate full name field"""
    if not name_field.value or name_field.value.strip() == "":
        name_error.visible = False
        name_field.border_color = "#D0D0D0"  # FIELD_BORDER
    else:
        is_valid, error_msg = validate_full_name(name_field.value)
        if not is_valid:
            name_error.value = error_msg
            name_error.visible = True
            name_field.border_color = "red"
        else:
            name_error.visible = False
            name_field.border_color = "green"
    page.update()


def validate_email_field(email_field, email_error, page):
    """Validate email field"""
    if not email_field.value or email_field.value.strip() == "":
        email_error.visible = False
        email_field.border_color = "#D0D0D0"  # FIELD_BORDER
    else:
        is_valid, error_msg = validate_email(email_field.value)
        if not is_valid:
            email_error.value = error_msg
            email_error.visible = True
            email_field.border_color = "red"
        else:
            email_error.visible = False
            email_field.border_color = "green"
    page.update()


def validate_password_field(password, new_password, password_error, page):
    """Validate new password field"""
    if not password:
        password_error.visible = False
        new_password.border_color = "#D0D0D0"  # FIELD_BORDER
    else:
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            password_error.value = error_msg
            password_error.visible = True
            new_password.border_color = "red"
        else:
            password_error.visible = False
            new_password.border_color = "green"
    page.update()

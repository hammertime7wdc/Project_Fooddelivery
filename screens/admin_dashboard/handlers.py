from .user_handlers import create_user_handlers
from .order_handlers import create_order_handlers


def create_admin_handlers(
    page,
    current_user,
    users_list,
    orders_list,
    new_email,
    new_password,
    new_name,
    new_role,
    email_error,
    password_error,
    name_error,
    password_strength_text,
    password_strength_bar,
    user_search_field,
    role_filter_buttons,
    status_filter_buttons,
    role_filter_selected,
    status_filter_selected,
    order_filter_buttons,
    order_search_field,
    date_range_dropdown,
    form_container,
    user_details_panel,
    user_details_content,
    order_details_panel,
    order_details_content,
    on_user_status_change=None,
):
    user_handlers = create_user_handlers(
        page=page,
        current_user=current_user,
        users_list=users_list,
        new_email=new_email,
        new_password=new_password,
        new_name=new_name,
        new_role=new_role,
        email_error=email_error,
        password_error=password_error,
        name_error=name_error,
        password_strength_text=password_strength_text,
        password_strength_bar=password_strength_bar,
        user_search_field=user_search_field,
        role_filter_buttons=role_filter_buttons,
        status_filter_buttons=status_filter_buttons,
        role_filter_selected=role_filter_selected,
        status_filter_selected=status_filter_selected,
        form_container=form_container,
        user_details_panel=user_details_panel,
        user_details_content=user_details_content,
        on_user_status_change=on_user_status_change,
    )

    order_handlers = create_order_handlers(
        page=page,
        current_user=current_user,
        orders_list=orders_list,
        order_filter_buttons=order_filter_buttons,
        order_search_field=order_search_field,
        date_range_dropdown=date_range_dropdown,
        order_details_panel=order_details_panel,
        order_details_content=order_details_content,
    )

    return {**user_handlers, **order_handlers}


__all__ = ["create_admin_handlers"]

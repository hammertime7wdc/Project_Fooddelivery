import flet as ft
from datetime import datetime
from core.auth import (
    get_all_users,
    create_user_by_admin,
    delete_user,
    disable_user,
    enable_user,
    validate_email,
    validate_password,
    validate_full_name,
    get_password_strength,
)
from utils import (
    show_snackbar,
    ACCENT_DARK,
    FIELD_BG,
    TEXT_DARK,
    FIELD_BORDER,
    ACCENT_PRIMARY,
    CREAM,
)


def create_user_handlers(
    page,
    current_user,
    users_list,
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
    form_container,
    user_details_panel,
    user_details_content,
):
    search_query = {"value": ""}

    def validate_email_field(e=None):
        if not new_email.value or new_email.value.strip() == "":
            email_error.visible = False
            new_email.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_email(new_email.value)
            if not is_valid:
                email_error.value = error_msg
                email_error.visible = True
                new_email.border_color = "red"
            else:
                email_error.visible = False
                new_email.border_color = "green"
        page.update()

    def validate_name_field(e=None):
        if not new_name.value or new_name.value.strip() == "":
            name_error.visible = False
            new_name.border_color = FIELD_BORDER
        else:
            is_valid, error_msg = validate_full_name(new_name.value)
            if not is_valid:
                name_error.value = error_msg
                name_error.visible = True
                new_name.border_color = "red"
            else:
                name_error.visible = False
                new_name.border_color = "green"
        page.update()

    def update_password_strength(e=None):
        password = new_password.value or ""
        if not password:
            password_strength_text.value = ""
            password_strength_bar.value = 0
            password_strength_bar.color = "grey"
            new_password.border_color = FIELD_BORDER
            password_error.visible = False
            page.update()
            return

        strength, score = get_password_strength(password)
        is_valid, error_msg = validate_password(password)

        password_strength_text.value = f"Password Strength: {strength.title()} ({score}%)"
        password_strength_bar.value = score / 100

        if strength == "weak":
            password_strength_bar.color = "red"
            password_strength_text.color = "red"
        elif strength == "medium":
            password_strength_bar.color = "orange"
            password_strength_text.color = "orange"
        elif strength == "strong":
            password_strength_bar.color = "yellow"
            password_strength_text.color = "yellow"
        else:
            password_strength_bar.color = "green"
            password_strength_text.color = "green"

        if is_valid:
            new_password.border_color = "green"
            password_error.visible = False
        else:
            new_password.border_color = "red"
            password_error.value = error_msg
            password_error.visible = True

        password_strength_text.visible = True
        page.update()

    def show_form(e):
        new_email.value = ""
        new_name.value = ""
        new_password.value = ""
        new_role.value = "customer"
        email_error.visible = False
        password_error.visible = False
        name_error.visible = False
        password_strength_text.value = ""
        password_strength_bar.value = 0
        new_email.border_color = FIELD_BORDER
        new_password.border_color = FIELD_BORDER
        new_name.border_color = FIELD_BORDER

        form_container.visible = True
        page.update()

    def hide_form(e):
        form_container.visible = False
        page.update()

    def update_role_filter_chips(selected_role):
        for role, button in role_filter_buttons.items():
            is_selected = role == selected_role
            button.content.color = "#FFFFFF" if is_selected else "#000000"
            button.bgcolor = ACCENT_DARK if is_selected else "#E0E0E0"
        page.update()

    def update_status_filter_chips(selected_status):
        for status, button in status_filter_buttons.items():
            is_selected = status == selected_status
            button.content.color = "#FFFFFF" if is_selected else "#000000"
            button.bgcolor = ACCENT_DARK if is_selected else "#E0E0E0"
        page.update()

    def filter_users_by_role(role):
        role_filter_selected["value"] = role
        update_role_filter_chips(role)
        load_users()

    def filter_users_by_status(status):
        status_filter_selected["value"] = status
        update_status_filter_chips(status)
        load_users()

    def on_user_search_change(e):
        search_query["value"] = e.control.value.lower().strip()
        load_users()

    def handle_enable_user(user_id):
        enable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, "User enabled successfully!")
        user_details_panel.visible = False
        load_users()
        page.update()

    def handle_disable_user(user_id):
        disable_user(user_id, current_user["user"]["id"])
        show_snackbar(page, "User disabled successfully!")
        user_details_panel.visible = False
        load_users()
        page.update()

    def handle_delete_user(user_id):
        success, msg = delete_user(user_id, current_user["user"]["id"])
        show_snackbar(page, msg)
        user_details_panel.visible = False
        if success:
            load_users()
        page.update()

    def hide_user_details(e):
        user_details_panel.visible = False
        page.update()

    def open_user_details(user):
        user_details_content.controls.clear()

        created_at = "N/A"
        if user.get("created_at"):
            try:
                created_dt = datetime.fromisoformat(user["created_at"])
                created_at = created_dt.strftime("%b %d, %Y at %I:%M %p")
            except Exception:
                created_at = user.get("created_at", "N/A")

        last_login = "Never"
        if user.get("last_login"):
            try:
                login_dt = datetime.fromisoformat(user["last_login"])
                last_login = login_dt.strftime("%b %d, %Y at %I:%M %p")
            except Exception:
                last_login = user.get("last_login", "Never")

        is_active = user.get("is_active", 0)
        status_text = "ACTIVE" if is_active else "DISABLED"
        status_color = "#FFFFFF" if is_active else "#666666"
        status_bg = "#4CAF50" if is_active else "#E0E0E0"

        user_details_content.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Account Information", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY),
                    ft.Divider(height=1, color=FIELD_BORDER),
                    ft.Row([
                        ft.Text("Email:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(user.get("email", "N/A"), size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Name:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(user.get("full_name", "N/A"), size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Role:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Container(
                            content=ft.Text(
                                user.get("role", "Unknown").upper(),
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=CREAM,
                            ),
                            bgcolor=ACCENT_PRIMARY,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=10,
                        ),
                    ]),
                    ft.Row([
                        ft.Text("Status:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Container(
                            content=ft.Text(
                                status_text,
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=status_color,
                            ),
                            bgcolor=status_bg,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=10,
                        ),
                    ]),
                    ft.Row([
                        ft.Text("Created:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(created_at, size=11, color=TEXT_DARK),
                    ]),
                    ft.Row([
                        ft.Text("Last Login:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_DARK, width=100),
                        ft.Text(last_login, size=11, color=TEXT_DARK),
                    ]),
                ], spacing=8),
                padding=12,
                bgcolor=FIELD_BG,
                border_radius=8,
            )
        )

        user_details_content.controls.append(ft.Container(height=10))
        user_details_content.controls.append(
            ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD, color=ACCENT_PRIMARY)
        )
        user_details_content.controls.append(ft.Divider(height=1, color=FIELD_BORDER))

        action_buttons = []
        if not is_active:
            action_buttons.append(
                ft.ElevatedButton(
                    "Activate",
                    bgcolor=ACCENT_PRIMARY,
                    color=CREAM,
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=lambda e, uid=user.get("id"): handle_enable_user(uid),
                )
            )

        if is_active:
            action_buttons.append(
                ft.ElevatedButton(
                    "Deactivate",
                    bgcolor="#FFA726",
                    color=CREAM,
                    icon=ft.Icons.BLOCK,
                    on_click=lambda e, uid=user.get("id"): handle_disable_user(uid),
                )
            )

        action_buttons.append(
            ft.ElevatedButton(
                "Delete",
                bgcolor="#EF5350",
                color=CREAM,
                icon=ft.Icons.DELETE,
                on_click=lambda e, uid=user.get("id"): handle_delete_user(uid),
            )
        )

        user_details_content.controls.append(
            ft.Row(action_buttons, spacing=8, wrap=True)
        )

        user_details_panel.visible = True
        page.update()

    def load_users():
        temp_controls = []
        all_users = get_all_users()

        filtered_users = all_users

        if role_filter_selected["value"] != "all":
            filtered_users = [u for u in filtered_users if u["role"] == role_filter_selected["value"]]

        if status_filter_selected["value"] != "all":
            if status_filter_selected["value"] == "active":
                filtered_users = [u for u in filtered_users if u["is_active"]]
            elif status_filter_selected["value"] == "disabled":
                filtered_users = [u for u in filtered_users if not u["is_active"]]
            elif status_filter_selected["value"] == "locked":
                locked_users = []
                for u in filtered_users:
                    if u.get("locked_until"):
                        try:
                            locked_until_dt = datetime.fromisoformat(u["locked_until"])
                            if datetime.now() < locked_until_dt:
                                locked_users.append(u)
                        except Exception:
                            pass
                filtered_users = locked_users

        if search_query["value"]:
            filtered_users = [
                u
                for u in filtered_users
                if search_query["value"] in u["full_name"].lower()
                or search_query["value"] in u["email"].lower()
            ]

        count_text = ft.Text(f"{len(filtered_users)} user(s)", size=13, color=TEXT_DARK, weight=ft.FontWeight.BOLD)
        temp_controls.append(count_text)

        if not filtered_users:
            temp_controls.append(ft.Text("No users found", size=12, color="#666666", italic=True))
            users_list.controls = temp_controls
            page.update()
            return

        for user in filtered_users:
            status_badge_text = "ACTIVE" if user["is_active"] else "DISABLED"
            status_badge_color = "#4CAF50" if user["is_active"] else "#FFC107"
            status_badge_text_color = "#FFFFFF" if user["is_active"] else "#000000"

            def on_card_hover(e, card_ref=None):
                if card_ref is None:
                    return
                if e.data == "true":
                    card_ref.scale = 1.02
                    card_ref.shadow = ft.BoxShadow(
                        spread_radius=2,
                        blur_radius=8,
                        color="#00000033",
                    )
                else:
                    card_ref.scale = 1
                    card_ref.shadow = None
                page.update()

            def handle_arrow_click(e, u=user):
                open_user_details(u)

            arrow_btn = ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                icon_size=18,
                icon_color=ACCENT_PRIMARY,
                tooltip="View details",
                on_click=handle_arrow_click,
            )

            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            user.get("full_name", "Unknown"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_DARK,
                                        ),
                                        ft.Text(user.get("email", "N/A"), size=11, color="#666666"),
                                        ft.Text(
                                            user.get("role", "unknown").upper(),
                                            size=10,
                                            color=ACCENT_PRIMARY,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        status_badge_text,
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                        color=status_badge_text_color,
                                    ),
                                    bgcolor=status_badge_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=12,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=1, color="#E5E5E5"),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color="#999999"),
                                ft.Text(
                                    f"Created: {datetime.fromisoformat(user['created_at']).strftime('%b %d, %Y')}",
                                    size=10,
                                    color="#666666",
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LOGIN, size=12, color="#999999"),
                                ft.Text(
                                    f"Last Login: {datetime.fromisoformat(user['last_login']).strftime('%b %d, %Y') if user.get('last_login') else 'Never'}",
                                    size=10,
                                    color="#666666",
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.Container(expand=True),
                                arrow_btn,
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=8,
                ),
                padding=14,
                border=ft.border.all(1, "#E5E5E5"),
                border_radius=12,
                bgcolor=CREAM,
                height=200,
                ink=False,
            )

            card.on_hover = lambda e, card_ref=card: on_card_hover(e, card_ref)
            temp_controls.append(card)

        users_list.controls = temp_controls
        page.update()

    def add_user(e):
        has_error = False

        email_valid, email_msg = validate_email(new_email.value or "")
        if not email_valid:
            email_error.value = email_msg
            email_error.visible = True
            new_email.border_color = "red"
            has_error = True
        else:
            email_error.visible = False

        password_valid, password_msg = validate_password(new_password.value or "")
        if not password_valid:
            password_error.value = password_msg
            password_error.visible = True
            new_password.border_color = "red"
            has_error = True
        else:
            password_error.visible = False

        name_valid, name_msg = validate_full_name(new_name.value or "")
        if not name_valid:
            name_error.value = name_msg
            name_error.visible = True
            new_name.border_color = "red"
            has_error = True
        else:
            name_error.visible = False

        if has_error:
            page.update()
            return

        success, msg = create_user_by_admin(
            new_email.value,
            new_password.value,
            new_name.value,
            new_role.value,
            current_user["user"]["id"],
        )
        show_snackbar(page, msg)
        if success:
            new_email.value = ""
            new_password.value = ""
            new_name.value = ""
            new_role.value = "customer"
            new_email.border_color = FIELD_BORDER
            new_password.border_color = FIELD_BORDER
            new_name.border_color = FIELD_BORDER
            email_error.visible = False
            password_error.visible = False
            name_error.visible = False
            password_strength_text.value = ""
            password_strength_bar.value = 0
            page.update()
            load_users()

    return {
        "validate_email_field": validate_email_field,
        "validate_name_field": validate_name_field,
        "update_password_strength": update_password_strength,
        "show_form": show_form,
        "hide_form": hide_form,
        "hide_user_details": hide_user_details,
        "filter_users_by_role": filter_users_by_role,
        "filter_users_by_status": filter_users_by_status,
        "on_search_change": on_user_search_change,
        "on_user_search_change": on_user_search_change,
        "load_users": load_users,
        "add_user": add_user,
    }

"""Profile screen UI components"""
import flet as ft
from utils import create_profile_pic_widget, TEXT_DARK, FIELD_BG, FIELD_BORDER, ACCENT_PRIMARY, ACCENT_DARK, CREAM, ORANGE
from core.auth import get_user_by_id
from utils import show_snackbar
from .handlers import (
    handle_pic_pick,
    save_profile,
    update_password_strength,
    save_profile_picture,
    send_profile_reset_code_handler,
    reset_password_with_profile_code_handler,
)
from .validation import validate_name_field


def profile_screen(page: ft.Page, current_user: dict, cart: list, back_callback):
    """Create profile settings screen with tabbed interface"""
    user = get_user_by_id(current_user["user"]["id"])
    if not user:
        show_snackbar(page, "User not found")
        back_callback(None)
        return ft.Container()
    
    # Mobile-friendly width with max width limit
    container_width = min(page.width - 30, 430)
    input_width = container_width - 44

    card_shadow = ft.BoxShadow(
        spread_radius=1,
        blur_radius=16,
        color="black12",
        offset=ft.Offset(0, 6)
    )

    primary_button_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10)
    )

    subtle_button_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10),
        side=ft.BorderSide(1, FIELD_BORDER)
    )
    
    # ==================== FORM FIELDS ====================
    name_field = ft.TextField(
        label="Full Name", 
        value=user["full_name"], 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        max_length=100,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: validate_name_field(name_field, name_error, page)
    )
    name_error = ft.Text("", size=11, color="red", visible=False)
    
    email_field = ft.TextField(
        label="Email Address", 
        value=user["email"], 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=FIELD_BORDER,
        border_radius=10,
        max_length=254,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        read_only=True,
        helper_text="Email cannot be changed here."
    )
    
    address_field = ft.TextField(
        label="Address", 
        value=user["address"] or "", 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        hint_text="Street, City, ZIP"
    )
    
    contact_field = ft.TextField(
        label="Contact Number", 
        value=user["contact"] or "", 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        hint_text="e.g. +63 912 345 6789"
    )

    current_password = ft.TextField(
        label="Current Password",
        password=True,
        can_reveal_password=True,
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        max_length=128,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK)
    )

    password_strength_bar = ft.ProgressBar(width=input_width, value=0, color="grey", bgcolor="white", visible=False)
    password_strength_text = ft.Text("", size=12, color="grey", visible=False)
    
    new_password = ft.TextField(
        label="New Password", 
        password=True, 
        can_reveal_password=True, 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        max_length=128,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        on_change=lambda e: update_password_strength(e.control.value, password_strength_bar, password_strength_text, page, new_password, password_error)
    )
    
    password_error = ft.Text("", size=11, color="red", visible=False)
    
    confirm_password = ft.TextField(
        label="Confirm New Password", 
        password=True, 
        can_reveal_password=True, 
        width=input_width,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        max_length=128,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK)
    )

    reset_code_field = ft.TextField(
        label="Verification Code",
        hint_text="Enter 6-digit code",
        width=input_width,
        max_length=6,
        text_align=ft.TextAlign.CENTER,
        bgcolor="white",
        color=TEXT_DARK,
        border_color=FIELD_BORDER,
        focused_border_color=ACCENT_PRIMARY,
        border_radius=10,
        text_style=ft.TextStyle(color=TEXT_DARK),
        label_style=ft.TextStyle(color=TEXT_DARK),
        visible=False,
    )

    reset_code_info = ft.Text("", size=12, color=ACCENT_DARK, visible=False)

    verify_code_button = ft.ElevatedButton(
        "Verify Code & Update Password",
        bgcolor=ORANGE,
        color=CREAM,
        width=input_width,
        style=primary_button_style,
        visible=False,
        on_click=lambda e: reset_password_with_profile_code_handler(
            page,
            current_user,
            current_password,
            reset_code_field,
            new_password,
            confirm_password,
            password_strength_bar,
            password_strength_text,
            reset_code_info,
            verify_code_button,
            resend_code_button,
        )
    )

    resend_code_button = ft.TextButton(
        "Resend Code",
        visible=False,
        style=ft.ButtonStyle(color=ACCENT_DARK),
        on_click=lambda e: send_profile_reset_code_handler(
            page,
            current_user,
            current_password,
            new_password,
            confirm_password,
            reset_code_field,
            reset_code_info,
            verify_code_button,
            resend_code_button,
        )
    )

    # ==================== PROFILE PICTURE ====================
    # Mobile-friendly profile picture size
    pic_size = 120
    
    profile_pic_preview = ft.Container(
        content=create_profile_pic_widget(user, pic_size, pic_size),
        width=pic_size,
        height=pic_size,
        border=ft.border.all(3, FIELD_BORDER),
        border_radius=ft.border_radius.all(pic_size // 2),
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black12", offset=ft.Offset(0, 3))
    )

    uploaded_pic = {"data": user.get("profile_picture"), "type": user.get("pic_type") or "emoji"}

    file_picker = ft.FilePicker(on_result=lambda e: handle_pic_pick(e, current_user, profile_pic_preview, uploaded_pic, page))
    page.overlay.append(file_picker)

    # ==================== SECTIONS ====================
    # Profile Picture Section
    profile_pic_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Profile Photo", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Text("Upload or change your display picture", size=12, color="#666666"),
                ft.Container(height=4),
                ft.Container(
                    content=profile_pic_preview,
                    padding=10,
                    border_radius=75
                ),
                ft.ElevatedButton(
                    "Upload New Photo",
                    icon=ft.Icons.UPLOAD_FILE,
                    bgcolor=ACCENT_DARK,
                    color=CREAM,
                    width=input_width,
                    style=primary_button_style,
                    on_click=lambda _: file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "gif"],
                        dialog_title="Select Profile Picture"
                    )
                ),
                ft.ElevatedButton(
                    "Save Photo",
                    bgcolor=ORANGE,
                    color="#ffffff",
                    width=input_width,
                    style=primary_button_style,
                    on_click=lambda e: save_profile_picture(page, current_user, uploaded_pic)
                ),
                ft.Text("We support PNGs, JPEGs and GIFs under 2MB", size=10, color="#888888", italic=True)
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=26,
        bgcolor="white",
        border_radius=18,
        border=ft.border.all(1, FIELD_BORDER),
        width=container_width,
        shadow=card_shadow
    )

    # Personal Information Section
    personal_info_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Personal Information", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Text("Keep your profile details up to date", size=12, color="#666666"),
                ft.Divider(color=FIELD_BORDER, height=15),
                name_field,
                name_error,
                email_field,
                address_field,
                contact_field,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Save Profile",
                    bgcolor=ACCENT_DARK,
                    color=CREAM,
                    width=input_width,
                    style=primary_button_style,
                    on_click=lambda e: save_profile(page, current_user, name_field, email_field, 
                                                    address_field, contact_field, name_error, 
                                                    uploaded_pic, back_callback)
                )
            ],
            spacing=12
        ),
        padding=26,
        bgcolor="white",
        border_radius=18,
        border=ft.border.all(1, FIELD_BORDER),
        width=container_width,
        shadow=card_shadow
    )

    # Account Security Section
    account_security_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Account Security", size=18, weight=ft.FontWeight.BOLD, color=ACCENT_DARK),
                ft.Text("Reset your password securely with OTP sent to your email", size=12, color="#666666"),
                ft.Divider(color=FIELD_BORDER, height=15),

                ft.Container(
                    content=ft.Column([
                        ft.Text("Account Email", size=11, weight=ft.FontWeight.BOLD, color="#666666"),
                        ft.Text(user.get("email", ""), size=13, color=TEXT_DARK, weight=ft.FontWeight.W_600),
                    ], spacing=4),
                    bgcolor=FIELD_BG,
                    border_radius=10,
                    padding=12,
                    width=input_width,
                ),
                
                ft.Column([
                    ft.Text("Current Password", size=12, weight=ft.FontWeight.BOLD, color="#666666"),
                    current_password,
                    ft.Container(height=5),
                    ft.Text("New Password", size=12, weight=ft.FontWeight.BOLD, color="#666666"),
                    new_password,
                    password_error,
                    ft.Container(height=5),
                    password_strength_bar,
                    password_strength_text,
                    ft.Container(height=10),
                    ft.Text("Confirm Password", size=12, weight=ft.FontWeight.BOLD, color="#666666"),
                    confirm_password
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                ft.Container(height=10),
                ft.Text("Step 1: Request a verification code", size=11, color="#666666"),
                ft.ElevatedButton(
                    "Send Reset Code",
                    bgcolor=ORANGE,
                    color=CREAM,
                    width=input_width,
                    style=primary_button_style,
                    on_click=lambda e: send_profile_reset_code_handler(
                        page,
                        current_user,
                        current_password,
                        new_password,
                        confirm_password,
                        reset_code_field,
                        reset_code_info,
                        verify_code_button,
                        resend_code_button,
                    )
                ),
                ft.Container(height=4),
                ft.Text("Step 2: Enter code and set your new password", size=11, color="#666666"),
                reset_code_info,
                reset_code_field,
                ft.Container(height=4),
                verify_code_button,
                resend_code_button
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=26,
        bgcolor="white",
        border_radius=18,
        border=ft.border.all(1, FIELD_BORDER),
        width=container_width,
        shadow=card_shadow
    )

    # ==================== TAB MANAGEMENT ====================
    # Tab Contents
    profile_tab = ft.Column(
        [profile_pic_section],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO
    )

    personal_tab = ft.Column(
        [personal_info_section],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO
    )

    security_tab = ft.Column(
        [account_security_section],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.AUTO
    )

    tabs_dict = {
        "profile": profile_tab,
        "personal": personal_tab,
        "security": security_tab
    }
    
    current_tab = {"value": "profile"}
    
    # Tab underline indicators
    profile_underline = ft.Container(height=3, bgcolor=ORANGE)
    personal_underline = ft.Container(height=3, bgcolor="transparent")
    security_underline = ft.Container(height=3, bgcolor="transparent")
    
    # Tab content container
    tab_content = ft.Container(content=profile_tab, expand=True, alignment=ft.alignment.top_center)

    def switch_tab(tab_name):
        current_tab["value"] = tab_name
        tab_content.content = tabs_dict[tab_name]
        
        profile_underline.bgcolor = ORANGE if tab_name == "profile" else "transparent"
        personal_underline.bgcolor = ORANGE if tab_name == "personal" else "transparent"
        security_underline.bgcolor = ORANGE if tab_name == "security" else "transparent"
        
        page.update()

    # Mobile-friendly padding for tabs
    btn_padding_left = 4
    btn_padding_right = 4
    btn_padding_top = 8
    btn_padding_bottom = 8
    tab_spacing = 0
    
    # Tab buttons with better styling
    profile_btn = ft.TextButton(
        "Profile", 
        style=ft.ButtonStyle(
            color=TEXT_DARK,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.only(bottom=btn_padding_bottom, top=btn_padding_top, left=btn_padding_left, right=btn_padding_right)
        ), 
        on_click=lambda e: switch_tab("profile")
    )
    personal_btn = ft.TextButton(
        "Personal Info", 
        style=ft.ButtonStyle(
            color=TEXT_DARK,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.only(bottom=btn_padding_bottom, top=btn_padding_top, left=btn_padding_left, right=btn_padding_right)
        ), 
        on_click=lambda e: switch_tab("personal")
    )
    security_btn = ft.TextButton(
        "Security", 
        style=ft.ButtonStyle(
            color=TEXT_DARK,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.only(bottom=btn_padding_bottom, top=btn_padding_top, left=btn_padding_left, right=btn_padding_right)
        ), 
        on_click=lambda e: switch_tab("security")
    )

    # Tab header with improved styling
    # Create tab buttons with their underlines paired together
    profile_tab_btn = ft.Column(
        [
            profile_btn,
            profile_underline
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )
    personal_tab_btn = ft.Column(
        [
            personal_btn,
            personal_underline
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )
    security_tab_btn = ft.Column(
        [
            security_btn,
            security_underline
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )
    
    # Create the tab row with left alignment
    tabs_row = ft.Row(
        [profile_tab_btn, personal_tab_btn, security_tab_btn],
        spacing=tab_spacing,
        alignment=ft.MainAxisAlignment.START
    )
    
    # Mobile-friendly tab header padding
    tab_header_padding = ft.padding.only(
        left=8,
        right=8,
        top=8,
        bottom=6
    )
    
    tab_header = ft.Container(
        content=tabs_row,
        bgcolor="white",
        padding=tab_header_padding,
        border=ft.border.all(1, FIELD_BORDER),
        border_radius=ft.border_radius.all(14),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black12", offset=ft.Offset(0, 3)),
        alignment=ft.alignment.top_left
    )
    
    # Remove resize handler since tabs are always left-aligned now
    page.on_resize = None

    # Combined tab UI with proper alignment
    scrollable_content = ft.Container(
        content=ft.Column(
            [tab_header, tab_content],
            spacing=12,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            alignment=ft.MainAxisAlignment.START
        ),
        border_radius=20
    )

    # ==================== LAYOUT ====================
    # Base layout with improved spacing
    base_layout = ft.Column(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=CREAM,
                                on_click=back_callback,
                                icon_size=24,
                                tooltip="Back"
                            ),
                            ft.Text("My Profile", size=24, weight=ft.FontWeight.BOLD, color=CREAM, expand=True),
                        ], alignment=ft.MainAxisAlignment.START, spacing=4),
                        ft.Text(
                            "Manage your account details and security",
                            size=12,
                            color=CREAM
                        )
                    ],
                    spacing=2
                ),
                bgcolor=ORANGE,
                padding=ft.padding.only(left=14, right=18, top=14, bottom=18),
            ),
            
            ft.Container(
                content=scrollable_content,
                expand=True,
                padding=ft.padding.only(left=15, right=15, top=14, bottom=15),
                bgcolor=CREAM,
                alignment=ft.alignment.top_center
            )
        ],
        spacing=0,
        expand=True
    )

    layout = base_layout

    return ft.Container(
        content=layout,
        expand=True,
        bgcolor=CREAM,
        padding=0
    )

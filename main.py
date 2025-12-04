import sys
import os
import flet as ft

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_database
from utils import show_snackbar
from screens.login import login_screen
from screens.signup import signup_screen
from screens.reset_password import reset_password_screen
from screens.browse_menu import browse_menu_screen
from screens.cart import cart_screen
from screens.order_history import order_history_screen
from screens.order_confirmation import order_confirmation_screen
from screens.profile import profile_screen
from screens.owner_dashboard import owner_dashboard_screen
from screens.admin_dashboard import admin_dashboard_screen

def main(page: ft.Page):
    page.title = "Food Delivery App"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#6B0113"
    page.padding = 0
    page.window_width = 412
    page.window_height = 917

    init_database()

    # GLOBAL APP STATE
    current_user = {"user": None}
    cart = []

    # Navigation helper
    def navigate_to(screen_func, **kwargs):
        page.controls.clear()
        page.add(screen_func(page, current_user, cart, **kwargs))
        page.update()

    # Callbacks for navigation
    def goto_login(e=None):
        navigate_to(login_screen, goto_signup=goto_signup, goto_reset=goto_reset, goto_dashboard=goto_dashboard)

    def goto_signup(e=None):
        navigate_to(signup_screen, goto_login=goto_login)

    def goto_reset(e=None):
        navigate_to(reset_password_screen, goto_login=goto_login)

    def goto_browse_menu(e=None):
        navigate_to(browse_menu_screen, goto_cart=goto_cart, goto_profile=goto_profile_customer, goto_history=goto_order_history, goto_logout=goto_login)

    def goto_cart(e=None):
        navigate_to(cart_screen, goto_menu=goto_browse_menu, goto_confirmation=goto_confirmation)

    def goto_order_history(e=None):
        navigate_to(order_history_screen, goto_menu=goto_browse_menu)

    def goto_confirmation(e=None):
        navigate_to(order_confirmation_screen, goto_menu=goto_browse_menu)

    def goto_profile_customer(e=None):
        navigate_to(profile_screen, back_callback=goto_browse_menu)

    def goto_profile_owner(e=None):
        navigate_to(profile_screen, back_callback=goto_owner_dashboard)

    def goto_profile_admin(e=None):
        navigate_to(profile_screen, back_callback=goto_admin_dashboard)

    def goto_owner_dashboard(e=None):
        navigate_to(owner_dashboard_screen, goto_profile=goto_profile_owner, goto_logout=goto_login)

    def goto_admin_dashboard(e=None):
        navigate_to(admin_dashboard_screen, goto_profile=goto_profile_admin, goto_logout=goto_login)

    def goto_dashboard(role):
        if role == "admin":
            goto_admin_dashboard()
        elif role == "customer":
            goto_browse_menu()
        else:
            goto_owner_dashboard()

    # Start with login
    goto_login()

ft.app(target=main)
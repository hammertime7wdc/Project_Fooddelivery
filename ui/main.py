import sys
import os
import flet as ft
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_database
from core.session_manager import SessionManager
from utils import show_snackbar
from screens.login import login_screen
from screens.splash import splash_screen
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
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#EBE1D1"
    page.padding = 0
    page.window_width = 412
    page.window_height = 917
    
    # Set theme for dropdown menus
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#E9762B",
            on_primary="#000000",
            surface="#EBE1D1",
            on_surface="#000000",
        )
    )

    init_database()

    # GLOBAL APP STATE
    current_user = {"user": None}
    cart = []
    session_timed_out = {"flag": False}
    
    
    session_manager = SessionManager(timeout_minutes=20, warning_minutes=2)
    
    # Universal activity tracker - resets timer on ANY user activity
    def update_session_activity(event_type=""):
        if current_user["user"] is not None and session_manager.is_active:
            session_manager.update_activity()
    
    # Track ALL possible user interactions
    page.on_keyboard_event = lambda e: update_session_activity("Keyboard")
    page.on_scroll = lambda e: update_session_activity("Scroll")
    page.on_window_event = lambda e: update_session_activity("Window") if e.data == "focus" else None
    page.on_click = lambda e: update_session_activity("Click")
    # Session warning notification
    def show_session_warning(remaining_seconds):
        """Show warning notification when session is about to expire"""
        # Show a snackbar warning 2 minutes before timeout
        if current_user["user"] is not None:
            minutes = remaining_seconds // 60
            snackbar = ft.SnackBar(
                content=ft.Text(f"Your session will expire in {minutes} minute(s) due to inactivity.", color="white", size=14),
                bgcolor="#FF8C00",  # Orange warning color
                duration=5000,
                open=True,
            )
            page.overlay.append(snackbar)
            page.update()
            # Auto-remove snackbar after duration to prevent memory accumulation
            def remove_snackbar():
                import time
                time.sleep(6)  # Wait for snackbar to close
                try:
                    if snackbar in page.overlay:
                        page.overlay.remove(snackbar)
                        page.update()
                except:
                    pass
            threading.Thread(target=remove_snackbar, daemon=True).start()
    
    def session_timeout():
        """Handle session timeout - logout user"""
        # Only timeout if user is still logged in (prevent double logout)
        if current_user["user"] is None:
            return
        
        session_manager.end_session()
        current_user["user"] = None
        cart.clear()
        session_timed_out["flag"] = True  # Set flag BEFORE going to login
        # Call goto_login without logout_message to trigger timeout message
        goto_login(e=None, logout_message=None, cause="timeout")
    
    # Navigation helper
    def navigate_to(screen_func, **kwargs):
        # Update session activity on EVERY navigation (most reliable trigger)
        if current_user["user"] is not None and session_manager.is_active:
            session_manager.update_activity()
        
        page.controls.clear()
        page.add(screen_func(page, current_user, cart, **kwargs))
        page.update()

    # Callbacks for navigation
    def goto_login(e=None, logout_message=None, cause=None):
        # Reset timeout flag IMMEDIATELY if this is a normal logout (has logout_message)
        # Do this FIRST, before anything else
        if logout_message is not None:
            session_timed_out["flag"] = False
        
        # End session when going to login (this stops the timeout monitor)
        session_manager.end_session()
        
        # Clear user data
        current_user["user"] = None
        
        # Clear old event handlers to prevent memory accumulation
        page.on_keyboard_event = None
        page.on_scroll = None
        page.on_window_event = None
        page.on_resize = None
        page.on_click = None
        
        navigate_to(
            login_screen,
            goto_signup=goto_signup,
            goto_reset=goto_reset,
            goto_dashboard=goto_dashboard,
            logout_message=logout_message,
            session_timed_out=session_timed_out,
            cause=cause,
        )

    def goto_splash(e=None):
        navigate_to(splash_screen, goto_login=goto_login)

    def goto_signup(e=None):
        navigate_to(signup_screen, goto_login=goto_login)

    def goto_reset(e=None):
        navigate_to(reset_password_screen, goto_login=goto_login)

    def goto_browse_menu(e=None):
        navigate_to(
            browse_menu_screen,
            goto_cart=goto_cart,
            goto_profile=goto_profile_customer,
            goto_history=goto_order_history,
            goto_logout=lambda e: goto_login(logout_message="You have been logged out successfully.", cause="logout"),
        )

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
        navigate_to(
            owner_dashboard_screen,
            goto_profile=goto_profile_owner,
            goto_logout=lambda e: goto_login(logout_message="You have been logged out successfully.", cause="logout"),
        )

    def goto_admin_dashboard(e=None):
        navigate_to(
            admin_dashboard_screen,
            goto_profile=goto_profile_admin,
            goto_logout=lambda e: goto_login(logout_message="You have been logged out successfully.", cause="logout"),
        )

    def goto_dashboard(role):
        # Start session timer when user successfully logs in
        if current_user["user"] is not None:
            # Re-attach event handlers for activity tracking
            page.on_keyboard_event = lambda e: update_session_activity("Keyboard")
            page.on_scroll = lambda e: update_session_activity("Scroll")
            page.on_window_event = lambda e: update_session_activity("Window") if e.data == "focus" else None
            page.on_click = lambda e: update_session_activity("Click")
            
            session_manager.start_session(
                user_data=current_user["user"],
                timeout_callback=session_timeout,
                warning_callback=show_session_warning,
                loop=None  # Flet handles the event loop internally
            )
        
        if role == "admin":
            goto_admin_dashboard()
        elif role == "customer":
            goto_browse_menu()
        else:
            goto_owner_dashboard()

    def on_page_close(e):
        """Handle app close - ensure clean shutdown"""
        session_manager.end_session()
        # Graceful shutdown - just end session, Flet handles the rest
    
    page.on_close = on_page_close
    
    # Start with splash
    goto_splash()

ft.app(target=main)
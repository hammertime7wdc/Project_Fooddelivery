from datetime import datetime, timedelta
import threading
import time
import asyncio

class SessionManager:
    def __init__(self, timeout_minutes=1, warning_minutes=0.5):
        """
        Initialize session manager
        
        Args:
            timeout_minutes: Minutes of inactivity before auto-logout (default: 15)
            warning_minutes: Minutes before timeout to show warning (default: 2)
        """
        self.timeout_minutes = timeout_minutes
        self.warning_minutes = warning_minutes
        self.last_activity = None
        self.user_data = None
        self.is_active = False
        self._monitor_thread = None
        self._stop_monitoring = False
        self.timeout_callback = None
        self.warning_callback = None
        self._warning_shown = False
        self.loop = None
    
    def start_session(self, user_data, timeout_callback=None, warning_callback=None, loop=None):
        """
        Start a new session
        
        Args:
            user_data: User information dict
            timeout_callback: Function to call when session times out
            warning_callback: Function to call to show warning dialog
            loop: Event loop for async operations
        """
        self.user_data = user_data
        self.last_activity = datetime.now()
        self.is_active = True
        self.timeout_callback = timeout_callback
        self.warning_callback = warning_callback
        self.loop = loop
        self._stop_monitoring = False
        self._warning_shown = False
        
        # Start monitoring thread
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_thread = threading.Thread(
                target=self._monitor_session, 
                daemon=True
            )
            self._monitor_thread.start()
    
    def update_activity(self):
        """Update last activity timestamp (call this on user interactions)"""
        if self.is_active:
            self.last_activity = datetime.now()
            self._warning_shown = False  # Reset warning if user is active
    
    def end_session(self):
        """Manually end the session"""
        self.is_active = False
        self.user_data = None
        self.last_activity = None
        self._stop_monitoring = True
        self._warning_shown = False
    
    def get_remaining_time(self):
        """Get remaining time before timeout in seconds"""
        if not self.is_active or not self.last_activity:
            return 0
        
        timeout_time = self.last_activity + timedelta(minutes=self.timeout_minutes)
        remaining = (timeout_time - datetime.now()).total_seconds()
        return max(0, remaining)
    
    def is_expired(self):
        """Check if session has expired"""
        if not self.is_active or not self.last_activity:
            return True
        
        return self.get_remaining_time() <= 0
    
    def _monitor_session(self):
        """Background thread to monitor session timeout"""
        while not self._stop_monitoring and self.is_active:
            if self._stop_monitoring:  # Double-check before sleeping
                break
            time.sleep(1)  # Check every second
            
            if self._stop_monitoring:  # Check again after sleep
                break
            
            remaining = self.get_remaining_time()
            warning_threshold = self.warning_minutes * 60  # Convert to seconds
            
            # Show warning when time is low
            if remaining <= warning_threshold and remaining > 0 and not self._warning_shown:
                self._warning_shown = True
                if self.warning_callback:
                    # Call callback from thread
                    self.warning_callback(int(remaining))
            
            # Timeout reached
            if self.is_expired():
                self.is_active = False
                if self.timeout_callback:
                    # Call callback from thread
                    self.timeout_callback()
                break            
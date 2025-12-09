# core/datetime_utils.py
"""
Datetime utility functions for consistent time formatting across the app
"""

from datetime import datetime


def format_datetime_philippine(dt_string):
    """
    Format datetime string to readable Philippine time display
    
    Args:
        dt_string: ISO format datetime string or None
    
    Returns:
        Formatted string like "December 05, 2024 02:30 PM" or "N/A"
    """
    if not dt_string:
        return "N/A"
    
    try:
        # Parse the ISO format datetime
        dt = datetime.fromisoformat(dt_string)
        
        # Format it nicely: "December 05, 2024 02:30 PM"
        return dt.strftime("%B %d, %Y %I:%M %p")
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_string


def format_datetime_short(dt_string):
    """
    Format datetime string to short format
    
    Args:
        dt_string: ISO format datetime string or None
    
    Returns:
        Formatted string like "Dec 05, 2024 2:30 PM" or "N/A"
    """
    if not dt_string:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_string


def format_date_only(dt_string):
    """
    Format datetime string to date only
    
    Args:
        dt_string: ISO format datetime string or None
    
    Returns:
        Formatted string like "December 05, 2024" or "N/A"
    """
    if not dt_string:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%B %d, %Y")
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_string


def format_time_only(dt_string):
    """
    Format datetime string to time only
    
    Args:
        dt_string: ISO format datetime string or None
    
    Returns:
        Formatted string like "02:30 PM" or "N/A"
    """
    if not dt_string:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%I:%M %p")
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_string
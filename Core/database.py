# core/database.py (Refactored with SQLAlchemy)
import json
from sqlalchemy import or_
from models.models import Session, MenuItem, Order, AuditLog, init_database as init_db


def init_database():
    """Initialize database and create tables"""
    init_db()


# ========== AUDIT LOGGING ==========
def log_action(user_id, action, details=""):
    session = Session()
    try:
        audit = AuditLog(user_id=user_id, action=action, details=details)
        session.add(audit)
        session.commit()
    finally:
        session.close()


def get_audit_logs(limit=100):
    session = Session()
    try:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
    finally:
        session.close()


# ========== MENU OPERATIONS ==========
def get_all_menu_items():
    """Return all available menu items (legacy helper)."""
    session = Session()
    try:
        items = session.query(MenuItem).filter_by(is_available=1).order_by(MenuItem.category, MenuItem.name).all()
        return [item.to_dict() for item in items]
    finally:
        session.close()


def get_menu_items_page(category=None, search=None, limit=10, offset=0):
    """Server-side pagination with optional category and search filters."""
    session = Session()
    try:
        query = session.query(MenuItem).filter_by(is_available=1)

        if category and category != "All":
            query = query.filter(MenuItem.category == category)

        if search:
            like = f"%{search}%"
            query = query.filter(or_(MenuItem.name.ilike(like), MenuItem.description.ilike(like)))

        total = query.count()
        items = query.order_by(MenuItem.category, MenuItem.name).limit(limit).offset(offset).all()

        return {"total": total, "items": [item.to_dict() for item in items]}
    finally:
        session.close()


def get_categories():
    session = Session()
    try:
        categories = session.query(MenuItem.category).filter_by(is_available=1).distinct().all()
        return sorted(set(c[0] for c in categories if c[0]))
    finally:
        session.close()


def create_menu_item(name, description, price, image, image_type='base64', category='Uncategorized', created_by=None):
    """Create menu item with image"""
    session = Session()
    try:
        item = MenuItem(
            name=name,
            description=description,
            price=price,
            image=image,
            image_type=image_type,
            category=category,
            created_by=created_by
        )
        session.add(item)
        session.commit()
        
        if created_by:
            log_action(created_by, "MENU_ITEM_CREATED", f"Created menu item: {name}")
    finally:
        session.close()


def update_menu_item(item_id, name, description, price, image, image_type='base64', category='Uncategorized', user_id=None):
    session = Session()
    try:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if item:
            item.name = name
            item.description = description
            item.price = price
            item.image = image
            item.image_type = image_type
            item.category = category
            session.commit()
            
            if user_id:
                log_action(user_id, "MENU_ITEM_UPDATED", f"Updated menu item: {name}")
    finally:
        session.close()


def delete_menu_item(item_id, user_id=None):
    session = Session()
    try:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if item:
            item_name = item.name
            item.is_available = 0
            session.commit()
            
            if user_id:
                log_action(user_id, "MENU_ITEM_DELETED", f"Deleted menu item: {item_name}")
    finally:
        session.close()


# ========== ORDER OPERATIONS ==========
def create_order(customer_id, customer_name, address, contact, items, total):
    session = Session()
    try:
        items_json = json.dumps(items)
        order = Order(
            customer_id=customer_id,
            customer_name=customer_name,
            delivery_address=address,
            contact_number=contact,
            total_amount=total,
            items=items_json
        )
        session.add(order)
        session.commit()
        
        order_id = order.id
        log_action(customer_id, "ORDER_PLACED", f"Order #{order_id} - Amount: {total}")
    finally:
        session.close()


def get_orders_by_customer(customer_id):
    """Get orders with per-customer numbering"""
    session = Session()
    try:
        orders = session.query(Order)\
            .filter_by(customer_id=customer_id)\
            .order_by(Order.created_at.asc())\
            .all()
        
        # Add customer-specific order number (chronological order)
        order_dicts = []
        for idx, order in enumerate(orders, start=1):
            order_dict = order.to_dict()
            order_dict['customer_order_number'] = idx
            order_dicts.append(order_dict)
        
        # Reverse to show newest first
        return list(reversed(order_dicts))
    finally:
        session.close()


def get_all_orders():
    """Get all orders with per-customer numbering for each customer"""
    session = Session()
    try:
        orders = session.query(Order).order_by(Order.created_at.desc()).all()
        order_dicts = [order.to_dict() for order in orders]
        
        # Group orders by customer_id and count them chronologically
        from collections import defaultdict
        customer_orders_by_time = defaultdict(list)
        
        # Group all orders by customer
        for order in order_dicts:
            customer_orders_by_time[order['customer_id']].append(order)
        
        # Sort each customer's orders chronologically and assign numbers
        for customer_id, customer_orders in customer_orders_by_time.items():
            # Sort by created_at ascending (oldest first)
            customer_orders.sort(key=lambda x: x['created_at'])
            # Assign numbers 1, 2, 3...
            for idx, order in enumerate(customer_orders, start=1):
                order['customer_order_number'] = idx
        
        return order_dicts
    finally:
        session.close()


# core/database.py

def update_order_status(order_id, new_status, user_id=None):
    """
    Update order status with proper state machine.
    Allowed transitions:
        placed          → preparing | out for delivery | cancelled
        preparing       → out for delivery | cancelled
        out for delivery→ delivered | cancelled
        delivered       → (nothing – final)
        cancelled       → (nothing – final)
    """
    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            return False, "Order not found"

        current = order.status.lower()

        # Normalise the incoming status (in case UI sends "Preparing" instead of "preparing")
        new_status = new_status.strip().lower()

        # Define the exact allowed next statuses
        allowed = {
            "placed":          ["preparing", "out for delivery", "cancelled"],
            "preparing":       ["out for delivery", "cancelled"],
            "out for delivery":["delivered", "cancelled"],
            "delivered":       [],                     # terminal
            "cancelled":       []                      # terminal
        }

        if new_status not in allowed.get(current, []):
            return False, f"Invalid status transition: {current} → {new_status}"

        order.status = new_status
        session.commit()

        if user_id:
            log_action(user_id, "ORDER_STATUS_UPDATED",
                      f"Order #{order_id} : {current} → {new_status}")

        return True, "Status updated"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
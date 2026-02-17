# core/database.py (Refactored with SQLAlchemy)
import json
from sqlalchemy import or_
from models.models import Session, MenuItem, Order, AuditLog, Favorite, init_database as init_db


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


def create_menu_item(name, description, price, stock, image, image_type='base64', category='Uncategorized', created_by=None, calories=0, ingredients='', recipe='', allergens='', is_on_sale=0, sale_percentage=0):
    """Create menu item with image and nutrition info"""
    session = Session()
    try:
        item = MenuItem(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image,
            image_type=image_type,
            category=category,
            created_by=created_by,
            calories=calories,
            ingredients=ingredients,
            recipe=recipe,
            allergens=allergens,
            is_on_sale=is_on_sale,
            sale_percentage=sale_percentage
        )
        session.add(item)
        session.commit()
        
        if created_by:
            log_action(created_by, "MENU_ITEM_CREATED", f"Created menu item: {name}")
    finally:
        session.close()


def update_menu_item(item_id, name, description, price, stock, image, image_type='base64', category='Uncategorized', user_id=None, calories=0, ingredients='', recipe='', allergens='', is_on_sale=0, sale_percentage=0):
    session = Session()
    try:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if item:
            item.name = name
            item.description = description
            item.price = price
            item.stock = stock
            item.image = image
            item.image_type = image_type
            item.category = category
            item.calories = calories
            item.ingredients = ingredients
            item.recipe = recipe
            item.allergens = allergens
            item.is_on_sale = is_on_sale
            item.sale_percentage = sale_percentage
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


def get_menu_item_stats(item_id):
    """Get statistics for a specific menu item"""
    session = Session()
    try:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if not item:
            return None
        
        # Get all orders
        orders = session.query(Order).all()
        
        total_orders = 0
        total_quantity = 0
        total_revenue = 0.0
        
        for order in orders:
            try:
                items_list = json.loads(order.items)
                for order_item in items_list:
                    if order_item.get("id") == item_id:
                        quantity = int(order_item.get("quantity", 0))
                        price = float(order_item.get("price", 0))
                        total_orders += 1
                        total_quantity += quantity
                        total_revenue += (quantity * price)
            except Exception:
                continue
        
        return {
            "item_name": item.name,
            "category": item.category,
            "current_price": item.price,
            "current_stock": item.stock,
            "total_orders": total_orders,
            "total_quantity_sold": total_quantity,
            "total_revenue": total_revenue,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }
    finally:
        session.close()


# ========== ORDER OPERATIONS ==========
def create_order(customer_id, customer_name, address, contact, items, total, payment_method="Cash on Delivery"):
    session = Session()
    try:
        # Decrease stock on order placement
        for item in items or []:
            try:
                item_id = item.get("id")
                qty = int(item.get("quantity", 0))
            except Exception:
                item_id = None
                qty = 0
            if not item_id or qty <= 0:
                continue
            menu_item = session.query(MenuItem).filter_by(id=item_id).first()
            if menu_item:
                current_stock = menu_item.stock or 0
                menu_item.stock = max(0, current_stock - qty)

        items_json = json.dumps(items)
        from datetime import datetime
        order = Order(
            customer_id=customer_id,
            customer_name=customer_name,
            delivery_address=address,
            contact_number=contact,
            total_amount=total,
            items=items_json,
            payment_method=payment_method,
            placed_at=datetime.now()
        )
        session.add(order)
        session.commit()
        
        order_id = order.id
        log_action(customer_id, "ORDER_PLACED", f"Order #{order_id} - Amount: {total} - Payment: {payment_method}")
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

        # If cancelled before preparation, restore stock
        if new_status == "cancelled" and current == "placed":
            try:
                items = json.loads(order.items) if order.items else []
            except Exception:
                items = []
            for item in items:
                try:
                    item_id = item.get("id")
                    qty = int(item.get("quantity", 0))
                except Exception:
                    item_id = None
                    qty = 0
                if not item_id or qty <= 0:
                    continue
                menu_item = session.query(MenuItem).filter_by(id=item_id).first()
                if menu_item:
                    current_stock = menu_item.stock or 0
                    menu_item.stock = current_stock + qty

        # Update timeline based on status change
        from datetime import datetime
        if new_status == "preparing":
            order.preparing_at = datetime.now()
        elif new_status == "out for delivery":
            order.out_for_delivery_at = datetime.now()
        elif new_status == "delivered":
            order.delivered_at = datetime.now()
        elif new_status == "cancelled":
            order.cancelled_at = datetime.now()

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


# ========== FAVORITE OPERATIONS ==========
def get_user_favorites(user_id):
    """Get all favorited menu items for a user"""
    session = Session()
    try:
        favorites = session.query(Favorite).filter_by(user_id=user_id).all()
        return [fav.menu_item_id for fav in favorites]
    finally:
        session.close()


def add_favorite(user_id, menu_item_id):
    """Add a menu item to user's favorites"""
    session = Session()
    try:
        # Check if already favorited
        existing = session.query(Favorite).filter_by(
            user_id=user_id, 
            menu_item_id=menu_item_id
        ).first()
        
        if not existing:
            favorite = Favorite(user_id=user_id, menu_item_id=menu_item_id)
            session.add(favorite)
            session.commit()
            return True, "Added to favorites"
        return False, "Already in favorites"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def remove_favorite(user_id, menu_item_id):
    """Remove a menu item from user's favorites"""
    session = Session()
    try:
        session.query(Favorite).filter_by(
            user_id=user_id, 
            menu_item_id=menu_item_id
        ).delete()
        session.commit()
        return True, "Removed from favorites"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
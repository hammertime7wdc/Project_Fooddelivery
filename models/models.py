# core/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

Base = declarative_base()
DB_FILE = "food_delivery.db"

# Thread-safe session
engine = create_engine(
    f'sqlite:///{DB_FILE}',
    connect_args={'check_same_thread': False, 'timeout': 10.0},
    echo=False
)
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
Session = scoped_session(session_factory)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    address = Column(String, default='')
    contact = Column(String, default='')
    profile_picture = Column(String, default='')
    pic_type = Column(String, default='')
    is_active = Column(Integer, default=1)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    orders = relationship("Order", back_populates="customer")
    menu_items = relationship("MenuItem", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'address': self.address,
            'contact': self.contact,
            'profile_picture': self.profile_picture,
            'pic_type': self.pic_type,
            'is_active': self.is_active,
            'failed_login_attempts': self.failed_login_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MenuItem(Base):
    __tablename__ = 'menu_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image = Column(String, default='')
    image_type = Column(String, default='base64')
    is_available = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    category = Column(String, default='Uncategorized')
    calories = Column(Integer, default=0)
    ingredients = Column(Text, default='')
    recipe = Column(Text, default='')
    allergens = Column(String, default='')
    is_on_sale = Column(Integer, default=0)
    sale_percentage = Column(Integer, default=0)

    # Relationships
    creator = relationship("User", back_populates="menu_items")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'image': self.image,
            'image_type': self.image_type,
            'is_available': self.is_available,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category': self.category,
            'calories': self.calories,
            'ingredients': self.ingredients,
            'recipe': self.recipe,
            'allergens': self.allergens,
            'is_on_sale': self.is_on_sale,
            'sale_percentage': self.sale_percentage
        }


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    customer_name = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    items = Column(Text, nullable=False)  # JSON string
    status = Column(String, default='placed')
    payment_method = Column(String, default='Cash on Delivery')
    created_at = Column(DateTime, default=datetime.now)
    placed_at = Column(DateTime, nullable=True)
    preparing_at = Column(DateTime, nullable=True)
    out_for_delivery_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("User", back_populates="orders")

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'delivery_address': self.delivery_address,
            'contact_number': self.contact_number,
            'total_amount': self.total_amount,
            'items': json.loads(self.items),
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'placed_at': self.placed_at.isoformat() if self.placed_at else None,
            'preparing_at': self.preparing_at.isoformat() if self.preparing_at else None,
            'out_for_delivery_at': self.out_for_delivery_at.isoformat() if self.out_for_delivery_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Favorite(Base):
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'menu_item_id': self.menu_item_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_database():
    """Initialize database and create default users from .env"""
    Base.metadata.create_all(engine)

    # Lightweight migration for existing DBs
    with engine.connect() as conn:
        # Migrate: Add stock column to menu_items if it doesn't exist
        result = conn.execute(text("PRAGMA table_info(menu_items)"))
        columns = [row[1] for row in result.fetchall()]
        if "stock" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN stock INTEGER DEFAULT 0"))
        
        # Migrate: Add nutrition and recipe columns to menu_items if they don't exist
        if "calories" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN calories INTEGER DEFAULT 0"))
        if "ingredients" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN ingredients TEXT DEFAULT ''"))
        if "recipe" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN recipe TEXT DEFAULT ''"))
        if "allergens" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN allergens STRING DEFAULT ''"))
        
        # Migrate: Add sale columns to menu_items if they don't exist
        sale_columns_added = False
        if "is_on_sale" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN is_on_sale INTEGER DEFAULT 0"))
            sale_columns_added = True
        if "sale_percentage" not in columns:
            conn.execute(text("ALTER TABLE menu_items ADD COLUMN sale_percentage INTEGER DEFAULT 0"))
            sale_columns_added = True
        
        if sale_columns_added:
            conn.commit()

        # Migrate: Add timestamp columns to orders if they don't exist
        result = conn.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result.fetchall()]
        
        timestamp_columns = ["placed_at", "preparing_at", "out_for_delivery_at", "delivered_at", "cancelled_at"]
        for col in timestamp_columns:
            if col not in columns:
                conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} DATETIME DEFAULT NULL"))
        
        # Migrate: Add payment_method column to orders if it doesn't exist
        if "payment_method" not in columns:
            conn.execute(text("ALTER TABLE orders ADD COLUMN payment_method STRING DEFAULT 'Cash on Delivery'"))
            conn.commit()

    session = Session()
    try:
        if session.query(User).count() == 0:
            from ..core.auth import hash_password

            admin = User(
                email=os.getenv("ADMIN_EMAIL"),
                password=hash_password(os.getenv("ADMIN_PASSWORD")),
                full_name='System Administrator',
                role='admin'
            )

            customer = User(
                email=os.getenv("CUSTOMER_EMAIL"),
                password=hash_password(os.getenv("CUSTOMER_PASSWORD")),
                full_name='John Doe',
                role='customer'
            )

            owner = User(
                email=os.getenv("OWNER_EMAIL"),
                password=hash_password(os.getenv("OWNER_PASSWORD")),
                full_name='Restaurant Owner',
                role='owner'
            )

            session.add_all([admin, customer, owner])
            session.commit()

            # Sample menu items
            lechon = MenuItem(
                name='Lechon',
                description='Classic pinoy lechon',
                price=240.0,
                stock=20,
                image='🐷',
                image_type='emoji',
                category='Mains'
            )

            sisig = MenuItem(
                name='Sisig',
                description='Classic Sisig',
                price=140.0,
                stock=25,
                image='🍳',
                image_type='emoji',
                category='Appetizers'
            )

            session.add_all([lechon, sisig])
            session.commit()
    finally:
        session.close()


def get_session():
    return Session()

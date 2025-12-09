# core/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
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
    image = Column(String, default='')
    image_type = Column(String, default='base64')
    is_available = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    category = Column(String, default='Uncategorized')

    # Relationships
    creator = relationship("User", back_populates="menu_items")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image': self.image,
            'image_type': self.image_type,
            'is_available': self.is_available,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category': self.category
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
    created_at = Column(DateTime, default=datetime.now)

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
            'created_at': self.created_at.isoformat() if self.created_at else None
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


def init_database():
    """Initialize database and create default users from .env"""
    Base.metadata.create_all(engine)

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
                image='🐷',
                image_type='emoji',
                category='Mains'
            )

            sisig = MenuItem(
                name='Sisig',
                description='Classic Sisig',
                price=140.0,
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

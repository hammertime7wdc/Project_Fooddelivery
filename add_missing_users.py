"""Script to add missing owner and admin users to existing database"""
from models.models import Session, User
from core.auth import hash_password
from dotenv import load_dotenv
import os

load_dotenv()

session = Session()

try:
    # Check if admin exists
    admin = session.query(User).filter_by(role='admin').first()
    if not admin:
        admin = User(
            email=os.getenv("ADMIN_EMAIL"),
            password=hash_password(os.getenv("ADMIN_PASSWORD")),
            full_name='System Administrator',
            role='admin'
        )
        session.add(admin)
        print(f"✓ Added admin: {os.getenv('ADMIN_EMAIL')}")
    else:
        print(f"✓ Admin already exists: {admin.email}")

    # Check if owner exists
    owner = session.query(User).filter_by(role='owner').first()
    if not owner:
        owner = User(
            email=os.getenv("OWNER_EMAIL"),
            password=hash_password(os.getenv("OWNER_PASSWORD")),
            full_name='Restaurant Owner',
            role='owner'
        )
        session.add(owner)
        print(f"✓ Added owner: {os.getenv('OWNER_EMAIL')}")
    else:
        print(f"✓ Owner already exists: {owner.email}")

    session.commit()
    print("\n✓ Done! All required users are now in the database.")

except Exception as e:
    session.rollback()
    print(f"✗ Error: {e}")
finally:
    session.close()

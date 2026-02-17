"""Check all users in database"""
from models.models import Session, User

session = Session()

try:
    users = session.query(User).all()
    print(f"\n{'='*60}")
    print(f"Total users in database: {len(users)}")
    print(f"{'='*60}\n")
    
    for user in users:
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Name: {user.full_name}")
        print(f"Active: {user.is_active}")
        print(f"Locked: {user.locked_until}")
        print(f"Failed attempts: {user.failed_login_attempts}")
        print("-" * 60)
        
finally:
    session.close()

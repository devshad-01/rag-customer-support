"""Seed script — creates default admin, agent, and customer users."""

import sys
import os

# Ensure the backend package is importable when running from workspace root
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.services.user_service import create_user, get_user_by_email  # noqa: E402

SEED_USERS = [
    {"name": "Admin User", "email": "admin@example.com", "password": "admin123", "role": UserRole.admin},
    {"name": "Agent User", "email": "agent@example.com", "password": "agent123", "role": UserRole.agent},
    {"name": "Customer User", "email": "customer@example.com", "password": "customer123", "role": UserRole.customer},
]


def seed():
    """Insert seed users if they don't already exist."""
    db = SessionLocal()
    try:
        for u in SEED_USERS:
            if get_user_by_email(db, u["email"]):
                print(f"  ✓ {u['role'].value:>8}  {u['email']} (already exists)")
                continue
            create_user(db, name=u["name"], email=u["email"], password=u["password"], role=u["role"])
            print(f"  + {u['role'].value:>8}  {u['email']} created")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding users …")
    seed()
    print("Done.")

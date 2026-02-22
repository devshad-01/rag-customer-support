"""User service — registration, authentication, lookup."""

import logging

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Look up a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Look up a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.customer,
) -> User:
    """Create a new user with hashed password.

    Raises ValueError if the email is already taken.
    """
    existing = get_user_by_email(db, email)
    if existing:
        raise ValueError("A user with this email already exists")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user id=%d email=%s role=%s", user.id, user.email, user.role.value)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Validate credentials. Returns the User on success, None on failure."""
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def list_users(db: Session, *, skip: int = 0, limit: int = 50) -> list[User]:
    """Return a paginated list of users."""
    return db.query(User).offset(skip).limit(limit).all()

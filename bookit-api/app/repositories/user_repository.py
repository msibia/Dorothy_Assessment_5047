from sqlalchemy.orm import Session
from typing import Optional

from app.models.models import User
from app.schemas.schemas import UserRegister, UserUpdate


class UserRepository:
    """User repository for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, user_data: UserRegister, password_hash: str) -> User:
        """Create new user"""
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user"""
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            user.email = user_data.email
        
        self.db.commit()
        self.db.refresh(user)
        return user
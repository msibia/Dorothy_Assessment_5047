from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.models import Review
from app.schemas.schemas import ReviewCreate, ReviewUpdate


class ReviewRepository:
    """Review repository for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, review_id: int) -> Optional[Review]:
        """Get review by ID"""
        return self.db.query(Review).filter(Review.id == review_id).first()
    
    def get_by_booking_id(self, booking_id: int) -> Optional[Review]:
        """Get review by booking ID"""
        return self.db.query(Review).filter(Review.booking_id == booking_id).first()
    
    def get_by_service_id(self, service_id: int) -> List[Review]:
        """Get all reviews for a service"""
        return self.db.query(Review).join(Review.booking).filter(
            Review.booking.has(service_id=service_id)
        ).all()
    
    def create(self, review_data: ReviewCreate) -> Review:
        """Create new review"""
        review = Review(**review_data.model_dump())
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def update(self, review: Review, review_data: ReviewUpdate) -> Review:
        """Update review"""
        update_data = review_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)
        
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def delete(self, review: Review) -> None:
        """Delete review"""
        self.db.delete(review)
        self.db.commit()
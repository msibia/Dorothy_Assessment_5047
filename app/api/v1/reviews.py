from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.repositories.review_repository import ReviewRepository
from app.repositories.booking_repository import BookingRepository
from app.schemas.schemas import ReviewCreate, ReviewUpdate, ReviewResponse, BookingStatus
from app.models.models import User, UserRole

router = APIRouter()


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create review (must be for completed booking by same user, one per booking)"""
    booking_repo = BookingRepository(db)
    review_repo = ReviewRepository(db)
    
    # Check if booking exists
    booking = booking_repo.get_by_id(review_data.booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if booking belongs to current user
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only review your own bookings"
        )
    
    # Check if booking is completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings"
        )
    
    # Check if review already exists
    existing_review = review_repo.get_by_booking_id(review_data.booking_id)
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking"
        )
    
    review = review_repo.create(review_data)
    return review


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get review by ID (public endpoint)"""
    review_repo = ReviewRepository(db)
    review = review_repo.get_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update review (owner only)"""
    review_repo = ReviewRepository(db)
    booking_repo = BookingRepository(db)
    
    review = review_repo.get_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns the booking
    booking = booking_repo.get_by_id(review.booking_id)
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review"
        )
    
    updated_review = review_repo.update(review, review_data)
    return updated_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete review (owner or admin)"""
    review_repo = ReviewRepository(db)
    booking_repo = BookingRepository(db)
    
    review = review_repo.get_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check authorization
    booking = booking_repo.get_by_id(review.booking_id)
    is_owner = booking.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review"
        )
    
    review_repo.delete(review)
    return None
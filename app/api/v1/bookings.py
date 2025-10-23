from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.repositories.booking_repository import BookingRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.schemas import BookingCreate, BookingUpdate, BookingResponse, BookingStatus
from app.models.models import User, UserRole

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new booking"""
    service_repo = ServiceRepository(db)
    booking_repo = BookingRepository(db)
    
    # Check if service exists and is active
    service = service_repo.get_by_id(booking_data.service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    if not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service is not active"
        )
    
    # Calculate end time based on service duration
    end_time = booking_data.start_time + timedelta(minutes=service.duration_minutes)
    
    # Check for booking conflicts
    has_conflict = booking_repo.check_conflict(
        service_id=booking_data.service_id,
        start_time=booking_data.start_time,
        end_time=end_time
    )
    
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking conflict: time slot is not available"
        )
    
    # Create booking
    booking = booking_repo.create(
        user_id=current_user.id,
        service_id=booking_data.service_id,
        start_time=booking_data.start_time,
        end_time=end_time
    )
    
    return booking


@router.get("", response_model=List[BookingResponse])
async def get_bookings(
    status_filter: Optional[BookingStatus] = Query(None, alias="status"),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bookings (user: own bookings, admin: all bookings)"""
    booking_repo = BookingRepository(db)
    
    # Users can only see their own bookings, admins see all
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    
    bookings = booking_repo.get_all(
        user_id=user_id,
        status=status_filter,
        from_date=from_date,
        to_date=to_date
    )
    
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get booking by ID (owner or admin)"""
    booking_repo = BookingRepository(db)
    booking = booking_repo.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check authorization
    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this booking"
        )
    
    return booking


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update booking (owner can reschedule/cancel, admin can update status)"""
    booking_repo = BookingRepository(db)
    service_repo = ServiceRepository(db)
    
    booking = booking_repo.get_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check authorization
    is_owner = booking.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this booking"
        )
    
    # Handle rescheduling (owner only, if pending or confirmed)
    if booking_data.start_time and is_owner:
        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only reschedule pending or confirmed bookings"
            )
        
        # Get service for duration calculation
        service = service_repo.get_by_id(booking.service_id)
        new_end_time = booking_data.start_time + timedelta(minutes=service.duration_minutes)
        
        # Check for conflicts
        has_conflict = booking_repo.check_conflict(
            service_id=booking.service_id,
            start_time=booking_data.start_time,
            end_time=new_end_time,
            exclude_booking_id=booking.id
        )
        
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Booking conflict: time slot is not available"
            )
        
        booking = booking_repo.update(
            booking,
            start_time=booking_data.start_time,
            end_time=new_end_time
        )
    
    # Handle status update (admin only or owner cancelling)
    if booking_data.status:
        if is_admin:
            # Admin can change to any status
            booking = booking_repo.update(booking, status=booking_data.status)
        elif is_owner and booking_data.status == BookingStatus.CANCELLED:
            # Owner can only cancel
            if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only cancel pending or confirmed bookings"
                )
            booking = booking_repo.update(booking, status=BookingStatus.CANCELLED)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change booking status"
            )
    
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete booking (owner before start_time, admin anytime)"""
    booking_repo = BookingRepository(db)
    booking = booking_repo.get_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    is_owner = booking.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this booking"
        )
    
    # Owner can only delete before start time
    if is_owner and not is_admin:
        if booking.start_time <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete booking after start time"
            )
    
    booking_repo.delete(booking)
    return None
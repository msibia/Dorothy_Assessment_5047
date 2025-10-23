from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import datetime

from app.models.models import Booking, BookingStatus


class BookingRepository:
    """Booking repository for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        """Get booking by ID"""
        return self.db.query(Booking).filter(Booking.id == booking_id).first()
    
    def get_all(
        self,
        user_id: Optional[int] = None,
        status: Optional[BookingStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Booking]:
        """Get all bookings with optional filters"""
        query = self.db.query(Booking)
        
        if user_id is not None:
            query = query.filter(Booking.user_id == user_id)
        
        if status is not None:
            query = query.filter(Booking.status == status)
        
        if from_date is not None:
            query = query.filter(Booking.start_time >= from_date)
        
        if to_date is not None:
            query = query.filter(Booking.start_time <= to_date)
        
        return query.order_by(Booking.start_time.desc()).all()
    
    def check_conflict(
        self,
        service_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: Optional[int] = None
    ) -> bool:
        """Check if there's a booking conflict"""
        query = self.db.query(Booking).filter(
            and_(
                Booking.service_id == service_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                or_(
                    and_(
                        Booking.start_time <= start_time,
                        Booking.end_time > start_time
                    ),
                    and_(
                        Booking.start_time < end_time,
                        Booking.end_time >= end_time
                    ),
                    and_(
                        Booking.start_time >= start_time,
                        Booking.end_time <= end_time
                    )
                )
            )
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        
        return query.first() is not None
    
    def create(
        self,
        user_id: int,
        service_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Booking:
        """Create new booking"""
        booking = Booking(
            user_id=user_id,
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING
        )
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking
    
    def update(self, booking: Booking, **kwargs) -> Booking:
        """Update booking"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(booking, key, value)
        
        self.db.commit()
        self.db.refresh(booking)
        return booking
    
    def delete(self, booking: Booking) -> None:
        """Delete booking"""
        self.db.delete(booking)
        self.db.commit()
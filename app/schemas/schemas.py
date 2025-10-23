from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# Auth schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# User schemas
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


# Service schemas
class ServiceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    price: float = Field(..., ge=0)
    duration_minutes: int = Field(..., gt=0)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    duration_minutes: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Booking schemas
class BookingCreate(BaseModel):
    service_id: int
    start_time: datetime
    
    @field_validator('start_time')
    def validate_start_time(cls, v):
        if v < datetime.utcnow():
            raise ValueError('start_time must be in the future')
        return v


class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    
    @field_validator('start_time')
    def validate_start_time(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('start_time must be in the future')
        return v


class BookingResponse(BaseModel):
    id: int
    user_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    created_at: datetime
    service: Optional[ServiceResponse] = None
    
    class Config:
        from_attributes = True


# Review schemas
class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=1000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=1, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    rating: int
    comment: str
    created_at: datetime
    
    class Config:
        from_attributes = True
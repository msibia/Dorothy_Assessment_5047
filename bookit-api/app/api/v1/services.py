from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.repositories.service_repository import ServiceRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.schemas import ServiceCreate, ServiceUpdate, ServiceResponse, ReviewResponse

router = APIRouter()


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    q: Optional[str] = Query(None, description="Search query"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get all services (public endpoint)"""
    service_repo = ServiceRepository(db)
    services = service_repo.get_all(q=q, price_min=price_min, price_max=price_max, active=active)
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get service by ID (public endpoint)"""
    service_repo = ServiceRepository(db)
    service = service_repo.get_by_id(service_id)
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Create new service (admin only)"""
    service_repo = ServiceRepository(db)
    service = service_repo.create(service_data)
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Update service (admin only)"""
    service_repo = ServiceRepository(db)
    service = service_repo.get_by_id(service_id)
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    updated_service = service_repo.update(service, service_data)
    return updated_service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Delete service (admin only)"""
    service_repo = ServiceRepository(db)
    service = service_repo.get_by_id(service_id)
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    service_repo.delete(service)
    return None


@router.get("/{service_id}/reviews", response_model=List[ReviewResponse])
async def get_service_reviews(service_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a service (public endpoint)"""
    service_repo = ServiceRepository(db)
    review_repo = ReviewRepository(db)
    
    # Check if service exists
    service = service_repo.get_by_id(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    reviews = review_repo.get_by_service_id(service_id)
    return reviews
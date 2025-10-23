from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.models import Service
from app.schemas.schemas import ServiceCreate, ServiceUpdate


class ServiceRepository:
    """Service repository for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, service_id: int) -> Optional[Service]:
        """Get service by ID"""
        return self.db.query(Service).filter(Service.id == service_id).first()
    
    def get_all(
        self,
        q: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        active: Optional[bool] = None
    ) -> List[Service]:
        """Get all services with optional filters"""
        query = self.db.query(Service)
        
        if q:
            query = query.filter(
                (Service.title.ilike(f"%{q}%")) | 
                (Service.description.ilike(f"%{q}%"))
            )
        
        if price_min is not None:
            query = query.filter(Service.price >= price_min)
        
        if price_max is not None:
            query = query.filter(Service.price <= price_max)
        
        if active is not None:
            query = query.filter(Service.is_active == active)
        
        return query.all()
    
    def create(self, service_data: ServiceCreate) -> Service:
        """Create new service"""
        service = Service(**service_data.model_dump())
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service
    
    def update(self, service: Service, service_data: ServiceUpdate) -> Service:
        """Update service"""
        update_data = service_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)
        
        self.db.commit()
        self.db.refresh(service)
        return service
    
    def delete(self, service: Service) -> None:
        """Delete service"""
        self.db.delete(service)
        self.db.commit()
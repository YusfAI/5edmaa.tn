from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.user import User
from models.service import Service
from models.schemas import ServiceCreate, ServiceResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/api/services", tags=["Services"])


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new service (only providers can create services)"""
    if current_user.role != "provider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only providers can create services"
        )
    
    new_service = Service(**service_data.dict(), provider_id=current_user.id)
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service


@router.get("/", response_model=List[ServiceResponse])
async def list_services(db: Session = Depends(get_db)):
    """List all services"""
    services = db.query(Service).all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Get a specific service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return service
@router.get("/provider/{provider_id}")
async def get_provider_services(provider_id: int, db: Session = Depends(get_db)):
    services = db.query(Service).filter(Service.provider_id == provider_id).all()
    return services

@router.put("/{service_id}")
async def update_service(service_id: int, service: ServiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if db_service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_service.title = service.title
    db_service.description = service.description
    db_service.category = service.category
    db_service.price = service.price
    db_service.duration = service.duration
    db_service.location = service.location
    db.commit()
    db.refresh(db_service)
    return db_service

@router.delete("/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if db_service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_service)
    db.commit()
    return {"message": "Service deleted"}

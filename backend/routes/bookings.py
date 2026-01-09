from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models import Booking, Service, User
from routes.auth import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

class BookingCreate(BaseModel):
    service_id: int
    total_price: float

@router.post("/", response_model=dict)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = db.query(Service).filter(Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    new_booking = Booking(
        customer_id=current_user.id,
        service_id=booking.service_id,
        total_price=booking.total_price,
        status="pending"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return {"id": new_booking.id, "status": "booking created"}

@router.get("/customer/{customer_id}")
def get_customer_bookings(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    bookings = db.query(Booking).filter(Booking.customer_id == customer_id).all()
    return [
        {
            "id": b.id,
            "service_id": b.service_id,
            "total_price": b.total_price,
            "status": b.status
        }
        for b in bookings
    ]
@router.get("/provider/{provider_id}")
async def get_provider_bookings(provider_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != provider_id or current_user.role != "provider":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    bookings = db.query(Booking).join(Service).filter(Service.provider_id == provider_id).all()
    return bookings

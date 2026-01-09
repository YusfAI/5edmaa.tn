from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: str = "customer"


class UserResponse(UserBase):
    id: int
    role: str
    
    class Config:
        from_attributes = True


# Service Schemas
class ServiceBase(BaseModel):
    title: str
    description: str
    category: str
    price: float
    duration: Optional[int] = None
    location: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceResponse(ServiceBase):
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

from pydantic import BaseModel, EmailStr

# Add simple registration schema after the existing schemas
class SimpleRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone: str
    role: str
    address: str = "Tunis"  # Default address

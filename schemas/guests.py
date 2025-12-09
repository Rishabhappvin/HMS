from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class GuestBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    address: Optional[str] = None
    id_number: str = Field(..., description="Government ID or passport number")

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    address: Optional[str] = None
    id_number: Optional[str] = None

class GuestResponse(GuestBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
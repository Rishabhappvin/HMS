from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from models.reservations import ReservationStatus

class ReservationBase(BaseModel):
    guest_id: int
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    number_of_guests: int = Field(default=1, ge=1)
    special_requests: Optional[str] = None
    
    @field_validator('check_out_date')
    @classmethod
    def check_dates(cls, v, info):
        if 'check_in_date' in info.data and v <= info.data['check_in_date']:
            raise ValueError('check_out_date must be after check_in_date')
        return v

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    status: Optional[ReservationStatus] = None
    number_of_guests: Optional[int] = Field(None, ge=1)
    special_requests: Optional[str] = None

class ReservationResponse(ReservationBase):
    id: int
    status: ReservationStatus
    total_price: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
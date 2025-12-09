from pydantic import BaseModel, Field
from typing import Optional
from models.rooms import RoomStatus, RoomType

class RoomBase(BaseModel):
    room_number: str = Field(..., description="Unique room number")
    room_type: RoomType
    price: float = Field(..., gt=0, description="Room price per night")
    floor: Optional[int] = None
    capacity: int = Field(default=1, ge=1)
    description: Optional[str] = None

class RoomCreate(RoomBase):
    status: RoomStatus = RoomStatus.AVAILABLE

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_type: Optional[RoomType] = None
    price: Optional[float] = Field(None, gt=0)
    status: Optional[RoomStatus] = None
    floor: Optional[int] = None
    capacity: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None

class RoomResponse(RoomBase):
    id: int
    status: RoomStatus
    
    class Config:
        from_attributes = True
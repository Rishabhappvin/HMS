from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum

class RoomStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"

class RoomType(enum.Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True, nullable=False)
    room_type = Column(Enum(RoomType), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    floor = Column(Integer)
    capacity = Column(Integer, default=1)
    description = Column(String, nullable=True)
    
    # Relationship
    reservations = relationship("Reservation", back_populates="room")
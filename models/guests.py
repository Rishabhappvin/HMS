from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database import Base


class Guest(Base):
    __tablename__ = "guests"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    id_number = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=None)
    deleted_at = Column(DateTime, default=None)
    
    # Relationship
    reservations = relationship("Reservation", back_populates="guest")
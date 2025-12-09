from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.rooms import Room, RoomStatus
from schemas.rooms import RoomCreate, RoomUpdate, RoomResponse
from auth import CurrentUser

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
)

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Create a new room"""
    # Check if room number already exists
    db_room = db.query(Room).filter(Room.room_number == room.room_number).first()
    if db_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room number already exists"
        )
    
    db_room = Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("/", response_model=List[RoomResponse])
def get_rooms(
    skip: int = 0,
    limit: int = 100,
    status: RoomStatus = None,
    db: Session = Depends(get_db)
):
    """Get all rooms with optional filtering"""
    query = db.query(Room)
    if status:
        query = query.filter(Room.status == status)
    rooms = query.offset(skip).limit(limit).all()
    return rooms

@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room by ID"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room

@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_update: RoomUpdate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Update a room"""
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if room number is being changed and if it already exists
    if room_update.room_number and room_update.room_number != db_room.room_number:
        existing_room = db.query(Room).filter(Room.room_number == room_update.room_number).first()
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room number already exists"
            )
    
    # Update fields
    update_data = room_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_room, field, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Delete a room"""
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    db.delete(db_room)
    db.commit()
    return None

@router.get("/available/search", response_model=List[RoomResponse])
def search_available_rooms(
    db: Session = Depends(get_db)
):
    """Get all available rooms"""
    rooms = db.query(Room).filter(Room.status == RoomStatus.AVAILABLE).all()
    return rooms
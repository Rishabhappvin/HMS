from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from datetime import datetime
from database import get_db
from models.reservations import Reservation, ReservationStatus
from models.rooms import Room, RoomStatus
from models.guests import Guest
from schemas.reservations import ReservationCreate, ReservationUpdate, ReservationResponse
from auth import CurrentUser

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
)

def check_room_availability(db: Session, room_id: int, check_in: datetime, check_out: datetime, exclude_reservation_id: int = None):
    """Check if a room is available for the given date range"""
    query = db.query(Reservation).filter(
        Reservation.room_id == room_id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]),
        or_(
            and_(Reservation.check_in_date <= check_in, Reservation.check_out_date > check_in),
            and_(Reservation.check_in_date < check_out, Reservation.check_out_date >= check_out),
            and_(Reservation.check_in_date >= check_in, Reservation.check_out_date <= check_out)
        )
    )
    
    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)
    
    overlapping = query.first()
    return overlapping is None

def calculate_total_price(db: Session, room_id: int, check_in: datetime, check_out: datetime):
    """Calculate total price for the reservation"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return 0
    
    nights = (check_out - check_in).days
    return room.price * nights

@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Create a new reservation"""
    # Verify guest exists
    guest = db.query(Guest).filter(Guest.id == reservation.guest_id).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Verify room exists
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check room availability
    if not check_room_availability(db, reservation.room_id, reservation.check_in_date, reservation.check_out_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is not available for the selected dates"
        )
    
    # Check if number of guests exceeds room capacity
    if reservation.number_of_guests > room.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Number of guests exceeds room capacity ({room.capacity})"
        )
    
    # Calculate total price
    total_price = calculate_total_price(db, reservation.room_id, reservation.check_in_date, reservation.check_out_date)
    
    # Create reservation
    db_reservation = Reservation(
        **reservation.model_dump(),
        total_price=total_price
    )
    db.add(db_reservation)
    
    # Update room status to reserved
    room.status = RoomStatus.RESERVED
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

@router.get("/", response_model=List[ReservationResponse])
def get_reservations(
    skip: int = 0,
    limit: int = 100,
    status: ReservationStatus = None,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get all reservations with optional status filter"""
    query = db.query(Reservation)
    if status:
        query = query.filter(Reservation.status == status)
    reservations = query.offset(skip).limit(limit).all()
    return reservations

@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get a specific reservation by ID"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    return reservation

@router.get("/guest/{guest_id}", response_model=List[ReservationResponse])
def get_guest_reservations(
    guest_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get all reservations for a specific guest"""
    reservations = db.query(Reservation).filter(Reservation.guest_id == guest_id).all()
    return reservations

@router.get("/room/{room_id}", response_model=List[ReservationResponse])
def get_room_reservations(
    room_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get all reservations for a specific room"""
    reservations = db.query(Reservation).filter(Reservation.room_id == room_id).all()
    return reservations

@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
    reservation_id: int,
    reservation_update: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Update a reservation"""
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not db_reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # If dates are being updated, check availability
    check_in = reservation_update.check_in_date or db_reservation.check_in_date
    check_out = reservation_update.check_out_date or db_reservation.check_out_date
    
    if reservation_update.check_in_date or reservation_update.check_out_date:
        if not check_room_availability(db, db_reservation.room_id, check_in, check_out, reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room is not available for the selected dates"
            )
        
        # Recalculate total price if dates changed
        db_reservation.total_price = calculate_total_price(db, db_reservation.room_id, check_in, check_out)
    
    # Update fields
    update_data = reservation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reservation, field, value)
    
    # Update room status based on reservation status
    room = db_reservation.room
    if reservation_update.status == ReservationStatus.CHECKED_IN:
        room.status = RoomStatus.OCCUPIED
    elif reservation_update.status == ReservationStatus.CHECKED_OUT:
        room.status = RoomStatus.AVAILABLE
    elif reservation_update.status == ReservationStatus.CANCELLED:
        # Check if there are other active reservations for this room
        active_reservations = db.query(Reservation).filter(
            Reservation.room_id == room.id,
            Reservation.id != reservation_id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        ).first()
        if not active_reservations:
            room.status = RoomStatus.AVAILABLE
    
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Delete a reservation"""
    db_reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not db_reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Update room status if this was the only active reservation
    room = db_reservation.room
    active_reservations = db.query(Reservation).filter(
        Reservation.room_id == room.id,
        Reservation.id != reservation_id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    ).first()
    
    if not active_reservations:
        room.status = RoomStatus.AVAILABLE
    
    db.delete(db_reservation)
    db.commit()
    return None

@router.post("/{reservation_id}/check-in", response_model=ReservationResponse)
def check_in(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Check in a guest"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed reservations can be checked in"
        )
    
    reservation.status = ReservationStatus.CHECKED_IN
    reservation.room.status = RoomStatus.OCCUPIED
    
    db.commit()
    db.refresh(reservation)
    return reservation

@router.post("/{reservation_id}/check-out", response_model=ReservationResponse)
def check_out(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Check out a guest"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only checked-in reservations can be checked out"
        )
    
    reservation.status = ReservationStatus.CHECKED_OUT
    reservation.room.status = RoomStatus.AVAILABLE
    
    db.commit()
    db.refresh(reservation)
    return reservation
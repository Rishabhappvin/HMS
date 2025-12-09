from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.guests import Guest
from schemas.guests import GuestCreate, GuestUpdate, GuestResponse
from auth import CurrentUser

router = APIRouter(
    prefix="/guests",
    tags=["guests"],
)

@router.post("/", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
def create_guest(
    guest: GuestCreate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    
    db_guest = db.query(Guest).filter(Guest.email == guest.email).first()
    if db_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if ID number already exists
    db_guest = db.query(Guest).filter(Guest.id_number == guest.id_number).first()
    if db_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID number already registered"
        )
    
    db_guest = Guest(**guest.model_dump())
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest

@router.get("/", response_model=List[GuestResponse])
def get_guests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get all guests"""
    guests = db.query(Guest).offset(skip).limit(limit).all()
    return guests

@router.get("/{guest_id}", response_model=GuestResponse)
def get_guest(
    guest_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Get a specific guest by ID"""
    guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    return guest

@router.get("/search/email/{email}", response_model=GuestResponse)
def get_guest_by_email(
    email: str,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Search for a guest by email"""
    guest = db.query(Guest).filter(Guest.email == email).first()
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    return guest

@router.put("/{guest_id}", response_model=GuestResponse)
def update_guest(
    guest_id: int,
    guest_update: GuestUpdate,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Update a guest"""
    db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not db_guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Check if email is being changed and if it already exists
    if guest_update.email and guest_update.email != db_guest.email:
        existing_guest = db.query(Guest).filter(Guest.email == guest_update.email).first()
        if existing_guest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if ID number is being changed and if it already exists
    if guest_update.id_number and guest_update.id_number != db_guest.id_number:
        existing_guest = db.query(Guest).filter(Guest.id_number == guest_update.id_number).first()
        if existing_guest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID number already registered"
            )
    
    # Update fields
    update_data = guest_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_guest, field, value)
    
    db.commit()
    db.refresh(db_guest)
    return db_guest

@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(
    guest_id: int,
    db: Session = Depends(get_db),
    current_user = CurrentUser
):
    """Delete a guest"""
    db_guest = db.query(Guest).filter(Guest.id == guest_id).first()
    if not db_guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Check if guest has active reservations
    if db_guest.reservations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete guest with existing reservations"
        )
    
    db.delete(db_guest)
    db.commit()
    return None
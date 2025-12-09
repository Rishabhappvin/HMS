from database import Base, engine
from models.guests import Guest
from models.rooms import Room
from models.reservations import Reservation

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
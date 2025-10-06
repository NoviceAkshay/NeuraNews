# backend/create_tables.py
from .database import engine, Base
from .models import News, User

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

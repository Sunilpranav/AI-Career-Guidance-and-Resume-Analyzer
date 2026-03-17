# backend/init_db.py
from .database import engine, Base
from .models import User, ResumeResult  # Ensure models are imported!

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

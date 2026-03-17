from .database import engine, Base
from .models import User, ResumeResult

print("--- DATABASE RESET ---")

# 1. Drop everything using SQLAlchemy (Safe & Correct Order)
print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Tables dropped.")

# 2. Create everything
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Success! Database is ready.")

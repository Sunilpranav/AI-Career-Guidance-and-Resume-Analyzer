from sqlalchemy import text
from .database import engine, Base
from .models import User, ResumeResult

print("--- ATOMIC RESET STARTED ---")

# 1. Force Drop Tables
with engine.connect() as conn:
    try:
        # Disable foreign key checks so we can drop tables freely
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS resume_results"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        print("Old tables deleted.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

# 2. Create Fresh Tables
Base.metadata.create_all(bind=engine)
print("New tables created with correct columns.")

# 3. Verify
from sqlalchemy import inspect
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
print(f"Current columns in 'users': {columns}")

if 'is_verified' in columns:
    print("SUCCESS! 'is_verified' column exists.")
else:
    print("FAILURE! Column still missing.")

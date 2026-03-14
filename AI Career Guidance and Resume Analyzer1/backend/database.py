from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Username: root (Try 'root' if 'admin' fails)
# Password: 21#Sunil@26 -> Encoded: 21%23Sunil%4026
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:21%23Sunil%4026@localhost/career_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))

class ResumeResult(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    filename = Column(String(255))
    extracted_skills = Column(JSON)
    career_recommendations = Column(JSON)
    roadmap = Column(JSON)

# This line creates the tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

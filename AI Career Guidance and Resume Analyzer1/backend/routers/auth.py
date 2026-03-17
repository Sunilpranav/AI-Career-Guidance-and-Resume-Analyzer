from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets


from ..database import get_db
from ..models import User

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HELPER: Simulate sending email by printing to console
def send_verification_email(email: str, token: str):
    print("\n" + "="*50)
    print(f"📧 EMAIL SENT TO: {email}")
    print(f"🔗 VERIFY LINK: http://127.0.0.1:8000/auth/verify/{token}")
    print("="*50 + "\n")

@router.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # 1. Check if user exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # 2. Create user with verification token
    hashed_password = pwd_context.hash(password)
    verification_token = secrets.token_urlsafe(16) # Generate secure token
    
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_verified=False,
        verification_token=verification_token
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. "Send" Email
    send_verification_email(email, verification_token)

    return {"msg": "Registration successful! Please check the server console to verify your email."}

@router.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user.is_verified = True
    user.verification_token = None # Clear token after use
    db.commit()
    
    return {"msg": "Email verified successfully! You can now login."}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # CHECK VERIFICATION STATUS
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first. Check server console for link.")

    if not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer", "user_id": user.id, "username": user.username}

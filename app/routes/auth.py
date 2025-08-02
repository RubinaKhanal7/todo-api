from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from database.connection import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin
from schemas.token import Token
from auth.utils import hash_password, verify_password, create_access_token
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **full_name**: User's full name (required, cannot be empty)
    - **email**: User's email address (required, must be valid email)
    - **password**: User's password (required)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and get access token
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT token for authentication
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
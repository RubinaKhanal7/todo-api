from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.schemas.token import Token
from app.auth.utils import hash_password, verify_password, create_access_token
from app.config.settings import settings
from app.auth.dependencies import get_current_user, is_admin 
from app.config.helpers import get_user_or_404 
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserStatusUpdate(BaseModel):
    status: bool

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **full_name**: User's full name (required, cannot be empty)
    - **email**: User's email address (required, must be valid email)
    - **password**: User's password (required)
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        user_status=True 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    
    return {
        "message": "User created successfully", 
        "user_id": new_user.id,
        "user_status": new_user.user_status,
        "created_at": new_user.created_at 
    }

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and get access token
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT token for authentication
    """
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.user_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.patch("/users/{user_id}/status", status_code=status.HTTP_200_OK)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)  
):
    """
    Update user active status (Admin only)
    
    - **user_id**: ID of user to update
    - **status**: boolean (true=active, false=inactive)
    """
    user = get_user_or_404(db, user_id)

    user.user_status = status_update.status
    db.commit()
    db.refresh(user) 
    
    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "new_status": "active" if user.user_status else "inactive",
        "updated_at": user.updated_at  
    }

@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """
    Get user details (Admin only)
    
    - **user_id**: ID of user to retrieve
    """
    user = get_user_or_404(db, user_id)
    
    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "user_status": user.user_status,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.get("/users", status_code=status.HTTP_200_OK)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin),
    page: int = 1,
    per_page: int = 10
):
    """
    Get all users with pagination (Admin only)
    
    - **page**: Page number (starts from 1)
    - **per_page**: Items per page (default: 10)
    """
    users = db.query(User).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "users": [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "user_status": user.user_status,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            for user in users
        ],
        "page": page,
        "per_page": per_page,
        "total": len(users)
    }
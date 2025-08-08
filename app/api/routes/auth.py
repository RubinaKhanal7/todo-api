from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.user import User, UserStatus
from app.schemas.user import (
    UserCreate, 
    UserLogin, 
    UserStatusUpdate, 
    UserResponse, 
    EmailVerificationRequest
)
from app.schemas.token import Token
from app.auth.utils import hash_password, verify_password, create_access_token
from app.config.settings import settings
from app.auth.dependencies import get_current_user, is_admin 
from app.config.helpers import get_user_or_404  
from app.config.email import email_service
from pydantic import BaseModel, ValidationError, EmailStr
from typing import List
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email"""
    email: EmailStr  

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = hash_password(user.password)

        is_admin_user = user.email in settings.ADMIN_EMAILS
        
        if is_admin_user:
            new_user = User(
                full_name=user.full_name,
                email=user.email,
                hashed_password=hashed_password,
                status=UserStatus.ACTIVE,
                user_status=True,
                email_verified=True,
                email_verification_token=None,
                email_verification_expires=None
            )
            email_sent = False
            verification_required = False
        else:
            verification_token = email_service.generate_verification_token()
            verification_expiry = email_service.get_verification_expiry()
            new_user = User(
                full_name=user.full_name,
                email=user.email,
                hashed_password=hashed_password,
                status=UserStatus.PENDING,
                user_status=False,
                email_verification_token=verification_token,
                email_verification_expires=verification_expiry
            )
            email_sent = email_service.send_verification_email(
                user.email, 
                user.full_name, 
                verification_token
            )
            verification_required = True
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": "User registered successfully." + (" Please check your email to verify your account." if verification_required else ""),
            "user_id": new_user.id,
            "status": new_user.status,
            "email_sent": email_sent,
            "verification_required": verification_required
        }
    
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            if error['type'] == 'value_error':
                error_details.append(error['msg'])
            else:
                error_details.append(f"{error['loc'][0]}: {error['msg']}")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Validation failed",
                "errors": error_details
            }
        )

@router.get("/verify-email/{token}", response_model=dict)
def verify_email_via_link(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email
    """
    user = db.query(User).filter(
        User.email_verification_token == token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    current_time = datetime.utcnow()
    if user.email_verification_expires and user.email_verification_expires.replace(tzinfo=None) < current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    user.status = UserStatus.ACTIVE
    user.email_verified = True
    user.user_status = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    db.commit()
    
    return {
        "message": "Email verified successfully",
        "status": user.status,
        "email_verified": True
    }

@router.post("/resend-verification", response_model=dict)
def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend verification email - user provides any email address
    
    This endpoint allows users to:
    1. Resend verification to their existing email (verified or not)
    2. Change to a new email and receive verification (status remains pending)
    
    Parameters:
    - email: Either their current registered email or a new email address
    """
    target_email = request.email

    existing_user_with_target_email = db.query(User).filter(User.email == target_email).first()
    
    if existing_user_with_target_email:
        verification_token = email_service.generate_verification_token()
        verification_expiry = email_service.get_verification_expiry()
        
        existing_user_with_target_email.email_verification_token = verification_token
        existing_user_with_target_email.email_verification_expires = verification_expiry

        if existing_user_with_target_email.status != UserStatus.PENDING:
            existing_user_with_target_email.status = UserStatus.ACTIVE
            existing_user_with_target_email.email_verified = True
            existing_user_with_target_email.user_status = True
        
        db.commit()
        
        email_sent = email_service.send_verification_email(
            target_email,
            existing_user_with_target_email.full_name,
            verification_token
        )
        
        return {
            "message": "Verification email sent successfully",
            "email_sent": email_sent,
            "target_email": target_email,
            "email_changed": False,
            "was_already_verified": existing_user_with_target_email.email_verified
        }
    else:
        pending_users = db.query(User).filter(User.status == UserStatus.PENDING).all()
        
        if not pending_users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending verification accounts found. Please register first."
            )

        if len(pending_users) == 1:

            user = pending_users[0]

            email_changed = user.email.lower() != target_email.lower()
            
            user.email = target_email
            verification_token = email_service.generate_verification_token()
            verification_expiry = email_service.get_verification_expiry()
            
            user.email_verification_token = verification_token
            user.email_verification_expires = verification_expiry
            user.status = UserStatus.PENDING  
            user.email_verified = False
            
            db.commit()
            db.refresh(user)
            
            email_sent = email_service.send_verification_email(
                target_email,
                user.full_name,
                verification_token
            )
            
            return {
                "message": f"Verification email sent to {target_email}",
                "email_sent": email_sent,
                "target_email": target_email,
                "email_changed": email_changed,
                "status": "pending"  
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multiple pending accounts found. Please contact support or try registering again."
            )

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.email not in settings.ADMIN_EMAILS:
        if user.status == UserStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    if user.status in [UserStatus.SUSPENDED, UserStatus.BANNED, UserStatus.DELETED]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value.lower()}. Contact support for assistance.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.patch("/users/{user_id}/status", response_model=dict)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """
    Update user status
    
    Available statuses:
    - PENDING: User registered but email not verified
    - ACTIVE: User active and can use the system
    - INACTIVE: User deactivated their account
    - SUSPENDED: Admin suspended the user
    - BANNED: User permanently banned
    - DELETED: Admin marked for deletion
    """
    user = get_user_or_404(db, user_id)
    old_status = user.status
    
    user.status = status_update.status

    if status_update.status == UserStatus.ACTIVE:
        user.user_status = True
    else:
        user.user_status = False
    
    db.commit()
    db.refresh(user)
    
    if old_status != status_update.status:
        email_service.send_status_change_email(
            user.email,
            user.full_name,
            status_update.status.value
        )
    
    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "old_status": old_status,
        "new_status": user.status,
        "updated_at": user.updated_at
    }

@router.patch("/users/{user_id}/deactivate", response_model=dict)
def deactivate_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate user's own account (User can deactivate their own account)
    """
    if current_user.id != user_id and not settings.is_admin_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only deactivate your own account"
        )
    
    user = get_user_or_404(db, user_id)
    
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already inactive"
        )
    
    user.status = UserStatus.INACTIVE
    user.user_status = False
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Account deactivated successfully",
        "user_id": user.id,
        "status": user.status
    }

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin)
):
    """
    Get user details 
    """
    user = get_user_or_404(db, user_id)
    return user

@router.get("/users", response_model=dict)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_check: bool = Depends(is_admin),
    page: int = 1,
    per_page: int = 10,
    status_filter: UserStatus = None
):
    """
    Get all users with pagination and filtering 
    """
    query = db.query(User)
    
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    total_count = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "users": [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "status": user.status,
                "email_verified": user.email_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            for user in users
        ],
        "page": page,
        "per_page": per_page,
        "total": total_count,
        "total_pages": (total_count + per_page - 1) // per_page
    }

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile
    """
    return current_user
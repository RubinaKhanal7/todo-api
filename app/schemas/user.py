from pydantic import BaseModel, EmailStr, field_validator
from app.config.validators import validate_password
from app.models.user import UserStatus
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    full_name: str
    email: EmailStr
    password: str
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        is_valid, errors = validate_password(v)
        if not is_valid:
            error_message = "Password validation failed: " + ", ".join(errors)
            raise ValueError(error_message)
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip() if v else None
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if v is not None:
            is_valid, errors = validate_password(v)
            if not is_valid:
                error_message = "Password validation failed: " + ", ".join(errors)
                raise ValueError(error_message)
        return v

class UserStatusUpdate(BaseModel):
    """Schema for updating user status"""
    status: UserStatus

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    full_name: str
    email: str
    status: UserStatus
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    token: str

class EmailVerificationToken(BaseModel):
    """Schema for email verification token in URL path"""
    token: str

    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        if not v or len(v) < 32:
            raise ValueError('Invalid verification token format')
        return v

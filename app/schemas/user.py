from pydantic import BaseModel, EmailStr, field_validator
from app.config.validators import validate_password
from fastapi import HTTPException, status

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
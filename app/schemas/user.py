from pydantic import BaseModel, EmailStr, field_validator

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

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
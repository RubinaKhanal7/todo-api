from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class TodoCreate(BaseModel):
    """Schema for creating a new todo"""
    full_name: str
    email: EmailStr
    task: str
    completed: bool = False
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()
    
    @field_validator('task')
    @classmethod
    def validate_task(cls, v):
        if not v or not v.strip():
            raise ValueError('Task cannot be empty')
        return v.strip()

class TodoUpdate(BaseModel):
    """Schema for updating a todo (all fields optional)"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    task: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    """Schema for todo response"""
    id: int
    user_id: int
    full_name: str
    email: str
    task: str
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
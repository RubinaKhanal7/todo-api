from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class TodoCreate(BaseModel):
    """Schema for creating a new todo"""
    task: str
    completed: bool = False
    
    @field_validator('task')
    @classmethod
    def validate_task(cls, v):
        if not v or not v.strip():
            raise ValueError('Task cannot be empty')
        return v.strip()

class TodoUpdate(BaseModel):
    """Schema for updating a todo"""
    task: Optional[str] = None
    completed: Optional[bool] = None
    
    @field_validator('task')
    @classmethod
    def validate_task(cls, v):
        if v is not None: 
            if not v.strip():
                raise ValueError('Task cannot be empty')
            return v.strip()
        return v

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
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
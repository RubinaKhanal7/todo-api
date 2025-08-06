from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.config.settings import settings

def get_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure current user is admin"""
    if not settings.is_admin_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def check_if_admin(current_user: User = Depends(get_current_user)):
    """Check if current user is admin (returns boolean)"""
    return settings.is_admin_email(current_user.email)
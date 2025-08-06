from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User

def get_user_or_404(db: Session, user_id: int) -> User:
    """
    Get user by ID or raise 404 if not found.
    
    Args:
        db: Database session
        user_id: ID of the user to retrieve
        
    Returns:
        User: User object if found
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

def get_user_by_email_or_404(db: Session, email: str) -> User:
    """
    Get user by email or raise 404 if not found.
    
    Args:
        db: Database session
        email: Email of the user to retrieve
        
    Returns:
        User: User object if found
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    return user
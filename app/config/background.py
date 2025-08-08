# app/config/background.py
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User, UserStatus
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

def cleanup_deleted_users():
    """
    Permanently deletes users with status=DELETED 
    where deleted_at is older than 30 days
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Get users to delete
        deleted_users = db.query(User).filter(
            User.status == UserStatus.DELETED,
            User.deleted_at <= cutoff_date
        ).all()
        
        if not deleted_users:
            logger.info("No deleted users older than 30 days found")
            return {"deleted_count": 0}

        # Delete each user
        for user in deleted_users:
            logger.info(f"Permanently deleting user {user.id} ({user.email})")
            db.delete(user)
        
        db.commit()
        logger.info(f"Permanently deleted {len(deleted_users)} users")
        return {"deleted_count": len(deleted_users)}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up deleted users: {str(e)}")
        raise
    finally:
        db.close()

def schedule_cleanup(background_tasks: BackgroundTasks):
    """Schedule the cleanup task to run in the background"""
    background_tasks.add_task(cleanup_deleted_users)
    return {"message": "Cleanup of deleted users scheduled"}
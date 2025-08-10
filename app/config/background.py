import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.todo import Todo

logger = logging.getLogger(__name__)

def get_expired_deleted_records(db: Session, model, months=6):
    """Get records deleted more than X months ago"""
    cutoff_date = datetime.utcnow() - timedelta(days=months*30) 
    return db.query(model).filter(
        model.deleted_at.isnot(None),
        model.deleted_at <= cutoff_date
    ).all()

def permanent_delete_expired_records():
    """Permanently delete users and todos deleted more than 6 months ago"""
    db = SessionLocal()
    try:
        expired_users = get_expired_deleted_records(db, User)
        for user in expired_users:
            db.delete(user)
            logger.info(f"Permanently deleted user {user.id} (deleted at {user.deleted_at})")

        expired_todos = get_expired_deleted_records(db, Todo)
        for todo in expired_todos:
            db.delete(todo)
            logger.info(f"Permanently deleted todo {todo.id} (deleted at {todo.deleted_at})")
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in permanent deletion task: {str(e)}")
    finally:
        db.close()
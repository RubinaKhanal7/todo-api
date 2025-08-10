import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User, UserStatus
from fastapi import BackgroundTasks

def get_deleted_users(db: Session):
    return db.query(User).filter(User.deleted_at.isnot(None)).all()
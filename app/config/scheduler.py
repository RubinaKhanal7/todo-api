from apscheduler.schedulers.background import BackgroundScheduler
from app.config.background import cleanup_deleted_users
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    """Start the background scheduler for periodic tasks"""
    scheduler = BackgroundScheduler()
    
    try:
        scheduler.add_job(
            cleanup_deleted_users,
            'cron',
            hour=0,
            minute=0,
            name="daily_deleted_users_cleanup"
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise
from fastapi import APIRouter, Depends, BackgroundTasks
from app.auth.dependencies import get_current_user, is_admin
from app.config.background import schedule_cleanup

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/cleanup-deleted-users")
def trigger_cleanup_deleted_users(
    background_tasks: BackgroundTasks,
    _=Depends(is_admin) 
):
    """
    Manually trigger cleanup of deleted users (status=DELETED and deleted_at > 30 days)
    """
    return schedule_cleanup(background_tasks)
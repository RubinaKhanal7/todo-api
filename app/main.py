from fastapi import FastAPI
from app.database.connection import create_tables
from app.api.routes import auth, todos  
from app.config.settings import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
try:
    create_tables()
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")
    raise

# FastAPI application
app = FastAPI(
    title="Todo API",
)

# Include routers
app.include_router(auth.router)
app.include_router(todos.router)

@app.get("/")
def read_root():
    """
    Welcome message with API information
    """
    return {
        "message": "Welcome to Todo API",
        "version": "1.1.0",
        "features": [
            "User Authentication", 
            "Password Validation", 
            "Todo Management",
            "Automatic User Cleanup"
        ],
        "password_requirements": {
            "minimum_length": 8,
            "must_contain": [
                "At least one uppercase letter (A-Z)",
                "At least one lowercase letter (a-z)", 
                "At least one digit (0-9)",
                "At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
            ]
        },
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout"
            },
            "todos": {
                "get_todos": "GET /todos",
                "create_todo": "POST /todos",
                "get_todo": "GET /todos/{id}",
                "update_todo": "PUT /todos/{id}",
                "delete_todo": "DELETE /todos/{id}"
            },
            "admin": {
                "cleanup_users": "POST /admin/cleanup-deleted-users",
                "scheduler_status": "GET /admin/scheduler-status"
            }
        }
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    print("Starting Todo API server with PostgreSQL...")
    print(f"Connecting to database at: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print("API Documentation will be available at: http://127.0.0.1:8000/docs")
    print("Daily user cleanup scheduled for midnight (00:00)")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
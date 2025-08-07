import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "todo_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "todo")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Admin Configuration
    ADMIN_EMAILS: list[str] = [
        "admin@example.com",
    ]

     # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "rubikhanal8@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "fntxemcolkmagbqo")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@example.com")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def is_admin_email(self, email: str) -> bool:
        """Check if an email belongs to admin"""
        return email in self.ADMIN_EMAILS

settings = Settings()
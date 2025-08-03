from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable echo=True for debugging SQL queries
engine = create_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=20,
    max_overflow=0
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready"""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except Exception as e:
            logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error("Database connection failed after all retries")
                raise
    return False

def create_tables():
    """Create all tables with explicit error handling and retry logic"""
    try:
        logger.info("Waiting for database to be ready...")
        wait_for_db()
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
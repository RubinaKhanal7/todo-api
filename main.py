from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, field_validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# PostgreSQL Database setup
POSTGRES_USER = os.getenv("POSTGRES_USER", "todo_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "todo")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# DATABASE MODELS
class User(Base):
    """User table to store user information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    todos = relationship("Todo", back_populates="owner")

class Todo(Base):
    """Todo table to store todo items"""
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    task = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="todos")

Base.metadata.create_all(bind=engine)

# PYDANTIC SCHEMAS (for data validation)
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    full_name: str
    email: EmailStr
    password: str
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class TodoCreate(BaseModel):
    """Schema for creating a new todo"""
    full_name: str
    email: EmailStr
    task: str
    completed: bool = False
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip()
    
    @field_validator('task')
    @classmethod
    def validate_task(cls, v):
        if not v or not v.strip():
            raise ValueError('Task cannot be empty')
        return v.strip()

class TodoUpdate(BaseModel):
    """Schema for updating a todo (all fields optional)"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    task: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    """Schema for todo response"""
    id: int
    user_id: int
    full_name: str
    email: str
    task: str
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str

# UTILITY FUNCTIONS
def get_db():
    """Get database session - this is a dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# FASTAPI APPLICATION
app = FastAPI(
    title="Simple Todo API"
)

# AUTHENTICATION ENDPOINTS
@app.post("/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **full_name**: User's full name (required, cannot be empty)
    - **email**: User's email address (required, must be valid email)
    - **password**: User's password (required)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/auth/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and get access token
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT token for authentication
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# TODO ENDPOINTS
@app.get("/todos", response_model=List[TodoResponse])
def get_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    per_page: int = 10
):
    """
    Get todos
    
    - page: Page number (starts from 1)
    - per_page: Items per page (default: 10)
    """
    todos = db.query(Todo)\
             .filter(Todo.user_id == current_user.id)\
             .offset((page - 1) * per_page)\
             .limit(per_page)\
             .all()
    
    return todos

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new todo
    
    - **full_name**: Person's full name (required, cannot be empty)
    - **email**: Person's email address (required, must be valid email)
    - **task**: Todo task description (required, cannot be empty)
    - **completed**: Whether task is completed (default: false)
    
    Requires authentication (Bearer token)
    """
    new_todo = Todo(
        user_id=current_user.id,
        full_name=todo.full_name,
        email=todo.email,
        task=todo.task,
        completed=todo.completed
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific todo by ID
    
    - **todo_id**: ID of the todo to retrieve
    
    Requires authentication (Bearer token)
    Users can only access their own todos
    """
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == current_user.id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a todo (partial update allowed)
    
    - **todo_id**: ID of the todo to update
    - **full_name**: New full name (optional)
    - **email**: New email address (optional)
    - **task**: New task description (optional)
    - **completed**: New completion status (optional)
    
    Requires authentication (Bearer token)
    Users can only update their own todos
    """
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == current_user.id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    # Update only provided fields
    update_data = todo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    db.commit()
    db.refresh(todo)
    return todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a todo
    
    - **todo_id**: ID of the todo to delete
    
    Requires authentication (Bearer token)
    Users can only delete their own todos
    """
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.user_id == current_user.id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    db.delete(todo)
    db.commit()
    return None

# ROOT ENDPOINT
@app.get("/")
def read_root():
    """
    Welcome message with API information
    """
    return {
        "message": "Welcome to Simple Todo API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login"
            },
            "todos": {
                "get_todos": "GET /todos",
                "create_todo": "POST /todos",
                "get_todo": "GET /todos/{id}",
                "update_todo": "PUT /todos/{id}",
                "delete_todo": "DELETE /todos/{id}"
            }
        }
    }

# RUN THE APPLICATION
if __name__ == "__main__":
    import uvicorn
    print("Starting Todo API server with PostgreSQL...")
    print(f"Connecting to database at: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print("API Documentation will be available at: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
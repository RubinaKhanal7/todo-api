from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.user import User
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/todos", tags=["Todos"])

@router.get("/", response_model=List[TodoResponse])
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

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
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

@router.get("/{todo_id}", response_model=TodoResponse)
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

@router.put("/{todo_id}", response_model=TodoResponse)
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

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
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
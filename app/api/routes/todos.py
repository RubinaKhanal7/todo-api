from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.user import User
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.auth.dependencies import get_current_user, is_admin

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
    try:
        admin_check = is_admin(current_user)
        query = db.query(Todo)
    except HTTPException:
        query = db.query(Todo).filter(Todo.user_id == current_user.id)
    
    todos = query.offset((page - 1) * per_page).limit(per_page).all()
    return todos

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new todo
    - **task**: Todo task description (required, cannot be empty)
    - **completed**: Whether task is completed (default: false)
    """
    new_todo = Todo(
        user_id=current_user.id,
        full_name=current_user.full_name, 
        email=current_user.email,         
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
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    try:
        is_admin(current_user)
    except HTTPException:
        if todo.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this todo"
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
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    try:
        is_admin(current_user)

    except HTTPException:
        if todo.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this todo"
            )
    
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
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    try:
        is_admin(current_user)
    except HTTPException:
        if todo.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this todo"
            )
    
    db.delete(todo)
    db.commit()
    return None
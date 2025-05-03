from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, Todo as TodoSchema

router = APIRouter()
logger = logging.getLogger(__name__)


class TodoUpdateStatus(BaseModel):
    completed: bool


@router.post("/todos/", response_model=TodoSchema, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_todo = Todo(**todo.model_dump(), user_id=current_user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.get("/todos/", response_model=List[TodoSchema])
def read_todos(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Todo).filter(Todo.user_id == current_user.id).all()


@router.get("/todos/{todo_id}", response_model=TodoSchema)
def read_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/todos/{todo_id}", response_model=TodoSchema)
async def update_todo(
    todo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 요청 본문을 로깅
    body = await request.body()
    logger.debug(f"Request body: {body}")

    # 요청 헤더를 로깅
    logger.debug(f"Request headers: {request.headers}")

    try:
        data = await request.json()
        logger.debug(f"Parsed JSON data: {data}")
        todo_update = TodoUpdateStatus(**data)
    except Exception as e:
        logger.error(f"Error parsing request data: {e}")
        raise HTTPException(status_code=422, detail="Invalid request data")

    db_todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db_todo.completed = todo_update.completed
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.user_id == current_user.id)
        .first()
    )
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
    return None

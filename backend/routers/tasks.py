from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task_in: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = models.Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=List[schemas.TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    tasks = (
        db.query(models.Task)
        .filter(models.Task.enabled.is_(True))
        .order_by(models.Task.name)
        .all()
    )
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.TaskRead)
def update_task(task_id: int, task_in: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field, value in task_in.model_dump().items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Soft delete: mark as disabled so historical data can remain intact
    task.enabled = False
    db.commit()
    return None

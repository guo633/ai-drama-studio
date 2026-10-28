from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import GenerationTask, User
from ..schemas import TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """前端轮询此接口获取生成进度与结果。"""
    task = db.get(GenerationTask, task_id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    if task.drama.owner_id != user.id:
        raise HTTPException(404, "任务不存在")
    return task

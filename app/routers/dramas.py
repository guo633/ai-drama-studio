import asyncio
import threading

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Drama, GenerationTask, User
from ..pipeline import run_pipeline
from ..prompts import PIPELINE_STEPS
from ..schemas import DramaCreateIn, DramaDetailOut, DramaOut
from ..settings import get_runtime_settings

router = APIRouter(prefix="/api/dramas", tags=["dramas"])

# 剧本成品的组装顺序（导出用）
EXPORT_ORDER = [s["key"] for s in PIPELINE_STEPS]
EXPORT_TITLES = {s["key"]: s["name"] for s in PIPELINE_STEPS}


def _get_owned_drama(drama_id: int, user: User, db: Session) -> Drama:
    drama = db.get(Drama, drama_id)
    if drama is None or drama.owner_id != user.id:
        raise HTTPException(404, "作品不存在")
    return drama


@router.get("/runtime")
def runtime_info():
    """公开的运行时信息，供前端展示当前使用的是真实模型还是演示模式。"""
    rt = get_runtime_settings()
    return {"model": rt.model, "mode": rt.mode}


@router.post("", response_model=DramaDetailOut)
def create_drama(
    body: DramaCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建作品并立即启动生成流水线。

    注意：这里用 threading.Thread 而不是 BackgroundTasks —— 后者在响应发出后才执行，
    真实 LLM 五步生成可能耗时 1-3 分钟，会拖住连接并可能被云平台网关超时切断。
    """
    drama = Drama(
        owner_id=user.id,
        title=body.title,
        idea=body.idea,
        genre=body.genre,
        style=body.style,
        episode_count=body.episode_count,
        status="generating",
    )
    db.add(drama)
    db.commit()
    db.refresh(drama)

    task = GenerationTask(drama_id=drama.id, status="queued")
    db.add(task)
    db.commit()
    db.refresh(task)

    # daemon 线程：主进程退出即回收，不阻塞 worker
    threading.Thread(
        target=lambda: asyncio.run(run_pipeline(drama.id, task.id)),
        daemon=True,
    ).start()

    out = DramaDetailOut.model_validate(drama)
    out.latest_task_id = task.id
    return out


@router.get("", response_model=list[DramaOut])
def list_dramas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Drama)
        .filter_by(owner_id=user.id)
        .order_by(Drama.created_at.desc())
        .all()
    )


@router.get("/{drama_id}", response_model=DramaDetailOut)
def get_drama(drama_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drama = _get_owned_drama(drama_id, user, db)
    latest = (
        db.query(GenerationTask)
        .filter_by(drama_id=drama.id)
        .order_by(GenerationTask.id.desc())
        .first()
    )
    out = DramaDetailOut.model_validate(drama)
    out.latest_task_id = latest.id if latest else None
    return out


@router.delete("/{drama_id}")
def delete_drama(drama_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drama = _get_owned_drama(drama_id, user, db)
    db.query(GenerationTask).filter_by(drama_id=drama.id).delete()
    db.delete(drama)
    db.commit()
    return {"ok": True}


@router.get("/{drama_id}/export", response_class=PlainTextResponse)
def export_drama(drama_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """把流水线各阶段产出合并为一份完整策划案文本。"""
    drama = _get_owned_drama(drama_id, user, db)
    latest = (
        db.query(GenerationTask)
        .filter_by(drama_id=drama.id, status="done")
        .order_by(GenerationTask.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(400, "该作品尚未生成完成，无法导出")

    lines = [f"《{drama.title}》短剧创作方案", f"题材：{drama.genre} | 风格：{drama.style} | 集数：{drama.episode_count}", ""]
    for key in EXPORT_ORDER:
        content = (latest.result or {}).get(key)
        if content:
            lines += ["=" * 40, EXPORT_TITLES[key], "=" * 40, content, ""]
    return "\n".join(lines)

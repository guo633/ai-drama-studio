from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import PromptTemplate, User
from ..schemas import PromptOut, PromptUpdateIn

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptOut])
def list_prompts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """列出全部 Prompt 模板（即项目内的可编辑 Skill）。"""
    return db.query(PromptTemplate).order_by(PromptTemplate.id).all()


@router.put("/{step}", response_model=PromptOut)
def update_prompt(
    step: str,
    body: PromptUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改模板后立即生效，下一次生成即使用新版本。"""
    tpl = db.query(PromptTemplate).filter_by(step=step).first()
    if tpl is None:
        raise HTTPException(404, "模板不存在")
    tpl.content = body.content
    db.commit()
    db.refresh(tpl)
    return tpl

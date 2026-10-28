"""运行时设置接口：查看当前模型状态、自检连通性、在线切换 API Key。

密钥安全：接口只返回打码后的 Key（sk-abc...wxyz），任何情况下不回显明文；
更新只在进程内存生效，不落库、不写日志。首次登录的用户即为管理员。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..llm import verify_connection
from ..models import User
from ..schemas import SettingsIn
from ..settings import get_runtime_settings, update_runtime_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


def require_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """仅允许最早注册的用户（管理员）修改全局生效的模型配置。"""
    first = db.query(User).order_by(User.id).first()
    if first is None or first.id != user.id:
        raise HTTPException(403, "仅管理员可修改模型配置")
    return user


def _snapshot() -> dict:
    rt = get_runtime_settings()
    return {
        "mode": rt.mode,
        "configured": rt.configured,
        "model": rt.model,
        "base_url": rt.base_url,
        "api_key_masked": rt.masked_key,
    }


@router.get("")
def read_settings(user: User = Depends(get_current_user)):
    return _snapshot()


@router.post("/llm")
def set_llm(
    body: SettingsIn,
    user: User = Depends(require_admin),
):
    """更新 LLM 凭据，立即生效。"""
    updater = {k: v for k, v in body.model_dump().items() if v}
    if not updater:
        raise HTTPException(400, "至少填写一项")
    update_runtime_settings(**updater)
    return _snapshot()


@router.post("/verify")
async def verify(user: User = Depends(require_admin)):
    """用最小请求验证 Key / BaseURL / 模型名是否真的可用。"""
    return await verify_connection()

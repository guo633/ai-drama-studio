"""生成流水线：按 5 步串联 Prompt，每步产出注入下一步上下文。"""
import logging

from .database import SessionLocal
from .llm import chat
from .models import Drama, GenerationTask, PromptTemplate
from .prompts import PIPELINE_STEPS

logger = logging.getLogger(__name__)


def _render(template: str, context: dict) -> str:
    """模板变量插值；缺失变量以空串兜底，避免整体报错。"""
    class _SafeDict(dict):
        def __missing__(self, key):
            return ""

    return template.format_map(_SafeDict(context))


async def run_pipeline(drama_id: int, task_id: int) -> None:
    """后台执行完整流水线。独立开数据库会话，不依赖请求生命周期。"""
    db = SessionLocal()
    try:
        task = db.get(GenerationTask, task_id)
        drama = db.get(Drama, drama_id)
        if task is None or drama is None:
            return

        task.status = "running"
        drama.status = "generating"
        db.commit()

        context = {
            "title": drama.title,
            "idea": drama.idea,
            "genre": drama.genre,
            "style": drama.style,
            "episode_count": drama.episode_count,
        }

        total = len(PIPELINE_STEPS)
        for index, step in enumerate(PIPELINE_STEPS):
            key, name = step["key"], step["name"]
            task.current_step = name
            db.commit()

            tpl = db.query(PromptTemplate).filter_by(step=key).first()
            if tpl is None:
                raise RuntimeError(f"缺少 Prompt 模板：{key}")
            prompt = _render(tpl.content, {**context, "_step": key})

            output = await chat(prompt, mock_context={**context, "_step": key})
            context[key] = output
            task.result = {**task.result, key: output}
            task.progress = int((index + 1) / total * 100)
            db.commit()

        task.status = "done"
        task.current_step = "完成"
        drama.status = "done"
        db.commit()
        logger.info("drama %s pipeline done", drama_id)

    except Exception as exc:  # noqa: BLE001 —— 流水线任何失败都要落库，便于前端展示
        logger.exception("pipeline failed for drama %s", drama_id)
        db.rollback()
        task = db.get(GenerationTask, task_id)
        if task:
            task.status = "failed"
            task.error = str(exc)[:500]
            db.commit()
        drama = db.get(Drama, drama_id)
        if drama:
            drama.status = "failed"
            db.commit()
    finally:
        db.close()

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .database import Base, SessionLocal, engine
from .models import PromptTemplate
from .prompts import DEFAULT_TEMPLATES
from .routers import auth_router, dramas, prompts, settings_router, tasks
from .settings import get_runtime_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表 + 首次启动时播种默认 Prompt 模板
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        for step, tpl in DEFAULT_TEMPLATES.items():
            exists = db.query(PromptTemplate).filter_by(step=step).first()
            if exists is None:
                db.add(PromptTemplate(step=step, name=tpl["name"], content=tpl["content"]))
        db.commit()
    finally:
        db.close()

    rt = get_runtime_settings()
    logger.info("AI Drama Studio 启动 | 环境=%s | 模型模式=%s(%s)",
                config.APP_ENV, rt.mode, rt.model)
    yield


app = FastAPI(title="AI Drama Studio", version="1.0.0", lifespan=lifespan)


@app.get("/healthz", include_in_schema=False)
def healthz():
    """云平台健康检查端点。"""
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(dramas.router)
app.include_router(tasks.router)
app.include_router(prompts.router)
app.include_router(settings_router.router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

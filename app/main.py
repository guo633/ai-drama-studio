import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, SessionLocal, engine
from .models import PromptTemplate
from .prompts import DEFAULT_TEMPLATES
from .routers import auth_router, dramas, prompts, tasks

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Drama Studio", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.on_event("startup")
def startup():
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


app.include_router(auth_router.router)
app.include_router(dramas.router)
app.include_router(tasks.router)
app.include_router(prompts.router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now():
    return datetime.now()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    dramas: Mapped[list["Drama"]] = relationship(back_populates="owner")


class Drama(Base):
    """一部短剧作品：用户输入创意 → 流水线生成各阶段内容"""
    __tablename__ = "dramas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    idea: Mapped[str] = mapped_column(Text)          # 一句话创意
    genre: Mapped[str] = mapped_column(String(50), default="都市")   # 题材
    style: Mapped[str] = mapped_column(String(100), default="爽剧")  # 风格
    episode_count: Mapped[int] = mapped_column(Integer, default=10)  # 集数
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft -> generating -> done / failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="dramas")
    tasks: Mapped[list["GenerationTask"]] = relationship(back_populates="drama")


class GenerationTask(Base):
    """一次生成任务：按 5 个步骤推进，结果逐段累积在 result 中"""
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drama_id: Mapped[int] = mapped_column(ForeignKey("dramas.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued -> running -> done / failed
    current_step: Mapped[str] = mapped_column(String(50), default="")
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0~100
    error: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[dict] = mapped_column(JSON, default=dict)   # {"world_view": "...", ...}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    drama: Mapped["Drama"] = relationship(back_populates="tasks")


class PromptTemplate(Base):
    """Prompt 模板（可视为项目内 Skill）：按步骤存储，支持变量插值"""
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    step: Mapped[str] = mapped_column(String(50), unique=True)  # world_view 等
    name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

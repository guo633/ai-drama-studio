from pydantic import BaseModel, Field


# ---------- Auth ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    username: str


class MeOut(BaseModel):
    id: int
    username: str


# ---------- Drama ----------
class DramaCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    idea: str = Field(min_length=2, max_length=1000)
    genre: str = "都市"
    style: str = "爽剧"
    episode_count: int = Field(default=10, ge=1, le=100)


class DramaOut(BaseModel):
    id: int
    title: str
    idea: str
    genre: str
    style: str
    episode_count: int
    status: str

    model_config = {"from_attributes": True}


class DramaDetailOut(DramaOut):
    latest_task_id: int | None = None


# ---------- Task ----------
class TaskOut(BaseModel):
    id: int
    drama_id: int
    status: str
    current_step: str
    progress: int
    error: str
    result: dict

    model_config = {"from_attributes": True}


# ---------- Prompt ----------
class PromptOut(BaseModel):
    step: str
    name: str
    content: str

    model_config = {"from_attributes": True}


class PromptUpdateIn(BaseModel):
    content: str = Field(min_length=10)

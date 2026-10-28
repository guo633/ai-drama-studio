import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 安全 ----
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-do-not-use-in-prod")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72

# ---- 数据库 ----
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "drama.db"))

# ---- LLM（OpenAI 兼容接口）----
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TIMEOUT = 120  # 秒，剧本生成长文本需要较长超时

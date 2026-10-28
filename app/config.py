import os

from .settings import resolve_secret_key

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 安全 ----
SECRET_KEY = resolve_secret_key()
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72

# ---- 数据库 ----
# 云平台若有持久磁盘，可把 DATABASE_URL 指向挂载路径（如 sqlite:////data/drama.db）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "drama.db"))

# ---- LLM ----
# 凭据统一走 app.settings（支持运行时热更新），这里仅保留超时等静态参数
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))  # 秒，剧本生成长文本需要较长超时

# ---- 部署 ----
PORT = int(os.getenv("PORT", "8000"))  # Render/Railway 等平台会注入 PORT
APP_ENV = os.getenv("APP_ENV", "development")

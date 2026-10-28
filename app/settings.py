"""运行时配置：从环境变量读取 LLM 凭据，支持运行中热更新。

线上部署时在平台的环境变量里配置 LLM_API_KEY 即可，无需改代码；
也可以通过 /api/settings 在运行时更新（仅保存在进程内存，重启后回到环境变量值）。
"""
import os
import secrets
from dataclasses import dataclass

DEFAULT_SECRET = "dev-secret-do-not-use-in-prod-please-change-me-32b"


@dataclass
class RuntimeSettings:
    api_key: str
    base_url: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def mode(self) -> str:
        return "live" if self.configured else "demo"

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 10:
            return "*" * len(self.api_key)
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"


_settings = RuntimeSettings(
    api_key=os.getenv("LLM_API_KEY", "").strip(),
    base_url=(os.getenv("LLM_BASE_URL") or "https://api.deepseek.com/v1").strip(),
    model=(os.getenv("LLM_MODEL") or "deepseek-chat").strip(),
)


def get_runtime_settings() -> RuntimeSettings:
    return _settings


def update_runtime_settings(api_key: str | None = None, base_url: str | None = None,
                            model: str | None = None) -> RuntimeSettings:
    if api_key is not None:
        _settings.api_key = api_key.strip()
    if base_url:
        _settings.base_url = base_url.strip()
    if model:
        _settings.model = model.strip()
    return _settings


def resolve_secret_key() -> str:
    """生产环境若未设置 SECRET_KEY，则生成随机值并告警（避免使用公开的默认密钥）。"""
    value = os.getenv("SECRET_KEY", "").strip()
    if value and value != DEFAULT_SECRET:
        return value
    if os.getenv("APP_ENV", "").lower() == "production":
        # 随机密钥意味着重启后所有登录态失效，但绝不能用默认值上线
        import logging
        logging.getLogger(__name__).warning(
            "SECRET_KEY 未配置，已生成临时随机密钥；重启后用户需重新登录。请在环境变量中设置 SECRET_KEY。"
        )
        return secrets.token_hex(32)
    return DEFAULT_SECRET

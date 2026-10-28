"""LLM 客户端：OpenAI 兼容接口（DeepSeek / 通义 / Kimi / OpenAI 等均可）。

凭据来自 app.settings 的运行时配置：
- 已配置 API Key → 调用真实模型
- 未配置       → 演示模式，返回确定性示例文案（流程完整跑通、不产生任何费用）
"""
import logging

import httpx

from . import config
from .settings import get_runtime_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位资深的短剧编剧，擅长微短剧（竖屏付费短剧）创作。"
    "输出使用简体中文，结构清晰，直接给结果，不要复述要求。"
)


async def _call_llm(prompt: str) -> str:
    """真正发起请求，失败时抛出可读异常（不降级）。"""
    rt = get_runtime_settings()
    payload = {
        "model": rt.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
    }
    headers = {"Authorization": f"Bearer {rt.api_key}"}
    url = rt.base_url.rstrip("/") + "/chat/completions"

    async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(_friendly_error(resp.status_code, resp.text))
        data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"模型返回格式异常：{str(data)[:150]}") from exc


async def chat(prompt: str, mock_context: dict | None = None) -> str:
    """调用 LLM 生成文本。未配置 Key 时返回演示文案。

    配置了 Key 但调用失败（余额不足 / 网络异常 / 模型名错误）时：
    若开启 LLM_FALLBACK_DEMO（默认开启），降级为演示文案并在开头标注原因，
    保证线上 Demo 不会因凭据问题中断整条流水线。
    """
    rt = get_runtime_settings()
    if not rt.configured:
        return _mock_reply(mock_context or {})

    try:
        return await _call_llm(prompt)
    except Exception as exc:  # noqa: BLE001
        if config.LLM_FALLBACK_DEMO:
            logger.warning("LLM 调用失败，降级为演示文案：%s", exc)
            return (
                f"⚠️ 模型调用失败（{exc}），本条为演示文案。\n\n"
                + _mock_reply(mock_context or {})
            )
        raise


def _friendly_error(status_code: int, text: str) -> str:
    """把上游错误翻译成人能看懂、能直接照做的提示。"""
    low = text.lower()
    if "insufficient balance" in low or "quota" in low or "balanc" in low:
        return "模型账户余额不足，请充值或更换 API Key"
    if status_code in (401, 403):
        return "API Key 无效或无权限，请在「模型设置」中检查"
    if status_code == 404:
        return "接口地址或模型名不存在，请检查 Base URL 与模型名"
    if status_code == 429:
        return "请求过于频繁或超出限额，请稍后重试"
    return f"模型接口返回 {status_code}：{text[:150]}"


async def verify_connection() -> dict:
    """连通性自检：绕过降级逻辑直接探测，确保错误如实暴露。"""
    rt = get_runtime_settings()
    if not rt.configured:
        return {"ok": True, "mode": "demo", "message": "未配置 API Key，当前为演示模式"}
    try:
        reply = await _call_llm("只回复两个字符：OK")
        return {"ok": True, "mode": "live", "model": rt.model, "reply": reply[:50]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "mode": "live", "model": rt.model, "message": str(exc)[:300]}


# ---------- 演示模式 ----------


def _mock_reply(ctx: dict) -> str:
    title = ctx.get("title", "未命名短剧")
    genre = ctx.get("genre", "都市")
    step = ctx.get("_step", "")
    episodes = ctx.get("episode_count", 10)

    samples = {
        "world_view": (
            f"【演示模式】《{title}》世界观设定（{genre}）\n\n"
            "一、时代与地点：故事发生在当代一线城市，围绕主角的生活半径展开。\n"
            "二、核心设定：主角隐藏的真实身份与当前处境形成强烈反差。\n"
            "三、规则：身份揭露前，主角只能用普通人的方式解决问题；\n"
            "每次出手都点到为止，冲突层层升级。\n"
            "四、基调：节奏快、反转密，每集结尾留钩子。"
        ),
        "characters": (
            "【演示模式】人物卡\n\n"
            "1. 主角（男/女，25-30）：表面落魄，实则深藏不露。动机：守护在意的人。\n"
            "   成长弧线：从隐忍到觉醒，最终掌控局面。\n"
            "2. 对手（35+）：仗势欺人的反派，制造前 8 集的主要冲突。\n"
            "3. 关键配角：主角的暗中助力，负责在关键时刻递信息、给道具。"
        ),
        "outline": (
            f"【演示模式】分集大纲（共 {episodes} 集）\n\n"
            "第1集：主角受辱，埋下身份悬念 —— 钩子：神秘来电。\n"
            "第2集：小试身手，打脸第一个反派爪牙。\n"
            f"第3-{max(3, episodes - 3)}集：冲突升级，误会与反转交替推进。\n"
            f"第{episodes - 2}集：身份即将暴露，危机到达顶点。\n"
            f"第{episodes}集：大反转 + 身份揭露，情绪拉满收官。"
        ),
        "script": (
            "【演示模式】第 1 集剧本（节选）\n\n"
            "场1 日 外 城中村巷口\n"
            "△ 主角提着旧包走过，被一群人拦住。\n"
            "反派爪牙：把东西交出来，别逼我们动手。\n"
            "主角（抬眼，平静）：三秒之内，你们会自己道歉。\n"
            "△ 众人哄笑。三秒后，一辆黑色轿车停下……\n"
            "钩子：主角手机亮起，备注『老爷子』的来电。"
        ),
        "storyboard": (
            "【演示模式】分镜与 AI 视频提示词（第 1 集开篇）\n\n"
            "镜头1：竖屏 9:16，低角度拍主角背影，雨后巷口，电影感冷色调。\n"
            "  AI 视频提示词：cinematic vertical shot, rainy alley, moody lighting, 9:16。\n"
            "镜头2：面部特写，主角眼神从平静转为锐利。\n"
            "镜头3：黑色轿车入画，低机位车轮特写，配重低音鼓点。"
        ),
    }
    return samples.get(step, "【演示模式】生成完成。")

# 🎬 AI Drama Studio — 短剧创作工作台

一句话创意 → 世界观 → 人物卡 → 分集大纲 → 第 1 集剧本 → 分镜与 AI 视频提示词，
五步 Prompt 流水线自动生成一部竖屏短剧的完整创作方案。

> 技术栈：FastAPI + SQLAlchemy + SQLite + JWT + 原生 HTML/JS（无前端构建依赖）
> LLM：任意 OpenAI 兼容接口（DeepSeek / 通义 / Kimi 等），未配置 Key 时自动进入演示模式

## ✨ 核心特性

- **五步生成流水线**：每一步的产出自动注入下一步上下文，像链条一样环环相扣
- **Prompt 即 Skill**：所有 Prompt 模板存数据库，前端可视化编辑，保存后下一次生成即时生效
- **异步任务 + 进度轮询**：后台生成不阻塞请求，前端 2 秒轮询实时展示进度与分步结果
- **演示模式**：不配 API Key 也能完整跑通全流程（返回演示文案），方便面试 Demo 与开发调试
- **一键导出**：生成完成后导出带分节标题的完整创作方案 .txt
- **JWT 认证 + 数据隔离**：注册/登录，作品与任务按用户隔离

## 🚀 快速启动

```bash
# 1. 安装依赖（建议 venv）
pip install -r requirements.txt

# 2. （可选）配置 LLM：复制 .env.example 为 .env，填入 LLM_API_KEY
#    不配置则运行在演示模式

# 3. 启动
uvicorn app.main:app --reload --port 8000

# 4. 打开 http://127.0.0.1:8000 注册账号，新建一部短剧
```

首次启动自动建表并播种默认 Prompt 模板，数据库为项目根目录下的 `drama.db`。

## 📁 目录结构

```
ai-drama-studio/
├── app/
│   ├── main.py          # 应用入口：建表、播种模板、挂载路由与静态页
│   ├── config.py        # 配置（SECRET_KEY / LLM / DB）
│   ├── database.py      # SQLAlchemy 引擎与会话
│   ├── models.py        # User / Drama / GenerationTask / PromptTemplate
│   ├── schemas.py       # Pydantic 入参出参
│   ├── auth.py          # PBKDF2 密码哈希 + JWT
│   ├── llm.py           # OpenAI 兼容客户端 + 演示模式
│   ├── pipeline.py      # 五步生成流水线（后台任务）
│   ├── prompts/
│   │   └── __init__.py  # 默认 Prompt 模板（项目内置 Skill 包）
│   └── routers/
│       ├── auth_router.py   # /api/auth    注册、登录、me
│       ├── dramas.py        # /api/dramas  创建（触发生成）、列表、详情、删除、导出
│       ├── tasks.py         # /api/tasks   任务进度轮询
│       └── prompts.py       # /api/prompts 模板查看与编辑
├── static/index.html    # 单页前端（登录/作品/新建/详情/模板编辑）
├── docs/
│   ├── PROMPT_DESIGN.md # Prompt 流水线设计文档
│   └── AI_DEV_CASE.md   # AI 辅助开发案例（简历投递附录用）
└── requirements.txt
```

## 🔌 API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| POST | /api/dramas | 创建短剧并后台启动流水线 |
| GET | /api/dramas | 我的作品列表 |
| GET | /api/dramas/{id} | 作品详情（含最新任务 id） |
| DELETE | /api/dramas/{id} | 删除作品 |
| GET | /api/dramas/{id}/export | 导出完整创作方案 txt |
| GET | /api/tasks/{id} | 任务进度与结果（前端轮询） |
| GET/PUT | /api/prompts[/{step}] | Prompt 模板查看 / 编辑 |

## 🧠 「Prompt 即 Skill」的设计

每个流水线步骤对应一条数据库模板，支持 `{变量}` 插值：
`{title} {idea} {genre} {style} {episode_count} {world_view} {characters} {outline} {script}`。
用户在前端改模板 → 保存 → 下一次生成即用新模板，无需重启服务。
详见 `docs/PROMPT_DESIGN.md`。

## ☁️ 上线建议

- 免费部署：Render / Railway / fly.io（SQLite 单文件足够 MVP）
- 上线前：修改 `SECRET_KEY`，配置真实 `LLM_API_KEY`
- 简历投递时附：GitHub 仓库 + 在线 Demo 链接 + `docs/AI_DEV_CASE.md`

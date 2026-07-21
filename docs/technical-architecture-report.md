# Pavo AI Agent — 技术架构报告

> 版本 2.3.0 | 生成日期: 2026-07-13

---

## 一、项目概览

**Pavo AI Agent** 是一个 AI 驱动的视频分镜生成平台。输入自然语言故事，经 7 个专用 AI 智能体协作，自动输出逐镜头的专业分镜剧本（角色、场景、道具、分镜表），支持 MCP 协议集成。

| 维度 | 详情 |
|---|---|
| 项目名称 | Pavo AI Agent |
| 当前版本 | v2.3.0 |
| Python 版本 | >= 3.10 |
| 许可证 | 未指定（开源） |
| 设计哲学 | **零外部依赖** — SQLite 替代 PostgreSQL, TTLCache 替代 Redis, asyncio.Queue 替代 Celery, 本地文件替代 MinIO |

---

## 二、总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户接入层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Cursor/MCP  │  │ Claude Code  │  │  Web 浏览器   │           │
│  │  (MCP Client) │  │ (MCP Client) │  │ (Next.js)    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                   │
├─────────┼─────────────────┼─────────────────┼───────────────────┤
│         ▼                 ▼                 │                   │
│  ┌──────────────────────┐                   │                   │
│  │   MCP Server (stdio) │                   │                   │
│  │   · 12 Tools         │                   │                   │
│  │   · 5 Resources     │    ┌───────────────┘                   │
│  │   · 2 Prompts       │    │  HTTP API                         │
│  └──────────┬───────────┘    ▼                                  │
│             │         ┌──────────────┐                          │
│             │         │  FastAPI     │                          │
│             │         │  (uvicorn)   │                          │
│             │         │  port 18080  │                          │
│             │         └──────┬───────┘                          │
│             │                │                                  │
├─────────────┼────────────────┼──────────────────────────────────┤
│             ▼                ▼                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              ProjectService (核心编排层)                │       │
│  │    run_workflow() — 串行调度 7 个 Agent               │       │
│  └────┬────┬────┬────┬────┬────┬────┬────┬─────────────┘       │
│       │    │    │    │    │    │    │    │                      │
│       ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼                       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                7 Agent 管线                            │       │
│  │  Planner → Character → Scene → Prop → Storyboard      │       │
│  │                                → Reviewer → Fixer     │       │
│  └──────────────────────────────────────────────────────┘       │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌─────────────┐     ┌──────────────────────┐                   │
│  │  Memory 层   │     │    RAG 知识库         │                   │
│  │  · 长期记忆   │     │  · 影视专业知识 60+条  │                   │
│  │  · 会话上下文 │     │  · 向量搜索 + 重排序   │                   │
│  └─────────────┘     └──────────────────────┘                   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                     基础设施层                                     │
│  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐       │
│  │ SQLite   │  │TTLCache│  │asyncio   │  │本地文件系统    │       │
│  │ +sqlite- │  │(内存)  │  │.Queue    │  │~/.pavo/      │       │
│  │ vec      │  │        │  │(任务队列) │  │storage/      │       │
│  └──────────┘  └────────┘  └──────────┘  └──────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────┐                    │
│  │  Agnes AI API (外部) — 统一模型网关        │                    │
│  │  Chat: agnes-2.0-flash                    │                    │
│  │  Video: agnes-video-v2.0                  │                    │
│  └──────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
pavo-ai-work/
├── pyproject.toml              # 项目元数据、入口点声明
├── README.md / README_EN.md    # 中英文项目说明
├── docker-compose.yml          # 仅作参考（不再需要）
│
├── backend/                    # Python 后端
│   ├── app/                    # 核心应用层
│   │   ├── __init__.py
│   │   ├── config.py           # pydantic-settings 配置管理
│   │   ├── main.py             # FastAPI 入口 + CLI (pavo-start)
│   │   │
│   │   ├── agents/             # 7 个 AI Agent
│   │   │   ├── base.py         # 基类: LLM 调用封装
│   │   │   ├── planner.py      # [Agent 1] 故事分析
│   │   │   ├── character_agent.py  # [Agent 2] 角色设计
│   │   │   ├── scene_agent.py      # [Agent 3] 场景设计
│   │   │   ├── prop_agent.py       # [Agent 4] 道具设计
│   │   │   ├── storyboard_agent.py # [Agent 5] 分镜生成
│   │   │   ├── reviewer.py         # [Agent 6] 质量审查
│   │   │   └── fixer.py            # [Agent 7] 自动修复
│   │   │
│   │   ├── api/
│   │   │   └── routes.py       # FastAPI REST 路由 (17 个端点)
│   │   │
│   │   ├── db/
│   │   │   ├── database.py     # SQLAlchemy 引擎 + 表定义
│   │   │   └── migrations/     # Alembic 迁移文件
│   │   │
│   │   ├── models/
│   │   │   ├── project.py      # ORM 模型: Project, VersionHistory, Feedback
│   │   │   └── schema.py       # Pydantic 验证模型
│   │   │
│   │   └── services/
│   │       ├── agnes_client.py     # Agnes AI API 客户端 (httpx)
│   │       ├── auth.py             # Token 认证
│   │       ├── cache.py            # TTLCache 内存缓存
│   │       ├── project_service.py  # 核心业务编排
│   │       ├── storage.py          # 本地文件存储
│   │       ├── task_queue.py       # asyncio.Queue 任务队列
│   │       ├── video_tasks.py      # 视频生成任务
│   │       └── export/             # 导出模块
│   │           ├── markdown.py     # Markdown/脚本导出
│   │           └── pdf.py          # PDF 导出
│   │
│   ├── mcp_server/              # MCP 协议层
│   │   ├── main.py              # MCP Server 入口 (12 Tools, 5 Resources, 2 Prompts)
│   │   ├── adapter/             # 适配器层
│   │   │   └── project_adapter.py   # 桥接 MCP ↔ ProjectService
│   │   ├── memory/              # 记忆系统
│   │   │   ├── interfaces.py    #   MemoryProvider 抽象接口
│   │   │   ├── store.py         #   SQLAlchemy 记忆存储 + 会话管理
│   │   │   ├── embedding_client.py # 向量嵌入客户端
│   │   │   └── importance.py    #   重要性评分策略
│   │   ├── middleware/
│   │   │   └── memory_middleware.py # 自动记忆注入中间件
│   │   ├── models/
│   │   │   └── mcp_schemas.py   #   MCP 响应模型
│   │   ├── rag/                 # RAG 知识库
│   │   │   ├── interfaces.py    #   RAGProvider 抽象接口
│   │   │   ├── retriever.py     #   向量检索 + 多级重排序
│   │   │   ├── builder.py       #   知识库构建器
│   │   │   └── knowledge_base/  #   影视专业知识文件
│   │   │       └── film_knowledge.md
│   │   ├── tools/
│   │   │   ├── guards.py        #   API Key 安全检查
│   │   │   └── memory_tools.py  #   记忆 CRUD 工具
│   │   └── prompts/             # MCP Prompts
│   │
│   └── tests/                   # 测试套件 (18 个测试文件)
│       ├── test_api.py
│       ├── test_e2e.py
│       ├── test_mcp_server/
│       └── ...
│
├── frontend/                    # Next.js 前端
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── WorkflowVisualizer.tsx  # SVG 管线可视化
│   │   │   ├── Timeline.tsx            # 时间线组件
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── PreviewPanel.tsx
│   │   │   ├── VideoPanel.tsx
│   │   │   ├── AuthGuard.tsx
│   │   │   ├── SortableShot.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── ConfirmDialog.tsx
│   │   ├── lib/
│   │   │   └── api.ts           # API 客户端
│   │   └── types/
│   │       └── project.ts       # TypeScript 类型定义
│   └── tests/
│       └── example.spec.ts
│
├── docs/                        # 项目文档
│   ├── user-guide.md
│   ├── technical-documentation.md
│   └── ...
│
└── scripts/                     # 开发/运维脚本
```

---

## 四、核心组件详解

### 4.1 配置管理 (`app/config.py`)

基于 `pydantic-settings`，从 `.env` 文件和环境变量加载。关键配置项：

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `agnes_api_base_url` | AI 服务地址 | `https://apihub.agnes-ai.com/v1` |
| `agnes_api_key` | API 密钥 | (必填) |
| `pavo_home` | 数据目录 | `~/.pavo` |
| `static_port` | 静态文件端口 | 18080 |
| `log_level` | 日志级别 | INFO |

### 4.2 数据库层 (`app/db/database.py`)

- **引擎**: SQLAlchemy Async + aiosqlite (SQLite)
- **向量支持**: sqlite-vec 扩展 (FLOAT[1536] 向量)
- **WAL 模式**: Pragma journal_mode=WAL 提升并发性能
- **内存数据库**: 支持 `:memory:` 用于测试
- **ORM 表**:
  - `projects` — 项目主表 (状态机: draft → generating → completed)
  - `version_history` — 版本历史 / 回滚
  - `feedback` — 用户反馈
  - `system_config` — 键值配置存储
  - `task_status` — 异步任务状态追踪
  - `vec_memories` — 向量记忆表
  - `user_memories` — 长期记忆
  - `knowledge_base` — RAG 知识库
  - `session_contexts` — 会话上下文 (30 分钟 TTL)

### 4.3 7 Agent 管线

```
输入: 自然语言故事
  │
  ▼
┌──────────┐
│ Planner  │ 分析故事: 角色、场景、主题、情感、时长建议
└────┬─────┘
     │
     ▼
┌──────────┐
│Character │ 生成角色设定: 姓名、年龄、外貌、性格、声音
└────┬─────┘
     │
     ▼
┌──────────┐
│  Scene   │ 生成场景: 环境、灯光、氛围
└────┬─────┘
     │
     ▼
┌──────────┐
│  Prop    │ 生成道具: 外观、交互、意义
└────┬─────┘
     │
     ▼
┌──────────┐
│Storyboard│ 逐镜头分镜: 景别、运镜、角度、对白
└────┬─────┘
     │
     ▼
┌──────────┐     需要修复?
│ Reviewer │ ──────────► ┌────────┐
│ 审查质量  │             │ Fixer  │ 自动修复问题
└──────────┘             └────────┘
     │
     ▼
  完成!
```

每个 Agent 继承自 `BaseAgent`，通过 `AgnesAIClient.chat()` 调用 LLM。

Agent 串行执行 — 上游输出是下游输入的上下文。

### 4.4 MCP Server (`mcp_server/main.py`)

基于 `mcp` Python SDK 的 stdio 协议服务器。

**12 个 Tools**:

| 工具名 | 说明 |
|---|---|
| `pavo_create_project` | 创建项目并启动管线 |
| `pavo_get_project` | 获取项目完整数据 |
| `pavo_list_projects` | 项目列表 |
| `pavo_generate_storyboard` | 重新生成指定模块 |
| `pavo_render_video` | 触发视频渲染 |
| `pavo_export_project` | 导出 (markdown/script/pdf) |
| `pavo_get_video_status` | 视频状态查询 |
| `pavo_auth_login` | 认证 Token |
| `pavo_save_memory` | 保存记忆 |
| `pavo_search_memory` | 检索记忆 |
| `pavo_list_memories` | 列出记忆 |
| `pavo_delete_memory` | 删除记忆 |

**5 个 Resources**:
- `pavo://projects` — 项目列表
- `pavo://projects/{id}` — 项目详情
- `pavo://projects/{id}/storyboard` — 分镜数据
- `pavo://projects/{id}/characters` — 角色数据
- `pavo://users/{id}/memories` — 用户记忆

**2 个 Prompts**:
- `generate_storyboard` — 生成分镜
- `design_characters` — 设计角色

### 4.5 记忆系统 (Memory)

双层记忆架构：

```
┌─────────────────────────────────────────────┐
│              MemoryMiddleware                │
│  pre_process: 自动注入用户记忆中继到工具参数    │
│  post_process: 自动提取交互信息写入记忆        │
└────────────┬────────────────────┬────────────┘
             │                    │
      ┌──────▼──────┐    ┌───────▼────────┐
      │ 短期记忆     │    │  长期记忆       │
      │ Session     │    │  UserMemoryORM │
      │ ContextORM  │    │  (SQLite)      │
      │ (30min TTL) │    │  + 向量嵌入     │
      └─────────────┘    └────────────────┘
```

- **MemoryStore**: 基于 `MemoryProvider` 抽象接口的 SQLAlchemy 实现
- **向量搜索**: 内容 → embedding_client → vec_memories (sqlite-vec)
- **重要性评分**: `ImportanceStrategy` 自动计算记忆重要性 (0.0~1.0)
- **自动提取**: 会话中关键词提及 ≥ 2 次自动升格为长期记忆

### 4.6 RAG 知识库

- **数据**: `mcp_server/rag/knowledge_base/film_knowledge.md` (60+ 条影视专业知识)
- **检索**: `RAGRetriever` — 按类别过滤 → 优先级排序 → 多级重排序 (`SimpleReranker`)
- **类别**:
  - `shot_language` — 景别、镜头、运镜、构图
  - `film_grammar` — 剪辑、轴线、视线
  - `classic_case` — 经典案例、名场面
  - `narrative_structure` — 叙事结构、三幕、起承转合
  - `genre_template` — 类型模板
  - `bgm_sound` — 配乐、音效

### 4.7 任务队列 (`app/services/task_queue.py`)

自制异步任务队列替代 Celery：

```
asyncio.Queue (FIFO)
    ↓
Semaphore (max_concurrent=3)
    ↓
_worker_loop (后台 asyncio.Task)
    ↓
_perform_task → 状态: pending → running → completed/failed
                   ↓
              SQLite TaskStatus 表 (持久化)
              + 内存 _status_cache (快速查询)
```

### 4.8 认证系统 (`app/services/auth.py`)

- **Token**: secrets.token_hex(32) + SHA256 哈希
- **存储**: 内存 dict 为主 (快速), SQLite 持久化为辅
- **过期**: 7 天 TTL, 惰性清除 + 主动清理

### 4.9 API 层 (`app/api/routes.py`)

FastAPI 应用, `uvicorn` 运行。17 个 HTTP 端点:

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/login | 登录获取 Token |
| GET | /api/auth/me | 验证 Token |
| POST | /api/projects | 创建项目 |
| GET | /api/projects | 项目列表 |
| GET | /api/projects/{id} | 项目详情 |
| PATCH | /api/projects/{id} | 更新项目 |
| DELETE | /api/projects/{id} | 删除项目 |
| GET | /api/projects/{id}/stream | SSE 事件流 |
| POST | /api/projects/{id}/regenerate | 重新生成模块 |
| POST | /api/projects/{id}/render | 渲染视频 |
| ... | ... | 版本管理、反馈、导出 |

### 4.10 AI 客户端 (`app/services/agnes_client.py`)

- **协议**: HTTP + SSE (Streaming)
- **重试**: 指数退避, 最多 3 次, 针对 429/503
- **限速**: 0.5s 最小间隔
- **超时**: connect=15s, read=120s, write=30s
- **模型**: `agnes-2.0-flash` (聊天), `agnes-video-v2.0` (视频)
- **端点**: `/v1/chat/completions`, `/v1/images/generations`

---

## 五、零依赖架构 (v2.3 核心特性)

| 原有组件 | 旧方案 | 新方案 | 节省 |
|---|---|---|---|
| 数据库 | PostgreSQL + pgvector (Docker ~500MB) | SQLite + sqlite-vec | ~500MB |
| 缓存 | Redis (Docker ~150MB) | TTLCache (内存) | ~150MB |
| 任务队列 | Celery + Redis (Docker ~350MB) | asyncio.Queue | ~350MB |
| 文件存储 | MinIO (Docker ~500MB) | 本地文件系统 | ~500MB |
| **合计** | **4 个 Docker 容器** | **零外部依赖** | **~1.5GB** |

---

## 六、数据流

### 6.1 Web 模式
```
用户浏览器 ──HTTP──► FastAPI ──► ProjectService ──► Agents ──► LLM
  ▲                       │                         │
  │   SSE (stream)        │                         │
  └───────────────────────┘                         │
                                                    ▼
                                              SQLite DB
```

### 6.2 MCP 模式
```
Cursor/Claude Code ──stdio──► MCP Server ──► ProjectAdapter ──► ProjectService
                                   │                                    │
                                   ▼                                    ▼
                              MemoryMiddleware ──────────────────► MemoryStore
                                   │                                    │
                                   ▼                                    ▼
                              RAGRetriever ─────────────────────► KnowledgeBase
```

---

## 七、关键技术选型理由

| 技术 | 选型理由 |
|---|---|
| **SQLite + sqlite-vec** | 零配置、嵌入式、WAL 支持并发、向量搜索能力 |
| **asyncio.Queue** | Python 原生 async 任务队列, 零依赖, 协程安全 |
| **TTLCache** | 轻量级内存缓存, 自动过期, 零外部依赖 |
| **SQLAlchemy Async** | 成熟 ORM, 支持异步, 切换数据库方便 |
| **FastAPI** | 高性能异步框架, 原生 SSE, 自动 API 文档 |
| **MCP (Model Context Protocol)** | 标准化 AI 工具协议, 兼容 Cursor/Claude Desktop |
| **Next.js 14** | 现代 React 框架, SSR/SSG, 开发体验好 |
| **httpx** | 异步 HTTP 客户端, 原生流式支持 |

---

## 八、测试体系

18 个测试文件, 覆盖层次:

| 测试层级 | 文件 | 覆盖范围 |
|---|---|---|
| 单元测试 | test_api.py, test_auth.py, test_schema.py | REST API、认证、数据验证 |
| 组件测试 | test_agnes_client.py | AI 客户端逻辑 |
| 集成测试 | test_integration.py, test_video_tasks.py | Agent 管线、视频任务 |
| 存储测试 | test_storage.py | 文件存储 |
| MCP 测试 | test_mcp_server/ | 记忆、中间件、RAG |
| E2E 测试 | test_e2e.py, test_zero_dependency_e2e.py | 端到端流程 |

---

## 九、安全设计

1. **API Key 守卫** — MCP 工具调用前检查 `AGNES_API_KEY`
2. **Token 认证** — 基于 SHA256 哈希的 Token 系统, 7 天过期
3. **CORS 限制** — 仅允许 `http://localhost:3000`
4. **缓存安全** — Cache-Control 头控制静态文件缓存策略
5. **分级降级** — 记忆系统异常时仅记录日志, 不阻断主流程
6. **写入检查** — 启动时验证数据目录权限

---

## 十、部署方式

### 10.1 快速启动
```bash
pip install .          # 安装
pavo-mcp-server       # MCP Server 模式
pavo-start            # Web 模式 (API + 前端)
```

### 10.2 环境变量
```
AGNES_API_KEY=sk-xxx              # 必填
AGNES_API_BASE_URL=...            # 可选
LOG_LEVEL=INFO                    # 可选
PAVO_HOME=/path/to/data           # 可选
PAVO_FRONTEND_PORT=3000           # 可选
PAVO_STATIC_PORT=18080            # 可选
DATABASE_URL=sqlite+aiosqlite:///...  # 可选 (测试用)
```

---

## 十一、技术债务与改进建议

| 类别 | 问题 | 建议 |
|---|---|---|
| **测试** | 部分测试跳过或标记 `@pytest.mark.skip` | 补全缺失测试 |
| **Agent 串行** | 7 Agent 强串行, 下游依赖上游 | 引入并行优化 (如角色+场景可并行) |
| **错误处理** | Agent 调用 JSON 解析失败时返回 `[]` 或 `{}` | 引入重试 + fallback 模型 |
| **向量搜索** | sqlite-vec 在 SQLite 上性能有限 | 大流量时考虑升级到 pgvector |
| **前端** | 无单元测试、TypeScript 类型不全 | 添加前端测试 + 类型完善 |
| **部署** | 无生产级 WSGI/ASGI 部署配置 | 添加 docker-compose 生产配置 |
| **监控** | 无 metrics 暴露 | 集成 Prometheus / health 端点增强 |
| **记忆系统** | 自动升格逻辑简单 (关键词计数) | 引入语义相似度 + LLM 摘要提取 |
| **RAG 构建** | 从 markdown 导入, 无增量更新 | 支持 Webhook / 定时增量同步 |

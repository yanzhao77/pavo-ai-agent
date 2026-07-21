# Pavo AI Agent 详细技术文档

> 版本 2.0 | 2026-07-12

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [后端架构详解](#3-后端架构详解)
4. [前端架构详解](#4-前端架构详解)
5. [AI 智能体系统](#5-ai-智能体系统)
6. [数据模型](#6-数据模型)
7. [API 接口文档](#7-api-接口文档)
8. [开发环境搭建](#8-开发环境搭建)
9. [测试策略](#9-测试策略)
10. [部署指南](#10-部署指南)
11. [安全说明](#11-安全说明)

---

## 1. 项目概述

### 1.1 项目定位

Pavo AI Agent 是一个面向短视频创作者的 AI 分镜生成平台，通过编排多个专用 AI 智能体，将自然语言故事输入转化为格式化的视频分镜脚本，并可对接 AI 视频模型生成视频。

### 1.2 核心能力

- **自然语言理解** — 理解用户的故事描述，提取关键叙事元素
- **多智能体协作** — 7 个专用 AI 智能体分工协作，逐步细化
- **结构化输出** — 输出符合行业规范的分镜 JSON 数据
- **实时流推送** — 通过 SSE 实时推送智能体工作进度

## 6. MCP Server 层架构（v2.3 新增）

### 6.1 概述

MCP (Model Context Protocol) Server 层是 v2.3 的核心新增架构。它将 Pavo AI Agent 的核心能力以标准化协议暴露给 AI 客户端（如 Cursor、Claude Code、自定义 MCP Client），使 AI 工具可以直接发现和调用系统的项目创建、分镜生成、记忆管理等功能。

### 6.2 模块结构

`
backend/mcp_server/
+-- main.py                    # MCP Server 入口：注册 12 个 Tools、5 个 Resources、2 个 Prompts
+-- models/
|   +-- mcp_schemas.py         # 统一返回格式 MCPToolResult + MCPError 错误码体系
+-- memory/
|   +-- interfaces.py          # MemoryProvider 抽象接口
|   +-- store.py               # Memory 存储（SQLAlchemy + pgvector 兼容）
|   +-- embedding_client.py    # Embedding 向量化客户端（缓存 + 批量 + 重试）
|   +-- importance.py          # 重要性评分策略（3 种来源）
|   +-- session_store.py       # Session 短期记忆（Redis TTL，滑动窗口）
+-- rag/
|   +-- interfaces.py          # RAGProvider 抽象接口
|   +-- retriever.py           # RAG 检索服务（向量搜索 + 多级 Re-ranker）
|   +-- builder.py             # 知识库构建 Pipeline
|   +-- reranker.py            # 重排器（category + priority 加权）
|   +-- knowledge_base/        # 种子知识数据（60+ 条）
+-- middleware/
|   +-- memory_middleware.py   # Memory 透明注入中间件（三级降级 + 可观测性）
+-- tools/
|   +-- memory_tools.py        # 4 个 Memory MCP Tools
+-- adapter/
|   +-- project_adapter.py     # 适配层：桥接现有 ProjectService

- **视频模型对接** — 支持对接 AI 视频模型生成视频片段
- **多格式导出** — 支持 Markdown、纯文本、PDF 三种导出格式

### 1.3 技术选型

| 层次 | 技术 | 选型理由 |
|------|------|---------|
| 后端框架 | FastAPI (async) | 高性能异步框架，原生支持 SSE、异步 ORM |
| AI 网关 | Agnes AI | 统一 API Key，兼容 OpenAI 协议，支持文本+视频+音视频同步 |
| 任务队列 | Celery + Redis | 异步处理视频生成等耗时任务 |
| 数据库 | PostgreSQL | 支持 JSON 字段，适合存储结构化和半结构化数据 |
| 前端框架 | Next.js 14 (App Router) | SSR + RSC，优秀的开发体验 |
| UI 方案 | TailwindCSS | 原子化 CSS，快速构建一致界面 |
| 存储 | MinIO (S3 兼容) | 自托管对象存储，适合视频文件 |

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端交互层 (Next.js)                      │
│  对话输入  │  实时预览  │  分镜编辑  │  导出  │  认证      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────┴──────────────────────────────────────┐
│                   API 路由层 (FastAPI)                       │
│  Routes: /api/projects /api/auth /api/health               │
│  请求校验 (Pydantic) │ 认证中间件 │ SSE 流推送               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   服务层 (Services)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ProjectService (工作流编排)                          │   │
│  │   create_project → run_workflow → render_video       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────┐ ┌────────────┐ ┌────────┐ ┌──────────────┐   │
│  │AgnesAI   │ │  Auth      │ │ Celery │ │ Export       │   │
│  │Client    │ │  (Token)   │ │ Tasks  │ │ Markdown/PDF │   │
│  └──────────┘ └────────────┘ └────────┘ └──────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   AI 智能体层 (Agents)                       │
│  Planner → Character → Scene → Prop → Storyboard → Review  │
│  ↑_____________________________Fixer_______________________ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                  基础设施层                                  │
│  PostgreSQL │ Redis │ MinIO │ Agnes AI Unified Gateway      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 请求生命周期

```
用户输入故事
    │
    ▼
1. POST /api/projects → 创建 Project (status=generating)
    │
    ▼
2. asyncio.create_task(run_workflow)  ← 异步后台执行
    │
    ▼
3. Agent Pipeline 按序执行
   ├─ Planner: 分析故事 → 存入 input_extracted
   ├─ Character Agent: 生成角色 → 存入 characters
   ├─ Scene Agent: 生成场景 → 存入 scenes
   ├─ Prop Agent: 生成道具 → 存入 props
   ├─ Storyboard Agent: 生成分镜 → 存入 storyboard
   ├─ Reviewer: 审查质量
   └─ Fixer (可选): 自动修正
    │
    ▼
4. 每个步骤完成后 project.status 更新，SSE 推送到前端
    │
    ▼
5. 用户通过 GET /api/projects/{id} 获取完整数据
```

---

## 3. 后端架构详解

### 3.1 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口, lifespan, CORS, 路由注册
│   ├── config.py            # Pydantic BaseSettings 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # 18 个 REST API 端点
│   ├── agents/
│   │   ├── base.py          # BaseAgent 抽象基类
│   │   ├── planner.py       # 故事分析与规划
│   │   ├── character_agent.py  # 角色生成
│   │   ├── scene_agent.py   # 场景生成
│   │   ├── prop_agent.py    # 道具生成
│   │   ├── storyboard_agent.py  # 分镜生成
│   │   ├── reviewer.py      # 质量审查
│   │   └── fixer.py         # 自动修复
│   ├── models/
│   │   ├── project.py       # SQLAlchemy ORM (Project, VersionHistory, Feedback)
│   │   └── schema.py        # Pydantic 校验模式
│   ├── db/
│   │   ├── database.py      # 异步 SQLAlchemy 引擎 + session 工厂
│   │   └── migrations/      # Alembic 迁移文件
│   ├── services/
│   │   ├── agnes_client.py  # Agnes AI HTTP 客户端
│   │   ├── auth.py          # Token 认证
│   │   ├── project_service.py  # 工作流编排
│   │   ├── storage.py       # MinIO 存储
│   │   ├── celery_app.py    # Celery 配置
│   │   ├── video_tasks.py   # 异步视频任务
│   │   └── export/
│   │       ├── markdown.py  # Markdown 导出
│   │       └── pdf.py       # PDF 导出
│   └── ...
├── tests/                   # 12 个测试套件
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

### 3.2 核心模块：config.py

```python
class Settings(BaseSettings):
    app_name: str = "Pavo AI Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    agnes_api_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_api_key: str = ""
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pavo_agent"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "minio_secret"
    minio_bucket: str = "pavo-videos"
    max_concurrent_video_jobs: int = 3
    video_timeout_seconds: int = 300
    model_config = {"env_file": ".env"}
```

配置通过 `pydantic-settings` 自动从环境变量或 `.env` 文件加载，所有配置项有合理的默认值。

### 3.3 核心模块：main.py

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, ...)
app.include_router(router, prefix="/api")
```

使用 FastAPI 的 `lifespan` 机制管理数据库连接生命周期，启动时自动创建表。

### 3.4 核心模块：Agnes AI 客户端

`agnes_client.py` 实现了一个完整的 HTTP 客户端，包含：

**重试机制**
```python
async def _retry_with_backoff(fn, max_retries=3, base_delay=1.0, max_delay=30.0):
    # 指数退避: 1s, 2s, 4s, max 30s
    # 仅对 429 (Rate Limit) 和 503 (Model Unavailable) 重试
```

**限流机制**
```python
async def _rate_limit(self):
    # 两次调用间隔不小于 min_interval (0.5s)
```

**异常分类**
```python
AgnesAIError          # 基础异常
AgnesAIRateLimitError  # 429 限流
AgnesAIModelNotFoundError # 503 模型不可用
AgnesAITimeoutError    # 请求超时
```

**支持的 API**
- `chat()` — 文本生成（流式/非流式）
- `chat_stream()` — 流式文本生成（异步生成器）
- `generate_video()` — 视频生成

### 3.5 核心模块：路由层

`routes.py` 包含 18 个端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/auth/login` | POST | 登录获取 Token |
| `/api/auth/me` | GET | 校验 Token |
| `/api/projects` | POST | 创建项目 |
| `/api/projects` | GET | 项目列表 |
| `/api/projects/{id}` | GET | 获取项目 |
| `/api/projects/{id}` | PATCH | 更新项目 |
| `/api/projects/{id}` | DELETE | 删除项目 |
| `/api/projects/{id}/stream` | GET | SSE 流 |
| `/api/projects/{id}/regenerate` | POST | 重生成模块 |
| `/api/projects/{id}/render` | POST | 渲染视频 |
| `/api/projects/{id}/versions` | POST | 创建版本 |
| `/api/projects/{id}/versions` | GET | 版本列表 |
| `/api/projects/{id}/versions/{vid}/restore` | POST | 回滚版本 |
| `/api/projects/{id}/videos` | GET | 视频列表 |
| `/api/projects/{id}/tasks` | GET | 任务状态 |
| `/api/projects/{id}/export` | GET | 导出 |
| `/api/projects/{id}/feedback` | POST | 提交反馈 |

**SSE 流实现**
```python
async def event_stream():
    last_trace_count = 0
    while True:
        await session.refresh(project)
        traces = project.trace_log or []
        # 推送新的 trace 条目
        for i in range(last_trace_count, len(traces)):
            yield f"data: {json.dumps(trace_item)}\n\n"
        if project.status in ("completed", "draft"):
            yield f"data: {json.dumps({'type': 'agent:complete'})}\n\n"
            break
        await asyncio.sleep(1)
```

### 3.6 核心模块：工作流编排

`project_service.py` 中的 `run_workflow` 方法编排整个智能体管线：

```python
async def run_workflow(self, project_id: uuid.UUID):
    # 1. Planner: 分析故事
    # 2. Character Agent: 生成角色 → validate_characters()
    # 3. Scene Agent: 生成场景 → validate_scenes()
    # 4. Prop Agent: 生成道具 → validate_props()
    # 5. Storyboard Agent: 生成分镜 → validate_storyboard()
    # 6. Reviewer: 审查 → 如果 needs_fix
    # 7. Fixer: 自动修复
    # 8. 设置 status = COMPLETED
```

**视频渲染** (`render_video`):
1. `build_t2v_prompts()` 将分镜数据转换为逐镜头的视频提示词
2. 每个镜头调用 `agnes_client.generate_video()`
3. 结果自动上传到 MinIO 存储
4. 视频 URL 保存在 project.videos 中

---

## 4. 前端架构详解

### 4.1 项目结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # 根布局 (zh-CN 语言)
│   │   ├── page.tsx        # 主页面 (认证 + 主内容)
│   │   └── globals.css     # TailwindCSS 全局样式
│   ├── components/
│   │   ├── AuthGuard.tsx   # 认证守卫 (登录界面)
│   │   ├── ChatPanel.tsx   # 故事输入 + 智能体日志
│   │   ├── PreviewPanel.tsx # 多标签预览 (分镜/角色/场景/道具)
│   │   ├── Timeline.tsx    # 镜头时间轴 (拖拽排序)
│   │   ├── VideoPanel.tsx  # 视频播放面板
│   │   ├── SortableShot.tsx # 可拖拽镜头卡片
│   │   ├── Skeleton.tsx    # 加载骨架屏
│   │   ├── Toast.tsx       # Toast 通知系统
│   │   └── ConfirmDialog.tsx # 确认对话框
│   ├── lib/
│   │   └── api.ts          # API 客户端 (fetch + auth)
│   └── types/
│       └── project.ts      # TypeScript 类型定义
├── tests/
│   └── example.spec.ts     # Playwright E2E 测试
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

### 4.2 组件层级

```
App (page.tsx)
├── AuthGuard (登录界面)
│
└── HomeContent (主内容)
    ├── ToastProvider (全局通知)
    │
    └── div.flex (左右布局)
        ├── ChatPanel (左侧 1/3)
        │   ├── 输入框
        │   └── 智能体日志列表
        │
        └── PreviewPanel (右侧 2/3)
            ├── TabBar (分镜 | 角色 | 场景 | 道具)
            ├── Timeline (分镜标签页)
            │   └── SortableShot[] (可拖拽镜头卡片)
            ├── CharactersTab (角色列表)
            ├── ScenesTab (场景列表)
            └── PropsTab (道具列表)
```

### 4.3 状态管理

使用 React 的 `useState` 进行本地状态管理，通过回调函数 `onProjectUpdate` 实现父子组件间通信。

**关键状态**:
- `project: Project | null` — 当前项目数据
- `loading: boolean` — 加载状态
- `auth: AuthState` — 认证状态 (token, userId, username)

### 4.4 API 客户端

`lib/api.ts` 封装了所有后端 API 调用：

```typescript
export async function createProject(input: string, token: string, userId: string)
export async function getProject(id: string): Promise<Project>
export async function updateProject(id: string, data: Partial<Project>, token: string)
export async function deleteProject(id: string, token: string)
export async function regenerateModule(id: string, module: string, token: string)
export async function renderVideo(id: string, token: string)
export async function exportProject(id: string, format: string, token: string)
```

### 4.5 SSE 实时通信

主页面通过 `EventSource` 建立 SSE 连接：

```typescript
const connectSSE = (projectId: string) => {
    const es = new EventSource(`/api/projects/${projectId}/stream?token=${auth.token}`);
    es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "agent:progress") {
            // 更新智能体日志
        } else if (data.type === "agent:complete") {
            // 关闭 SSE, 拉取最终数据
            es.close();
            fetchProject(projectId);
        }
    };
};
```

---

## 5. AI 智能体系统

### 5.1 BaseAgent 基类

所有智能体继承自 `BaseAgent`，提供：

```python
class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    async def _call_structured(self, messages, temperature=0.7):
        """调用 Agnes AI 并解析结构化 JSON 输出"""
        response = await agnes_client.chat(
            messages=[
                {"role": "system", "content": self.system_prompt},
                *messages
            ],
            temperature=temperature,
            model="agnes-2.0-flash",
        )
        # 尝试解析 JSON，失败时返回原始文本
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return response
```

### 5.2 Planner（规划师）

**职责**: 理解用户故事，提取主题、情感、关键元素和预估时长。

**System Prompt**: 分析故事的关键元素，输出结构化的 JSON。

**输出示例**:
```json
{
  "theme": "亲情与温暖",
  "emotion": "温暖、感动",
  "main_characters": ["父亲", "儿子"],
  "estimated_duration": "30s",
  "key_elements": ["下班回家", "洗脚", "父子互动"]
}
```

### 5.3 Character Agent（角色智能体）

**职责**: 基于故事生成 2-4 个角色档案。

**输出模式** (Pydantic):
```python
class CharacterSchema(BaseModel):
    name: str              # 角色姓名
    role: str              # main / supporting / extra
    age: str               # 年龄描述
    gender: str            # 性别
    appearance: {          # 外貌详情
        build, face, eyes, hair, clothing, distinctive
    }
    personality: list[str] # 性格标签
    voice: str             # 声音描述
    relationship: str      # 人物关系
    consistencyKey: str    # 外貌关键特征摘要
```

### 5.4 Scene Agent（场景智能体）

**职责**: 生成 2-4 个场景设计。

**输出模式** (Pydantic):
```python
class SceneSchema(BaseModel):
    name: str                    # 场景名称
    timeOfDay: str               # 时段
    environment: {               # 环境详情
        type, style, size, furniture[], decor[], flooring
    }
    lighting: {                  # 灯光详情
        type, color, mood
    }
    atmosphere: str              # 氛围描述
```

### 5.5 Prop Agent（道具智能体）

**职责**: 识别并设计核心道具。

**输出模式** (Pydantic):
```python
class PropSchema(BaseModel):
    name: str            # 道具名称
    type: str            # anchor / prop
    appearance: str      # 外观描述
    interaction: str     # 交互方式
    significance: str    # 叙事意义
```

### 5.6 Storyboard Agent（分镜智能体）

**职责**: 生成完整的逐镜头视频分镜。

**System Prompt 核心要求**:
1. 按幕次组织，每幕包含标题、总时长、关键帧、音效音乐
2. 每个镜头包含：编号、景别、运镜、角度、画面描述、对白、时长
3. 遵循起承转合叙事结构
4. 总时长 30-60 秒
5. 输出必须是有效的 JSON

**输出结构**:
```python
class StoryboardSchema(BaseModel):
    projectName: str                          # 项目名称
    globalBGM: str                            # 全局背景音乐
    scenes: list[{                           # 场景列表
        title: str,                           #   场景标题
        duration: str,                        #   场景时长
        mood: str,                            #   情感基调
        music: str,                           #   BGM + SFX 描述
        keyframe: str,                        #   关键帧描述
        shots: list[{                         #   镜头列表
            shotNumber: int,                  #     镜头编号
            shotType: str,                    #     景别
            cameraMove: str,                  #     运镜
            cameraAngle: str,                 #     角度
            description: str,                 #     画面描述
            dialogue: str,                    #     对白
            duration: str,                    #     时长
            characters: list[str]             #     出场角色
        }]
    }]
```

### 5.7 Reviewer（审查智能体）

**职责**: 检查分镜的一致性、完整性和质量。

**审查项**:
1. 角色外貌是否跨镜头一致
2. 道具/场景是否一致
3. 镜头间动作、位置关系是否连贯
4. 故事是否有完整起承转合
5. 景别/运镜标注是否准确，时长分配是否均衡

### 5.8 Fixer（修复智能体）

**职责**: 根据审查反馈自动修复分镜问题。

---

## 6. 数据模型

### 6.1 Project（项目主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | str | 用户标识 |
| title | str | 项目标题 |
| status | enum | draft / generating / completed |
| input_raw | text | 原始故事输入 |
| input_extracted | json | 规划师分析结果 |
| characters | json | 角色档案数组 |
| scenes | json | 场景设计数组 |
| props | json | 道具定义数组 |
| storyboard | json | 完整分镜对象 |
| videos | json | 视频元数据数组 |
| task_ids | json | Celery 任务 ID 数组 |
| trace_log | json | 智能体执行轨迹 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 6.2 VersionHistory（版本历史）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| project_id | UUID | 关联项目 |
| version_number | int | 递增版本号 |
| snapshot | json | 项目完整快照 |
| description | str | 版本描述 |
| created_at | datetime | 创建时间 |

### 6.3 Feedback（用户反馈）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| project_id | UUID | 关联项目 |
| user_id | str | 用户标识 |
| rating | str | up / down |
| comment | text | 评论文本 |
| created_at | datetime | 创建时间 |

### 6.4 数据校验

使用 Pydantic 进行数据校验，每个模块有对应的校验函数：

```python
validate_characters(data)   # 校验角色数据
validate_scenes(data)       # 校验场景数据
validate_props(data)        # 校验道具数据
validate_storyboard(data)   # 校验分镜数据
```

校验失败的字段会回退到原始字典，保证管线不中断。

---

## 7. API 接口文档

### 7.1 认证

**POST /api/auth/login**
```json
// Request
{"username": "alice"}
// Response
{"token": "hex_string_64_chars", "user_id": "alice"}
```

**GET /api/auth/me**
```
// Query: ?token=xxx
// Response: {"user_id": "alice"} 或 401
```

### 7.2 项目 CRUD

**POST /api/projects**
```json
// Request
{"input": "故事描述文本", "user_id": "alice"}
// Response (202)
{"projectId": "uuid", "status": "generating"}
```

**GET /api/projects/{id}**
```
// Response (200): 完整 Project JSON
```

**PATCH /api/projects/{id}**
```json
// Request (partial update)
{"characters": [...], "storyboard": {...}}
// Response
{"status": "updated"}
```

### 7.3 SSE 实时流

**GET /api/projects/{id}/stream**
```
SSE Protocol:
data: {"type":"agent:progress","agent":"planner","action":"Analyzing","status":"passed","timestamp":"..."}
data: {"type":"agent:complete","status":"completed"}
```

### 7.4 视频相关

**POST /api/projects/{id}/render**
```json
// Response
{"videos": [{"shot_number": 1, "status": "completed", "storage_url": "...", ...}]}
```

### 7.5 导出

**GET /api/projects/{id}/export?format=markdown**
**GET /api/projects/{id}/export?format=script**
**GET /api/projects/{id}/export?format=pdf**

---

## 8. 开发环境搭建

### 8.1 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Agnes AI API Key

### 8.2 后端开发

```bash
# 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements-dev.txt
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 AGNES_API_KEY 等

# 启动基础设施
docker compose up -d postgres redis minio

# 启动开发服务器
uvicorn app.main:app --reload --port 8000 --log-level debug
```

### 8.3 前端开发

```bash
cd frontend
npm install
npm run dev  # 默认 http://localhost:3000
```

### 8.4 数据库迁移

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 9. 测试策略

### 9.1 测试文件分布

```
backend/tests/
├── conftest.py              # 测试配置 + mock 项目工厂
├── test_agents_direct.py    # 智能体输出结构测试
├── test_agnes_client.py     # Agnes AI 客户端测试（mock）
├── test_api.py              # API 路由测试
├── test_auth.py             # 认证模块测试
├── test_e2e.py              # 端到端全流程测试
├── test_exports.py          # 导出功能测试
├── test_integration.py      # 集成测试
├── test_phase2.py           # 阶段二功能测试
├── test_schema.py           # Pydantic 模式校验测试
├── test_storage.py          # MinIO 存储测试
├── test_t2v.py              # 分镜→视频提示词转换测试
└── test_video_tasks.py      # Celery 视频任务测试

frontend/tests/
└── example.spec.ts          # Playwright E2E 测试
```

### 9.2 测试配置

测试使用 SQLite 内存数据库，mock API Key：

```python
# conftest.py
os.environ["AGNES_API_KEY"] = "test-key-12345"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
```



## 7. Agent Memory + RAG 系统（v2.3 新增）

### 7.1 Agent Memory 系统

Memory 系统分为两层：

**短期记忆（Session Memory）**
- 存储位置: Redis（开发环境 SQLite）
- TTL: 30 分钟，滑动窗口刷新
- 内容: 对话历史、当前项目上下文、临时状态
- 每次 Tool 调用自动续期 TTL

**长期记忆（User Memory）**
- 存储位置: PostgreSQL + pgvector（1536 维）
- 6 种类型: style / character / scene / preference / story_arc / feedback
- 重要性评分: user_saved(0.9) / auto_extracted(公式) / feedback_derived(0.7/0.2)
- 自动清理: importance < 0.2 且 > 30 天未访问自动删除

**MCP Tools（4 个）**
pavo_save_memory / pavo_search_memory / pavo_list_memories / pavo_delete_memory

### 7.2 RAG 影视知识库

知识库包含 60+ 条影视专业知识，分为 6 大类：
镜头语言(15) / 电影语法(10) / 经典案例(10) / 叙事结构(8) / 类型模板(7) / BGM 音效(10)

检索 Pipeline: 用户输入 → Embedding → pgvector ANN → Re-ranker → Context Injector → Agent Prompt

注入目标: Storyboard Agent（主）+ Character/Scene Agent（辅）

### 7.3 Memory Middleware

位于 MCP Server 调度层，对所有 Tool 调用透明拦截：
- pre_process: 自动检索用户记忆 → 注入 context.memory
- post_process: 提取交互信息 → 评估重要性 → 存入长期记忆
- 三级降级: 不可用 → 超时 → 未知错误
- 可观测性: 6 项指标（命中率/降级次数/耗时等）

### 7.4 Workflow 可视化

前端 WorkflowVisualizer 组件以 SVG 管线图展示 7 个 Agent 的执行状态：
- 节点: 7 个 Agent 卡片（状态色编码 + 图标）
- 连线: SVG 贝塞尔曲线箭头
- 动画: CSS transitions 状态过渡
- 详情面板: 点击节点查看输入/输出/错误摘要
- 时间线: 横向条形图展示各 Agent 耗时比例
### 9.3 运行测试

```bash
cd backend
python -m pytest tests/ -v                    # 运行所有测试
python -m pytest tests/ --cov=app -v          # 运行 + 覆盖率
python -m pytest tests/test_api.py -v -k "create"  # 按名称筛选
```

---

## 10. 部署指南

### 10.1 Docker Compose 部署

```bash
# 全栈部署
docker compose up --build -d

# 查看日志
docker compose logs -f backend
docker compose logs -f celery_worker
```

**服务组成**:
- `postgres`: PostgreSQL 16 数据库
- `redis`: Redis 7 缓存队列
- `minio`: MinIO 对象存储
- `backend`: FastAPI 应用
- `celery_worker`: Celery 异步任务消费者

### 10.2 环境变量

完整的环境变量配置参考 `.env.example`。关键变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AGNES_API_KEY` | AI API 密钥（必填） | - |
| `DATABASE_URL` | 数据库连接串 | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `MINIO_ENDPOINT` | MinIO 端点 | `http://localhost:9000` |
| `APP_ENV` | 运行环境 | `development` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 10.3 CI/CD

GitHub Actions 配置在 `.github/workflows/test.yml`：

- 每次 push / PR 自动运行
- 启动 PostgreSQL 和 Redis 服务容器
- 安装依赖并运行 pytest
- 上传覆盖率报告到 Codecov

---

## 11. 安全说明

### 11.1 API Key 管理

- API Key 仅在后端使用，严禁暴露到前端或公共仓库
- 通过 `.env` 文件或密钥管理服务注入
- `.gitignore` 已配置排除 `.env` 文件

### 11.2 认证机制

基于内存的 Token 认证：
- Token 生成：`secrets.token_hex(32)`（64 字符十六进制）
- Token 存储：服务端 SHA256 哈希存储
- 过期时间：7 天
- 支持主动撤销

### 11.3 数据传输

- 前端 ↔ 后端：HTTP (开发) / HTTPS (生产)
- SSE 流通过 Token 参数鉴权
- MinIO 存储默认不加密（可配置 HTTPS）

### 11.4 数据隔离

- 项目数据通过 `user_id` 逻辑隔离（数据库层面）
- 文件存储按 `projects/{project_id}/shots/` 路径组织
- 数据库未启用行级权限（RLS），多租户场景需增强

---

> 更多信息，请参阅 [用户操作指南](user-guide.md) 或 [English Technical Documentation](technical-documentation-en.md)

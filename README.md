<div align="center">

<img src="https://raw.githubusercontent.com/yanzhao77/pavo-ai-agent/master/frontend/public/logo.png" width="120" alt="Pavo Logo" />

# Pavo AI Agent

**专为影视创作者打造的 AI 视频分镜生成引擎**

*输入一段故事 → 7 个 AI 智能体协同工作 → 输出专业级逐镜分镜脚本*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-Protocol-8B5CF6?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![SQLite](https://img.shields.io/badge/SQLite-Zero_Dep-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)

<br/>

```bash
pip install .  &&  pavo-start
```

**🚀 零依赖开箱即用：无需 Docker · 无需 PostgreSQL · 无需 Redis · 无需 Celery · 无需 MinIO**

</div>

---

## 🎬 它能做什么？

给 Pavo 一段自然语言故事，它会自动完成一位专业导演需要数小时才能完成的工作：

```text
输入 ──► "一位父亲下班回家，5 岁的儿子端来一盆洗脚水..."

输出 ──► 角色设定 + 场景设计 + 道具清单 + 完整分镜表
         ↓
         镜头 01 / 全景 / 固定机位 / 父亲推开门
         镜头 02 / 中景 / 推镜头 / 儿子端着水盆走来
         镜头 03 / 特写 / 跟焦 / 父亲眼眶泛红
         ...（自动生成 BGM 建议、对白、景别、运镜）
```

并且，每一次生成都会**记住你的创作偏好**，结合**影视专业知识库**，让输出越来越懂你。

---

## ✨ 核心特性

### 🤖 7 智能体协同管线

不是单个 AI 一次性生成，而是 7 个专业 AI 智能体像真实剧组一样分工协作：

```text
用户故事
   │
   ▼
① Planner 规划师 ──── 分析主题、情感、时长、叙事结构
   │
   ▼
② Character 角色师 ── 设计每个角色（外貌、性格、声音、一致性 Key）
   │
   ▼
③ Scene 场景师 ────── 构建场景（环境、灯光、氛围、色调）
   │
   ▼
④ Prop 道具师 ──────── 规划道具（外观、交互方式、象征意义）
   │
   ▼
⑤ Storyboard 分镜师 ─ 逐镜生成（景别、运镜、角度、对白、BGM）
   │
   ▼
⑥ Reviewer 审查员 ─── 质量审查（逻辑、视觉、情感一致性）
   │
   ▼
⑦ Fixer 修复师 ──────── 自动修复审查发现的问题
   │
   ▼
完整专业分镜脚本 ✓
```

### 🧠 Memory + RAG 双重增强（v2.3 新特性）

Pavo 不只是一个无状态的生成器，它会**持续学习**：

- **长期记忆（Memory）**：自动提取并存储你的创作偏好（喜欢的风格、常用的镜头语言、惯用的叙事结构），在下次创作时自动注入。
- **RAG 知识检索**：内置 60+ 条影视专业知识条目（景别定义、运镜技巧、色彩心理学、BGM 搭配原则），在分镜生成阶段自动检索并注入相关知识。

```text
Planner ◄──── Memory 注入（你的历史偏好）
                    ↑
              用户记忆数据库
              (sqlite-vec 向量检索)

Storyboard ◄── RAG 注入（影视专业知识）
                    ↑
              知识库 (60+ 条目)
              (语义相似度召回)
```

### 🔌 原生 MCP Server

Pavo 实现了完整的 [Model Context Protocol](https://modelcontextprotocol.io) 标准，可以作为独立 MCP Server 接入 **Cursor**、**Claude Desktop**、**Claude Code** 等任意 MCP 客户端。

| 类型 | 数量 | 说明 |
|------|------|------|
| **Tools** | 12 | 项目管理、分镜生成、记忆操作、视频渲染等 |
| **Resources** | 5 | 项目数据、分镜内容、角色设定等只读资源 |
| **Prompts** | 2 | 内置的创作提示词模板 |

### ⚡ 零依赖，开箱即用

v2.3 完成了彻底的轻量化改造，告别一切重型中间件：

| 组件 | 改造前 | 改造后 | 节省 |
|------|--------|--------|------|
| 数据库 | PostgreSQL + pgvector（Docker） | **SQLite + sqlite-vec** | ~500 MB |
| 缓存 | Redis（Docker） | **TTLCache（进程内）** | ~150 MB |
| 任务队列 | Celery + Redis（Docker） | **asyncio.Queue** | ~350 MB |
| 文件存储 | MinIO（Docker） | **本地文件系统** | ~500 MB |
| **合计** | **4 个 Docker 容器** | **零外部依赖** | **~1.5 GB** |

---

## 🚀 快速开始

### 环境要求

- Python **3.10+**
- Node.js **18+**（仅运行前端 Web 界面时需要）
- [Agnes AI API Key](https://apihub.agnes-ai.com)（用于 LLM 和视频生成）

### 方式一：MCP Server（推荐，无需前端）

适合 Cursor / Claude Desktop 用户，直接将 Pavo 作为工具接入你的 AI IDE：

```bash
# 1. 克隆仓库
git clone https://github.com/yanzhao77/pavo-ai-agent.git
cd pavo-ai-agent

# 2. 安装依赖
cd backend
pip install -r requirements.txt

# 3. 配置 API Key（任选其一）
export AGNES_API_KEY="your_api_key_here"
# 或者创建 .env 文件

# 4. 启动 MCP Server
python -m mcp_server.main
```

所有数据（数据库、存储文件、日志）将自动生成在 `~/.pavo/` 目录下，无需任何额外配置。

### 方式二：完整 Web 工作台

适合需要可视化界面进行创作的用户：

```bash
# 启动后端 API
cd backend
python -m app.main
# 后端运行在 http://localhost:8000

# 新开终端，启动前端
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:3000
```

---

## 🔌 MCP 客户端接入

### Cursor 配置

打开 `Cursor Settings` → `Features` → `MCP Servers`，添加以下配置：

```json
{
  "mcpServers": {
    "pavo": {
      "command": "python",
      "args": [
        "-m", "mcp_server.main"
      ],
      "cwd": "/path/to/pavo-ai-agent/backend",
      "env": {
        "AGNES_API_KEY": "your_api_key_here",
        "PAVO_HOME": "~/.pavo"
      }
    }
  }
}
```

配置完成后，你可以在 Cursor 中直接使用自然语言调用 Pavo：

> *"帮我用 pavo_create_project 创建一个关于赛博朋克风格咖啡馆的短视频项目，然后用 pavo_run_workflow 生成完整分镜。"*

### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）：

```json
{
  "mcpServers": {
    "pavo": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "cwd": "/path/to/pavo-ai-agent/backend",
      "env": {
        "AGNES_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 可用 MCP Tools 完整列表

| Tool 名称 | 功能描述 |
|-----------|---------|
| `pavo_create_project` | 创建新的视频项目 |
| `pavo_run_workflow` | 运行完整的 7 Agent 生成管线 |
| `pavo_get_project` | 获取项目详情与分镜内容 |
| `pavo_list_projects` | 列出所有项目 |
| `pavo_update_project` | 更新项目信息 |
| `pavo_delete_project` | 删除项目 |
| `pavo_save_memory` | 保存用户创作偏好记忆 |
| `pavo_search_memory` | 语义搜索历史记忆 |
| `pavo_list_memories` | 列出所有记忆条目 |
| `pavo_delete_memory` | 删除指定记忆 |
| `pavo_render_video` | 触发视频渲染任务 |
| `pavo_export_project` | 导出项目（Markdown / PDF） |

---

## 🏗️ 技术架构

```text
┌─────────────────────────────────────────────────────────────┐
│                      客户端层                                │
│   Cursor / Claude Code    │    Web 浏览器 (Next.js 14)      │
│      (MCP Client)         │    React 18 + TailwindCSS       │
└──────────────┬────────────┴──────────────┬──────────────────┘
               │ MCP Protocol              │ HTTP REST API
               ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务层                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │    MCP Server        │    │      FastAPI Backend         │ │
│  │  · 12 Tools          │    │      (port 18080)            │ │
│  │  · 5 Resources       │    │  · REST API Routes           │ │
│  │  · 2 Prompts         │    │  · Auth Service              │ │
│  │  · guards 安全检查   │    │  · Static Files              │ │
│  └──────────┬──────────┘    └──────────────┬──────────────┘ │
│             └──────────────┬───────────────┘                 │
│                            ▼                                  │
│              ┌─────────────────────────┐                     │
│              │   ProjectService (核心)  │                     │
│              │   run_workflow() 编排    │                     │
│              └────────────┬────────────┘                     │
└───────────────────────────┼─────────────────────────────────┘
                            │ 7 Agent 串行管线
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent 层                                │
│  Planner → Character → Scene → Prop → Storyboard            │
│                                    → Reviewer → Fixer       │
│      ↑ Memory 注入                      ↑ RAG 知识注入      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层（零依赖）                     │
│  SQLite + sqlite-vec  │  TTLCache  │  asyncio.Queue          │
│  (关系型 + 向量检索)   │  (缓存层)  │  (任务队列)             │
│                                                              │
│  LocalStorageClient   │  aiosqlite │  SQLAlchemy 2.0         │
│  (文件存储)            │  (异步驱动) │  (ORM + 迁移)          │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI 0.115 + Uvicorn | 高性能异步 Web 框架 |
| **MCP 协议** | MCP Python SDK 1.28+ | 标准 Tools / Resources 接口 |
| **ORM** | SQLAlchemy 2.0（异步） | 数据库抽象层 |
| **数据库** | SQLite + aiosqlite | 本地轻量级存储，WAL 模式 |
| **向量检索** | sqlite-vec | SQLite 原生向量扩展，替代 pgvector |
| **任务队列** | asyncio.Queue + Semaphore | 纯内存并发控制，替代 Celery |
| **文件存储** | LocalStorageClient | 本地文件系统，替代 MinIO/S3 |
| **前端框架** | Next.js 14 + React 18 | 服务端渲染 + 客户端交互 |
| **前端样式** | TailwindCSS + shadcn/ui | 现代化 UI 组件库 |
| **LLM 接入** | Agnes AI API（OpenAI 兼容） | 支持多模型切换 |

---

## 📁 项目结构

```text
pavo-ai-agent/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 个 AI 智能体
│   │   │   ├── planner.py
│   │   │   ├── character_agent.py
│   │   │   ├── scene_agent.py
│   │   │   ├── prop_agent.py
│   │   │   ├── storyboard_agent.py
│   │   │   ├── reviewer.py
│   │   │   └── fixer.py
│   │   ├── api/             # REST API 路由
│   │   ├── db/              # 数据库引擎与迁移
│   │   ├── models/          # ORM 数据模型
│   │   ├── services/        # 核心业务服务
│   │   │   ├── auth.py      # 认证服务
│   │   │   ├── cache.py     # TTLCache 统一缓存
│   │   │   ├── storage.py   # 本地文件存储
│   │   │   ├── task_queue.py # asyncio 任务队列
│   │   │   └── video_tasks.py # 视频渲染任务
│   │   └── vectorstore/     # VectorStore 抽象接口
│   ├── mcp_server/
│   │   ├── main.py          # MCP Server 入口（12 Tools）
│   │   ├── memory/          # 记忆系统
│   │   │   ├── store.py     # 记忆存储与检索
│   │   │   └── embedding_client.py # Embedding 接口
│   │   ├── rag/             # RAG 知识库
│   │   │   ├── builder.py   # 知识库构建
│   │   │   └── retriever.py # 语义检索
│   │   ├── middleware/      # 记忆注入中间件
│   │   └── tools/           # MCP Tool 实现
│   └── tests/               # 测试套件（47 个用例）
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React 组件
│   │   └── lib/             # API 客户端
│   └── package.json
└── docs/                    # 技术文档
```

---

## 🗺️ 版本路线图

| 版本 | 核心特性 | 状态 |
|------|---------|------|
| **v1.0** | 7 Agent 基础管线 + 前端可视化 + Markdown/PDF 导出 | ✅ 已完成 |
| **v2.0** | MCP Server 标准化接口（8 个核心 Tools） | ✅ 已完成 |
| **v2.3** | Memory + RAG + MCP 扩展 + 零依赖轻量化改造 | ✅ **当前版本** |
| **v3.0** | 视频 Agent 完整版（Prompt 动态优化 + 多版本资产管理） | 📅 规划中 |

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [📘 用户操作指南](docs/user-guide.md) | 产品使用流程、界面导航、功能详解、常见问题 |
| [📙 技术架构报告](docs/technical-architecture-report.md) | 完整系统架构分析、组件详解、数据流 |
| [📋 技术债务报告](docs/技术债务解决方案报告.md) | 零依赖改造分析与剩余债务解决方案 |
| [🌐 English User Guide](docs/user-guide-en.md) | Product usage workflow, interface guide |
| [🌐 Technical Documentation](docs/technical-documentation-en.md) | Architecture, API reference, deployment |

---

## 🙏 致谢

Pavo 的诞生离不开以下优秀的开源项目与平台：

- **[Agnes AI](https://agnes-ai.com)** — 提供稳定强大的 LLM 与视频生成 API
- **[Model Context Protocol](https://modelcontextprotocol.io)** — 推动 AI 工具标准化的 MCP 协议
- **[sqlite-vec](https://github.com/asg017/sqlite-vec)** — 极速的 SQLite 本地向量搜索扩展
- **[FastAPI](https://fastapi.tiangolo.com)** — 高性能 Python Web 框架
- **[Next.js](https://nextjs.org)** — 卓越的 React 全栈框架

---

<div align="center">

Built with ❤️ by [yanzhao77](https://github.com/yanzhao77)

[GitHub](https://github.com/yanzhao77/pavo-ai-agent) · [提交 Issue](https://github.com/yanzhao77/pavo-ai-agent/issues) · [English README](README_EN.md)

</div>

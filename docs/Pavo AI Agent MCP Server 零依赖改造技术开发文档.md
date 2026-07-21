# Pavo AI Agent MCP Server 零依赖改造技术开发文档

**文档版本：** v1.0  
**日期：** 2026年7月13日  
**作者：** Manus AI

---

## 1. 概述与改造目标

`pavo-ai-agent` 项目（当前 v2.3）作为一个全栈应用，其 MCP Server 模块在独立运行时，深度耦合了 PostgreSQL（含 pgvector）、Redis、Celery 和 MinIO 等重型基础设施。这导致普通用户（尤其是非开发人员）在使用 Cursor 等客户端接入时，必须先配置复杂的 Docker 环境，极大地提高了接入门槛。

**改造目标：**
实现 MCP Server 的 **零外部依赖（Zero Dependency）**。用户无需安装任何独立数据库或中间件，仅需 `pip install` 即可运行。同时支持纯 MCP 使用（`.env` 配置）和 Web 界面使用（UI 配置）两种双模式，所有数据和状态均安全地保存在用户本地文件系统中。

## 2. 核心架构与技术选型

### 2.1 整体改造蓝图

| 原组件 | 替换方案 | 核心考量 |
|---------|---------|---------|
| **PostgreSQL** | SQLite + `sqlite-vec` | 结构化数据与向量检索统一单文件存储，`sqlite-vec` 提供纯 C 扩展的向量能力。 |
| **Redis** | `cachetools.TTLCache` | 内存缓存，用于管理 30 分钟的短期会话记忆，避免进程重启外的数据污染。 |
| **Celery + Redis** | `asyncio` 原生队列 | 进程内异步任务，移除外部 Broker，使用 SQLite 的 `task_status` 表持久化任务状态。 |
| **MinIO** | 本地文件系统 | 视频等媒体文件直接存储于 `~/.pavo/storage/` 目录，通过内置静态 HTTP 服务提供访问。 |
| **FastAPI / Uvicorn** | CLI 封装 | 提供 `pavo-mcp-server` 和 `pavo-start` 命令统一启动。 |

### 2.2 风险评估与防御性设计

基于前期的技术评审，本方案在架构上引入了以下防御性设计：

1. **SQLite 写入锁冲突防御**：强制开启 SQLite 的 WAL（Write-Ahead Logging）模式，并配合异步重试装饰器，解决高并发下的 `database is locked` 问题。
2. **底层实现解耦**：封装统一的 `VectorStore` 和 `Cache` 接口，避免业务代码（如 7 个 Agent 的管线）与 `sqlite-vec` 的特定 SQL 语法深度绑定。
3. **前端部署模式明确**：前端保持独立的 Node.js 运行模式（非纯静态导出），通过 API 与后端通信，避免 Next.js 静态导出带来的动态路由和 API 失效问题。

## 3. 详细设计与实现

### 3.1 数据库与向量检索层 (SQLite + sqlite-vec)

项目现有的 6 张表（`projects`, `version_history`, `feedback`, `user_memories`, `knowledge_base`, `session_contexts`）将全部迁移至 SQLite。

**关键实现细节：**
- 使用 `aiosqlite` 作为 SQLAlchemy 的异步驱动。
- 在引擎创建时，通过 `sqlalchemy.event` 监听器确保每个新连接都正确加载 `sqlite-vec` 扩展。

```python
# app/db/database.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlite_vec

@event.listens_for(Engine, "connect")
def load_sqlite_vec(dbapi_connection, connection_record):
    dbapi_connection.enable_load_extension(True)
    sqlite_vec.load(dbapi_connection)
    dbapi_connection.enable_load_extension(False)

# 启用 WAL 模式以提升并发写入性能
engine = create_async_engine(
    "sqlite+aiosqlite:///~/.pavo/pavo_local.db",
    connect_args={
        "check_same_thread": False,
        "pragma": {"journal_mode": "wal", "synchronous": "normal"}
    }
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### 3.2 缓存与短期记忆层 (TTLCache)

移除 Redis 依赖，使用 `cachetools` 库实现带 TTL（Time-To-Live）的内存缓存，用于存储 Session Context。

```python
# app/services/cache.py
from cachetools import TTLCache

# 短期记忆缓存，最大 1000 个会话，TTL 30 分钟 (1800秒)
session_cache = TTLCache(maxsize=1000, ttl=1800)

def get_session_memory(session_id: str) -> dict:
    return session_cache.get(session_id)

def set_session_memory(session_id: str, data: dict):
    session_cache[session_id] = data
```

### 3.3 异步任务队列 (Asyncio Queue)

移除 Celery，实现一个基于 `asyncio.Queue` 的轻量级进程内任务队列。为了防止进程重启导致任务状态丢失，在 SQLite 中新增 `task_status` 表进行持久化跟踪。

```python
# app/services/task_queue.py
import asyncio
import uuid
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    coro: callable
    args: tuple
    kwargs: dict

class AsyncTaskQueue:
    def __init__(self, max_concurrent: int = 3):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def submit(self, coro, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        # TODO: 写入 SQLite task_status 表，状态为 'pending'
        await self.queue.put(Task(id=task_id, coro=coro, args=args, kwargs=kwargs))
        return task_id
    
    async def worker(self):
        while True:
            task = await self.queue.get()
            async with self.semaphore:
                try:
                    # TODO: 更新 SQLite task_status 表，状态为 'running'
                    result = await task.coro(*task.args, **task.kwargs)
                    # TODO: 更新 SQLite task_status 表，状态为 'done'
                except Exception as e:
                    # TODO: 更新 SQLite task_status 表，状态为 'failed'
                    pass
            self.queue.task_done()
```

### 3.4 本地文件存储与静态服务

将生成的视频文件存储在 `~/.pavo/storage/` 目录下，并启动一个轻量级的 HTTP 服务供前端或客户端访问。

```python
# app/services/storage.py
from pathlib import Path
from app.config import settings

class LocalStorageClient:
    def __init__(self):
        self.storage_root = Path.home() / ".pavo" / "storage"
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    def upload_bytes(self, data: bytes, object_name: str) -> str:
        file_path = self.storage_root / object_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return self.get_url(object_name)
    
    def get_url(self, object_name: str) -> str:
        # STATIC_PORT 默认建议为 18080，避免与原 MinIO 9000 端口混淆
        return f"http://localhost:{settings.STATIC_PORT}/static/{object_name}"
```

### 3.5 配置管理与优先级机制

实现统一的配置管理，支持三种配置源的优先级解析：**页面配置（数据库） > 环境变量（.env文件） > 默认值**。

```python
# app/config.py
import os
from cachetools import TTLCache
from sqlalchemy import text
from app.db.database import async_session

# 配置缓存，TTL 60秒
config_cache = TTLCache(maxsize=100, ttl=60)

async def get_config(key: str, default: str = "") -> str:
    if key in config_cache:
        return config_cache[key]
    
    # 优先从数据库查询 (需使用参数化查询防止 SQL 注入)
    async with async_session() as session:
        result = await session.execute(
            text("SELECT value FROM system_config WHERE key = :key"),
            {"key": key}
        )
        db_value = result.scalar_one_or_none()
        if db_value:
            config_cache[key] = db_value
            return db_value
            
    # 其次从环境变量读取
    env_value = os.getenv(key)
    if env_value:
        return env_value
        
    return default
```

## 4. 实施路线图

本改造分为五个阶段，建议按顺序实施：

| 阶段 | 任务描述 | 涉及核心文件 |
|------|---------|-------------|
| **Phase 1: 数据层改造** | 1. 替换为 SQLite 异步引擎并加载 `sqlite-vec`<br>2. 启用 WAL 模式<br>3. 创建 `system_config` 和 `task_status` 表 | `app/db/database.py`<br>`app/db/migrations/` |
| **Phase 2: 存储与缓存改造** | 1. 实现 `LocalStorageClient`<br>2. 实现 `TTLCache` 缓存<br>3. 移除 Redis 相关调用 | `app/services/storage.py`<br>`app/services/cache.py` |
| **Phase 3: 任务队列改造** | 1. 实现 `AsyncTaskQueue`<br>2. 重写视频生成任务逻辑<br>3. 移除 Celery 配置 | `app/services/task_queue.py`<br>`app/services/video_tasks.py` |
| **Phase 4: 封装与配置管理** | 1. 实现配置优先级解析逻辑<br>2. 创建统一的 CLI 启动入口<br>3. 集成静态文件 HTTP 路由 | `app/config.py`<br>`pavo_mcp_server/cli.py` |
| **Phase 5: 前端与测试** | 1. 前端新增配置管理页面（保留 Node.js 运行模式）<br>2. 补充 SQLite 和本地队列的单元测试 | `frontend/`<br>`tests/` |

## 5. 依赖变更清单

**移除的依赖：**
- `psycopg2-binary`, `asyncpg` (PostgreSQL)
- `redis`, `celery` (缓存与队列)
- `boto3` (MinIO/S3)

**新增的依赖：**
- `aiosqlite` (SQLite 异步驱动)
- `sqlite-vec` (纯 C 向量检索扩展)
- `cachetools` (内存 TTL 缓存)
- `click` (CLI 命令行封装)

**最终核心依赖 (`requirements.txt`)：**
```text
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.35
aiosqlite>=0.20.0
sqlite-vec>=0.1.0
cachetools>=5.3.0
click>=8.1.0
python-dotenv>=1.0.0
mcp>=1.28.0
```

## 6. 验收标准

1. **零依赖启动**：在纯净的 Python 3.10+ 环境中，执行 `pip install -r requirements.txt` 后，MCP Server 能够成功启动，不依赖任何外部 Docker 容器。
2. **工具可用性**：所有 12 个 MCP Tools（包括项目管理、分镜生成、记忆检索）在配置好 `AGNES_API_KEY` 后能够正常执行。
3. **配置优先级生效**：通过 Web 页面修改 API Key 后，MCP Server 能够在 60 秒内（TTL）感知并使用新密钥，覆盖 `.env` 中的配置。
4. **异步任务流转**：视频渲染任务能够被正确提交到本地 `AsyncTaskQueue`，状态在 `task_status` 表中正确流转（pending -> running -> done），最终视频文件落盘至 `~/.pavo/storage/`。

# Pavo AI Agent MCP Server 零依赖改造技术开发文档

**文档版本：** v1.2  
**日期：** 2026年7月13日  
**修订说明：** 在 v1.1 基础上修正 `task_type` 硬编码、`VectorStore` 类型导入缺失、`vec_memories` 表结构缺失三项问题；新增日志系统规划、`pavo-start` 命令定义及静态文件缓存控制头。

---

## 目录

1. [概述与改造目标](#1-概述与改造目标)
2. [核心架构与技术选型](#2-核心架构与技术选型)
3. [详细设计与实现](#3-详细设计与实现)
   - 3.1 数据库与向量检索层
   - 3.2 缓存与短期记忆层
   - 3.3 异步任务队列
   - 3.4 本地文件存储与静态服务
   - 3.5 配置管理与优先级机制
   - 3.6 VectorStore 抽象接口
   - 3.7 MCP Tool 全局兜底机制
   - 3.8 启动初始化流程与 CLI 命令
4. [实施路线图](#4-实施路线图)
5. [依赖变更清单](#5-依赖变更清单)
6. [验收标准](#6-验收标准)
7. [迁移说明](#7-迁移说明)

---

## 1. 概述与改造目标

`pavo-ai-agent` 项目（当前 v2.3）作为一个全栈应用，其 MCP Server 模块在独立运行时，深度耦合了 PostgreSQL（含 pgvector）、Redis、Celery 和 MinIO 等重型基础设施。这导致普通用户（尤其是非开发人员）在使用 Cursor 等客户端接入时，必须先配置复杂的 Docker 环境，极大地提高了接入门槛。

**改造目标：** 实现 MCP Server 的**零外部依赖（Zero Dependency）**。用户无需安装任何独立数据库或中间件，仅需 `pip install` 即可运行。同时支持纯 MCP 使用（`.env` 配置）和 Web 界面使用（UI 配置）两种双模式，所有数据和状态均安全地保存在用户本地文件系统中。

### 1.1 用户场景

| 场景 | 适用人群 | 配置方式 | 启动命令 |
|------|---------|---------|---------|
| 纯 MCP 使用 | 开发者、Cursor 用户 | 编辑 `.env` 文件 | `pavo-mcp-server` |
| Web 界面使用 | 非技术用户 | 页面表单填写 | `pavo-start` |
| 混合模式 | 所有用户 | 页面配置优先，`.env` 作为备选 | 任一方式均可 |

---

## 2. 核心架构与技术选型

### 2.1 整体改造蓝图

| 原组件 | 替换方案 | 核心考量 |
|---------|---------|---------|
| **PostgreSQL** | SQLite + `sqlite-vec` | 结构化数据与向量检索统一单文件存储，`sqlite-vec` 提供纯 C 扩展的向量能力，`pip install sqlite-vec` 即可获得预编译 wheel，无需本地编译环境。 |
| **Redis（缓存）** | `cachetools.TTLCache` | 内存缓存，用于管理 30 分钟的短期会话记忆。在 `asyncio` 单事件循环中，同一时刻只有一个协程运行，无并发修改风险，无需额外加锁。 |
| **Celery + Redis（队列）** | `asyncio` 原生队列 | 进程内异步任务，移除外部 Broker，使用 SQLite 的 `task_status` 表持久化任务状态，防止进程重启后任务状态丢失。 |
| **MinIO** | 本地文件系统 | 视频等媒体文件直接存储于 `~/.pavo/storage/` 目录，通过内置静态 HTTP 服务（FastAPI + Uvicorn 后台线程）提供访问。 |
| **FastAPI / Uvicorn** | CLI 封装 | 提供 `pavo-mcp-server` 和 `pavo-start` 命令统一启动。 |

### 2.2 防御性设计原则

基于前期技术评审，本方案在架构上引入以下三项防御性设计：

**SQLite 写入锁防御：** 强制开启 WAL（Write-Ahead Logging）模式，允许读写并发，并配合异步重试机制，解决多 Agent 并发写入时的 `database is locked` 问题。

**底层实现解耦：** 封装统一的 `VectorStore` 抽象接口（见第 3.6 节），业务代码（7 个 Agent 管线）不直接调用 `sqlite-vec` 特有的 SQL 函数（如 `vec_distance_cosine`），确保未来可平滑切换至其他向量引擎。

**前端部署模式：** 前端保持独立的 Node.js 运行模式（`next start`），**不采用**纯静态导出（`output: 'export'`）。这一决策规避了静态导出带来的动态路由失效、`/api` 路由禁用、环境变量硬编码等五类问题，前端通过 HTTP API 与后端通信。

---

## 3. 详细设计与实现

### 3.1 数据库与向量检索层 (SQLite + sqlite-vec)

项目现有的 6 张业务表（`projects`, `version_history`, `feedback`, `user_memories`, `knowledge_base`, `session_contexts`）将全部迁移至 SQLite，并新增 `system_config` 和 `task_status` 两张管理表。

**数据库路径配置：** 支持通过环境变量 `PAVO_HOME` 覆盖默认路径，方便测试环境和 CI/CD 使用。

```python
# app/db/database.py
import os
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlite_vec

PAVO_HOME = Path(os.getenv("PAVO_HOME", Path.home() / ".pavo"))
DB_PATH = PAVO_HOME / os.getenv("PAVO_DB_NAME", "pavo_local.db")
PAVO_HOME.mkdir(parents=True, exist_ok=True)

@event.listens_for(Engine, "connect")
def load_sqlite_vec(dbapi_connection, connection_record):
    """确保每个新连接都正确加载 sqlite-vec 扩展"""
    dbapi_connection.enable_load_extension(True)
    sqlite_vec.load(dbapi_connection)
    dbapi_connection.enable_load_extension(False)

engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    connect_args={
        "check_same_thread": False,
        "pragma": {"journal_mode": "wal", "synchronous": "normal"}
    }
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**新增表建表语句：**

```sql
-- system_config 表：存储通过 Web UI 设置的配置项
CREATE TABLE IF NOT EXISTS system_config (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- task_status 表：持久化异步任务状态，防止进程重启后状态丢失
CREATE TABLE IF NOT EXISTS task_status (
    task_id       TEXT PRIMARY KEY,
    task_type     TEXT NOT NULL,
    status        TEXT NOT NULL,       -- pending / running / done / failed
    progress      INTEGER DEFAULT 0,
    result_path   TEXT,
    error_message TEXT,
    project_id    TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_task_status_project ON task_status(project_id);

-- vec_memories 表：存储向量记忆的原始数据（id、metadata 等）
CREATE TABLE IF NOT EXISTS vec_memories (
    id         TEXT PRIMARY KEY,
    metadata   TEXT NOT NULL,    -- JSON 对象，存储记忆内容和标签
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- vec_memories_vec 虚拟表：供 sqlite-vec 执行 MATCH 向量搜索
-- 注意：维度 1536 需与实际 Embedding 模型输出维度保持一致
CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories_vec USING vec0(
    id        TEXT PRIMARY KEY,
    embedding FLOAT[1536]
);
-- 使用说明：upsert 时需同时写入 vec_memories 和 vec_memories_vec；
-- search 时对 vec_memories_vec 执行 MATCH 查询，再 JOIN vec_memories 获取完整 metadata。
```

### 3.2 缓存与短期记忆层 (TTLCache)

移除 Redis 依赖，使用 `cachetools.TTLCache` 实现带 TTL 的内存缓存，用于存储 Session Context。`TTLCache` 在 `asyncio` 单事件循环中是安全的，无需额外防护。

```python
# app/services/cache.py
from cachetools import TTLCache

# 短期记忆缓存，最大 1000 个会话，TTL 30 分钟
session_cache = TTLCache(maxsize=1000, ttl=1800)

def get_session_memory(session_id: str) -> dict:
    return session_cache.get(session_id)

def set_session_memory(session_id: str, data: dict):
    session_cache[session_id] = data

def clear_session_memory(session_id: str):
    session_cache.pop(session_id, None)
```

### 3.3 异步任务队列 (Asyncio Queue)

移除 Celery，实现基于 `asyncio.Queue` 的轻量级进程内任务队列。**关键修正：** `task_done()` 必须置于 `finally` 块中，确保无论任务成功或失败，每次 `get()` 都对应一次 `task_done()`，防止 `queue.join()` 永久阻塞。

```python
# app/services/task_queue.py
import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class Task:
    id: str
    task_type: str           # 任务类型，由 submit 时传入，避免硬编码
    coro: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

class AsyncTaskQueue:
    def __init__(self, max_concurrent: int = 3):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def submit(self, task_type: str, coro: Callable, *args, **kwargs) -> str:
        """提交任务，task_type 由调用方传入（如 'video_render'、'storyboard_gen'）"""
        task_id = str(uuid.uuid4())
        await self._update_status(task_id, "pending", task_type=task_type)
        await self.queue.put(Task(id=task_id, task_type=task_type, coro=coro, args=args, kwargs=kwargs))
        return task_id

    async def worker(self):
        while True:
            task = await self.queue.get()
            try:
                async with self.semaphore:
                    await self._update_status(task.id, "running", task_type=task.task_type)
                    result = await task.coro(*task.args, **task.kwargs)
                    await self._update_status(task.id, "done", task_type=task.task_type, result=result)
            except Exception as e:
                await self._update_status(task.id, "failed", task_type=task.task_type, error=str(e))
            finally:
                # 确保每个 get() 都对应一次 task_done()，防止 join() 永久阻塞
                self.queue.task_done()

    async def start_workers(self, num_workers: int = 2):
        for _ in range(num_workers):
            asyncio.create_task(self.worker())

    async def _update_status(
        self, task_id: str, status: str,
        task_type: str = "unknown", result=None, error: str = None
    ):
        """将任务状态写入 SQLite task_status 表"""
        from sqlalchemy import text
        from app.db.database import async_session
        async with async_session() as session:
            await session.execute(
                text("""
                    INSERT INTO task_status (task_id, task_type, status, result_path, error_message, updated_at)
                    VALUES (:task_id, :task_type, :status, :result_path, :error, CURRENT_TIMESTAMP)
                    ON CONFLICT(task_id) DO UPDATE SET
                        status = :status,
                        result_path = :result_path,
                        error_message = :error,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "task_id": task_id, "task_type": task_type, "status": status,
                    "result_path": str(result) if result else None, "error": error
                }
            )
            await session.commit()
```

### 3.4 本地文件存储与静态服务

**存储客户端：** 将生成的视频文件存储在 `~/.pavo/storage/` 目录下。

```python
# app/services/storage.py
from pathlib import Path
from app.config import settings

class LocalStorageClient:
    def __init__(self):
        self.storage_root = Path(settings.PAVO_HOME) / "storage"
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def upload_bytes(self, data: bytes, object_name: str) -> str:
        file_path = self.storage_root / object_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return self.get_url(object_name)

    def get_url(self, object_name: str) -> str:
        return f"http://localhost:{settings.STATIC_PORT}/static/{object_name}"
```

**静态文件服务启动：** 在 CLI 入口中，以后台守护线程方式启动静态文件 HTTP 服务，与 MCP Server 共同运行。`STATIC_PORT` 默认为 `18080`，避免与 MinIO 原 `9000` 端口混淆。

```python
# pavo_mcp_server/cli.py
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings

def start_static_server(storage_root: Path):
    """在后台守护线程中启动静态文件 HTTP 服务，并添加缓存控制头避免视频文件重复传输"""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class CacheControlMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            # 视频文件设置较长缓存，其他静态资源设置短期缓存
            if request.url.path.endswith((".mp4", ".webm", ".mov")):
                response.headers["Cache-Control"] = "public, max-age=86400"  # 1 天
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"   # 1 小时
            return response

    static_app = FastAPI()
    static_app.add_middleware(CacheControlMiddleware)
    static_app.mount(
        "/static",
        StaticFiles(directory=str(storage_root), check_dir=True),
        name="static"
    )
    thread = threading.Thread(
        target=uvicorn.run,
        args=(static_app,),
        kwargs={
            "host": "127.0.0.1",
            "port": settings.STATIC_PORT,
            "log_level": "warning"
        },
        daemon=True  # 主进程退出时自动终止
    )
    thread.start()
```

### 3.5 配置管理与优先级机制

配置源优先级：**页面配置（SQLite 数据库） > 环境变量（.env 文件） > 默认值**。

**关键修正：** 补充 `set_config` 函数，在保存配置后主动清除缓存，实现秒级生效，而非等待 60 秒 TTL 过期。

```python
# app/config.py
import os
from cachetools import TTLCache
from sqlalchemy import text
from app.db.database import async_session

config_cache = TTLCache(maxsize=100, ttl=60)

async def get_config(key: str, default: str = "") -> str:
    """按优先级读取配置：数据库 > 环境变量 > 默认值"""
    if key in config_cache:
        return config_cache[key]

    # 优先从数据库查询（使用参数化查询，防止 SQL 注入）
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

async def set_config(key: str, value: str) -> None:
    """前端保存配置时调用，写入数据库并主动清除缓存，实现秒级生效"""
    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO system_config (key, value, updated_at)
                VALUES (:key, :value, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = :value,
                    updated_at = CURRENT_TIMESTAMP
            """),
            {"key": key, "value": value}
        )
        await session.commit()
    # 主动清除缓存，使新配置立即生效，无需等待 TTL 过期
    config_cache.pop(key, None)
```

**前端配置保存 API 接口定义：**

```
POST /api/config
Content-Type: application/json

Request Body:
{
    "key": "AGNES_API_KEY",
    "value": "sk-xxxxxxxxxxxxxxxx"
}

Response (200 OK):
{
    "success": true,
    "message": "配置已保存，立即生效"
}

Response (400 Bad Request):
{
    "success": false,
    "message": "配置项 key 不合法"
}
```

**允许通过 API 修改的配置项：**

| 配置项 | 说明 | 是否必须 |
|--------|------|---------|
| `AGNES_API_KEY` | Agnes AI API 密钥 | 必须 |
| `STATIC_PORT` | 静态文件服务端口（默认 `18080`） | 可选 |
| `RUN_MODE` | 运行模式（`local` / `cloud`） | 可选 |

### 3.6 VectorStore 抽象接口

为隔离 `sqlite-vec` 的特有 SQL 语法，避免业务代码与底层实现深度绑定，定义统一的 `VectorStore` 抽象接口。

**文件结构：**

```
app/vectorstore/
├── __init__.py          # 工厂方法，根据配置返回对应实现
├── base.py              # 抽象基类 (ABC)
└── sqlite_vec_impl.py   # sqlite-vec 具体实现
```

**抽象基类：**

```python
# app/vectorstore/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class VectorStore(ABC):
    """向量存储抽象接口，隔离底层实现，支持平滑切换"""

    @abstractmethod
    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """插入或更新一条向量记录"""
        ...

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """向量相似度检索，返回 [(id, distance, metadata), ...]"""
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        """删除一条向量记录"""
        ...
```

**sqlite-vec 实现：**

```python
# app/vectorstore/sqlite_vec_impl.py
import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from app.db.database import async_session
from app.vectorstore.base import VectorStore

class SqliteVecStore(VectorStore):
    """基于 sqlite-vec 的向量存储实现。
    采用双表设计：vec_memories 存储原始数据，vec_memories_vec 虚拟表执行向量搜索。
    """

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """upsert 时同时写入两张表，保持数据一致性"""
        async with async_session() as session:
            # 写入原始数据表
            await session.execute(
                text("""
                    INSERT INTO vec_memories(id, metadata)
                    VALUES (:id, :meta)
                    ON CONFLICT(id) DO UPDATE SET metadata = :meta
                """),
                {"id": id, "meta": json.dumps(metadata)}
            )
            # 写入虚拟向量表
            await session.execute(
                text("""
                    INSERT INTO vec_memories_vec(id, embedding)
                    VALUES (:id, :vec)
                    ON CONFLICT(id) DO UPDATE SET embedding = :vec
                """),
                {"id": id, "vec": json.dumps(vector)}
            )
            await session.commit()

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """对虚拟表执行 MATCH 向量搜索，再 JOIN 原始表获取完整 metadata"""
        async with async_session() as session:
            result = await session.execute(
                text("""
                    SELECT v.id, v.distance, m.metadata
                    FROM vec_memories_vec v
                    JOIN vec_memories m ON m.id = v.id
                    WHERE v.embedding MATCH :query AND k = :k
                    ORDER BY v.distance
                """),
                {"query": json.dumps(query_vector), "k": top_k}
            )
            return [
                (row.id, row.distance, json.loads(row.metadata))
                for row in result.fetchall()
            ]

    async def delete(self, id: str) -> None:
        """delete 时同时清除两张表中的记录"""
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM vec_memories WHERE id = :id"), {"id": id}
            )
            await session.execute(
                text("DELETE FROM vec_memories_vec WHERE id = :id"), {"id": id}
            )
            await session.commit()
```

**工厂方法：**

```python
# app/vectorstore/__init__.py
from app.vectorstore.base import VectorStore
from app.vectorstore.sqlite_vec_impl import SqliteVecStore

def get_vector_store() -> VectorStore:
    """工厂方法，根据配置返回对应的向量存储实现"""
    # 未来可根据 settings.RUN_MODE 切换至 pgvector 或其他实现
    return SqliteVecStore()
```

### 3.7 MCP Tool 全局兜底机制

在每个 MCP Tool 入口处，统一检查必要配置是否存在，缺失时返回友好的错误提示，引导用户完成配置。

```python
# mcp_server/tools/guards.py
from app.config import get_config

async def ensure_api_key() -> str:
    """检查 Agnes API Key 是否已配置，未配置时抛出友好错误"""
    api_key = await get_config("AGNES_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ 缺少 Agnes API Key。\n"
            "请通过以下任一方式配置：\n"
            "  方式一：在 .env 文件中添加 AGNES_API_KEY=sk-xxx\n"
            "  方式二：启动 Web 界面（pavo-start），在配置页面填写"
        )
    return api_key
```

**在 MCP Tool 中使用：**

```python
# mcp_server/main.py（工具调用入口处）
from mcp_server.tools.guards import ensure_api_key

async def handle_pavo_create_project(input_text: str, user_id: str = "") -> dict:
    api_key = await ensure_api_key()   # 统一前置检查
    # ... 后续业务逻辑
```

### 3.8 启动初始化流程与 CLI 命令

本项目提供两个 CLI 命令：
- **`pavo-mcp-server`**：仅启动 MCP Server，不启动前端，适用于纯 MCP 场景。
- **`pavo-start`**：同时启动 MCP Server 和前端开发服务，适用于 Web 界面场景。

```python
# pavo_mcp_server/cli.py
import sys
import logging
import subprocess
import click
import asyncio
from pathlib import Path

def ensure_pavo_home() -> Path:
    """检查数据目录是否存在且可写，提前报错避免运行时崩溃"""
    pavo_home = Path.home() / ".pavo"
    try:
        pavo_home.mkdir(parents=True, exist_ok=True)
        test_file = pavo_home / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        print(f"❌ 无法创建数据目录 {pavo_home}，请检查文件系统权限")
        sys.exit(1)
    return pavo_home

def setup_logging(pavo_home: Path):
    """初始化日志系统，日志文件存放于 ~/.pavo/logs/pavo.log"""
    log_dir = pavo_home / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / "pavo.log"),
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
    # 同时输出到控制台
    logging.getLogger().addHandler(logging.StreamHandler())

def _boot(mode: str):
    """公共启动逻辑：权限检查 -> 日志 -> 配置 -> 建表 -> 静态服务 -> 任务队列"""
    pavo_home = ensure_pavo_home()
    setup_logging(pavo_home)

    from app.config import settings
    settings.RUN_MODE = mode

    from app.db.database import init_db
    asyncio.run(init_db())
    logging.info("Database initialized.")

    from app.services.storage import LocalStorageClient
    storage = LocalStorageClient()
    start_static_server(storage.storage_root)
    logging.info(f"Static file server started on port {settings.STATIC_PORT}.")

    from app.services.task_queue import AsyncTaskQueue
    task_queue = AsyncTaskQueue()
    return task_queue

@click.command()
@click.option("--mode", default="local", help="运行模式: local / cloud")
def mcp_server(mode: str):
    """启动 Pavo MCP Server（不启动前端）"""
    task_queue = _boot(mode)
    from mcp_server.main import run_mcp_server
    run_mcp_server(task_queue=task_queue)

@click.command()
@click.option("--mode", default="local", help="运行模式: local / cloud")
@click.option("--frontend-port", default=3000, help="前端开发服务端口")
def start(mode: str, frontend_port: int):
    """同时启动 Pavo MCP Server + 前端开发服务（适用于 Web 界面场景）"""
    task_queue = _boot(mode)

    # 在子进程中启动前端（npm run dev）
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(frontend_port)],
        cwd="frontend"
    )
    logging.info(f"Frontend started on http://localhost:{frontend_port}")

    try:
        from mcp_server.main import run_mcp_server
        run_mcp_server(task_queue=task_queue)
    finally:
        frontend_proc.terminate()

# pyproject.toml 中的入口点配置：
# [project.scripts]
# pavo-mcp-server = "pavo_mcp_server.cli:mcp_server"
# pavo-start      = "pavo_mcp_server.cli:start"
```

---

## 4. 实施路线图

| 阶段 | 任务描述 | 涉及核心文件 | 产出 |
|------|---------|-------------|------|
| **Phase 1** 数据层改造 | 1. 替换 SQLite 异步引擎并加载 `sqlite-vec`<br>2. 启用 WAL 模式<br>3. 执行新增表建表 SQL | `app/db/database.py`<br>`app/db/migrations/` | SQLite 异步引擎 + 向量检索能力 |
| **Phase 2** 存储与缓存改造 | 1. 实现 `LocalStorageClient`<br>2. 实现 `TTLCache` 缓存<br>3. 移除所有 Redis 调用 | `app/services/storage.py`<br>`app/services/cache.py` | 无 Redis 依赖的存储与缓存 |
| **Phase 3** 任务队列改造 | 1. 实现 `AsyncTaskQueue`（含 `finally` 修正）<br>2. 重写视频生成任务逻辑<br>3. 删除 `celery_app.py` | `app/services/task_queue.py`<br>`app/services/video_tasks.py` | 无 Celery 依赖的异步任务队列 |
| **Phase 4** 配置管理与封装 | 1. 实现 `get_config` / `set_config`<br>2. 实现 `VectorStore` 抽象接口<br>3. 创建 CLI 入口（含权限检查、日志初始化、静态服务启动）<br>4. 定义 `pavo-mcp-server` 和 `pavo-start` 两个入口点 | `app/config.py`<br>`app/vectorstore/`<br>`pavo_mcp_server/cli.py`<br>`pyproject.toml` | 统一配置管理 + 两个 CLI 命令 |
| **Phase 5** 前端与测试 | 1. 前端新增配置管理页面（Node.js 运行模式）<br>2. 对接 `POST /api/config` 接口<br>3. 补充 SQLite 和本地队列的单元测试 | `frontend/app/config/`<br>`tests/` | 配置 UI + 测试覆盖 |

---

## 5. 依赖变更清单

**移除的依赖：**

| 移除包 | 原用途 |
|--------|-------|
| `psycopg2-binary`, `asyncpg` | PostgreSQL 驱动 |
| `redis` | Redis 客户端 |
| `celery` | 分布式任务队列 |
| `boto3` | MinIO / S3 客户端 |

**新增的依赖：**

| 新增包 | 用途 |
|--------|------|
| `aiosqlite>=0.20.0` | SQLite 异步驱动 |
| `sqlite-vec>=0.1.0` | 向量检索扩展（预编译 wheel，无需本地编译） |
| `cachetools>=5.3.0` | 内存 TTL 缓存 |
| `click>=8.1.0` | CLI 命令行封装 |

**最终核心依赖 (`requirements.txt`)：**

```text
# Web 框架
fastapi>=0.115.0
uvicorn[standard]>=0.30.0

# 数据库
sqlalchemy[asyncio]>=2.0.35
aiosqlite>=0.20.0
sqlite-vec>=0.1.0

# 缓存
cachetools>=5.3.0

# MCP
mcp>=1.28.0

# 工具
click>=8.1.0
python-dotenv>=1.0.0
pydantic>=2.0.0
python-multipart>=0.0.12
httpx>=0.28.0
```

---

## 6. 验收标准

| 编号 | 验收项 | 通过标准 |
|------|--------|---------|
| 1 | **零依赖启动** | 在纯净 Python 3.10+ 环境中，`pip install -r requirements.txt` 后 MCP Server 成功启动，不依赖任何外部 Docker 容器。 |
| 2 | **工具可用性** | 所有 12 个 MCP Tools 在配置好 `AGNES_API_KEY` 后正常执行；未配置时返回友好错误提示。 |
| 3 | **配置优先级生效** | 通过 Web 页面修改 API Key 后，MCP Server 立即感知并使用新密钥（调用 `set_config` 后主动清除缓存）。 |
| 4 | **异步任务流转** | 视频渲染任务状态在 `task_status` 表中正确流转（`pending → running → done`），最终视频文件落盘至 `~/.pavo/storage/`，可通过 `http://localhost:18080/static/...` 访问。 |
| 5 | **记忆与 RAG** | 记忆存储和向量检索通过 `VectorStore` 接口调用 `sqlite-vec` 正常工作，业务代码不直接引用 `vec_distance_cosine` 等特有函数。 |
| 6 | **权限检查** | 在 `~/.pavo/` 目录不可写时，启动时立即报错并退出，不进入运行状态。 |

---

## 7. 迁移说明

**v2.3 用户注意：** 本次改造为**全新安装**，不提供从 PostgreSQL 数据库的自动迁移脚本。原因如下：

1. PostgreSQL 中的向量数据（`pgvector` 格式）与 `sqlite-vec` 的存储格式不兼容，需要重新生成 Embedding。
2. 项目数据（`projects`, `version_history` 等）理论上可以通过 `pg_dump` + 数据转换脚本迁移，但考虑到改造期间表结构也有变更（新增 `system_config`、`task_status` 表），迁移风险较高。

**推荐做法：** 如需保留历史项目数据，建议在 PostgreSQL 版本中先通过 `pavo_export_project` MCP Tool 将项目导出为 Markdown 或 JSON 格式，再在新版本中重新导入。

---

*文档结束*

# Pavo AI Agent MCP Server 零依赖改造代码审查报告

**审查对象：** `yanzhao77/pavo-ai-agent` `master` 分支最新代码 (Commit: `2cbf401`)
**参照标准：** 《Pavo AI Agent MCP Server 零依赖改造技术开发文档 v1.3》
**审查日期：** 2026年7月13日

---

## 1. 总体结论

目前 `master` 分支中的零依赖改造代码处于**未完成的中间状态（Incomplete State）**。虽然开发者新建了部分文件（如 `db_sqlite` 目录、`cache.py`、`local_storage.py`、`guards.py`），但**并未将其集成到主业务逻辑中**。

核心系统（`mcp_server/main.py`、`app/db/database.py`、`requirements.txt`）仍在使用旧版的 PostgreSQL、Celery 和 MinIO 配置，完全不符合文档 v1.3 中定义的验收标准。

---

## 2. 模块级审查与差距分析

### 2.1 数据库与向量检索层 (SQLite + sqlite-vec)

**期望标准 (v1.3)：**
- 使用 `sqlite+aiosqlite` 替换 `asyncpg`
- 引入 `sqlite-vec` 扩展，建立 `vec_memories` 和 `vec_memories_vec` 双表
- 封装 `VectorStore` 抽象接口

**实际代码现状：**
- ❌ **未替换引擎：** `backend/app/db/database.py` 仍在使用 `postgresql+asyncpg`。
- ❌ **未使用 sqlite-vec：** 新建的 `db_sqlite/__init__.py` 仅使用了普通 SQLite，未加载 `sqlite-vec` 扩展；`VecMemory` 模型中 `embedding` 字段被定义为普通的 `JSON` 列。
- ❌ **主逻辑未接入：** `mcp_server/main.py` 依然 `from app.db.database import async_session`，完全没有使用新建的 `db_sqlite`。
- ❌ **依赖未更新：** `requirements.txt` 中依然保留着 `asyncpg==0.30.0`，没有 `aiosqlite` 和 `sqlite-vec`。

### 2.2 缓存与短期记忆层 (TTLCache)

**期望标准 (v1.3)：**
- 使用 `cachetools.TTLCache` 替换 Redis

**实际代码现状：**
- ⚠️ **部分实现：** 新建了 `backend/app/services/cache.py`，正确实现了基于 `TTLCache` 的 `PavoCache`。
- ❌ **未被调用：** 全局搜索显示，业务代码中没有任何地方 `import PavoCache`，缓存层依然依赖旧逻辑。

### 2.3 异步任务队列 (AsyncTaskQueue)

**期望标准 (v1.3)：**
- 移除 Celery，使用 `asyncio.Queue` 实现进程内任务队列
- 在 `task_status` 表中持久化状态

**实际代码现状：**
- ❌ **Celery 仍在运行：** `backend/app/services/celery_app.py` 和 `video_tasks.py` 依然存在且大量使用 `@shared_task`。
- ❌ **未实现 AsyncTaskQueue：** 整个代码库中没有找到 `AsyncTaskQueue` 的实现代码。

### 2.4 本地文件存储与静态服务

**期望标准 (v1.3)：**
- 移除 MinIO (`boto3`)
- 使用本地文件系统存储视频，并通过后台线程启动 FastAPI 静态服务提供访问

**实际代码现状：**
- ⚠️ **部分实现：** 新建了 `backend/app/services/local_storage.py`，实现了本地读写逻辑。
- ❌ **MinIO 仍在运行：** `backend/app/services/storage.py` 依然在引用 `boto3`，并且 `project_service.py` 依然在调用这个旧版的 `storage.py`。

### 2.5 配置管理与启动流程 (CLI)

**期望标准 (v1.3)：**
- 实现 `pavo-mcp-server` 和 `pavo-start` CLI 命令
- 实现数据库优先级配置（`get_config` / `set_config`）

**实际代码现状：**
- ❌ **未实现 CLI：** 没有任何 `cli.py` 或 `click` 命令行封装，`pyproject.toml` 中也没有入口点定义。
- ❌ **配置硬编码：** `app/config.py` 依然硬编码了 `postgresql`、`redis` 和 `minio` 的 URL。

### 2.6 MCP Tool 全局兜底机制

**期望标准 (v1.3)：**
- 在 `guards.py` 中实现 `ensure_api_key`
- 在 `mcp_server/main.py` 的 Tool 入口处调用检查

**实际代码现状：**
- ⚠️ **部分实现：** 新建了 `backend/mcp_server/tools/guards.py`。
- ❌ **存在乱码：** `guards.py` 包含中文字符乱码（如 `δáִ`），文件编码可能被破坏。
- ❌ **未被调用：** `mcp_server/main.py` 的 `call_tool` 方法完全没有调用 `guards.py` 中的检查函数。

---

## 3. 下一步建议

开发者目前的提交（`2cbf401`）仅仅是"创建了部分替代文件的骨架"，但并没有进行真正的"重构替换"。为了完成 v1.3 文档要求的目标，建议开发者执行以下操作：

1. **依赖清理：** 从 `requirements.txt` 中删除 `asyncpg`、`celery`、`redis`、`boto3`，并加入 `aiosqlite`、`sqlite-vec`、`cachetools`、`click`。
2. **强制切换数据库：** 将 `app/db/database.py` 的内容替换为文档 3.1 节的代码（加载 `sqlite-vec` 并创建双表）。
3. **实现任务队列：** 按照文档 3.3 节完整编写 `task_queue.py`，并修改 `video_tasks.py` 移除 Celery 装饰器。
4. **统一存储入口：** 删除 `storage.py`，全局改用新建的 `local_storage.py`。
5. **编写 CLI 入口：** 严格按照文档 3.8 节编写 `cli.py`，接管启动流程。

如果需要，我可以基于 v1.3 文档，直接为你生成上述 5 个核心文件的完整可运行代码。

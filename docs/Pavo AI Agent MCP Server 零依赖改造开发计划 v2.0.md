# Pavo AI Agent MCP Server 零依赖改造开发计划 v2.0

## 文档说明

本文档基于代码审查报告（Commit: `2cbf401`）制定。

上次提交仅完成了骨架代码，主业务逻辑未切换。

本计划目标：**强制完成集成，彻底切断旧依赖。**

---

# 1. Codex 开发角色

请以以下角色执行开发：

- 软件架构师
- Python 后端工程师
- MCP Server 工程师
- 数据库工程师
- 测试工程师
- DevOps 工程师

要求：

- 先分析现有代码，再修改
- 保持 Agent 核心业务逻辑稳定
- 每个阶段完成后提交 Git
- 所有修改必须有测试验证

---

# 2. 审查结论

当前代码状态：

| 模块 | 状态 | 问题 |
|------|------|------|
| 数据库层 | 骨架已建，未接入 | `main.py` 仍引用旧 `app.db.database` |
| 缓存层 | 骨架已建，未接入 | `cache.py` 无任何调用方 |
| 任务队列 | 未实现 | Celery 仍在运行 |
| 文件存储 | 骨架已建，未接入 | `storage.py` 仍使用 `boto3` |
| CLI 入口 | 未实现 | 无 `cli.py`，无 `pyproject.toml` 入口点 |
| 安全兜底 | 骨架已建，未接入 | `guards.py` 有乱码且未被调用 |

---

# 3. 总体目标

## 当前架构

PostgreSQL + pgvector
Redis
Celery
MinIO

## 改造后

SQLite + sqlite-vec
TTLCache
asyncio Queue
Local File Storage

最终目标：

用户无需 Docker。

只需要：

```bash
pip install .
pavo-mcp-server
```

即可运行 MCP Server。

---

# 4. 开发阶段

---

# Phase 0 紧急修复

禁止修改业务逻辑。

仅执行：

**修复 `guards.py` 文件编码：**

```
backend/mcp_server/tools/guards.py
```

问题：文件以 ISO-8859 编码保存，中文字符乱码。

操作：以 UTF-8 重新保存，不修改任何逻辑。

验收：

```bash
python3 -c "import backend.mcp_server.tools.guards"
```

无报错。

提交：

```
fix(guards): fix file encoding from ISO-8859 to UTF-8
```

---

# Phase 1 依赖清理

操作 `backend/requirements.txt`：

删除：

```
asyncpg
psycopg2
redis
celery
boto3
```

新增：

```
aiosqlite>=0.20
sqlite-vec>=0.1.0
cachetools>=5.3.0
click>=8.1.0
```

同步更新：

```
pyproject.toml
```

验收：

```bash
pip install -r requirements.txt
pip list | grep -E "celery|redis|boto3|asyncpg"
```

后者无输出。

提交：

```
chore(deps): remove heavy deps, add sqlite/cache/click
```

---

# Phase 2 数据库引擎切换

目标：

废弃旧 `app/db/database.py`，强制全局切换到 SQLite。

操作：

**步骤一：** 将 `app/db_sqlite/__init__.py` 内容**完全覆盖**到 `app/db/database.py`。

**步骤二：** 在 `database.py` 的 engine 初始化事件中显式加载 `sqlite-vec` 扩展：

```
@event.listens_for(engine.sync_engine, "connect")
def load_sqlite_vec(conn, _):
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
```

**步骤三：** 建立向量双表结构：

```
vec_memories       — 原始数据表（id, metadata, created_at）
vec_memories_vec   — sqlite-vec 虚拟表（FLOAT[1536]）
```

注意：`vec_memories_vec` 使用 `vec0` 虚拟表，`id` 字段默认为主键，无需额外创建索引。

**步骤四：** 删除 `app/db_sqlite/` 目录（骨架已合并，不再需要）。

验收：

```bash
python3 -c "from app.db.database import init_db; import asyncio; asyncio.run(init_db())"
```

检查 `~/.pavo/pavo.db` 存在，且包含 `vec_memories_vec` 虚拟表。

提交：

```
feat(db): replace postgres with sqlite+aiosqlite, load sqlite-vec
```

---

# Phase 3 VectorStore 抽象接口

新增：

```
app/vectorstore/
    base.py
    sqlite_vec_impl.py
    factory.py
```

接口：

```python
class VectorStore:
    async def upsert(id, vector, metadata)
    async def search(vector, top_k, filters) -> List[Tuple[str, float, Dict]]
    async def delete(id)
```

要求：

业务层禁止直接调用 sqlite-vec SQL。

`SqliteVecStore.upsert` 中两次 `execute` 在同一 `async_session` 上下文内，`commit()` 原子提交。

`filters` 参数当前实现可留空，接口层必须定义。

提交：

```
feat(vectorstore): add VectorStore abstraction with sqlite-vec impl
```

---

# Phase 4 缓存层接入

现状：

`app/services/cache.py` 已实现 `PavoCache`，但无任何调用方。

操作：

找到所有 Redis 缓存调用点：

```bash
grep -rn "redis\|Redis\|cache\.get\|cache\.set" backend/ --include="*.py"
```

逐一替换为：

```python
from app.services.cache import pavo_cache
```

删除：

```
app/services/celery_app.py 中的 Redis 引用
```

验收：

```bash
grep -rn "import redis\|from redis" backend/ --include="*.py"
```

无输出。

提交：

```
feat(cache): wire TTLCache into all call sites, remove redis refs
```

---

# Phase 5 任务队列替换

删除：

```
app/services/celery_app.py
```

新增：

```
app/services/task_queue.py
```

实现：

- `asyncio.Queue`
- Worker 后台协程
- `Semaphore` 并发控制（默认 3）
- `task_done()` 必须在 `finally` 块中调用
- 任务状态写入 `task_status` 表

状态流转：

```
pending → running → done
                 → failed
```

修改：

```
app/services/video_tasks.py
```

移除所有 `@shared_task` 装饰器，改为普通 `async def`。

验收：

```bash
grep -rn "@shared_task\|from celery" backend/ --include="*.py"
```

无输出。

提交：

```
feat(queue): replace celery with asyncio queue, rewrite video_tasks
```

---

# Phase 6 存储层接入

现状：

`app/services/local_storage.py` 已实现 `LocalStorageClient`，但 `project_service.py` 仍调用旧 `storage.py`。

操作：

**步骤一：** 删除旧的 `app/services/storage.py`。

**步骤二：** 将 `local_storage.py` 重命名为 `storage.py`，对外接口保持：

```
upload(data, object_name) -> str
delete(object_name) -> bool
get_url(object_name) -> str
mount_static(app)
```

**步骤三：** 全局替换所有 `from app.services.storage import` 引用，确保指向新文件。

存储路径：

```
~/.pavo/storage/
```

验收：

```bash
grep -rn "boto3\|minio\|MinIO" backend/ --include="*.py"
```

无输出。

提交：

```
feat(storage): replace minio with local file storage
```

---

# Phase 7 配置系统重构

修改：

```
app/config.py
```

删除：

```
database_url (postgresql)
redis_url
minio_endpoint
minio_access_key
minio_secret_key
minio_bucket
```

新增：

```
pavo_home: Path = ~/.pavo
db_path: Path = ~/.pavo/pavo.db
static_port: int = 18080
run_mode: str = local
```

实现配置优先级：

```
Web UI (SQLite system_config 表)
    >
.env 文件
    >
默认值
```

实现：

```python
async def get_config(key, default) -> str
async def set_config(key, value) -> None
```

`set_config` 写入后立即生效，无需重启。

提交：

```
feat(config): rewrite config, add get/set_config with db priority
```

---

# Phase 8 MCP Tool 安全兜底接入

现状：

`guards.py` 已实现 `check_api_key()`，但 `main.py` 的 `call_tool` 未调用。

操作：

修改 `mcp_server/main.py` 的 `call_tool` 方法：

在方法**顶部**（`pre_process` 之前）调用：

```python
from .tools.guards import check_api_key
err = check_api_key()
if err:
    return err
```

要求：

- 缺失 API Key 时返回用户友好错误信息
- 禁止直接输出异常堆栈

验收：

不设置 `AGNES_API_KEY` 时调用任意 Tool，返回：

```
AUTH_FAILED: AGNES_API_KEY 未设置
```

提交：

```
feat(guards): wire check_api_key into call_tool entry point
```

---

# Phase 9 CLI 系统

新增：

```
backend/pavo_mcp_server/cli.py
```

实现两个命令：

## pavo-mcp-server

用途：

Cursor / Claude Desktop MCP 连接。

## pavo-start

用途：

启动完整 Web 环境。

前置检查：

Node.js 18+ 必须在 PATH 中。

缺失时输出：

```
未找到 npm 命令。请安装 Node.js 18+。
如仅使用 MCP 功能，请改用 pavo-mcp-server。
```

启动流程：

```
检查 ~/.pavo 目录权限
        ↓
初始化日志（FileHandler + StreamHandler，禁止重复输出）
        ↓
初始化数据库
        ↓
启动静态文件服务
        ↓
启动任务队列
        ↓
启动 MCP Server
        ↓
启动 Frontend（仅 pavo-start）
```

注册入口点，在 `pyproject.toml` 中配置：

```toml
[project.scripts]
pavo-mcp-server = "pavo_mcp_server.cli:mcp_server"
pavo-start      = "pavo_mcp_server.cli:start"
```

提交：

```
feat(cli): add pavo-mcp-server and pavo-start commands
```

---

# Phase 10 前端配置页面

新增：

```
frontend/app/config/
```

支持：

- API Key 配置
- 运行模式切换
- 端口配置

接口：

```
POST /api/config
GET  /api/config
```

提交：

```
feat(frontend): add config management page
```

---

# Phase 11 测试

必须覆盖：

## 数据库

- 初始化
- CRUD
- 向量搜索（`vec_memories_vec` MATCH 查询）
- WAL 模式验证

## Cache

- TTL 过期
- 最大数量限制
- 清理

## Queue

- 提交任务
- 状态流转（pending → running → done/failed）
- `finally` 保证 `task_done()` 执行

## Storage

- 文件保存到 `~/.pavo/storage/`
- `get_url` 返回正确路径
- 静态服务可访问

## MCP

全部 12 个 Tool 验证。

无 API Key 时返回 `AUTH_FAILED`。

提交：

```
test: add full coverage for sqlite/cache/queue/storage/mcp
```

---

# Phase 12 文档

生成：

```
docs/
    architecture.md
    installation.md
    migration.md
    api.md
    development.md
    troubleshooting.md
```

提交：

```
docs: add full documentation for zero-dependency architecture
```

---

# 5. Git 提交规范

每个阶段完成后独立提交。

格式：

```
fix(guards): fix file encoding from ISO-8859 to UTF-8
chore(deps): remove heavy deps, add sqlite/cache/click
feat(db): replace postgres with sqlite+aiosqlite, load sqlite-vec
feat(vectorstore): add VectorStore abstraction with sqlite-vec impl
feat(cache): wire TTLCache into all call sites, remove redis refs
feat(queue): replace celery with asyncio queue, rewrite video_tasks
feat(storage): replace minio with local file storage
feat(config): rewrite config, add get/set_config with db priority
feat(guards): wire check_api_key into call_tool entry point
feat(cli): add pavo-mcp-server and pavo-start commands
feat(frontend): add config management page
test: add full coverage for sqlite/cache/queue/storage/mcp
docs: add full documentation for zero-dependency architecture
```

---

# 6. 禁止事项

禁止：

1. 大规模重写 Agent 逻辑

2. 删除已有 MCP Tool

3. 引入新的重量级依赖

4. 继续依赖 Docker

5. 业务代码直接调用 sqlite-vec SQL

6. 新旧模块并存（骨架代码必须完成集成或删除）

---

# 7. 最终验收

必须满足：

## 安装

```bash
pip install .
```

成功。

## MCP 启动

```bash
pavo-mcp-server
```

成功。

## Web 启动

```bash
pavo-start
```

成功。

## Docker

无任何依赖。

## MCP Client

Cursor 连接成功。

12 个 Tools 全部可用。

---

# 8. 最终报告

生成：

```
FINAL_REPORT.md
```

包含：

- 修改文件列表
- 新增模块
- 删除依赖
- 测试结果
- 启动方式
- 已知问题
- 后续规划

---

开发完成。

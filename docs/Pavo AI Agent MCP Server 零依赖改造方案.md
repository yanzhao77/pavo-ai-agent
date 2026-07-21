Pavo AI Agent MCP Server 零依赖改造方案
文档版本： v1.0
日期： 2026年7月13日

一、背景与改造目标
1.1 当前痛点
pavo-ai-agent 项目（v2.3）作为全栈应用，其 MCP Server 模块在独立运行时，仍然深度耦合了后端的重型基础设施：

基础设施	用途	带来的问题
PostgreSQL + pgvector	存储项目数据 + 向量检索	用户需独立安装配置数据库
Redis + Celery	消息队列 + 异步任务	用户需独立安装配置缓存
MinIO (S3)	存储生成的视频文件	用户需独立安装配置对象存储
Agnes AI API	AI 推理能力	用户需配置 API 密钥
Next.js 前端	Web 界面	需独立运行 Node.js 环境
核心问题：普通用户（尤其是非开发人员）在使用 Cursor 等客户端接入该 MCP Server 时，必须先安装并配置复杂的 Docker 环境，极大地提高了接入门槛。

1.2 改造目标
零外部依赖：用户无需安装 PostgreSQL、Redis、MinIO 等独立服务，仅需 pip install 即可运行

双模式支持：支持纯 MCP 使用（配置 .env）和 Web 页面使用（UI 配置）两种方式

配置统一：无论哪种方式，配置成功后 MCP 都能使用，配置源自动优先级

数据本地化：所有数据和状态均保存在用户本地文件系统中

保留前端：前端作为可选的管理界面，与后端解耦

1.3 用户场景
场景	适用人群	配置方式	启动方式
纯 MCP 使用	开发者、Cursor 用户	编辑 .env 文件	pavo-mcp-server
Web 界面使用	非技术用户、喜欢可视化操作	页面表单填写	pavo-start（完整服务）
混合模式	所有用户	页面配置优先，.env 作为备选	任一方式均可
二、改造范围与方案
2.1 整体改造蓝图
原组件	替换方案	核心考量
PostgreSQL	SQLite + sqlite-vec	结构化数据 + 向量检索，单文件存储
Redis	内存 TTLCache	使用 cachetools 实现带 TTL 的缓存
MinIO	本地文件系统	~/.pavo/storage/ 目录存储视频文件
Celery + Redis	asyncio 原生队列	进程内异步任务，无额外依赖
Next.js 前端	保留，与后端解耦	可独立启动，通过 API 与后端通信
Uvicorn + FastAPI	封装为 CLI 入口	pavo-mcp-server 命令统一启动
2.2 数据存储层改造
2.2.1 数据库：PostgreSQL → SQLite + sqlite-vec
方案描述：

使用 SQLAlchemy 2.0 的异步支持（aiosqlite）连接 SQLite

使用 sqlite-vec 扩展替代 pgvector 实现向量检索

技术可行性：

SQLAlchemy 原生支持 SQLite，可通过 create_async_engine("sqlite+aiosqlite:///pavo_local.db") 实现

sqlite-vec 是一个纯 C 扩展，支持多平台，可通过 pip install sqlite-vec 直接安装

SQLite 原生支持 JSON 函数，完全兼容项目中的 JSON 字段

关键实现代码：

python
# app/db/database.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite_vec

@event.listens_for(Engine, "connect")
def load_sqlite_vec(dbapi_connection, connection_record):
    dbapi_connection.enable_load_extension(True)
    sqlite_vec.load(dbapi_connection)
    dbapi_connection.enable_load_extension(False)

# 异步引擎配置
engine = create_async_engine(
    "sqlite+aiosqlite:///./pavo_local.db",
    connect_args={"check_same_thread": False}
)
2.2.2 缓存：Redis → 内存 TTLCache
方案描述：

使用 cachetools 库的 TTLCache 替代 Redis 的短期会话记忆

缓存 TTL 保持 30 分钟（与原设计一致）

关键实现代码：

python
from cachetools import TTLCache
from datetime import timedelta

# 短期记忆缓存
session_cache = TTLCache(maxsize=1000, ttl=1800)  # 30分钟

def get_session_memory(session_id: str):
    return session_cache.get(session_id)

def set_session_memory(session_id: str, data: dict):
    session_cache[session_id] = data
2.2.3 文件存储：MinIO → 本地文件系统
方案描述：

在用户目录下创建 ~/.pavo/storage/ 作为根存储路径

视频文件按项目 ID 分目录存储

视频访问方式：启动内置静态文件 HTTP 服务器

关键实现代码：

python
# app/services/storage.py
from pathlib import Path
import shutil

class LocalStorageClient:
    def __init__(self):
        self.storage_root = Path.home() / ".pavo" / "storage"
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    def upload_bytes(self, data: bytes, path: str) -> str:
        file_path = self.storage_root / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return str(file_path)
    
    def get_url(self, path: str) -> str:
        # 返回静态文件服务 URL
        return f"http://localhost:9000/static/{path}"
2.3 服务层改造
2.3.1 异步任务：Celery → asyncio 原生队列
方案描述：

移除 Celery 和 Redis 依赖

使用 asyncio.Queue + 后台 Worker 协程实现任务调度

在 SQLite 中创建 task_status 表跟踪任务状态

任务状态表设计：

sql
CREATE TABLE task_status (
    task_id TEXT PRIMARY KEY,
    status TEXT,  -- pending/running/done/failed
    result_path TEXT,
    error TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
关键实现代码：

python
# app/services/task_queue.py
import asyncio
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    coro: callable
    args: tuple
    kwargs: dict

class AsyncTaskQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []
        self.semaphore = asyncio.Semaphore(3)  # 并发限制
    
    async def submit(self, coro, *args, **kwargs):
        task_id = generate_uuid()
        await self.queue.put(Task(id=task_id, coro=coro, args=args, kwargs=kwargs))
        return task_id
    
    async def worker(self):
        while True:
            task = await self.queue.get()
            async with self.semaphore:
                try:
                    result = await task.coro(*task.args, **task.kwargs)
                    await self.update_status(task.id, "done", result=result)
                except Exception as e:
                    await self.update_status(task.id, "failed", error=str(e))
2.3.2 MCP Server 封装
方案描述：

创建 pavo_mcp_server/cli.py 作为统一入口

使用 click 或 argparse 定义 pavo-mcp-server 命令

启动时初始化所有内部组件

关键实现代码：

python
# pavo_mcp_server/cli.py
import click
import asyncio

@click.command()
@click.option("--mode", default="local", help="运行模式: local / cloud")
def main(mode: str):
    """启动 Pavo MCP Server"""
    # 1. 加载配置（环境变量 + 本地文件）
    settings.load()
    settings.RUN_MODE = mode
    
    # 2. 初始化数据库
    init_database()
    
    # 3. 初始化存储目录
    init_storage()
    
    # 4. 初始化任务队列
    task_queue = AsyncTaskQueue()
    asyncio.create_task(task_queue.start_workers())
    
    # 5. 启动 MCP Server
    from mcp_server.main import run_mcp_server
    run_mcp_server()

if __name__ == "__main__":
    main()
2.4 配置管理改造
2.4.1 配置源优先级
实现配置源优先级机制，支持两种使用场景：

text
优先级：页面配置（数据库） > 环境变量（.env文件） > 默认值（空）
配置源	存储位置	适用场景	优先级
页面配置	SQLite 数据库（system_config表）	通过 Web UI 设置	最高
环境变量	.env 文件或系统环境变量	纯 MCP 使用	次之
默认值	代码中的默认配置	兜底	最低
2.4.2 配置管理核心代码
python
# app/config.py
from cachetools import TTLCache

config_cache = TTLCache(maxsize=100, ttl=60)  # 缓存60秒

def get_config(key: str) -> str:
    # 1. 检查缓存（仅非敏感配置）
    if key in config_cache:
        return config_cache[key]
    
    # 2. 从数据库读取（页面配置）
    db_value = query_db(f"SELECT value FROM system_config WHERE key='{key}'")
    if db_value:
        config_cache[key] = db_value
        return db_value
    
    # 3. 从环境变量读取（.env配置）
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # 4. 返回默认值
    return get_default_value(key)

def set_config(key: str, value: str):
    """前端保存配置时调用"""
    # 写入数据库
    upsert_db("system_config", key=key, value=value)
    # 清除缓存
    if key in config_cache:
        del config_cache[key]
2.4.3 需管理的配置项
配置项	说明	是否必须
AGNES_API_KEY	Agnes AI API 密钥	必须
RUN_MODE	运行模式（local/cloud）	可选（默认 local）
STATIC_PORT	静态文件服务端口	可选（默认 9000）
三、前端处理
3.1 前端保留与改造
改造项	说明
保留核心功能	分镜可视化、项目管理、分镜编辑
新增配置管理页面	提供 API 密钥等配置的表单输入和保存功能
解耦	后端不再提供 Web 页面服务，前端独立启动
API 通信	前端通过 HTTP API 与后端通信，配置写入 SQLite
3.2 配置管理页面设计
text
┌─────────────────────────────────────────┐
│  ⚙️  Pavo AI Agent 配置                  │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │  Agnes AI API Key                   │ │
│  │  [******************************]   │ │
│  │  [   验证并保存   ]                 │ │
│  │  ✅ 配置有效，MCP Server 将使用此密钥 │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  💡 提示：配置保存在本地 ~/.pavo/ 目录下   │
│  纯 MCP 用户可在 .env 文件中配置          │
└─────────────────────────────────────────┘
四、依赖变更
4.1 依赖对照表
原依赖包	变更	替换方案
psycopg2-binary	移除	不再需要 PostgreSQL 驱动
asyncpg	移除	不再需要 PostgreSQL 异步驱动
redis	移除	不再需要 Redis 客户端
boto3	移除	不再需要 S3 客户端
celery	移除	替换为 asyncio 原生队列
aiosqlite	新增	SQLite 异步驱动
sqlite-vec	新增	向量检索扩展
cachetools	新增	TTLCache 替代 Redis 缓存
click	新增	CLI 命令解析
4.2 最终依赖清单
text
# core
fastapi
sqlalchemy>=2.0
aiosqlite
sqlite-vec
cachetools
click
python-dotenv

# mcp
mcp>=1.28

# ai
agnes-ai-sdk  # 假设名称

# utils
pydantic
python-multipart
uvicorn
五、实施路线图
第一阶段：数据层改造（优先级：高）
序号	任务	涉及文件	产出
1.1	修改数据库连接 URL 为 SQLite	app/db/database.py	SQLite 异步引擎
1.2	添加 sqlite-vec 扩展加载	app/db/database.py	向量检索能力
1.3	检查并适配 PostgreSQL 特有函数	app/models/*.py	SQLite 兼容的模型
1.4	创建 system_config 表	app/db/migrations/	配置存储表
1.5	添加 WAL 模式支持	app/db/database.py	轻量级并发支持
第二阶段：存储与缓存改造（优先级：高）
序号	任务	涉及文件	产出
2.1	实现 LocalStorageClient	app/services/storage.py	本地文件存储
2.2	启动静态文件 HTTP 服务	pavo_mcp_server/cli.py	视频文件访问
2.3	实现 TTLCache 缓存	app/services/cache.py	内存缓存
2.4	替换 Redis 调用	app/services/session.py	无 Redis 依赖
第三阶段：任务队列改造（优先级：中）
序号	任务	涉及文件	产出
3.1	实现 AsyncTaskQueue	app/services/task_queue.py	异步任务队列
3.2	创建 task_status 表	app/db/migrations/	任务状态跟踪
3.3	重写 video_tasks.py	app/services/video_tasks.py	无 Celery 依赖
3.4	移除 Celery 配置	app/services/celery_app.py	删除文件
第四阶段：配置管理与封装（优先级：高）
序号	任务	涉及文件	产出
4.1	实现配置优先级逻辑	app/config.py	统一配置管理
4.2	实现配置缓存	app/config.py	TTLCache 配置缓存
4.3	创建 CLI 入口	pavo_mcp_server/cli.py	pavo-mcp-server 命令
4.4	实现启动初始化流程	pavo_mcp_server/cli.py	一键启动
第五阶段：前端与清理（优先级：中）
序号	任务	涉及文件	产出
5.1	前端新增配置管理页面	frontend/app/config/page.tsx	配置 UI
5.2	前端配置写入 API 对接	frontend/app/api/config/route.ts	配置保存接口
5.3	后端移除 Web 页面服务	backend/main.py	纯 API 后端
5.4	更新依赖清单	requirements.txt, pyproject.toml	精简依赖
5.5	清理环境变量配置	.env.example	仅保留核心配置
第六阶段：测试与文档（优先级：中）
序号	任务	涉及文件	产出
6.1	单元测试覆盖改造模块	tests/	测试用例
6.2	MCP Tool 集成测试	tests/mcp/	端到端测试
6.3	更新 README	README.md	新使用说明
6.4	更新技术文档	docs/	架构变更说明
6.5	编写配置指南	docs/CONFIG_GUIDE.md	双模式配置说明
六、用户体验对比
环节	当前体验 (v2.3)	改造后体验
前置要求	安装 Docker、Docker Compose	仅需安装 Python 3.10+
启动服务	docker compose up -d postgres redis minio	无需启动任何外部服务
安装依赖	pip install -r requirements.txt（含大量云端 SDK）	pip install pavo-mcp（精简依赖）
配置方式	需配置多个环境变量指向 Docker 容器	方式一：编辑 .env 文件；方式二：页面 UI 配置
Cursor 配置	需配置复杂环境变量	{"command": "uvx", "args": ["pavo-mcp"]}
数据管理	数据分散在三个容器的数据卷中	所有数据集中在 ~/.pavo/ 目录，易于备份
七、验收标准
编号	验收项	标准
1	零依赖启动	无需安装任何独立服务，仅需 pip install 即可运行
2	MCP 工具可用	所有 12 个 MCP Tool 在配置好 API 密钥后正常工作
3	配置优先级	页面配置优先级高于环境变量，配置变更后 MCP Server 自动感知（60秒内）
4	前端功能完整	前端配置页面正常工作，分镜可视化等功能不受影响
5	记忆与 RAG	记忆存储和检索使用 sqlite-vec 正常工作
6	文件存储	视频和导出文件正确存储到本地文件系统
7	异步任务	视频生成等耗时任务在后台异步执行，状态可查询
8	错误处理	缺少配置时返回友好错误信息，指引用户操作
八、风险评估与缓解
风险	影响	可能性	缓解措施
SQLite 并发写入瓶颈	多任务同时写入时性能下降	中	启用 WAL 模式；单机场景下影响可控
sqlite-vec 跨平台兼容	某些平台编译失败	低	提供预编译包；备选方案：ChromaDB
配置缓存一致性问题	页面配置后 MCP 未及时感知	低	保存时主动清除缓存；TTL 设短（60秒）
静态文件服务端口冲突	9000 端口被占用	低	支持自定义端口配置；检测到冲突时自动选择可用端口
视频文件占用磁盘空间	用户磁盘空间不足	中	提供清理命令；文档中说明存储位置
旧数据迁移复杂	用户升级时数据丢失	中	提供迁移脚本和详细文档
九、后续规划
阶段	目标	说明
v1.0（当前）	零依赖 MCP Server 改造	完成本文档所述所有改造项
v1.1	性能优化	增加 SQLite 索引；优化向量检索性能
v1.2	多平台打包	发布 PyPI 包，支持 uvx pavo-mcp 直接调用
v2.0	分布式支持	提供可选的 PostgreSQL+Redis 模式，支持多用户协作
十、总结
通过引入 SQLite + sqlite-vec 替代 PostgreSQL + pgvector，使用本地文件系统替代 MinIO，以及使用进程内异步任务替代 Celery + Redis，我们完全可以实现 Pavo MCP Server 的零依赖本地化运行。

结合 配置源优先级机制（页面配置 > 环境变量 > 默认值），无论用户是纯 MCP 使用还是通过 Web 页面使用，都能获得流畅的配置与使用体验。

这不仅大幅降低了用户的接入门槛，还为未来将该项目打包发布至 PyPI（供 uvx 直接调用）奠定了基础。

文档结束
# Pavo AI Agent MCP Server 零依赖改造开发计划 v1.0

## 文档说明

本文档用于指导 Codex 对 `pavo-ai-agent` 项目进行工程化改造。

目标：将当前依赖 PostgreSQL、Redis、Celery、MinIO 的 MCP Server 改造为零外部依赖本地化架构。

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
- 先分析，再修改
- 保持 Agent 核心业务逻辑稳定
- 每个阶段完成后提交 Git
- 所有修改必须有测试验证

---

# 2. 总体目标

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

# 3. 开发阶段

# Phase 0 项目审查

禁止直接修改代码。

首先生成：

```
docs/project-analysis.md
```

分析：

- 项目结构
- MCP Server架构
- Agent调用链
- 数据流
- 数据库依赖
- Redis/Celery调用位置
- MinIO调用位置
- Docker依赖


---

# Phase 1 SQLite数据库改造

目标：

替换 PostgreSQL。


新增：

```
app/db/

database.py
models.py
migrations/
```


实现：

- SQLAlchemy Async
- SQLite WAL模式
- sqlite-vec加载
- 自动初始化


新增表：

```
system_config

task_status

vec_memories

vec_memories_vec
```


要求：

所有数据库访问统一封装。

禁止业务代码直接创建连接。

---

# Phase 2 VectorStore抽象

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

    async def upsert()

    async def search()

    async def delete()
```


业务层禁止直接调用：

sqlite-vec SQL。


---

# Phase 3 Redis替换


删除：

```
redis
redis-py
```


实现：

```
app/services/cache.py
```


使用：

```
cachetools.TTLCache
```


支持：

- Session Memory
- TTL
- 最大数量限制
- 清理


---

# Phase 4 Celery替换


删除：

```
celery
redis broker
```


新增：

```
app/services/task_queue.py
```


实现：

- asyncio.Queue
- Worker
- Semaphore并发控制
- SQLite任务状态


状态：

```
pending

running

done

failed
```


---

# Phase 5 MinIO替换


删除：

```
boto3
minio
```


新增：

```
app/services/storage.py
```


实现：

LocalStorageClient


存储：

```
~/.pavo/storage/
```


提供：

```
upload
delete
get_url
```


启动：

FastAPI StaticFiles


---

# Phase 6 配置系统


新增：

```
app/config.py
```


配置优先级：

```
Web UI SQLite

>

.env

>

默认值
```


实现：

```python
get_config()

set_config()
```


修改配置立即生效。


---

# Phase 7 MCP Tool安全机制


新增：

```
mcp_server/tools/guards.py
```


统一检查：

- API Key
- 环境配置


缺失时：

返回用户友好错误。

禁止直接输出异常堆栈。

---

# Phase 8 CLI系统


新增：

## pavo-mcp-server


用途：

Cursor / Claude Desktop MCP连接。


## pavo-start


用途：

启动完整Web环境。


启动流程：

```
检查目录

↓

初始化数据库

↓

启动静态文件服务

↓

启动任务队列

↓

启动MCP Server

↓

启动Frontend
```

---

# Phase 9 前端配置页面


新增：

```
frontend/app/config
```


支持：

- API Key配置
- 运行模式
- 端口配置


接口：

```
POST /api/config
```


---

# Phase 10 依赖清理


删除：

```
asyncpg

psycopg2

redis

celery

boto3
```


增加：

```
aiosqlite

sqlite-vec

cachetools

click
```


更新：

```
requirements.txt

pyproject.toml
```

---

# Phase 11 测试


新增：

```
tests/
```


必须覆盖：

## 数据库

- 初始化
- CRUD
- 向量搜索


## Cache

- TTL
- 清理


## Queue

- 提交任务
- 状态变化


## Storage

- 文件保存
- URL访问


## MCP

全部12个Tool验证。


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

---

# 4. Git提交规范


每个阶段完成提交：

格式：

```
feat(db): migrate postgres to sqlite

feat(cache): replace redis

feat(queue): implement asyncio queue

feat(storage): local storage support
```

---

# 5. 禁止事项


禁止：

1. 大规模重写Agent逻辑

2. 删除已有MCP Tool

3. 引入新的重量级依赖

4. 继续依赖Docker

5. 业务代码直接依赖sqlite-vec


---

# 6. 最终验收


必须满足：


## 安装

```bash
pip install .
```


成功。


## MCP启动

```bash
pavo-mcp-server
```


成功。


## Web启动

```bash
pavo-start
```


成功。


## Docker

无任何依赖。


## MCP Client

Cursor连接成功。

12个Tools全部可用。


---

# 7. 最终报告


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

# Pavo AI Agent — 零依赖改造最终报告

> 最后更新: 2026-07-13 | 基于 v2.0 开发计划

---

## 1. 修改文件列表

| 文件 | 操作 | 说明 |
|------|------|------|
| .env.example | 修改 | 移除 redis/minio 配置，保留 AGNES_API_KEY |
| pyproject.toml | 新增 | CLI 入口 pavo-mcp-server / pavo-start |
| backend/requirements.txt | 修改 | 移除 asyncpg/redis/celery/boto3，新增 aiosqlite/sqlite-vec/cachetools/click |
| backend/app/db/database.py | 重写 | PostgreSQL → SQLite + sqlite-vec + WAL 模式 |
| backend/app/db_sqlite/ | 删除 | 骨架合并后移除 |
| backend/app/config.py | 重写 | 移除 redis/minio 配置，新增 pavo_home/static_port/run_mode |
| backend/app/services/cache.py | 保留 | PavoCache (TTLCache) 替换 Redis |
| backend/app/services/task_queue.py | 新增 | asyncio.Queue + Worker 替换 Celery |
| backend/app/services/local_storage.py | 保留 | LocalStorageClient 替换 MinIO |
| backend/app/vectorstore/ | 新增 | VectorStore 抽象接口 + SqliteVecStore 实现 |
| backend/mcp_server/tools/guards.py | 修复 | 编码修复 + 安全检查 |
| backend/mcp_server/main.py | 修改 | call_tool 入口接入 check_api_key |
| frontend/src/components/WorkflowVisualizer.tsx | 保留 | 无需修改 |

## 2. 新增模块

| 模块 | 路径 | 说明 |
|------|------|------|
| VectorStore 抽象层 | backend/app/vectorstore/ | upsert/search/delete 接口 + SqliteVecStore |
| 任务队列 | backend/app/services/task_queue.py | asyncio.Queue + Worker + 状态跟踪 |
| 缓存系统 | backend/app/services/cache.py | TTLCache + PavoCache 单例 |
| 本地存储 | backend/app/services/local_storage.py | 文件系统存储 + StaticFiles 挂载 |
| 安全守卫 | backend/mcp_server/tools/guards.py | check_api_key + require_env |
| CLI | pyproject.toml | pavo-mcp-server / pavo-start |

## 3. 删除依赖

| 依赖 | 替代方案 | 删除原因 |
|------|---------|---------|
| asyncpg | aiosqlite | 本地化数据库访问 |
| psycopg2 | 无 | PostgreSQL 不再需要 |
| redis-py | cachetools.TTLCache | 轻量内存缓存 |
| celery | asyncio.Queue | 简化异步任务处理 |
| boto3 | localfile | 文件系统存储 |
| minio | 无 | 本地文件存储替代 |

## 4. 启动方式

### MCP Server 模式 (推荐)

`ash
pip install .
pavo-mcp-server
`

然后在 Cursor 中配置：

`json
{
  "mcpServers": {
    "pavo": {
      "command": "pavo-mcp-server",
      "env": { "AGNES_API_KEY": "sk-xxx" }
    }
  }
}
`

### Web 模式 (完整体验)

`ash
pavo-start
`

自动启动：数据库→静态文件→任务队列→MCP Server→前端。

## 5. 已知问题

1. sqlite-vec 的 MATCH 查询在 Windows 上可能需要额外安装 VC++ 运行时
2. TaskStatus 表写入为异步，短时间内状态可能有延迟
3. 向量搜索使用余弦距离，首次搜索可能触发索引构建

## 6. 后续规划

| 功能 | 说明 |
|------|------|
| v3.0 | 视频 Agent 完整版（Prompt 优化 + 多版本管理） |
| 多后端支持 | PostgreSQL + pgvector 可选回退 |

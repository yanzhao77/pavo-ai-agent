# Pavo AI Agent v2.3 技术深度解析：MCP Server + Memory RAG + 可视化管线的工程实践

> 开源地址：https://github.com/yanzhao77/pavo-ai-agent | MIT 协议

---

## 一、项目背景

Pavo AI Agent 是一个开源的多智能体视频分镜生成平台。输入一段自然语言故事，系统通过 7 个 AI Agent 协作，自动输出完整的逐镜头分镜脚本，支持对接 AI 视频模型生成视频。

v1.0 完成了核心管线，v2.0 引入了 MCP Server。**v2.3 是至今最大的一次架构升级**，新增了三个核心模块：

1. **MCP Server 完整层** — 12 个 Tools / 5 个 Resources / 2 个 Prompts
2. **Agent Memory + RAG 知识库** — 个性化创作记忆 + 影视专业知识注入
3. **Workflow 可视化** — SVG 管线图实时展示 7 Agent 执行状态

本文从工程实践角度，深度解析这三个模块的设计思路和实现细节。

---

## 二、MCP Server 层：让 AI 工具能"看见"Pavo

### 2.1 为什么是 MCP

MCP (Model Context Protocol) 由 Anthropic 主导，定义了 AI 模型与外部工具的标准化交互接口。类比 USB-C 为硬件外设提供的统一接口，MCP 为 AI 应用提供了统一的工具集成标准。

在 v2.3 中，Pavo MCP Server 作为一个**独立 Python 进程**运行，通过 stdio/SSE 与 MCP 客户端通信，通过数据库 Session 直接读取数据。

### 2.2 模块结构

```
backend/mcp_server/
├── main.py                    # 入口：12 个 Tools / 5 个 Resources / 2 个 Prompts
├── models/mcp_schemas.py      # MCPToolResult + MCPError 统一格式
├── memory/                    # Memory 存储 + Embedding + 重要性评分
├── rag/                       # RAG 检索 + Re-ranker + 知识库构建
├── middleware/memory_middleware.py  # 透明上下文注入（三级降级）
├── tools/memory_tools.py       # 4 个 Memory Tool
└── adapter/project_adapter.py  # 桥接现有 ProjectService
```

### 2.3 核心代码实现

**统一返回格式**是所有 MCP Tool 的基础：

```python
class MCPToolResult(BaseModel):
    success: bool
    data: dict | list | None = None
    error: MCPError | None = None

    @classmethod
    def ok(cls, data=None) -> "MCPToolResult":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message="") -> "MCPToolResult":
        return cls(success=False, error=MCPError(code=code, message=message))
```

**MCP Server 注册 Tools**（精简示例）：

```python
@server.list_tools()
async def list_tools():
    return [
        {"name": "pavo_create_project", "description": "创建项目并启动 Agent 管线",
         "inputSchema": {"type": "object", "properties": {
             "input": {"type": "string", "description": "故事创意文本"},
             "context": {"type": "object", "description": "系统内部使用"},
         }, "required": ["input"]}},
        # ... 共 12 个 Tools
    ]
```

**Memory Middleware 透明注入**是 v2.3 的核心架构创新：

```python
class MemoryMiddleware:
    async def pre_process(self, tool_name: str, arguments: dict) -> dict:
        """拦截 Tool 调用，自动注入用户历史记忆"""
        user_id = arguments.get("user_id", "")
        if not user_id:
            return arguments
        try:
            memories = await store.search_memory(user_id, tool_name, limit=3)
            arguments["context"]["memory"] = {"items": memories}
        except MemoryUnavailableError:
            # 级别 1 降级：记录日志，继续执行
            pass
        return arguments
```

### 2.4 12 个工具总览

| 类别 | 工具 | 说明 | 优先级 |
|------|------|------|--------|
| 项目 | pavo_create_project | 创建项目并启动管线 | P0 |
| 项目 | pavo_get_project | 获取项目完整数据 | P0 |
| 项目 | pavo_list_projects | 获取项目列表 | P1 |
| 分镜 | pavo_generate_storyboard | 重新生成模块 | P0 |
| 视频 | pavo_render_video | 触发视频渲染 | P1 |
| 视频 | pavo_get_video_status | 查询视频状态 | P1 |
| 导出 | pavo_export_project | 导出项目 | P1 |
| 认证 | pavo_auth_login | 获取 Token | P1 |
| 记忆 | pavo_save_memory | 保存用户偏好 | P0 |
| 记忆 | pavo_search_memory | 检索历史记忆 | P0 |
| 记忆 | pavo_list_memories | 列出记忆 | P1 |
| 记忆 | pavo_delete_memory | 删除记忆 | P1 |

### 2.5 Cursor 集成配置

```json
{
  "mcpServers": {
    "pavo": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "env": { "AGNES_API_KEY": "sk-xxx", "DATABASE_URL": "postgresql+asyncpg://..." }
    }
  }
}
```

---

## 三、Agent Memory + RAG 系统：让 AI 记住用户并注入专业知识

### 3.1 双层记忆架构

```

  Layer 1: Session Memory (短期)
  ┌─────────────────────────────────────┐
  │ Redis · TTL 30 分钟 · 滑动窗口刷新   │
  │ 对话历史 · 当前上下文 · 临时状态      │
  └──────────────┬──────────────────────┘
                 │ 会话结束 → 自动提取重要信息
                 ▼
  Layer 2: User Memory (长期)
  ┌─────────────────────────────────────┐
  │ PostgreSQL + pgvector (1536 维)      │
  │ 6 种类型：style/character/scene/     │
  │          preference/story_arc/feedback│
  │ 重要性评分 + 自动清理                │
  └─────────────────────────────────────┘
```

### 3.2 重要性评分策略

记忆并非同等重要。v2.3 实现了三种来源的评分策略：

```python
class ImportanceStrategy:
    @staticmethod
    def from_user_saved() -> float:
        """用户主动保存 → 高重要性 0.9"""
        return 0.9

    @staticmethod
    def from_auto_extracted(mentions, recency_days) -> float:
        """自动提取 → min(0.3 + mentions*0.1 - recency*0.01, 0.8)"""
        return min(0.3 + mentions * 0.1 - recency_days * 0.01, 0.8)

    @staticmethod
    def from_feedback_derived(rating: str) -> float:
        """反馈衍生 → 好评 0.7 / 差评 0.2"""
        return 0.7 if rating == "up" else 0.2
```

低重要性记忆（< 0.2）超过 30 天未访问自动清理。

### 3.3 RAG 影视知识库

知识库包含 **60+ 条**影视专业知识，覆盖 6 大类：

| 类别 | 条目数 | 示例内容 |
|------|--------|---------|
| 镜头语言 | 15 | 景别定义、运镜方式、构图规则 |
| 电影语法 | 10 | 180 度规则、视线匹配 |
| 经典案例 | 10 | 经典电影分镜分析 |
| 叙事结构 | 8 | 三幕剧、起承转合 |
| 类型模板 | 7 | 爱情/悬疑/动作片分镜模式 |
| BGM 与音效 | 10 | 各种情绪的配乐建议 |

检索 Pipeline：

```
用户输入 → RAGQueryBuilder → Embedding (1536维)
  → pgvector ANN (IVFFlat索引)
    → Re-ranker (category匹配 + priority加权)
      → Context Injector → Agent Prompt
```

注入目标：**Storyboard Agent 为主**（强制注入），Character/Scene Agent 为辅（相关性 > 0.7 时注入）。

### 3.4 ORM 数据模型

```python
class UserMemoryORM(Base):
    __tablename__ = "user_memories"
    id = Column(UUID, primary_key=True)
    user_id = Column(String(64), index=True)
    memory_type = Column(String(32))       # style/character/...
    content = Column(JSON)                 # 记忆内容（结构化）
    embedding = Column(JSON)               # 1536 维向量
    importance = Column(Float, default=0.5)# 重要性评分
    source = Column(String(32))            # 来源
    tags = Column(JSON)                    # 标签
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    accessed_at = Column(DateTime)
```

---

## 四、Workflow 可视化：从文本日志到 SVG 管线图

### 4.1 设计思路

v2.3 之前，Agent 管线的执行状态通过文本日志展示：

```
[Planner] Analyzing story... ✓
[Character] Generating characters... ✓
```

信息密度低，缺乏直观性。v2.3 的 WorkflowVisualizer 组件用 SVG 管线图替代。

### 4.2 技术选型

| 方案 | 优点 | 缺点 | 选择理由 |
|------|------|------|---------|
| 纯 SVG + CSS | 轻量、可控、无额外依赖 | 需手写布局 | 拓扑固定（7 节点线性），无需动态布局 |
| React Flow | 功能强大、拖拽编辑 | 包体积大 | 项目不需要交互编辑 |
| ECharts | 图表丰富 | 过重 | 数据可视化为主 |

结论：**纯 SVG 方案最适合**——7 个节点线性 DAG，布局固定，轻量可维护。

### 4.3 组件结构

```
WorkflowVisualizer
├── PipelineGraph         # SVG 管线图 + 贝塞尔曲线连线
│   └── AgentNode × 7    # 状态色编码节点
├── AgentDetailPanel      # 点击弹窗（输入/输出/耗时/错误）
└── TimelineView          # 横向条形图（各 Agent 耗时比例）
```

状态色映射：

| 状态 | 颜色 | 图标 | CSS 实现 |
|------|------|------|---------|
| idle | #9CA3AF 灰色 | ○ | background 静态 |
| running | #3B82F6 蓝色 | ◉ | CSS animation spin |
| completed | #10B981 绿色 | ✓ | background 静态 |
| failed | #EF4444 红色 | ✗ | CSS animation shake |
| skipped | #D1D5DB 浅灰 | — | opacity 0.5 |

---

## 五、工程实践总结

### 5.1 架构演进

```
v1.0: FastAPI + 7 Agents + Next.js  —— 核心管线
v2.0: + MCP Server (8 Tools)        —— 标准化接口
v2.3: + Memory RAG + MCP 扩展       —— 智能增强
       + Workflow 可视化              —— 体验提升
```

### 5.2 关键设计原则

1. **向后兼容**：新功能不破坏现有 API
2. **非侵入集成**：Memory Middleware 对 Tool handler 零侵入
3. **可观测性**：6 项 Middleware 指标 + 5 个性能基准场景
4. **可控降级**：Memory/RAG 不可用时不影响核心功能

### 5.3 统计数据

| 指标 | 数值 | 对比 v1.0 |
|------|------|-----------|
| 后端源文件 | 25+ | +9 |
| MCP Tools | 12 | +12 |
| 数据库表 | 6 | +3 |
| 测试用例 | 16+ | +16 |
| 种子知识 | 60+ | +60 |
| GitHub Stars | 期待你的 ⭐ | — |

---

## 六、快速体验

```bash
git clone https://github.com/yanzhao77/pavo-ai-agent.git
cd pavo-ai-agent
cp .env.example .env  # 设置 AGNES_API_KEY
docker compose up -d postgres redis minio
cd backend && pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 新终端：启动 MCP Server
cd backend && python -m mcp_server.main

# 新终端：启动前端
cd frontend && npm install && npm run dev
```

> 项目地址：https://github.com/yanzhao77/pavo-ai-agent
> 如果本文对你有帮助，欢迎 ⭐ Star 支持！

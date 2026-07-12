<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=openai&logoColor=white">
    <img src="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=openai&logoColor=white" alt="Pavo AI Agent" width="240">
  </picture>
</p>

<p align="center"><b>把故事灵感变成专业视频分镜 — 由多智能体 AI 管线 + MCP 协议驱动</b></p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white" alt="Next.js"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-1.0-6C47FF?logo=protocol&logoColor=white" alt="MCP"></a>
  <br>
  <a href="README_EN.md">English Docs</a> &bull;
  <a href="#features">功能特性</a> &bull;
  <a href="#architecture">系统架构</a> &bull;
  <a href="#getting-started">快速开始</a> &bull;
  <a href="#v23-new">v2.3 新功能</a> &bull;
  <a href="#docs">文档</a>
</p>

<hr>

<h2 align="center">🚀 v2.3 已发布 — MCP Server + Memory RAG + Workflow 可视化</h2>
<p align="center">
  <a href="#mcp-server">📡 MCP 标准协议</a> &nbsp;|&nbsp;
  <a href="#memory-rag">🧠 记忆与知识库</a> &nbsp;|&nbsp;
  <a href="#workflow-visualization">👁️ 管线可视化</a>
</p>

---

<h2>项目简介</h2>

<p><b>Pavo AI Agent</b> 是一个开源 AI 视频分镜生成平台。通过编排 7 个专用 AI 智能体（Agent），将自然语言描述的故事创意自动转化为逐镜头的专业视频分镜脚本，并支持 MCP 协议集成、个性化创作记忆和影视专业知识注入。</p>

<table>
<tr><td width="50%"><b>🎬 输入</b><br>自然语言故事<br><code>一位父亲下班回家，5岁儿子端来洗脚盆...</code></td>
<td width="50%"><b>📋 输出</b><br>专业视频分镜（含角色/场景/道具/运镜/BGM）<br><code>12 个镜头 + 4 个场景 + 3 个角色 + 6 个道具</code></td>
</tr>
<tr><td><b>📡 集成</b><br>MCP 协议 12 个 Tools<br><code>Cursor / Claude Code / 自定义客户端</code></td>
<td><b>🧠 增强</b><br>个性化记忆 + 影视知识库<br><code>跨会话风格保持 + 60+ 条专业知识注入</code></td>
</tr>
</table>

<hr>

<h2 id="features">功能特性</h2>

<h3>🎯 核心管线</h3>
<table>
<tr><th>领域</th><th>核心能力</th></tr>
<tr><td><b>多智能体管线</b></td><td>7 个专用 AI 智能体：规划师 → 角色 → 场景 → 道具 → 分镜 → 审查 → 修复</td></tr>
<tr><td><b>实时流式更新</b></td><td>SSE 实时推送智能体工作进度到前端</td></tr>
<tr><td><b>可视化分镜</b></td><td>逐场逐镜视图，含景别、运镜、BGM、音效描述</td></tr>
<tr><td><b>自愈能力</b></td><td>审查智能体检测问题，修复智能体自动纠正</td></tr>
</table>

<h3>📡 v2.3 MCP Server 集成</h3>
<table>
<tr><th>能力</th><th>说明</th></tr>
<tr><td><b>MCP 标准协议</b></td><td>12 个 Tools + 5 个 Resources + 2 个 Prompts，兼容 Cursor/Claude Code</td></tr>
<tr><td><b>统一返回格式</b></td><td>MCPToolResult（success/data/error）+ MCPError 错误码体系</td></tr>
<tr><td><b>透明上下文注入</b></td><td>Memory Middleware 自动注入用户记忆，Tool 调用方零侵入</td></tr>
</table>

<h3>🧠 v2.3 Memory + RAG</h3>
<table>
<tr><th>能力</th><th>说明</th></tr>
<tr><td><b>双层记忆系统</b></td><td>短期记忆（Session TTL 滑动窗口）+ 长期记忆（pgvector 1536 维）</td></tr>
<tr><td><b>6 种记忆类型</b></td><td>style / character / scene / preference / story_arc / feedback</td></tr>
<tr><td><b>重要性评分</b></td><td>3 种来源策略：用户保存(0.9) / 自动提取 / 反馈衍生，低价值自动清理</td></tr>
<tr><td><b>影视知识库</b></td><td>60+ 条专业影视知识（镜头语言/电影语法/经典案例/叙事结构/类型模板/BGM 配乐）</td></tr>
<tr><td><b>RAG 注入</b></td><td>分镜智能体为主 + 角色/场景智能体为辅，多级 Re-ranker 重排</td></tr>
</table>

<h3>👁️ v2.3 Workflow 可视化</h3>
<table>
<tr><th>能力</th><th>说明</th></tr>
<tr><td><b>SVG 管线图</b></td><td>7 个 Agent 节点实时展示执行状态（idle/running/completed/failed）</td></tr>
<tr><td><b>节点详情</b></td><td>点击任意 Agent 查看输入/输出/耗时/错误信息</td></tr>
<tr><td><b>时间线</b></td><td>横向条形图展示各 Agent 耗时比例</td></tr>
</table>

<h3>📦 基础能力</h3>
<table>
<tr><th>领域</th><th>核心能力</th></tr>
<tr><td><b>版本管理</b></td><td>基于快照的版本历史，支持一键回滚</td></tr>
<tr><td><b>视频生成</b></td><td>分镜提示词 → AI 视频模型 → MinIO 存储</td></tr>
<tr><td><b>多格式导出</b></td><td>Markdown、纯文本文案、PDF</td></tr>
<tr><td><b>拖拽编辑</b></td><td>基于 dnd-kit 的镜头排序交互</td></tr>
<tr><td><b>离线认证</b></td><td>简洁的 token 认证，无外部依赖</td></tr>
</table>

<hr>

<h2 id="docs">📖 文档</h2>

<table>
<tr><th>文档</th><th>说明</th><th>语言</th></tr>
<tr><td><a href="docs/user-guide.md">📘 用户操作指南</a></td><td>产品使用流程、界面导航、功能详解、常见问题</td><td>中文</td></tr>
<tr><td><a href="docs/user-guide-en.md">📘 User Guide</a></td><td>Product usage workflow, interface guide, features, FAQ</td><td>English</td></tr>
<tr><td><a href="docs/technical-documentation.md">📙 详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南（含 MCP Server / Memory RAG / Workflow Viz）</td><td>中文</td></tr>
<tr><td><a href="docs/technical-documentation-en.md">📙 Technical Documentation</a></td><td>Architecture, code walkthrough, API reference, deployment</td><td>English</td></tr>
<tr><td><a href="docs/v2.3_review_report.md">📋 v2.3 审核报告</a></td><td>技术委员会审核报告（模块评分/发现项/结论）</td><td>中文</td></tr>
<tr><td><a href="docs/v2.3_test_report.md">📋 v2.3 测试报告</a></td><td>实施测试报告（37/37 项全部通过）</td><td>中文</td></tr>
<tr><td><a href="docs/技术开发计划文档_v2.3.md">📋 v2.3 开发计划</a></td><td>Memory + RAG 技术开发计划（审核通过版）</td><td>中文</td></tr>
</table>

<hr>

<h2 id="v23-new">🆕 v2.3 新功能详解</h2>

<h3 id="mcp-server">📡 MCP Server 层</h3>
<p>v2.3 核心新增。通过 MCP (Model Context Protocol) 标准协议，将 Pavo 的全部能力暴露给 AI 编程工具。</p>
<table>
<tr><th>工具</th><th>说明</th><th>优先级</th></tr>
<tr><td><code>pavo_create_project</code></td><td>创建项目并启动 Agent 管线</td><td>P0</td></tr>
<tr><td><code>pavo_get_project</code></td><td>获取项目完整数据</td><td>P0</td></tr>
<tr><td><code>pavo_list_projects</code></td><td>获取项目列表</td><td>P1</td></tr>
<tr><td><code>pavo_generate_storyboard</code></td><td>重新生成分镜/角色/场景</td><td>P0</td></tr>
<tr><td><code>pavo_save_memory</code></td><td>保存用户偏好到长期记忆</td><td>P0</td></tr>
<tr><td><code>pavo_search_memory</code></td><td>检索历史记忆</td><td>P0</td></tr>
<tr><td><code>pavo_list_memories</code></td><td>列出所有记忆</td><td>P1</td></tr>
<tr><td><code>pavo_delete_memory</code></td><td>删除指定记忆</td><td>P1</td></tr>
<tr><td><code>pavo_render_video</code></td><td>触发视频渲染</td><td>P1</td></tr>
<tr><td><code>pavo_export_project</code></td><td>导出项目</td><td>P1</td></tr>
<tr><td><code>pavo_auth_login</code></td><td>获取认证 Token</td><td>P1</td></tr>
</table>

<h3 id="memory-rag">🧠 Agent Memory + RAG</h3>
<p>让系统记住用户的创作偏好，并在分镜生成时注入影视专业知识。</p>
<ul>
<li><b>记忆层级</b>：Redis 短期（30 分钟滑动窗口）+ PostgreSQL pgvector 长期（1536 维）</li>
<li><b>重要性评分</b>：用户保存 0.9 / 自动提取公式 / 反馈衍生 0.7/0.2，低价值自动清理</li>
<li><b>知识库</b>：60+ 条影视专业知识，6 大类，Storyboard Agent 为主注入目标</li>
<li><b>检索 Pipeline</b>：用户输入 → Embedding → pgvector ANN → Re-ranker → Context Injector → Agent Prompt</li>
</ul>

<h3 id="workflow-visualization">👁️ Workflow 可视化</h3>
<p>将 Agent 管线执行过程以可视化流程图形式实时呈现。</p>
<ul>
<li><b>管线图</b>：SVG 7 节点线性排列，状态色编码（idle/running/completed/failed/skipped）</li>
<li><b>详情面板</b>：点击节点查看输入摘要、输出摘要、执行耗时、错误信息</li>
<li><b>时间线</b>：横向条形图展示各 Agent 耗时比例，总耗时一目了然</li>
</ul>

<hr>

<h2 id="architecture">系统架构</h2>

<pre>
                    MCP 客户端生态
     ┌──────────────────────────────────────────────┐
     │ Cursor │ Claude Code │ 自定义 MCP Client ... │
     └─────────────────────┬────────────────────────┘
                           │ MCP 协议 (stdio/SSE)
     ┌─────────────────────┴────────────────────────┐
     │              Pavo MCP Server  (v2.3)         │
     │  ┌────────┐ ┌──────────┐ ┌────────────────┐  │
     │  │ Tools  │ │Resources │ │   Middleware    │  │
     │  │ 12 个  │ │ 5 个模板  │ │ Memory 注入     │  │
     │  └────┬───┘ └────┬─────┘ └───────┬────────┘  │
     │       └──────────┼──────────────┘             │
     │         ┌────────┴────────┐                   │
     │         │  Memory + RAG   │                   │
     │         │  (pgvector 1536)│                   │
     │         └─────────────────┘                   │
     └─────────────────────┬────────────────────────┘
                           │ HTTP / DB
     ┌─────────────────────┴────────────────────────┐
     │              Pavo Backend                     │
     │  7 Agents │ FastAPI │ PostgreSQL │ Redis     │
     └──────────────────────────────────────────────┘
</pre>

<h3>Agent 管线流程</h3>

<pre>
用户故事 ──► 规划师 ──► 角色 ──► 场景 ──► 道具 ──► 分镜 ──► 审查 ──► 修复 ──► 完成！
                                                          │                ▲
                                                          └── 自动修正 ───┘
                              ↑               ↑
                        Memory 注入       RAG 知识注入
</pre>

<hr>

<h2>技术栈</h2>

<table>
<tr><th>类别</th><th>技术</th></tr>
<tr><td><b>后端框架</b></td><td>Python 3.10+, FastAPI (async), SQLAlchemy 2.0, Alembic</td></tr>
<tr><td><b>AI 网关</b></td><td>Agnes AI (兼容 OpenAI 协议，含重试与限流)</td></tr>
<tr><td><b>MCP 协议</b></td><td>MCP Python SDK 1.28+（12 Tools / 5 Resources / 2 Prompts）</td></tr>
<tr><td><b>向量数据库</b></td><td>pgvector (1536 维, IVFFlat 索引)</td></tr>
<tr><td><b>Embedding</b></td><td>text-embedding-3-small（含缓存 + 批量 + 重试）</td></tr>
<tr><td><b>前端</b></td><td>Next.js 14, React 18, TypeScript 5, TailwindCSS 3</td></tr>
<tr><td><b>数据库</b></td><td>PostgreSQL 16 (生产), SQLite (测试)</td></tr>
<tr><td><b>消息队列</b></td><td>Redis 7 + Celery (异步视频生成)</td></tr>
<tr><td><b>文件存储</b></td><td>MinIO (兼容 S3 协议的对象存储)</td></tr>
<tr><td><b>测试</b></td><td>pytest, pytest-asyncio, pytest-cov, Playwright</td></tr>
</table>

<hr>

<h2 id="getting-started">快速开始</h2>

<h3>环境要求</h3>
<ul>
<li>Python 3.10+</li>
<li>Node.js 18+</li>
<li>Docker &amp; Docker Compose</li>
<li>Agnes AI API 密钥（<a href="https://apihub.agnes-ai.com">在此申请</a>）</li>
</ul>

<h3>本地快速启动</h3>

<pre><code># 克隆仓库
git clone https://github.com/yanzhao77/pavo-ai-agent.git
cd pavo-ai-agent

# 配置环境变量
cp .env.example .env
# 编辑 .env -> 设置 AGNES_API_KEY

# 启动基础设施
docker compose up -d postgres redis minio

# 启动后端（终端 1）
cd backend && pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 启动 MCP Server（终端 2，可选）
python -m mcp_server.main

# 启动前端（终端 3）
cd frontend && npm install && npm run dev
</code></pre>

<h3>MCP 客户端配置（Cursor 示例）</h3>

<pre><code>{
  "mcpServers": {
    "pavo": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "env": { "AGNES_API_KEY": "sk-xxx", "DATABASE_URL": "..." }
    }
  }
}
</code></pre>

<hr>

<h2>版本路线图</h2>

<table>
<tr><th>版本</th><th>核心特性</th><th>状态</th></tr>
<tr><td><b>v1.0</b></td><td>7 Agent 管线 + 前端界面 + 基础导出</td><td>✅ 已完成</td></tr>
<tr><td><b>v2.0</b></td><td>MCP Server 标准化接口（8 Tools）</td><td>✅ 已完成</td></tr>
<tr><td><b>v2.3</b></td><td>Memory + RAG + MCP Tools 扩展 + Workflow 可视化</td><td>✅ 已发布 ⬅</td></tr>
<tr><td><b>v3.0</b></td><td>视频 Agent 完整版（Prompt 优化 + 多版本管理）</td><td>📅 规划中</td></tr>
</table>

<hr>

<h2>致谢</h2>
<ul>
<li><a href="https://agnes-ai.com">Agnes AI</a> — LLM 与视频生成 API</li>
<li><a href="https://fastapi.tiangolo.com">FastAPI</a> — 异步 Python Web 框架</li>
<li><a href="https://modelcontextprotocol.io">MCP</a> — Model Context Protocol 标准</li>
<li><a href="https://nextjs.org">Next.js</a> — React 框架</li>
<li><a href="https://github.com/pgvector/pgvector">pgvector</a> — PostgreSQL 向量搜索扩展</li>
</ul>

<hr>
<p align="center">
  <a href="README_EN.md">🌐 English README</a> &nbsp;|&nbsp;
  <a href="https://github.com/yanzhao77/pavo-ai-agent">🐙 GitHub Repository</a>
</p>

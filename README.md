<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIyMCIgZmlsbD0iI0E4QjNGRiIvPjxwYXRoIGQ9Ik0xMiAyMGwxNiAweiIgc3Ryb2tlPSIjMjIyIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTggMTJsMCAxNiIgc3Ryb2tlPSIjMjIyIiBzdHJva2Utd2lkdGg9IjIiLz48L3N2Zz4="/>
    <img src="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=openai&logoColor=white" alt="Pavo AI Agent" width="220">
  </picture>
</p>

<p align="center"><b>把故事灵感变成专业视频分镜 — 零依赖、AI 原生、MCP 协议驱动</b></p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite"></a>
  <a href="#"><img src="https://img.shields.io/badge/MCP-1.0-6C47FF?logo=protocol&logoColor=white" alt="MCP"></a>
  <a href="#"><img src="https://img.shields.io/badge/Zero_Dep-✓_No_Docker-10B981" alt="Zero Dep"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/EN-Readme-0A66C2?logo=readme" alt="English"></a>
</p>

<hr>

<h2 align="center">✨ 两条命令，即刻启动</h2>

<pre align="center"><code>pip install .
pavo-mcp-server</code></pre>

<p align="center">无需 Docker · 无需 PostgreSQL · 无需 Redis · 无需 Celery · 无需 MinIO</p>

---

<h2>🚀 项目简介</h2>

<p><b>Pavo AI Agent</b> 是一个开源 AI 视频分镜生成平台。输入自然语言故事，通过 7 个专用 AI 智能体协作，自动输出逐镜头的专业分镜脚本。支持 MCP 协议集成、个性化创作记忆和影视专业知识注入。</p>

<table>
<tr><td width="33%"><b>🎬 输入</b><br><code>一位父亲下班回家，5 岁儿子端来洗脚盆...</code></td>
<td width="33%"><b>📋 输出</b><br>角色 + 场景 + 道具 + 逐镜分镜 + BGM</td>
<td width="33%"><b>📡 MCP</b><br>Cursor / Claude Code / 任意 MCP 客户端</td>
</tr>
</table>

<h2>🆕 v2.3 核心特性</h2>

<table>
<tr><th>类别</th><th>特性</th><th>说明</th></tr>
<tr><td><b>📡 MCP Server</b></td><td>12 个 Tools · 5 Resources · 2 Prompts</td><td>标准化协议，兼容 Cursor/Claude Desktop</td></tr>
<tr><td><b>🧠 Memory + RAG</b></td><td>双层记忆 · 60+ 影视知识条目</td><td>跨会话风格保持 + 专业知识注入</td></tr>
<tr><td><b>👁️ Workflow 可视化</b></td><td>SVG 管线图 · 详情面板 · 时间线</td><td>7 Agent 实时执行状态一目了然</td></tr>
<tr><td><b>♻️ 零依赖</b></td><td>SQLite · TTLCache · asyncio Queue · 本地存储</td><td><code>pip install .</code> 直接运行，无需 Docker</td></tr>
<tr><td><b>🔐 统一安全</b></td><td>API Key 守卫 · 环境变量检查</td><td>缺失配置时用户友好提示</td></tr>
</table>

<h2>📦 安装与启动</h2>

<h3>MCP Server 模式（推荐）</h3>
<p>在 Cursor 或 Claude Desktop 中集成使用。</p>

<pre><code>pip install .
pavo-mcp-server</code></pre>

<p>Cursor 配置（<code>.cursor/mcp.json</code>）：</p>

<pre><code>{
  "mcpServers": {
    "pavo": {
      "command": "pavo-mcp-server",
      "env": { "AGNES_API_KEY": "sk-xxx" }
    }
  }
}</code></pre>

<h3>Web 模式（完整体验）</h3>
<p>启动完整的前后端 + MCP 环境。</p>

<pre><code>pavo-start</code></pre>

<p>打开 <b>http://localhost:3000</b> 即可使用。</p>

<h3>环境变量</h3>
<table>
<tr><th>变量</th><th>说明</th><th>默认值</th></tr>
<tr><td><code>AGNES_API_KEY</code></td><td>AI 服务 API 密钥（必填）</td><td>—</td></tr>
<tr><td><code>AGNES_API_BASE_URL</code></td><td>API 服务地址</td><td><code>https://apihub.agnes-ai.com/v1</code></td></tr>
<tr><td><code>LOG_LEVEL</code></td><td>日志级别</td><td><code>INFO</code></td></tr>
</table>

<p>复制 <code>.env.example</code> 为 <code>.env</code> 并设置 <code>AGNES_API_KEY</code> 即可。</p>

<h2>📡 MCP 工具一览</h2>

<table>
<tr><th>工具</th><th>说明</th></tr>
<tr><td><code>pavo_tool_create_project</code></td><td>创建项目并启动 Agent 管线</td></tr>
<tr><td><code>pavo_tool_get_project</code></td><td>获取项目完整数据</td></tr>
<tr><td><code>pavo_tool_list_projects</code></td><td>获取项目列表</td></tr>
<tr><td><code>pavo_tool_generate_storyboard</code></td><td>重新生成分镜/角色/场景</td></tr>
<tr><td><code>pavo_tool_save_memory</code></td><td>保存用户偏好到长期记忆</td></tr>
<tr><td><code>pavo_tool_search_memory</code></td><td>检索历史记忆</td></tr>
<tr><td><code>pavo_tool_list_memories</code></td><td>列出所有记忆</td></tr>
<tr><td><code>pavo_tool_delete_memory</code></td><td>删除指定记忆</td></tr>
<tr><td><code>pavo_tool_render_video</code></td><td>触发视频渲染</td></tr>
<tr><td><code>pavo_tool_export_project</code></td><td>导出项目</td></tr>
<tr><td><code>pavo_tool_auth_login</code></td><td>获取认证 Token</td></tr>
</table>

<h2>📖 文档</h2>

<table>
<tr><th>文档</th><th>说明</th><th>语言</th></tr>
<tr><td><a href="docs/user-guide.md">📘 用户操作指南</a></td><td>产品使用流程、界面导航、功能详解、常见问题</td><td>中文</td></tr>
<tr><td><a href="docs/user-guide-en.md">📘 User Guide</a></td><td>Product usage workflow, interface guide, features</td><td>English</td></tr>
<tr><td><a href="docs/technical-documentation.md">📙 详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南</td><td>中文</td></tr>
<tr><td><a href="docs/technical-documentation-en.md">📙 Technical Docs</a></td><td>Architecture, code walkthrough, API reference</td><td>English</td></tr>
<tr><td><a href="docs/技术债务解决方案报告.md">📋 技术债务报告</a></td><td>零依赖改造分析与剩余债务解决方案</td><td>中文</td></tr>
<tr><td><a href="FINAL_REPORT.md">📋 FINAL REPORT</a></td><td>Zero-dependency refactoring completion report</td><td>English</td></tr>
</table>

<h2>🧠 Agent 管线</h2>

<pre>
用户故事 ──► 规划师 ──► 角色 ──► 场景 ──► 道具 ──► 分镜 ──► 审查 ──► 修复 ──► 完成！
                  ↑                        ↑
            Memory 注入               RAG 知识注入</pre>

<p>7 个 Agent 协作完成从故事到分镜的完整转化。v2.3 新增 Memory + RAG 注入层，让分镜更懂用户的偏好、更符合专业标准。</p>

<h2>♻️ 零依赖架构</h2>

<table>
<tr><th>组件</th><th>旧方案</th><th>新方案</th><th>节省</th></tr>
<tr><td>数据库</td><td>PostgreSQL + pgvector (Docker)</td><td>SQLite + sqlite-vec</td><td>~500MB</td></tr>
<tr><td>缓存</td><td>Redis (Docker)</td><td>TTLCache (内存)</td><td>~150MB</td></tr>
<tr><td>任务队列</td><td>Celery + Redis (Docker)</td><td>asyncio.Queue</td><td>~350MB</td></tr>
<tr><td>文件存储</td><td>MinIO (Docker)</td><td>本地文件系统</td><td>~500MB</td></tr>
<tr><td><b>合计</b></td><td><b>4 个 Docker 容器</b></td><td><b>零外部依赖</b></td><td><b>~1.5GB</b></td></tr>
</table>

<h2>🛤️ 版本路线图</h2>

<table>
<tr><th>版本</th><th>核心特性</th><th>状态</th></tr>
<tr><td><b>v1.0</b></td><td>7 Agent 管线 + 前端界面 + 基础导出</td><td>✅ 已完成</td></tr>
<tr><td><b>v2.0</b></td><td>MCP Server 标准化接口</td><td>✅ 已完成</td></tr>
<tr><td><b>v2.3</b></td><td>Memory + RAG + MCP 扩展 + Workflow 可视化 + 零依赖</td><td>✅ 已发布 ⬅</td></tr>
<tr><td><b>v3.0</b></td><td>视频 Agent 完整版（Prompt 优化 + 多版本管理）</td><td>📅 规划中</td></tr>
</table>

<hr>

<p align="center">
  Built with ❤️ by <a href="https://github.com/yanzhao77">yanzhao77</a> ·
  <a href="https://github.com/yanzhao77/pavo-ai-agent">GitHub</a> ·
  <a href="README_EN.md">English README</a>
</p>

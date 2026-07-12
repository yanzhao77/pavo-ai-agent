<p align="center">
  <b>Pavo AI Agent</b>
</p>

<p align="center">
  <b>把故事灵感变成专业视频分镜 — 由多智能体 AI 管线驱动</b>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white" alt="Next.js"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <br>
  <a href="README_EN.md">English Docs</a> &bull;
  <a href="#features">功能特性</a> &bull;
  <a href="#architecture">系统架构</a> &bull;
  <a href="#getting-started">快速开始</a> &bull;
  <a href="#api">API 文档</a> &bull;
  <a href="#agent-pipeline">智能体管线</a>
</p>

<hr>

<h2>项目简介</h2>

<p><b>Pavo AI Agent</b> 是一个开源平台，通过编排多个专用 AI 智能体（Agent），将自然语言描述的故事创意自动转化为专业的、逐镜头的视频分镜脚本。</p>

<p>只需用自然语言描述一个故事，系统自动完成：角色设计、场景规划、道具编目、镜头拆解（含运镜指令），甚至对接 AI 视频模型生成视频。</p>

<hr>

<h2>功能特性</h2>

<table>
<tr><th>领域</th><th>核心能力</th></tr>
<tr><td><b>多智能体管线</b></td><td>7 个专用 AI 智能体：规划师、角色、场景、道具、分镜、审查、修复</td></tr>
<tr><td><b>实时流式更新</b></td><td>SSE 实时推送智能体工作进度到前端</td></tr>
<tr><td><b>可视化分镜</b></td><td>逐场逐镜视图，含景别、运镜、BGM、音效描述</td></tr>
<tr><td><b>自愈能力</b></td><td>审查智能体检测问题，修复智能体自动纠正</td></tr>
<tr><td><b>版本管理</b></td><td>基于快照的版本历史，支持一键回滚</td></tr>
<tr><td><b>视频生成</b></td><td>分镜提示词 → AI 视频模型 → MinIO 存储</td></tr>
<tr><td><b>多格式导出</b></td><td>Markdown、纯文本文案、PDF</td></tr>
<tr><td><b>拖拽编辑</b></td><td>基于 dnd-kit 的镜头排序交互</td></tr>
<tr><td><b>离线认证</b></td><td>简洁的 token 认证，无外部依赖</td></tr>
</table>

<h2>📖 文档</h2>

<table>
<tr><th>文档</th><th>说明</th><th>语言</th></tr>
<tr><td><a href="docs/user-guide.md">用户操作指南</a></td><td>产品使用流程、界面导航、功能详解、常见问题</td><td>中文</td></tr>
<tr><td><a href="docs/user-guide-en.md">User Guide</a></td><td>Product usage workflow, interface guide, features, FAQ</td><td>English</td></tr>
<tr><td><a href="docs/technical-documentation.md">详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南</td><td>中文</td></tr>
<tr><td><a href="docs/technical-documentation-en.md">Technical Documentation</a></td><td>Architecture, code walkthrough, API reference, deployment</td><td>English</td></tr>
</table>

<hr>

<h2>系统架构</h2>

<h3>整体架构</h3>

<pre>
                         前端 (Next.js 14)
         +---------------------------------------------+
         |  对话面板             预览面板               |
         |  · 故事输入            · 分镜/镜头视图       |
         |  · 智能体日志          · 角色/场景/道具展示  |
         +----------+-----------+----------+-----------+
                    | HTTP/SSE             | HTTP
         +----------v----------------------v-----------+
         |              后端 (FastAPI)                  |
         |  +--------------------------------------+   |
         |  |           智能体管线                  |   |
         |  | 规划师→角色→场景→道具→分镜→审查→修复 |   |
         |  +-----------------+--------------------+   |
         |  +-----------------v--------------------+   |
         |  |           服务层                     |   |
         |  |  ProjectService, AgnesAIClient,     |   |
         |  |  CeleryTasks, MinIO, 导出模块       |   |
         |  +------------------------------------+   |
         +------+---------+---------+----------+
                |         |         |
          PostgreSQL  Redis  MinIO  Agnes AI
          (数据)    (队列)  (视频)  (LLM+视频)
</pre>

<h3>智能体管线流程</h3>

<pre>
用户输入故事
      |
      v
+-------------+     故事分析：主题、情感、时长、关键元素
|   规划师    |
+------+------+
      |
      v
+-------------+     角色形象：姓名、年龄、外貌、性格、声音
|  角色智能体  |
+------+------+
      |
      v
+-------------+     场景设计：环境、灯光、氛围、时段
|  场景智能体  |
+------+------+
      |
      v
+-------------+     道具编目：外观、交互方式、叙事意义
|  道具智能体  |
+------+------+
      |
      v
+-------------+   +-------------+   +-------------+
|  分镜智能体  |-->|  审查智能体  |-->|  修复智能体  |
+-------------+   +-------------+   +-------------+
      |                                    |
      v                                    v
   通过审核                               自动修正
      |
      v
+-------------+     每镜提示词 → Agnes AI 视频 → MinIO MP4
|  视频生成器  |
+-------------+
</pre>

<hr>

<h2>技术栈</h2>

<table>
<tr><th>类别</th><th>技术</th></tr>
<tr><td>后端框架</td><td>Python 3.10+, FastAPI (异步), SQLAlchemy 2.0, Alembic</td></tr>
<tr><td>AI 网关</td><td>Agnes AI (兼容 OpenAI 协议，含重试与限流)</td></tr>
<tr><td>前端</td><td>Next.js 14, React 18, TypeScript 5, TailwindCSS 3</td></tr>
<tr><td>数据库</td><td>PostgreSQL 16 (生产), SQLite (测试)</td></tr>
<tr><td>消息队列</td><td>Redis 7 + Celery (异步视频生成)</td></tr>
<tr><td>文件存储</td><td>MinIO (兼容 S3 协议的对象存储)</td></tr>
<tr><td>拖拽组件</td><td>dnd-kit</td></tr>
<tr><td>图标库</td><td>Lucide React</td></tr>
<tr><td>测试</td><td>pytest, pytest-asyncio, pytest-cov, Playwright</td></tr>
<tr><td>CI</td><td>GitHub Actions</td></tr>
<tr><td>容器化</td><td>Docker Compose (全栈)</td></tr>
</table>
<hr>
<h2>项目结构</h2>

<pre>
pavo-ai-work/
│
├── backend/                     # FastAPI 后端服务
│   ├── app/
│   │   ├── agents/              # 7 个 AI 智能体
│   │   │   ├── base.py          #   BaseAgent 基类（共享 LLM 客户端）
│   │   │   ├── planner.py       #   故事分析与规划
│   │   │   ├── character_agent.py # 角色设计
│   │   │   ├── scene_agent.py   #   场景环境设计
│   │   │   ├── prop_agent.py    #   道具编目
│   │   │   ├── storyboard_agent.py # 逐镜分镜
│   │   │   ├── reviewer.py      #   质量审查与校验
│   │   │   └── fixer.py         #   自动修复
│   │   ├── api/routes.py        #   REST API（18 个端点）
│   │   ├── db/
│   │   │   ├── database.py      #   异步 SQLAlchemy 引擎
│   │   │   └── migrations/      #   Alembic 数据库迁移
│   │   ├── models/
│   │   │   ├── project.py       #   ORM（Project, VersionHistory, Feedback）
│   │   │   └── schema.py        #   Pydantic 校验模式
│   │   ├── services/
│   │   │   ├── agnes_client.py  #   LLM 客户端（重试、限流）
│   │   │   ├── project_service.py # 工作流编排
│   │   │   ├── auth.py          #   Token 认证
│   │   │   ├── storage.py       #   MinIO 文件存储
│   │   │   ├── celery_app.py    #   Celery 配置
│   │   │   ├── video_tasks.py   #   异步视频生成任务
│   │   │   └── export/          #   导出格式
│   │   │       ├── markdown.py
│   │   │       └── pdf.py
│   │   ├── config.py            #   Pydantic 配置
│   │   ├── main.py              #   FastAPI 入口
│   ├── tests/                   # 12 个测试套件
│   ├── Dockerfile
│   └── requirements.txt / requirements-dev.txt
│
├── frontend/                    # Next.js 14 前端
│   ├── src/
│   │   ├── app/                 #   页面 + 布局
│   │   ├── components/          #   8 个 UI 组件
│   │   ├── lib/api.ts           #   API 客户端
│   │   └── types/project.ts     #   TypeScript 类型
│   ├── tests/                   #   Playwright E2E 测试
│   └── tailwind.config.js / tsconfig.json
│
├── docs/                        # 中文文档 &amp; 用户手册
│   ├── 技术开发文档.md
│   ├── 技术开发计划文档_v5.md
│   ├── 技术委员会评审报告_v6_修正版.md
│   ├── user-guide.md            #   用户操作指南
│   ├── user-guide-en.md         #   User Guide (English)
│   ├── technical-documentation.md           #   详细技术文档
│   └── technical-documentation-en.md        #   Technical Documentation (English)
│
├── scripts/                     # 工具脚本
├── .github/workflows/test.yml   # CI 流水线
├── docker-compose.yml           # 基础设施编排
├── .env.example                 # 环境变量模板
├── .gitignore
├── README.md                    # 本文件（中文）
└── README_EN.md                 # English Documentation
</pre>

<hr>

<h2>快速开始</h2>

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
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 启动前端（终端 2）
cd frontend
npm install
npm run dev
</code></pre>

<p>打开 <b>http://localhost:3000</b>，输入用户名，然后输入一个故事创意即可体验。</p>

<h3>全栈 Docker 启动</h3>

<pre><code>docker compose up --build -d
</code></pre>

<h3>试试看</h3>

<p>输入类似这样的故事：</p>

<blockquote><i>一位父亲下班疲惫地回到家，他 5 岁的儿子端来一盆热水，认真地为爸爸洗脚。</i></blockquote>

<p>实时观看 7 个智能体依次工作，然后浏览生成的分镜脚本。</p>

<hr>

<h2>API 文档</h2>

<p>所有端点位于 <code>http://localhost:8000/api</code>。</p>

<h3>核心接口</h3>
<table>
<tr><th>方法</th><th>路径</th><th>说明</th></tr>
<tr><td>POST</td><td><code>/api/projects</code></td><td>创建项目并启动智能体管线</td></tr>
<tr><td>GET</td><td><code>/api/projects</code></td><td>项目列表（可选 <code>?user_id=</code>）</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}</code></td><td>获取完整项目数据</td></tr>
<tr><td>PATCH</td><td><code>/api/projects/{id}</code></td><td>更新项目字段</td></tr>
<tr><td>DELETE</td><td><code>/api/projects/{id}</code></td><td>删除项目</td></tr>
</table>

<h3>实时与视频</h3>
<table>
<tr><th>方法</th><th>路径</th><th>说明</th></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/stream</code></td><td>SSE 流，实时推送智能体进度</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/render</code></td><td>触发视频生成</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/videos</code></td><td>获取视频结果及存储 URL</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/tasks</code></td><td>Celery 任务状态</td></tr>
</table>

<h3>迭代与版本</h3>
<table>
<tr><th>方法</th><th>路径</th><th>说明</th></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/regenerate</code></td><td>重新生成指定模块</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/versions</code></td><td>创建版本快照</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/versions</code></td><td>版本历史列表</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/versions/{vid}/restore</code></td><td>回滚到指定版本</td></tr>
</table>

<h3>导出与认证</h3>
<table>
<tr><th>方法</th><th>路径</th><th>说明</th></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=markdown</code></td><td>导出 Markdown</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=script</code></td><td>导出纯文本文案</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=pdf</code></td><td>导出 PDF</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/feedback</code></td><td>提交反馈</td></tr>
<tr><td>POST</td><td><code>/api/auth/login</code></td><td>登录获取 Token</td></tr>
<tr><td>GET</td><td><code>/api/auth/me</code></td><td>校验 Token</td></tr>
</table>

<h3>创建项目示例</h3>

<pre><code>curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"input": "一位父亲下班回到家，5岁儿子端来洗脚盆..."}'

# 响应
{"projectId":"abc-123","status":"generating"}
</code></pre>

<h3>SSE 流示例</h3>

<pre><code>curl -N http://localhost:8000/api/projects/abc-123/stream

data: {"type":"agent:progress","agent":"planner","action":"Analyzing","status":"passed"}
data: {"type":"agent:progress","agent":"character","action":"Generating","status":"passed"}
...
data: {"type":"agent:complete","status":"completed"}
</code></pre>

<hr>

<h2>AI 智能体管线</h2>

<table>
<tr><th>#</th><th>智能体</th><th>模型</th><th>职责</th></tr>
<tr><td>1</td><td><b>规划师</b></td><td>agnes-2.0-flash</td><td>提取主题、情感、关键角色、预估时长</td></tr>
<tr><td>2</td><td><b>角色智能体</b></td><td>agnes-2.0-flash</td><td>姓名、年龄、外貌、性格、声音、一致性标识</td></tr>
<tr><td>3</td><td><b>场景智能体</b></td><td>agnes-2.0-flash</td><td>环境类型、风格、灯光、氛围、时段</td></tr>
<tr><td>4</td><td><b>道具智能体</b></td><td>agnes-2.0-flash</td><td>核心道具：外观、交互方式、叙事意义</td></tr>
<tr><td>5</td><td><b>分镜智能体</b></td><td>agnes-2.0-flash</td><td>逐镜拆解：景别、运镜、角度、对白、时长</td></tr>
<tr><td>6</td><td><b>审查智能体</b></td><td>agnes-2.0-flash</td><td>校验一致性、完整性、叙事逻辑</td></tr>
<tr><td>7</td><td><b>修复智能体</b></td><td>agnes-2.0-flash</td><td>自动纠正审查发现的问题</td></tr>
</table>

<p>所有智能体继承自 <code>BaseAgent</code>，提供限流的异步 HTTP 调用、指数退避自动重试（应对 429/503）、结构化 JSON 输出解析、以及优雅的错误降级。</p>

<hr>

<h2>配置说明</h2>

<h3>环境变量 (.env)</h3>

<pre><code># === Agnes AI API ===
AGNES_API_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_API_KEY=sk-your-key-here

# === 数据库 ===
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pavo_agent

# === 缓存与队列 ===
REDIS_URL=redis://localhost:6379/0

# === 文件存储 (MinIO/S3) ===
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secret
MINIO_BUCKET=pavo-videos

# === 应用 ===
APP_ENV=development
LOG_LEVEL=INFO
MAX_CONCURRENT_VIDEO_JOBS=3
VIDEO_TIMEOUT_SECONDS=300
</code></pre>

<h3>基础设施端口</h3>
<table>
<tr><th>端口</th><th>服务</th><th>用途</th></tr>
<tr><td>5432</td><td>PostgreSQL</td><td>主数据库</td></tr>
<tr><td>6379</td><td>Redis</td><td>缓存与 Celery 代理</td></tr>
<tr><td>9000</td><td>MinIO API</td><td>S3 兼容存储</td></tr>
<tr><td>9001</td><td>MinIO 控制台</td><td>Web 管理界面</td></tr>
<tr><td>8000</td><td>后端 API</td><td>FastAPI 服务</td></tr>
<tr><td>3000</td><td>前端</td><td>Next.js 开发服务器</td></tr>
</table>

<hr>

<h2>测试</h2>

<pre><code># 后端 - 12 个测试套件
cd backend
python -m pytest tests/ --cov=app -v --cov-report=term --cov-report=html

# 前端 - Playwright E2E
cd frontend
npx playwright test
</code></pre>

<p>测试覆盖：智能体输出结构与模式校验的单元测试、API 路由与导出的集成测试、Mock LLM 的 E2E 测试、限流与重试的边界测试、Playwright 关键用户路径测试。</p>

<hr>

<h2>数据模型</h2>

<pre><code>Project:
  id: UUID                  主键
  user_id: str              所有者标识
  title: str                自动生成标题
  status: enum              draft | generating | completed
  input_raw: text           原始故事输入
  input_extracted: json     规划师分析结果
  characters: json[]        角色档案数组
  scenes: json[]            场景设计数组
  props: json[]             道具定义数组
  storyboard: json          完整分镜对象
  videos: json[]            生成视频元数据
  trace_log: json[]         智能体执行轨迹
  created_at: datetime      自动设置
  updated_at: datetime      自动更新

VersionHistory:
  id: UUID
  project_id: UUID          外键关联 Project
  version_number: int       递增版本号
  snapshot: json            完整项目快照
  description: str          版本描述
  created_at: datetime

Feedback:
  id: UUID
  project_id: UUID          外键关联 Project
  user_id: str
  rating: str               up | down
  comment: text
  created_at: datetime
</code></pre>

<hr>

<h2>许可证</h2>
<p>MIT</p>

<hr>

<h2>致谢</h2>
<ul>
<li><a href="https://agnes-ai.com">Agnes AI</a> — LLM 与视频生成 API</li>
<li><a href="https://fastapi.tiangolo.com">FastAPI</a> — 异步 Python Web 框架</li>
<li><a href="https://nextjs.org">Next.js</a> — React 框架</li>
<li><a href="https://tailwindcss.com">TailwindCSS</a> — 工具类优先的 CSS</li>
<li><a href="https://lucide.dev">Lucide</a> — 精美的图标库</li>
<li><a href="https://dndkit.com">dnd-kit</a> — 拖拽工具包</li>
<li><a href="https://min.io">MinIO</a> — S3 兼容对象存储</li>
</ul>

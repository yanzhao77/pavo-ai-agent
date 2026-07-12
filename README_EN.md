<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIyMCIgZmlsbD0iI0E4QjNGRiIvPjxwYXRoIGQ9Ik0xMiAyMGwxNiAweiIgc3Ryb2tlPSIjMjIyIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTggMTJsMCAxNiIgc3Ryb2tlPSIjMjIyIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTAgMTBjMiAyIDIgMiA0IDQiIHN0cm9rZT0iIzIyMiIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48L3N2Zz4=/>
    <img src="https://img.shields.io/badge/Pavo_AI_Agent-1B1B2F?style=for-the-badge&logo=data:image/svg+xml;base64,..." alt="Pavo AI Agent" width="200">
  </picture>
</p>
<p align="center"><b>Turn story ideas into professional video storyboards — powered by a multi-agent AI pipeline</b></p>
<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white" alt="Next.js"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
  <a href="https://tailwindcss.com/"><img src="https://img.shields.io/badge/TailwindCSS-3-06B6D4?logo=tailwindcss&logoColor=white" alt="TailwindCSS"></a><br>
  <a href="#features">Features</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#getting-started">Getting Started</a> &bull;
  <a href="#api">API</a> &bull;
  <a href="#ai-agent-pipeline">Agents</a>
</p>
<hr>
<h2>Overview</h2>
<p><b>Pavo AI Agent</b> is an open-source platform that transforms natural language story ideas into professional, shot-by-shot video storyboards through a coordinated pipeline of specialized AI agents.</p>
<p>Describe a story in plain language &mdash; the system handles the rest: character design, scene planning, prop cataloging, shot composition with camera instructions, and even AI video generation.</p>
<hr>
<h2>Features</h2>
<table>
<tr><th>Area</th><th>Highlights</th></tr>
<tr><td><b>Multi-Agent Pipeline</b></td><td>7 specialized AI agents: Planner, Character, Scene, Prop, Storyboard, Reviewer, Fixer</td></tr>
<tr><td><b>Real-Time Streaming</b></td><td>SSE-powered live progress tracking from agent pipeline</td></tr>
<tr><td><b>Visual Storyboard</b></td><td>Scene-by-scene, shot-by-shot view with camera moves, BGM, SFX</td></tr>
<tr><td><b>Self-Healing</b></td><td>Reviewer detects issues, Fixer auto-corrects</td></tr>
<tr><td><b>Version History</b></td><td>Snapshot-based versioning with restore</td></tr>
<tr><td><b>Video Generation</b></td><td>Shot prompts, AI video model, MinIO storage</td></tr>
<tr><td><b>Export</b></td><td>Markdown, plain text script, PDF</td></tr>
<tr><td><b>Drag &amp; Drop</b></td><td>Reorder shots with dnd-kit</td></tr>
<tr><td><b>Auth</b></td><td>Simple token-based (no external dependency)</td></tr>
</table>

<h2>📖 Documentation</h2>

<table>
<tr><th>Document</th><th>Description</th><th>Language</th></tr>
<tr><td><a href="docs/user-guide-en.md">User Guide</a></td><td>Product usage workflow, interface guide, features walkthrough, FAQ</td><td>English</td></tr>
<tr><td><a href="docs/user-guide.md">用户操作指南</a></td><td>产品使用流程、界面导航、功能详解、常见问题</td><td>中文</td></tr>
<tr><td><a href="docs/technical-documentation-en.md">Technical Documentation</a></td><td>System architecture, code walkthrough, API reference, deployment guide</td><td>English</td></tr>
<tr><td><a href="docs/technical-documentation.md">详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南</td><td>中文</td></tr>
</table>

<hr>

<h2>Architecture</h2>
<h3>System Overview</h3>
<pre>
                         Frontend (Next.js 14)
         +------------------------------------------+
         |  ChatPanel           PreviewPanel        |
         |  - Input              - Storyboard/Shots |
         |  - TraceLog           - Characters/Scenes|
         +-----------+----------+--------+---------+
                     | HTTP/SSE          | HTTP
         +-----------v------------------v---------+
         |           Backend (FastAPI)             |
         |  +----------------------------------+  |
         |  |         Agent Pipeline           |  |
         |  | Planner -> Character -> Scene -> |  |
         |  | Prop -> Storyboard -> Rev -> Fix |  |
         |  +--------------+-------------------+  |
         |  +--------------v-------------------+  |
         |  |     Services Layer              |  |
         |  | ProjectService, AgnesAIClient,  |  |
         |  | CeleryTasks, MinIO, Export      |  |
         |  +--------------------------------+  |
         +------+---------+---------+---------+
                |         |         |
         PostgreSQL  Redis  MinIO  Agnes AI
         (data)   (queue) (videos) (LLM+Video)
</pre>
<h3>Agent Pipeline Flow</h3>
<pre>
User Story Input
       |
       v
+--------------+     Story analysis: theme, emotion, duration
|   Planner    |
+------+-------+
       |
       v
+--------------+     Character profiles: name, age, appearance, personality
|  Character   |
|    Agent     |
+------+-------+
       |
       v
+--------------+     Scene designs: environment, lighting, atmosphere
|   Scene      |
|    Agent     |
+------+-------+
       |
       v
+--------------+     Prop catalog: appearance, interaction, significance
|   Prop       |
|    Agent     |
+------+-------+
       |
       v
+--------------+   +--------------+   +--------------+
|  Storyboard  |-->|   Reviewer   |-->|    Fixer     |
|    Agent     |   |    Agent     |   |    Agent     |
+--------------+   +--------------+   +--------------+
       |                                      |
       v                                      v
   Passed                                 Corrected
       |
       v
+--------------+     Prompt per shot -> Agnes AI video -> MinIO MP4
|    Video     |
|  Generator   |
+--------------+
</pre>
<hr>
<h2>Tech Stack</h2>
<table>
<tr><th>Category</th><th>Technology</th></tr>
<tr><td>Backend</td><td>Python 3.10+, FastAPI (async), SQLAlchemy 2.0, Alembic</td></tr>
<tr><td>AI Gateway</td><td>Agnes AI (OpenAI-compatible, retry &amp; rate-limit)</td></tr>
<tr><td>Frontend</td><td>Next.js 14, React 18, TypeScript 5, TailwindCSS 3</td></tr>
<tr><td>Database</td><td>PostgreSQL 16 (primary), SQLite (test)</td></tr>
<tr><td>Queue</td><td>Redis 7 + Celery (async video processing)</td></tr>
<tr><td>Storage</td><td>MinIO (S3-compatible object storage)</td></tr>
<tr><td>Drag &amp; Drop</td><td>dnd-kit</td></tr>
<tr><td>Icons</td><td>Lucide React</td></tr>
<tr><td>Testing</td><td>pytest, pytest-asyncio, pytest-cov, Playwright</td></tr>
<tr><td>CI</td><td>GitHub Actions</td></tr>
<tr><td>Container</td><td>Docker Compose (full-stack)</td></tr>
</table>
<hr>
<h2>Getting Started</h2>
<h3>Prerequisites</h3>
<ul>
<li>Python 3.10+</li>
<li>Node.js 18+</li>
<li>Docker &amp; Docker Compose</li>
<li>Agnes AI API key (<a href="https://apihub.agnes-ai.com">get one here</a>)</li>
</ul>
<h3>Quick Start (Local)</h3>
<pre><code># Clone
git clone https://github.com/your-username/pavo-ai-work.git
cd pavo-ai-work

# Configure environment
cp .env.example .env
# Edit .env -> set AGNES_API_KEY

# Start infrastructure
docker compose up -d postgres redis minio

# Start backend (terminal 1)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Start frontend (terminal 2)
cd frontend
npm install
npm run dev
</code></pre>
<p>Open <b>http://localhost:3000</b>, enter a username, then type a story idea.</p>
<h3>Docker Compose (Full Stack)</h3>
<pre><code>docker compose up --build -d
</code></pre>
<h3>Try It</h3>
<p>Paste a story like:</p>
<blockquote><i>A father comes home tired from work. His 5-year-old son carefully brings him a wooden foot basin and washes his feet.</i></blockquote>
<p>Watch all 7 agents run in real-time, then explore the generated storyboard.</p>
<hr>
<h2>Project Structure</h2>
<pre>
pavo-ai-work/
│
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── agents/              # 7 AI agent implementations
│   │   │   ├── base.py          #   BaseAgent shared LLM client
│   │   │   ├── planner.py       #   Story analysis & planning
│   │   │   ├── character_agent.py
│   │   │   ├── scene_agent.py
│   │   │   ├── prop_agent.py
│   │   │   ├── storyboard_agent.py
│   │   │   ├── reviewer.py      #   Quality review & validation
│   │   │   └── fixer.py         #   Auto-fix detected issues
│   │   ├── api/routes.py        #   REST API (18 endpoints)
│   │   ├── db/
│   │   │   ├── database.py      #   Async SQLAlchemy engine
│   │   │   └── migrations/      #   Alembic schema migrations
│   │   ├── models/
│   │   │   ├── project.py       #   ORM (Project, VersionHistory, Feedback)
│   │   │   └── schema.py        #   Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── agnes_client.py  #   LLM client (retry, rate-limit)
│   │   │   ├── project_service.py #  Workflow orchestrator
│   │   │   ├── auth.py          #   Token-based auth
│   │   │   ├── storage.py       #   MinIO file storage
│   │   │   ├── celery_app.py    #   Celery config
│   │   │   ├── video_tasks.py   #   Async video generation
│   │   │   └── export/          #   Export formatters
│   │   │       ├── markdown.py
│   │   │       └── pdf.py
│   │   ├── config.py            #   Pydantic settings
│   │   ├── main.py              #   FastAPI entry point
│   ├── tests/                   # 12 test suites
│   ├── Dockerfile
│   └── requirements.txt / requirements-dev.txt
│
├── frontend/                    # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                 #   Pages + layout
│   │   ├── components/          #   8 UI components
│   │   ├── lib/api.ts           #   API client
│   │   └── types/project.ts     #   TypeScript interfaces
│   ├── tests/                   #   Playwright E2E tests
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docs/                        # Documentation
│   ├── 技术开发文档.md           #   Technical development guide (Chinese)
│   ├── user-guide-en.md         #   User Guide (English)
│   ├── user-guide.md            #   User Guide (Chinese)
│   ├── technical-documentation-en.md      #   Technical Documentation (English)
│   └── technical-documentation.md         #   Technical Documentation (Chinese)
│   ├── 技术开发计划文档_v5.md     #   Development plan
│   ├── 技术委员会评审报告_v6_修正版.md
│   └── (project reviews & reports)
│
├── scripts/                     # Utility scripts
│   ├── gen_doc.py / _v2 / _final.py
│   ├── gen_plan.py
│   └── write_readme.py
│
├── .github/workflows/test.yml   # CI pipeline
├── docker-compose.yml           # Infrastructure orchestration
├── .env.example                 # Environment template
├── .gitignore
└── README.md
</pre>
<hr>
<h2>API Reference</h2>
<p>All endpoints under <code>http://localhost:8000/api</code>.</p>
<h3>Core Endpoints</h3>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>POST</td><td><code>/api/projects</code></td><td>Create project &amp; start agent pipeline</td></tr>
<tr><td>GET</td><td><code>/api/projects</code></td><td>List projects (optional <code>?user_id=</code>)</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}</code></td><td>Full project data</td></tr>
<tr><td>PATCH</td><td><code>/api/projects/{id}</code></td><td>Update project fields</td></tr>
<tr><td>DELETE</td><td><code>/api/projects/{id}</code></td><td>Delete project</td></tr>
</table>
<h3>Real-Time &amp; Video</h3>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/stream</code></td><td>SSE stream for agent progress</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/render</code></td><td>Trigger video generation</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/videos</code></td><td>Video results with storage URLs</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/tasks</code></td><td>Celery task status</td></tr>
</table>
<h3>Iteration &amp; History</h3>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/regenerate</code></td><td>Re-run specific module</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/versions</code></td><td>Create version snapshot</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/versions</code></td><td>List version history</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/versions/{vid}/restore</code></td><td>Restore version</td></tr>
</table>
<h3>Export &amp; Auth</h3>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=markdown</code></td><td>Export as Markdown</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=script</code></td><td>Export as script text</td></tr>
<tr><td>GET</td><td><code>/api/projects/{id}/export?format=pdf</code></td><td>Export as PDF</td></tr>
<tr><td>POST</td><td><code>/api/projects/{id}/feedback</code></td><td>Submit feedback</td></tr>
<tr><td>POST</td><td><code>/api/auth/login</code></td><td>Login (get token)</td></tr>
<tr><td>GET</td><td><code>/api/auth/me</code></td><td>Verify token</td></tr>
</table>
<h3>Create a Project</h3>
<pre><code>curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"input": "A father comes home tired from work..."}'

# Response
{"projectId":"abc-123","status":"generating"}
</code></pre>
<h3>SSE Stream</h3>
<pre><code>curl -N http://localhost:8000/api/projects/abc-123/stream

data: {"type":"agent:progress","agent":"planner","action":"Analyzing","status":"passed"}
data: {"type":"agent:progress","agent":"character","action":"Generating","status":"passed"}
...
data: {"type":"agent:complete","status":"completed"}
</code></pre>
<hr>
<h2>AI Agent Pipeline</h2>
<table>
<tr><th>#</th><th>Agent</th><th>Model</th><th>Responsibility</th></tr>
<tr><td>1</td><td><b>Planner</b></td><td>agnes-2.0-flash</td><td>Extract theme, emotions, characters, duration from story</td></tr>
<tr><td>2</td><td><b>Character</b></td><td>agnes-2.0-flash</td><td>Name, age, appearance, personality, voice, consistency key</td></tr>
<tr><td>3</td><td><b>Scene</b></td><td>agnes-2.0-flash</td><td>Environment type, style, lighting, atmosphere, time of day</td></tr>
<tr><td>4</td><td><b>Prop</b></td><td>agnes-2.0-flash</td><td>Anchor props: appearance, interaction, narrative significance</td></tr>
<tr><td>5</td><td><b>Storyboard</b></td><td>agnes-2.0-flash</td><td>Shot-by-shot: type, camera move, angle, dialogue, duration</td></tr>
<tr><td>6</td><td><b>Reviewer</b></td><td>agnes-2.0-flash</td><td>Validate consistency, completeness, narrative flow</td></tr>
<tr><td>7</td><td><b>Fixer</b></td><td>agnes-2.0-flash</td><td>Auto-correct identified issues</td></tr>
</table>
<p>All agents inherit from <code>BaseAgent</code> which provides rate-limited async HTTP calls, automatic retry with exponential backoff (429/503), structured JSON parsing, and graceful fallback.</p>
<hr>
<h2>Configuration</h2>
<h3>Environment Variables (.env)</h3>
<pre><code># === Agnes AI API ===
AGNES_API_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_API_KEY=sk-your-key-here

# === Database ===
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pavo_agent

# === Cache & Queue ===
REDIS_URL=redis://localhost:6379/0

# === File Storage (MinIO / S3) ===
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secret
MINIO_BUCKET=pavo-videos

# === Application ===
APP_ENV=development
LOG_LEVEL=INFO
MAX_CONCURRENT_VIDEO_JOBS=3
VIDEO_TIMEOUT_SECONDS=300
</code></pre>
<h3>Infrastructure Ports</h3>
<table>
<tr><th>Port</th><th>Service</th><th>Purpose</th></tr>
<tr><td>5432</td><td>PostgreSQL</td><td>Primary database</td></tr>
<tr><td>6379</td><td>Redis</td><td>Cache &amp; Celery broker</td></tr>
<tr><td>9000</td><td>MinIO API</td><td>S3-compatible storage</td></tr>
<tr><td>9001</td><td>MinIO Console</td><td>Web UI</td></tr>
<tr><td>8000</td><td>Backend API</td><td>FastAPI server</td></tr>
<tr><td>3000</td><td>Frontend</td><td>Next.js dev server</td></tr>
</table>
<hr>
<h2>Testing</h2>
<pre><code># Backend - all 12 test suites
cd backend
python -m pytest tests/ --cov=app -v --cov-report=term --cov-report=html

# Frontend - Playwright E2E
cd frontend
npx playwright test
</code></pre>
<p>Coverage includes: unit tests for agent outputs and schema validation, integration tests for API routes and exports, E2E with mock LLM, edge cases for rate limiting and retries, and Playwright E2E for critical UI flows.</p>
<hr>
<h2>Data Model</h2>
<pre><code>Project:
  id: UUID                  Primary key
  user_id: str              Owner identifier
  title: str                Auto-generated title
  status: enum              draft | generating | completed
  input_raw: text           Original story input
  input_extracted: json     Planner analysis result
  characters: json[]        Array of character profiles
  scenes: json[]            Array of scene designs
  props: json[]             Array of prop definitions
  storyboard: json          Complete storyboard object
  videos: json[]            Generated video metadata
  trace_log: json[]         Agent execution trace
  created_at: datetime      Auto-set
  updated_at: datetime      Auto-updated

VersionHistory:
  id: UUID
  project_id: UUID          FK to Project
  version_number: int       Sequential version
  snapshot: json            Full project state
  description: str          Version label
  created_at: datetime

Feedback:
  id: UUID
  project_id: UUID          FK to Project
  user_id: str
  rating: str               up | down
  comment: text
  created_at: datetime
</code></pre>
<hr>
<h2>License</h2>
<p>MIT</p>
<hr>
<h2>Acknowledgments</h2>
<ul>
<li><a href="https://agnes-ai.com">Agnes AI</a> - LLM and video generation API</li>
<li><a href="https://fastapi.tiangolo.com">FastAPI</a> - Async Python web framework</li>
<li><a href="https://nextjs.org">Next.js</a> - React framework</li>
<li><a href="https://tailwindcss.com">TailwindCSS</a> - Utility-first CSS</li>
<li><a href="https://lucide.dev">Lucide</a> - Beautiful icons</li>
<li><a href="https://dndkit.com">dnd-kit</a> - Drag &amp; drop toolkit</li>
<li><a href="https://min.io">MinIO</a> - S3-compatible object storage</li>
</ul>

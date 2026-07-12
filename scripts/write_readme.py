import os
content = r"""# Pavo AI Agent

AI-powered video storyboard generation platform. Users describe a story idea, and a pipeline of AI agents generates characters, scenes, props, shot-by-shot storyboards, and eventually video assets.

## Architecture Overview

```
User Input (story idea)
    |
    v
+-----------------------------------------------------------+
|              Backend (FastAPI + PostgreSQL)                |
|                                                           |
|  +--------+  +----------+  +--------+  +-------+         |
|  |Planner |->|Character |->| Scene  |->| Prop  |         |
|  |        |  |  Agent   |  | Agent  |  | Agent |         |
|  +--------+  +----------+  +--------+  +-------+         |
|                                    |                      |
|  +--------+  +----------+         |                      |
|  | Fixer  |<-| Reviewer |<--------+                      |
|  | Agent  |  |  Agent   |                                |
|  +--------+  +----------+                                |
|        |                                                  |
|        v                                                  |
|  +------------------+                                     |
|  | Storyboard Agent |  ->  JSON storyboard                |
|  +------------------+                                     |
|                                                           |
|  +------------------+                                     |
|  | Video Generator  |  ->  MP4 output (MinIO)            |
|  +------------------+                                     |
+-----------------------------------------------------------+
    |
    v
+-----------------------------------------------------------+
|           Frontend (Next.js 14 + TailwindCSS)              |
|                                                           |
|  +----------------+  +--------------------------------+   |
|  |   ChatPanel    |  |       PreviewPanel              |   |
|  | - Input field  |  | - Storyboard (scene/shot view) |   |
|  | - Agent trace  |  | - Characters tab               |   |
|  | - Send button  |  | - Scenes tab                   |   |
|  +----------------+  | - Props tab                    |   |
|                       | - Copy / export                |   |
|                       +--------------------------------+   |
+-----------------------------------------------------------+
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, FastAPI 0.115, SQLAlchemy 2.0 (async), asyncpg |
| **Frontend** | Next.js 14, React 18, TypeScript 5, TailwindCSS 3 |
| **AI Gateway** | Agnes AI API (OpenAI-compatible, httpx client) |
| **Database** | PostgreSQL 16 |
| **Cache / Queue** | Redis 7 |
| **File Storage** | MinIO (S3-compatible) |
| **Migrations** | Alembic |
| **Orchestration** | Docker Compose |

## Project Structure

```
pavo-ai-work/
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── agents/              # 7 AI Agents
│   │   │   ├── base.py          # BaseAgent (shared API client)
│   │   │   ├── planner.py       # Story analysis
│   │   │   ├── character_agent.py
│   │   │   ├── scene_agent.py
│   │   │   ├── prop_agent.py
│   │   │   ├── storyboard_agent.py
│   │   │   ├── reviewer.py      # Quality review
│   │   │   └── fixer.py         # Autofix
│   │   ├── api/routes.py        # REST endpoints
│   │   ├── db/database.py       # SQLAlchemy engine
│   │   ├── models/project.py    # Project ORM model
│   │   ├── services/
│   │   │   ├── agnes_client.py  # Agnes AI HTTP client
│   │   │   └── project_service.py  # Workflow orchestrator
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── main.py              # FastAPI entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── verify.py                # Import verification
├── frontend/                    # Next.js frontend
│   └── src/
│       ├── app/
│       │   ├── layout.tsx       # Root layout (zh-CN)
│       │   ├── page.tsx         # Main app page
│       │   └── globals.css      # TailwindCSS base
│       ├── components/
│       │   ├── ChatPanel.tsx    # Input + progress trace
│       │   └── PreviewPanel.tsx # Tabs: storyboard/characters/scenes/props
│       ├── lib/api.ts           # API client
│       └── types/project.ts     # TypeScript interfaces
├── docs/                        # Chinese documentation
│   ├── 技术开发文档.md
│   ├── 技术开发计划文档.md
│   └── 技术开发文档审核报告.md
├── scripts/                     # Utility scripts
├── .env                         # Environment (gitignored)
├── .env.example                 # Environment template
├── docker-compose.yml           # PostgreSQL + Redis + MinIO + Backend
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose (for PostgreSQL, Redis, MinIO)
- Agnes AI API key (obtain from [Agnes AI Console](https://apihub.agnes-ai.com))

### 1. Environment Setup

```bash
cd pavo-ai-work
cp .env.example .env
```

Edit `.env` and set your `AGNES_API_KEY`.

### 2. Start Infrastructure

```bash
docker compose up -d postgres redis minio
```

### 3. Start Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/health`

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in a browser.

### 5. Use the App

1. Type a story idea in the ChatPanel, e.g.:
   > "A father comes home from work tired, his 5-year-old son brings him a foot basin"
2. Press Send — the backend runs the 7-agent pipeline
3. Watch agent progress in the ChatPanel
4. Browse results in PreviewPanel tabs (Storyboard / Characters / Scenes / Props)

## API Reference

All endpoints under `http://localhost:8000/api`.

### POST /api/projects

Create a project and start the generation workflow.

```json
// Request
{ "input": "A father comes home from work..." }

// Response
{ "projectId": "uuid", "status": "generating" }
```

### GET /api/projects/{project_id}

Fetch full project data with all generated content.

```json
{
  "id": "uuid",
  "title": "...",
  "status": "completed",
  "input": "story text",
  "characters": [...],
  "scenes": [...],
  "props": [...],
  "storyboard": { ... },
  "videos": [],
  "traceLog": [...],
  "createdAt": "...",
  "updatedAt": "..."
}
```

### GET /api/projects/{project_id}/stream

Server-Sent Events stream for real-time agent progress.

```
data: {"type":"agent:progress","agent":"planner","action":"Analyzing story","status":"passed","timestamp":"..."}
data: {"type":"agent:complete","status":"completed"}
```

### PATCH /api/projects/{project_id}

Update project fields (characters, scenes, props, storyboard).

### POST /api/projects/{project_id}/regenerate

Re-run a specific module.

```json
// Request
{ "module": "characters" | "scenes" | "storyboard" }

// Response
{ "status": "regenerated", "module": "characters" }
```

## AI Agent Pipeline

| Agent | Default Model | Input | Output | Description |
|---|---|---|---|---|
| **Planner** | agnes-2.0-flash | User story text | JSON: characters, scene, theme, emotion, duration | Analyzes story, extracts high-level elements |
| **Character** | agnes-2.0-flash | Story text | JSON array of character profiles | Designs name, age, appearance, personality, voice |
| **Scene** | agnes-2.0-flash | Story + Characters | JSON array of scene settings | Designs environment, lighting, atmosphere |
| **Prop** | agnes-2.0-flash | Story + Characters + Scenes | JSON array of props | Creates anchor props with appearance and interaction |
| **Storyboard** | agnes-2.0-flash | Story + Characters + Scenes + Props | JSON storyboard object | Full shot-by-shot storyboard |
| **Reviewer** | agnes-2.0-flash | Full project data | JSON: passed, issues, needs_fix | Quality review pass |
| **Fixer** | agnes-2.0-flash | Issues + Storyboard | Corrected storyboard JSON | Fixes issues automatically |

### Storyboard Structure

Follows Chinese **起承转合** (qi-cheng-zhuan-he) narrative structure:
- 3–4 acts
- 30–60 seconds total duration
- Each scene has BGM and SFX descriptions
- Each shot includes shotType, cameraMove, cameraAngle, description, dialogue, duration

**Shot Types:** 远景 (wide) | 全景 (full) | 中景 (medium) | 中近景 (medium-close) | 近景 (close) | 特写 (extreme close)

**Camera Moves:** 固定 (static) | 横移 (track) | 推近 (push in) | 拉远 (pull out) | 摇移 (pan/tilt) | 跟拍 (follow)

**Camera Angles:** 平视 (eye-level) | 平视微俯 (slight high angle) | 平视侧面 (profile)

## Data Model

### Project

```python
class Project(Base):
    __tablename__ = "projects"

    id: UUID              # Primary key
    title: str            # Project title (max 255 chars)
    status: ProjectStatus # Enum: draft | generating | completed
    input_raw: str        # Original user input text
    input_extracted: dict # Parsed analysis result from planner
    characters: list      # JSON array of character objects
    scenes: list          # JSON array of scene objects
    props: list           # JSON array of prop objects
    storyboard: dict      # JSON storyboard object with scenes and shots
    videos: list          # Generated video file metadata
    version: str          # Schema version, default "1.0"
    trace_log: list       # Agent execution trace entries
    created_at: datetime  # Auto-set on creation
    updated_at: datetime  # Auto-updated on modification
```

## Configuration (.env)

```ini
# Agnes AI API
AGNES_API_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_API_KEY=sk-your-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pavo_agent

# Cache / Queue
REDIS_URL=redis://localhost:6379/0

# File Storage (video output)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secret
MINIO_BUCKET=pavo-videos

# App
APP_ENV=development
LOG_LEVEL=INFO
MAX_CONCURRENT_VIDEO_JOBS=3
VIDEO_TIMEOUT_SECONDS=300
```
"""
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)
print('README.md written successfully')

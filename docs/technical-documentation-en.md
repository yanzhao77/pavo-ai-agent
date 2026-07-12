# Pavo AI Agent Technical Documentation

> Version 2.0 | 2026-07-12

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [AI Agent System](#5-ai-agent-system)
6. [Data Model](#6-data-model)
7. [API Reference](#7-api-reference)
8. [Development Setup](#8-development-setup)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Guide](#10-deployment-guide)
11. [Security](#11-security)

---

## 1. Project Overview

### 1.1 Mission

Pavo AI Agent is an AI-powered storyboard generation platform for short video creators. It orchestrates multiple specialized AI agents to transform natural language story descriptions into formatted video storyboard scripts, with optional AI video generation.

### 1.2 Core Capabilities

- **Natural Language Understanding** — Understand story descriptions, extract key narrative elements
- **Multi-Agent Collaboration** — 7 specialized AI agents working in sequence
- **Structured Output** — Industry-standard storyboard JSON format
- **Real-Time Streaming** — SSE-powered live agent progress tracking
- **Video Model Integration** — AI video generation from storyboard prompts
- **Multi-Format Export** — Markdown, plain text, PDF

### 1.3 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | FastAPI (async) | High performance async framework, native SSE, async ORM |
| AI Gateway | Agnes AI | Unified API Key, OpenAI-compatible, text+video+sync audio |
| Task Queue | Celery + Redis | Async video generation for long-running tasks |
| Database | PostgreSQL | JSON fields for structured + semi-structured data |
| Frontend | Next.js 14 (App Router) | SSR + RSC, excellent DX |
| UI | TailwindCSS | Utility-first CSS, rapid consistent UI |
| Storage | MinIO (S3-compatible) | Self-hosted object storage for video files |

---

## 2. System Architecture

### 2.1 Layered Architecture

```
+--------------------------------------------------------------+
|                   Presentation Layer (Next.js)                |
|  Chat Input | Real-time Preview | Edit | Export | Auth       |
+--------------------------+-----------------------------------+
                           | HTTP / SSE
+--------------------------v-----------------------------------+
|                    API Routing Layer (FastAPI)                |
|  /api/projects /api/auth /api/health                        |
|  Request validation (Pydantic) | Auth middleware | SSE push  |
+--------------------------+-----------------------------------+
                           |
+--------------------------v-----------------------------------+
|                    Service Layer                              |
|  +-------------------------------------------------------+   |
|  |  ProjectService (Workflow Orchestrator)               |   |
|  |  create_project -> run_workflow -> render_video       |   |
|  +-------------------------------------------------------+   |
|  +----------+ +------------+ +--------+ +---------------+     |
|  |AgnesAI   | | Auth       | | Celery | | Export        |     |
|  |Client    | | (Token)    | | Tasks  | | Markdown/PDF  |     |
|  +----------+ +------------+ +--------+ +---------------+     |
+--------------------------+-----------------------------------+
                           |
+--------------------------v-----------------------------------+
|                    AI Agent Layer                             |
|  Planner -> Character -> Scene -> Prop -> Storyboard -> Rev  |
|  ^______________________________Fixer_______________________ |
+--------------------------+-----------------------------------+
                           |
+--------------------------v-----------------------------------+
|                    Infrastructure Layer                       |
|  PostgreSQL | Redis | MinIO | Agnes AI Unified Gateway       |
+--------------------------------------------------------------+
```

### 2.2 Request Lifecycle

```
User submits story
    |
    v
1. POST /api/projects -> Create Project (status=generating)
    |
    v
2. asyncio.create_task(run_workflow)  <- async background
    |
    v
3. Agent Pipeline executes sequentially
   Planner -> Character -> Scene -> Prop -> Storyboard -> Review -> Fix
    |
    v
4. After each step: project updated, SSE pushes to frontend
    |
    v
5. User GET /api/projects/{id} for final result
```

---

## 3. Backend Architecture

### 3.1 Module Structure

```
backend/
+-- app/
|   +-- main.py                  # FastAPI entry, lifespan, CORS
|   +-- config.py                # Pydantic BaseSettings
|   +-- api/routes.py            # 18 REST API endpoints
|   +-- agents/
|   |   +-- base.py              # BaseAgent abstract class
|   |   +-- planner.py           # Story analysis
|   |   +-- character_agent.py   # Character generation
|   |   +-- scene_agent.py       # Scene generation
|   |   +-- prop_agent.py        # Prop generation
|   |   +-- storyboard_agent.py  # Storyboard generation
|   |   +-- reviewer.py          # Quality review
|   |   +-- fixer.py             # Auto-fix
|   +-- models/
|   |   +-- project.py           # SQLAlchemy ORM
|   |   +-- schema.py            # Pydantic validation
|   +-- db/database.py           # Async engine + session factory
|   +-- services/
|       +-- agnes_client.py      # Agnes AI HTTP client
|       +-- auth.py              # Token auth
|       +-- project_service.py   # Workflow orchestrator
|       +-- storage.py           # MinIO storage
|       +-- celery_app.py        # Celery config
|       +-- video_tasks.py       # Async video tasks
|       +-- export/markdown.py   # Markdown export
|       +-- export/pdf.py        # PDF export
+-- tests/                       # 12 test suites
```

### 3.2 Config Module

```python
class Settings(BaseSettings):
    app_name: str = "Pavo AI Agent"
    agnes_api_base_url: str = "https://apihub.agnes-ai.com/v1"
    agnes_api_key: str = ""
    database_url: str = "postgresql+asyncpg://..."
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "http://localhost:9000"
    max_concurrent_video_jobs: int = 3
    video_timeout_seconds: int = 300
    model_config = {"env_file": ".env"}
```

Uses `pydantic-settings` for auto-loading from environment or `.env`.

### 3.3 FastAPI Entry

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
```

### 3.4 Agnes AI Client

The HTTP client (`agnes_client.py`) includes:

**Retry Mechanism**:
```python
async def _retry_with_backoff(fn, max_retries=3, base_delay=1.0, max_delay=30.0):
    # Exponential backoff: 1s, 2s, 4s, max 30s
    # Only retries on 429 (Rate Limit) and 503 (Model Unavailable)
```

**Rate Limiting**:
```python
async def _rate_limit(self):
    # Minimum interval of 0.5s between calls
```

**Exception Hierarchy**:
- `AgnesAIError` (base)
- `AgnesAIRateLimitError` (429)
- `AgnesAIModelNotFoundError` (503)
- `AgnesAITimeoutError`

**Supported APIs**:
- `chat()` — Text generation (sync/stream)
- `chat_stream()` — Streaming text (async generator)
- `generate_video()` — Video generation

### 3.5 SSE Stream Implementation

```python
async def event_stream():
    last_trace_count = 0
    while True:
        await session.refresh(project)
        traces = project.trace_log or []
        for i in range(last_trace_count, len(traces)):
            yield f"data: {json.dumps(trace_item)}\n\n"
        if project.status in ("completed", "draft"):
            yield f"data: {json.dumps({'type': 'agent:complete'})}\n\n"
            break
        await asyncio.sleep(1)
```

---

## 4. Frontend Architecture

### 4.1 Module Structure

```
frontend/
+-- src/app/
|   +-- layout.tsx        # Root layout (zh-CN)
|   +-- page.tsx          # Main page (auth + content)
|   +-- globals.css       # TailwindCSS global styles
+-- src/components/
|   +-- AuthGuard.tsx     # Login gate component
|   +-- ChatPanel.tsx     # Story input + agent log
|   +-- PreviewPanel.tsx  # Multi-tab preview
|   +-- Timeline.tsx      # Shot timeline (drag & drop)
|   +-- VideoPanel.tsx    # Video playback
|   +-- SortableShot.tsx  # Draggable shot card
|   +-- Skeleton.tsx      # Loading skeletons
|   +-- Toast.tsx         # Toast notifications
|   +-- ConfirmDialog.tsx # Confirmation modal
+-- src/lib/api.ts         # API client
+-- src/types/project.ts   # TypeScript types
```

### 4.2 Component Hierarchy

```
App (page.tsx)
+-- AuthGuard
+-- HomeContent
    +-- ToastProvider
    +-- div (left-right layout)
        +-- ChatPanel
        |   +-- Input box
        |   +-- Agent log list
        +-- PreviewPanel
            +-- TabBar (Storyboard | Characters | Scenes | Props)
            +-- Timeline (Storyboard tab)
            |   +-- SortableShot[]
            +-- Characters/Scenes/Props tabs
```

---

## 5. AI Agent System

### 5.1 BaseAgent

```python
class BaseAgent:
    async def _call_structured(self, messages, temperature=0.7):
        """Call Agnes AI and parse structured JSON output"""
        response = await agnes_client.chat(
            messages=[{"role": "system", "content": self.system_prompt}, *messages],
            temperature=temperature,
            model="agnes-2.0-flash",
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return response
```

### 5.2 Agent Pipeline

| # | Agent | Responsibility | Output Schema |
|---|-------|---------------|---------------|
| 1 | **Planner** | Story analysis: theme, emotion, elements, duration | `{theme, emotion, main_characters, estimated_duration, key_elements}` |
| 2 | **Character** | Character profiles: name, age, appearance, personality | `CharacterSchema[]{name, role, age, gender, appearance, personality, voice, relationship, consistencyKey}` |
| 3 | **Scene** | Scene designs: environment, lighting, atmosphere | `SceneSchema[]{name, timeOfDay, environment, lighting, atmosphere}` |
| 4 | **Prop** | Prop catalog: appearance, interaction, significance | `PropSchema[]{name, type, appearance, interaction, significance}` |
| 5 | **Storyboard** | Shot-by-shot storyboard | `StoryboardSchema{projectName, globalBGM, scenes[]}` |
| 6 | **Reviewer** | Quality review: consistency, completeness | Review report with `needs_fix` flag |
| 7 | **Fixer** | Auto-correct identified issues | Corrected storyboard JSON |

### 5.3 Storyboard Schema

```python
class StoryboardSchema(BaseModel):
    projectName: str
    globalBGM: str
    scenes: list[{
        title: str,           # Scene/Act title
        duration: str,        # Total duration
        mood: str,            # Emotional tone
        music: str,           # BGM + SFX text
        keyframe: str,        # Keyframe description
        shots: list[{
            shotNumber: int,  # Sequential number
            shotType: str,    # Wide/Full/Medium/Close/ECU
            cameraMove: str,  # Static/Track/Push in/Pull out/Pan/Follow
            cameraAngle: str, # Eye-level/Slight high angle/Profile
            description: str, # Scene description
            dialogue: str,    # Dialogue text
            duration: str,    # Duration
            characters: list  # Characters present
        }]
    }]
```

---

## 6. Data Model

### 6.1 Project

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | str | Owner |
| title | str | Auto-generated title |
| status | enum | draft / generating / completed |
| input_raw | text | Original story |
| input_extracted | json | Planner analysis |
| characters | json | Character profiles |
| scenes | json | Scene designs |
| props | json | Props |
| storyboard | json | Complete storyboard |
| videos | json | Generated video metadata |
| task_ids | json | Celery task IDs |
| trace_log | json | Agent execution trace |
| created_at | datetime | Auto-set |
| updated_at | datetime | Auto-updated |

### 6.2 VersionHistory

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to Project |
| version_number | int | Sequential |
| snapshot | json | Full state |
| description | str | Version label |
| created_at | datetime | Auto-set |

### 6.3 Feedback

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to Project |
| user_id | str | User identifier |
| rating | str | up / down |
| comment | text | Feedback text |
| created_at | datetime | Auto-set |

---

## 7. API Reference

### Endpoints

All endpoints under `/api`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | Login, get token |
| GET | `/auth/me` | Verify token |
| POST | `/projects` | Create project |
| GET | `/projects` | List projects |
| GET | `/projects/{id}` | Get project |
| PATCH | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/projects/{id}/stream` | SSE stream |
| POST | `/projects/{id}/regenerate` | Regenerate module |
| POST | `/projects/{id}/render` | Render video |
| POST | `/projects/{id}/versions` | Create version |
| GET | `/projects/{id}/versions` | List versions |
| POST | `/projects/{id}/versions/{vid}/restore` | Restore version |
| GET | `/projects/{id}/videos` | Video list |
| GET | `/projects/{id}/tasks` | Task status |
| GET | `/projects/{id}/export` | Export |
| POST | `/projects/{id}/feedback` | Submit feedback |

---

## 8. Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Agnes AI API Key

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt -r requirements.txt
cp .env.example .env         # Set AGNES_API_KEY
docker compose up -d postgres redis minio
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 9. Testing Strategy

The project includes 12 backend test suites and Playwright E2E tests.

**Test Configuration**:
```python
# conftest.py
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
```

**Running Tests**:
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term --cov-report=html

cd frontend
npx playwright test
```

---

## 10. Deployment Guide

### Docker Compose

```bash
docker compose up --build -d
```

**Services**: PostgreSQL, Redis, MinIO, Backend (FastAPI), Celery Worker.

### CI/CD

GitHub Actions (`.github/workflows/test.yml`):
- Runs on push/PR
- Spins up PostgreSQL + Redis
- Installs dependencies and runs pytest
- Uploads coverage report to Codecov

---

## 11. Security

- **API Key**: Backend-only, injected via `.env` or secret manager. `.gitignore` excludes `.env`.
- **Auth**: In-memory token store, SHA256 hashed, 7-day expiry, supports revocation.
- **Transport**: HTTP (dev) / HTTPS (prod). SSE authenticated via token parameter.
- **Data Isolation**: Logical per `user_id` (no RLS on PostgreSQL yet).

---

> See the [User Guide](user-guide-en.md) for usage instructions, or the  [中文技术文档](technical-documentation.md) for the Chinese version.

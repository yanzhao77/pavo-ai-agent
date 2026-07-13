# Pavo AI Agent — Project Analysis
> Generated: 2026-07-13 | Phase 0 of MCP Server zero-dependency refactoring

---

## 1. Project Structure

`
pavo-ai-work/
├── backend/
│   ├── app/
│   │   ├── agents/           # 7 AI Agents (base + planner + character + scene + prop + storyboard + reviewer + fixer)
│   │   ├── api/              # REST API routes
│   │   ├── db/               # Database (async SQLAlchemy + PostgreSQL)
│   │   ├── models/           # ORM + Pydantic schemas
│   │   ├── services/         # Business logic + integrations (AgnesAI/Auth/Celery/Storage/Export)
│   │   ├── config.py         # Pydantic settings (venv)
│   │   └── main.py           # FastAPI entry
│   ├── mcp_server/           # MCP Server (12 Tools + Memory + RAG + Middleware)
│   ├── tests/                # Test suites
│   └── requirements.txt      # Dependencies
├── frontend/                 # Next.js 14
├── docker-compose.yml        # PostgreSQL + Redis + MinIO + Backend
└── docs/                     # Documentation
`

## 2. External Dependencies

| Service | Library | Usage Location | Phase |
|---------|---------|----------------|-------|
| PostgreSQL | asyncpg + SQLAlchemy | backend/app/db/database.py, models/, services/ | Phase 1 |
| pgvector | PostgreSQL extension | mcp_server/memory/store.py | Phase 2 |
| Redis | redis-py | backend/app/services/celery_app.py, video_tasks.py | Phase 3 |
| Celery | celery | backend/app/services/celery_app.py, video_tasks.py | Phase 4 |
| MinIO | boto3 | backend/app/services/storage.py | Phase 5 |

## 3. Agent Call Chain

`
POST /api/projects
  → ProjectService.create_project()
    → asyncio.create_task(run_workflow())
      → PlannerAgent.plan()
      → CharacterAgent.generate()
      → SceneAgent.generate()
      → PropAgent.generate()
      → StoryboardAgent.generate()
      → ReviewerAgent.review()
      → FixerAgent.fix()
      → status = completed
`

All agents use BaseAgent._call_structured() → gnes_client.chat().

## 4. MCP Server Structure

`
mcp_server/
├── main.py          # Entry: 12 tools, 5 resources, 2 prompts
├── models/          # MCPToolResult + MCPError
├── memory/          # MemoryStore + Embedding + Importance
├── rag/             # RAGRetriever + Builder + Re-ranker
├── middleware/      # MemoryMiddleware
├── tools/           # MemoryTools (4 tools)
└── adapter/         # ProjectAdapter (bridges to ProjectService)
`

## 5. Database Schema

Current tables (PostgreSQL):
- projects (UUID PK, user_id, title, status, input_raw, input_extracted, characters, scenes, props, storyboard, videos, task_ids, trace_log, created_at, updated_at)
- version_history (UUID PK, project_id, version_number, snapshot, description, created_at)
- feedback (UUID PK, project_id, user_id, rating, comment, created_at)
- user_memories (UUID PK, user_id, memory_type, content, embedding JSON, importance, source, tags, created_at, updated_at, accessed_at)
- knowledge_base (UUID PK, category, title, content, tags, embedding JSON, source, priority, created_at, updated_at)
- session_contexts (session_id PK, user_id, project_id, messages, context, created_at, expires_at)

## 6. Refactoring Plan Summary

| Phase | Change | Impact |
|-------|--------|--------|
| 1 | PostgreSQL → SQLite + sqlite-vec | All DB code |
| 2 | VectorStore abstraction layer | Memory/RAG module |
| 3 | Redis → TTLCache | Session/cache |
| 4 | Celery → asyncio Queue | Video tasks |
| 5 | MinIO → Local storage | File upload |
| 6-12 | Config/CLI/Testing/Docs | Full project |

## 7. Key Risks

1. sqlite-vec compatibility with existing pgvector schema
2. asyncio Queue persistence for video tasks
3. Local storage path handling on different OS
4. Existing PostgreSQL test suite migration

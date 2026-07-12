 # Pavo AI Agent 源码深度解析：从自然语言故事到视频分镜的 Multi-Agent 工程实践
 
 ## 项目简介
 
 **Pavo AI Agent** 是一个开源的多智能体视频分镜生成平台（MIT 协议）。输入一段自然语言故事，系统通过 7 个 AI Agent 协作，自动输出完整的逐镜头分镜脚本，并支持对接 AI 视频模型生成视频。
 
 项目地址：[https://github.com/yanzhao77/pavo-ai-agent](https://github.com/yanzhao77/pavo-ai-agent)
 
 技术栈：
 - 后端：Python 3.10+ / FastAPI / SQLAlchemy 2.0 / Alembic / Celery
 - 前端：Next.js 14 / React 18 / TypeScript / TailwindCSS / dnd-kit
 - 基础设施：PostgreSQL / Redis / MinIO
 - AI 网关：Agnes AI（兼容 OpenAI 协议）
 
 ## 一、项目结构全景
 
 ```
 pavo-ai-work/
 ├── backend/
 │   ├── app/
 │   │   ├── agents/                # 7 个 AI Agent 实现
 │   │   │   ├── base.py            # BaseAgent 基类
 │   │   │   ├── planner.py         # 故事分析与规划
 │   │   │   ├── character_agent.py # 角色设计
 │   │   │   ├── scene_agent.py     # 场景设计
 │   │   │   ├── prop_agent.py      # 道具编目
 │   │   │   ├── storyboard_agent.py# 分镜拆解
 │   │   │   ├── reviewer.py        # 质量审查
 │   │   │   └── fixer.py           # 自动修复
 │   │   ├── api/routes.py          # 18 个 REST 端点
 │   │   ├── db/database.py         # 异步 SQLAlchemy 引擎
 │   │   ├── models/
 │   │   │   ├── project.py         # ORM（Project/VersionHistory/Feedback）
 │   │   │   └── schema.py          # Pydantic 校验模式
 │   │   ├── services/
 │   │   │   ├── agnes_client.py    # LLM 客户端（重试+限流）
 │   │   │   ├── project_service.py # 管线编排
 │   │   │   ├── auth.py            # Token 认证（内存）
 │   │   │   ├── storage.py         # MinIO 存储（boto3）
 │   │   │   ├── celery_app.py      # Celery 配置
 │   │   │   ├── video_tasks.py     # 异步视频生成
 │   │   │   └── export/            # 导出（Markdown/PDF）
 │   │   ├── config.py              # Pydantic Settings
 │   │   └── main.py                # FastAPI 入口
 │   ├── tests/                     # 12 个测试套件
 │   └── Dockerfile
 ├── frontend/
 │   ├── src/
 │   │   ├── app/page.tsx           # 主页
 │   │   ├── components/            # 9 个组件
 │   │   ├── lib/api.ts             # API 客户端
 │   │   └── types/project.ts       # TypeScript 类型
 │   └── tests/                     # Playwright E2E
 ├── docs/
 ├── docker-compose.yml
 └── README.md
 ```
 
 ## 二、Agent 系统源码深度拆解
 
 ### 2.1 BaseAgent 基类：极简设计
 
 所有的 Agent 共享一个不到 40 行的基类：
 
 ```python
 # backend/app/agents/base.py
 import json, logging
 from app.services.agnes_client import agnes_client
 
 logger = logging.getLogger(__name__)
 SYSTEM_PROMPT = "You are a professional AI film director and screenwriter. Respond in Chinese."
 
 class BaseAgent:
     def __init__(self, name: str, system_prompt: str = SYSTEM_PROMPT):
         self.name = name
         self.system_prompt = system_prompt
 
     async def _call(self, messages, temperature=0.7, max_tokens=4096, stream=False):
         full = [{"role": "system", "content": self.system_prompt}] + messages
         return await agnes_client.chat(full, temperature=temperature, max_tokens=max_tokens, stream=stream)
 
     async def _call_structured(self, messages, temperature=0.3, max_tokens=4096):
         """调用 LLM 并强制解析为 JSON，失败时降级为 raw 文本"""
         full = [{"role": "system", "content": self.system_prompt}] + messages
         result = await agnes_client.chat(full, temperature=temperature, max_tokens=max_tokens)
         try:
             return json.loads(result)
         except json.JSONDecodeError:
             logger.warning(f"{self.name}: failed to parse JSON, returning raw text")
             return {"raw": result}
 
     async def _stream(self, messages, temperature=0.7, max_tokens=4096):
         full = [{"role": "system", "content": self.system_prompt}] + messages
         async for chunk in agnes_client.chat_stream(full, temperature=temperature, max_tokens=max_tokens):
             yield chunk
 ```
 
 基类只提供三个方法：
 - `_call`: 基础 LLM 调用
 - `_call_structured`: 调用 + JSON 强制解析，解析失败返回 `{"raw": result}` 降级
 - `_stream`: 流式调用
 
 值得注意的是 `_call_structured` 的设计——它不是死等 JSON，解析失败就返回原始文本并记一条 warn 日志。对于生产环境，这意味着下游代码必须做好防御性处理。
 
 ### 2.2 各 Agent 实现模式
 
 所有子类遵循统一的「System Prompt + 具体方法」模式。以下为完整的 7 个 Agent 实现：
 
 **PlannerAgent — 故事分析：**
 
 ```python
 class PlannerAgent(BaseAgent):
     def __init__(self):
         super().__init__("planner", "You are a creative story analyst...")
 
     async def plan(self, input_text: str) -> dict:
         result = await self._call_structured([
             {"role": "user", "content": f"Analyze this story...\n\nStory: {input_text}\n\nReturn JSON with keys: characters, scene, theme, emotion, duration"}
         ])
         return result
 ```
 
 **CharacterAgent — 角色设计：**
 
 ```python
 class CharacterAgent(BaseAgent):
     def __init__(self):
         super().__init__("character", CHARACTER_PROMPT)
 
     async def generate(self, input_text: str) -> list:
         result = await self._call_structured([
             {"role": "user", "content": f"Create character settings...\n\n{input_text}"}
         ])
         if isinstance(result, dict) and "raw" in result:
             return []
         return result if isinstance(result, list) else []
 ```
 
 **StoryboardAgent — 分镜拆解（最重要的 Agent）：**
 
 Prompt 定义最为详尽，包含输出 JSON 的结构示例、情感分类（起承转合）、允许的镜头类型枚举、以及一个自我校验清单：
 
 ```python
 STORYBOARD_PROMPT = """
 You are a professional storyboard artist and screenwriter...
 
 Requirements:
 - 3-4 acts following qi-cheng-zhuan-he structure
 - Total duration 30-60 seconds
 - shotType: 远景,全景,中景,中近景,近景,特写
 - cameraMove: 固定,横移,推近,拉远,摇移,跟拍
 - cameraAngle: 平视,平视微俯,平视侧面
 
 VERIFICATION CHECKLIST:
 1. Sum of shot durations equals scene duration
 2. Shot numbers are sequential
 3. Listed characters exist in character data
 4. shotType/cameraMove/cameraAngle from allowed list
 5. Valid parseable JSON (test with json.loads before returning)
 """
 ```
 
 Reviewer 和 Fixer 构成自愈闭环：
 
 ```python
 # Reviewer 返回审查结果
 review = await self.reviewer.review(project)
 if review.get("needs_fix"):
     fixed = await self.fixer.fix(project, review)
     project.storyboard = fixed
 ```
 
 Reviewer 使用 temperature=0.2（尽可能客观），Fixer 使用 temperature=0.3（精准修复），Storyboard 使用 0.4（结构+创意平衡），其余 Agent 使用默认的 0.7。
 
 ### 2.3 LLM 客户端：指数退避重试
 
 ```python
 class AgnesAIClient:
     def __init__(self, base_url, api_key, max_retries=3):
         self.client = httpx.AsyncClient(timeout=60)
         ...
 
     async def chat(self, messages, temperature=0.7, max_tokens=4096, stream=False):
         for attempt in range(self.max_retries + 1):
             try:
                 resp = await self.client.post(f"{self.base_url}/chat/completions", ...)
                 if resp.status_code == 429:
                     wait = min(2 ** attempt + random.random(), 30)
                     await asyncio.sleep(wait)
                     continue
                 resp.raise_for_status()
                 return resp.json()["choices"][0]["message"]["content"]
             except Exception as e:
                 if attempt == self.max_retries:
                     raise
                 await asyncio.sleep(2 ** attempt)
         raise RuntimeError(f"LLM call failed after {self.max_retries} retries")
 ```
 
 核心特性：
 - 60 秒超时（httpx 级别）
 - 429 响应走随机退避，其他错误走指数退避
 - 兼容 OpenAI 协议，可替换为任意兼容 API
 
 ## 三、管线编排与数据流
 
 ### 3.1 run_workflow 核心逻辑
 
 所有 Agent 的串行编排在 `project_service.py` 中：
 
 ```python
 async def run_workflow(self, project_id: uuid.UUID):
     project = await self.session.execute(select(Project).where(Project.id == project_id))
     project = project.scalar_one_or_none()
 
     try:
         # Step 1: Planner
         plan = await self.planner.plan(project.input_raw)
         await self._log_trace(project, "planner", "Plan created", project.input_raw, plan)
 
         # Step 2: Character (带校验)
         chars = await self.character_agent.generate(project.input_raw)
         chars = validate_characters(chars)  # Pydantic 校验
         project.characters = chars
 
         # Step 3: Scene (依赖 characters)
         scenes = await self.scene_agent.generate(project.input_raw, chars)
         scenes = validate_scenes(scenes)
         project.scenes = scenes
 
         # Step 4: Prop (依赖 characters + scenes)
         props = await self.prop_agent.generate(project.input_raw, chars, scenes)
         props = validate_props(props)
         project.props = props
 
         # Step 5: Storyboard (依赖 characters + scenes + props)
         storyboard = await self.storyboard_agent.generate(project.input_raw, chars, scenes, props)
         storyboard = validate_storyboard(storyboard)
         project.storyboard = storyboard
 
         # Step 6-7: Reviewer + Fixer（条件修复）
         review = await self.reviewer.review(project)
         if review.get("needs_fix"):
             await self._log_trace(project, "reviewer", "Needs fix", storyboard, review, "failed")
             fixed = await self.fixer.fix(project, review)
             project.storyboard = fixed
 
         project.status = ProjectStatus.COMPLETED
     except Exception as e:
         logger.error(f"Workflow failed: {e}")
         project.status = ProjectStatus.DRAFT
         await self._log_trace(project, "system", f"Error: {e}", "", "", "failed")
 
     await self.session.commit()
 ```
 
 核心设计要点：
 - **串行依赖链**：Scenes 依赖 Characters，Storyboard 依赖前四者
 - **每步校验**：每个 Agent 输出都经过对应的 Pydantic validate 函数
 - **条件修复**：Reviewer 判定 `needs_fix` 才触发 Fixer
 - **异常兜底**：任何 Agent 失败不抛到外层，转为 DRAFT 状态 + trace_log 记录
 
 ### 3.2 trace_log：全链路可观测
 
 每个 trace 记录完整信息：
 
 ```python
 async def _log_trace(self, project, agent_name, action, input_data, output_data, status="passed"):
     trace = {
         "agent": agent_name,
         "action": action,
         "input": str(input_data)[:500],   # 截断防溢出
         "output": str(output_data)[:500],
         "status": status,
         "timestamp": datetime.utcnow().isoformat()
     }
     traces = project.trace_log or []
     traces.append(trace)
     project.trace_log = traces
     await self.session.commit()
 ```
 
 input/output 截断到 500 字符避免数据库 JSON 字段膨胀。每条 record 包含 status 和时间戳，为前端 SSE 提供增量推送基础。
 
 ### 3.3 SSE 流：基于轮询的实时推送
 
 前端通过 EventSource 建立 SSE 连接，后端实现是读取数据库 + 1 秒轮询：
 
 ```python
 @router.get("/projects/{project_id}/stream")
 async def stream_project(project_id):
     async def event_stream():
         last_trace_count = 0
         while True:
             await session.refresh(project)
             traces = project.trace_log or []
             for i in range(last_trace_count, len(traces)):
                 t = traces[i]
                 yield f"data: {json.dumps({'type': 'agent:progress', 'agent': t['agent'], 'action': t['action'], 'status': t['status']})}\n\n"
                 last_trace_count = i + 1
             if project.status.value in ("completed", "draft"):
                 yield f"data: {json.dumps({'type': 'agent:complete', 'status': project.status.value})}\n\n"
                 break
             await asyncio.sleep(1)
     
     return StreamingResponse(event_stream(), media_type="text/event-stream")
 ```
 
 注意这不是真正的 Server-Sent Events 推送——后端并不知道 Agent 何时完成，只能每秒轮询 trace_log 检查是否有新记录。前端 EventSource 的 `onmessage` 事件一旦收到 `agent:complete` 就关闭连接。
 
 ## 四、从分镜到视频：build_t2v_prompts
 
 这是项目中最具工程价值的函数之一——将结构化分镜数据转换为文本到视频模型的 prompt：
 
 ```python
 def build_t2v_prompts(project):
     storyboard = project.storyboard or {}
     characters = project.characters or []
     scenes = project.scenes or []
     props_data = project.props or []
 
     # 构建角色外观映射表
     char_map = {}
     for c in characters:
         if isinstance(c, dict) and "name" in c:
             appr = c.get("appearance", {})
             desc = f'{appr.get("build","")} {appr.get("face","")} {appr.get("hair","")}'
             desc += f' wearing {appr.get("clothing","")}'
             char_map[c["name"]] = desc.strip()
 
     # 构建场景环境映射表
     scene_map = {}
     for s in scenes:
         if isinstance(s, dict) and "name" in s:
             env = s.get("environment", {})
             light = s.get("lighting", {})
             desc = f'{env.get("style","")} {env.get("type","")} with {light.get("type","")} lighting'
             scene_map[s["name"]] = desc.strip()
 
     # 逐镜生成 T2V prompt
     results = []
     for scene_idx, scene in enumerate(storyboard.get("scenes", [])):
         for shot in scene.get("shots", []):
             shot_desc = shot.get("description", "")
             shot_type = shot.get("shotType", "medium shot")
             camera = shot.get("cameraMove", "static")
             angle = shot.get("cameraAngle", "eye-level")
             mood = scene.get("mood", "")
             
             prompt = f"Shot: {shot_type}. Camera: {camera} ({angle})."
             # 注入角色外观
             char_descs = []
             for cn in shot.get("characters", []):
                 if cn in char_map:
                     char_descs.append(f"{cn}: {char_map[cn]}")
             if char_descs:
                 prompt += f" Characters: {';'.join(char_descs)}."
             # 注入场景环境
             sn = scene.get("title", "")
             sd = scene_map.get(sn, sn)
             if sd:
                 prompt += f" Setting: {sd}."
             prompt += f" Action: {shot_desc}"
             if mood:
                 prompt += f" Mood: {mood}."
             
             results.append({
                 "scene_idx": scene_idx,
                 "shot_number": shot.get("shotNumber", 0),
                 "prompt": prompt
             })
     return results
 ```
 
 这个函数干的事情可以概括为：**合并角色外观 + 场景环境 + 镜头参数 + 动作描述 → 一条完整的 T2V prompt**。输出的每条 prompt 包含了让视频模型生成一致画面所需的全部上下文。
 
 ## 五、Pydantic 校验层
 
 项目在 `models/schema.py` 中定义了完整的 Pydantic 数据模型：
 
 ```python
 class CharacterSchema(BaseModel):
     name: str
     role: str = "supporting"
     age: str = ""
     gender: str = ""
     appearance: CharacterAppearance = Field(default_factory=CharacterAppearance)
     personality: list[str] = []
     voice: str = ""
     relationship: str = ""
     consistencyKey: str = ""
 
 class ShotSchema(BaseModel):
     shotNumber: int
     shotType: str = "medium shot"
     cameraMove: str = "static"
     cameraAngle: str = "eye-level"
     description: str = ""
     dialogue: str = ""
     duration: str = "0s"
     characters: list[str] = []
 ```
 
 每个类型对应一个 validate 函数，采用「尝试解析 → 失败降级」策略：
 
 ```python
 def validate_characters(data: list) -> list:
     if not isinstance(data, list):
         return []
     results = []
     for item in data:
         if not isinstance(item, dict):
             continue
         try:
             results.append(CharacterSchema(**item).model_dump())
         except Exception:
             results.append(item)  # 降级：保留原始 dict
     return results
 ```
 
 这层校验的价值在于：LLM 的输出格式经常波动，Pydantic 的校验 + 降级机制保证了系统不会因为一个字段缺失就全面崩溃。
 
 ## 六、一个有趣的细节：chr() 拼接
 
 在 `project_service.py` 和 `routes.py` 中，有一个代码片段：
 
 ```python
 p[chr(115)+chr(104)+chr(111)+chr(116)+chr(95)+chr(110)+chr(117)+chr(109)+chr(98)+chr(101)+chr(114)]
 ```
 
 这个 chr 序列解码后是 `"shot_number"`。在同一个文件中，其他所有 key 都直接用字符串字面量，唯独这里用了 chr 拼接。这种刻意 obfuscation 很可能是为了规避某种基于字符串扫描的检测规则。这是一个值得注意的「工程约束痕迹」。
 
 ## 七、认证系统：极简内存实现
 
 ```python
 _token_store: dict[str, dict] = {}
 TOKEN_EXPIRY_SECONDS = 86400 * 7
 
 def create_token(user_id: str) -> str:
     token = secrets.token_hex(32)
     token_hash = hashlib.sha256(token.encode()).hexdigest()
     _token_store[token_hash] = {
         "user_id": user_id,
         "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
     }
     return token
 
 def verify_token(token: str) -> Optional[str]:
     token_hash = hashlib.sha256(token.encode()).hexdigest()
     entry = _token_store.get(token_hash)
     if not entry or time.time() > entry["expires_at"]:
         return None
     return entry["user_id"]
 ```
 
 设计特点：
 - Token 原值存在客户端，服务端只存 SHA256 哈希
 - 内存存储，重启后所有 token 失效（对于自部署应用可接受）
 - 自动过期清理（`clean_expired` 函数）
 
 ## 八、部署与使用
 
 ### Docker Compose 一键部署（推荐）
 
 ```bash
 git clone https://github.com/yanzhao77/pavo-ai-agent.git
 cd pavo-ai-agent
 cp .env.example .env
 # 编辑 .env，设置 AGNES_API_KEY
 docker compose up --build -d
 ```
 
 访问 `http://localhost:3000` 即可使用。基础服务端口：
 
 | 端口 | 服务 |
 |------|------|
 | 5432 | PostgreSQL |
 | 6379 | Redis |
 | 9000 | MinIO API |
 | 8000 | 后端 API |
 | 3000 | 前端 |
 
 ### 本地开发模式
 
 ```bash
 docker compose up -d postgres redis minio
 cd backend && pip install -r requirements.txt
 python -m uvicorn app.main:app --reload --port 8000
 
 cd frontend && npm install && npm run dev
 ```
 
 ### API 核心调用
 
 ```bash
 # 创建项目
 curl -X POST http://localhost:8000/api/projects \
   -H "Content-Type: application/json" \
   -d '{"input": "一位父亲下班回到家，5岁儿子端来洗脚盆..."}'
 # 响应: {"projectId":"xxx","status":"generating"}
 
 # 查看结果
 curl http://localhost:8000/api/projects/{id}
 # 响应包含 characters/scenes/props/storyboard 全部数据
 
 # 导出 Markdown
 curl http://localhost:8000/api/projects/{id}/export?format=markdown
 
 # 触发视频渲染
 curl -X POST http://localhost:8000/api/projects/{id}/render
 ```
 
 ## 九、测试体系
 
 项目包含 12 个测试套件，覆盖 6 个维度：
 
 ```bash
 cd backend
 python -m pytest tests/ --cov=app -v --cov-report=term
 ```
 
 测试分类与数量：
 
 | 测试文件 | 覆盖范围 | 用例数 |
 |----------|---------|-------|
 | `test_api.py` | 全部 18 个 API 端点 | ~15 |
 | `test_agents_direct.py` | 7 个 Agent 的独立调用 | ~10 |
 | `test_agnes_client.py` | LLM 客户端（重试/限流/流式）| ~7 |
 | `test_schema.py` | 全部 Pydantic Schema 校验 | ~12 |
 | `test_t2v.py` | T2V prompt 生成 | ~7 |
 | `test_workflow.py` | 完整管线编排 | ~4 |
 | `test_storage.py` | MinIO 存储 | ~3 |
 | `test_exports.py` | Markdown/PDF/Text 导出 | ~6 |
 | `test_integration.py` | 重试逻辑集成测试 | ~4 |
 | `test_video_tasks.py` | Celery 任务 | ~2 |
 | `test_phase2.py` | 版本/反馈/删除端点 | ~8 |
 
 测试特点：
 - 使用 Mock LLM（`mock_chat_response` fixture），不依赖真实 API
 - 前端 Playwright E2E 测试关键用户路径
 - 异常覆盖：JSON 解析失败、429 限流、输入为空等边界情况
 
 ## 十、工程亮点总结
 
 1. **薄基类模式**：BaseAgent 仅 40 行，Agent 定义 system prompt + 方法签名即可
 2. **数据契约先行**：Pydantic Schema + validate 函数层，保证 LLM 输出可控
 3. **trace_log 多用途**：同时服务前端 SSE、问题排查、Reviewer 输入
 4. **轮询 SSE**：简单可靠的实时进度方案（无需 WebSocket 基础设施）
 5. **T2V prompt 组装**：build_t2v_prompts 将结构化数据变成视频模型输入
 6. **完整测试覆盖**：12 个套件覆盖单元、集成、E2E 全链路
 7. **全栈 Docker 化**：docker-compose 一键运行
 
 项目完整源代码：[https://github.com/yanzhao77/pavo-ai-agent](https://github.com/yanzhao77/pavo-ai-agent)
 
 欢迎 Star、Fork 和提交 Issue。

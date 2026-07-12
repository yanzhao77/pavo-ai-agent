Pavo AI Agent — Memory + RAG 技术开发计划文档 v2.1
审核报告
审核对象：技术开发计划文档_v2.1_Memory_RAG.md
审核日期：2026-07-13
审核人：架构评审组
文档状态：🔄 评审中

目录
总体评价

架构设计审核

Agent Memory 模块审核

RAG 影视知识库审核

Memory Middleware 审核

MCP Tool 扩展审核

数据库与 Schema 审核

实施计划审核

测试策略审核

风险识别审核

审核结论与修改清单

1. 总体评价
1.1 评分
维度	评分（1-5）	说明
文档完整性	⭐⭐⭐⭐⭐	结构清晰，覆盖全面
技术方案合理性	⭐⭐⭐⭐☆	整体设计优秀，部分细节可优化
与 v2.0 兼容性	⭐⭐⭐⭐⭐	向后兼容设计良好
实施可行性	⭐⭐⭐⭐☆	计划合理，部分任务工时略紧
风险识别	⭐⭐⭐⭐☆	覆盖全面，可补充1-2项
1.2 核心结论
结论	说明
方案总体可行	Memory + RAG 设计合理，技术选型务实
与 v2.0 衔接良好	基于 Phase 1 交付清单，依赖关系清晰
需补充若干设计细节	见下文各章节具体意见
工时整体合理	20天预估可接受，部分任务建议微调
2. 架构设计审核
2.1 整体架构评估
✅ 架构设计合理，模块划分清晰

text
┌─────────────────────────────────────────────────────────────┐
│                   v2.1 新增架构评分                         │
├─────────────────────────────────────────────────────────────┤
│  模块              │ 设计质量 │ 说明                       │
│────────────────────┼─────────┼────────────────────────────│
│  Memory Store      │ ⭐⭐⭐⭐⭐ │ 分层清晰，接口完整          │
│  RAG Pipeline      │ ⭐⭐⭐⭐☆ │ 设计合理，种子数据量需确认    │
│  Memory Middleware │ ⭐⭐⭐⭐⭐ │ 透明集成，降级策略完善       │
│  MCP Tools 扩展    │ ⭐⭐⭐⭐☆ │ 4个Tool设计合理             │
│  数据库 Schema     │ ⭐⭐⭐⭐⭐ │ pgvector 集成规范           │
└─────────────────────────────────────────────────────────────┘
2.2 关键架构决策审核
决策	评估	说明
pgvector 作为向量数据库	✅ 合理	与 PostgreSQL 复用，运维简单，适合起步
Memory 分层（短期+长期）	✅ 合理	Redis TTL + pgvector 持久化，覆盖完整
Middleware 透明集成	✅ 优秀	对现有 Tool 零侵入，符合开闭原则
RAG 与 Memory 共用 Embedding	✅ 合理	减少依赖，统一向量化服务
context 参数预留	✅ 优秀	为未来扩展预留接口
3. Agent Memory 模块审核
3.1 记忆类型设计
✅ 设计合理，6 种记忆类型覆盖全面：

memory_type	用途	评估
style	创作风格偏好	✅ 核心类型
character	常用角色	✅ 核心类型
scene	偏好场景	✅ 核心类型
preference	通用偏好	✅ 辅助类型
story_arc	叙事结构偏好	✅ 辅助类型
feedback	用户反馈摘要	⚠️ 建议明确：是自动提取还是用户主动保存？
建议：在文档中明确 feedback 类型的来源——是 Agent 自动从用户对话中提取，还是用户通过 Tool 主动保存？两者在实现上差异较大。

3.2 重要性评分机制
⚠️ 设计未细化

文档中定义了 importance: float (0-1)，但未说明：

如何计算重要性？

谁负责设定？（用户？系统自动？）

默认值是多少？

建议补充：

python
# 重要性评分策略
class ImportanceStrategy:
    """重要性评分计算策略"""
    
    @staticmethod
    def from_user_saved() -> float:
        """用户主动保存 → 0.8-1.0"""
        return 0.9
    
    @staticmethod
    def from_auto_extracted(mentions: int, recency: float) -> float:
        """自动提取 → 基于提及次数和时效性"""
        # mentions: 同一内容在对话中出现的次数
        # recency: 距离当前时间的天数 (0-30)
        return min(0.3 + mentions * 0.1 - recency * 0.01, 0.8)
    
    @staticmethod
    def from_feedback_derived(rating: str) -> float:
        """用户反馈衍生 → 好评 0.7，差评 0.2"""
        return 0.7 if rating == "up" else 0.2
3.3 Embedding 策略
⚠️ 需明确具体实现

文档提到 "Embedding 客户端 (Agnes AI 接入)"，但未说明：

使用哪个 Embedding 模型？

向量维度是多少？

Batch 处理策略？

失败重试机制？

建议补充：

yaml
# embedding_config.yaml
model: "text-embedding-3-small"
dimension: 1536
batch_size: 100
max_retries: 3
timeout: 30s
cache_ttl: 3600s  # 相同文本缓存 1 小时
3.4 Session Memory TTL
✅ 设计合理，但需确认：

参数	文档值	评估
TTL	30 分钟	✅ 合理
存储	Redis	✅ 合理
触发更新	每次 Tool 调用	⚠️ 需确认：是否每次调用都更新 TTL？
建议：明确 Session TTL 的刷新策略——每次有活动时自动延长 TTL（滑动过期），避免用户在创作过程中会话超时。

4. RAG 影视知识库审核
4.1 知识库内容规划
✅ 覆盖面合理，但种子数据量需确认：

类别	首期条目	评估
镜头语言	15	✅ 合理
电影语法	10	✅ 合理
经典案例	10	✅ 合理
叙事结构	8	✅ 合理
类型模板	7	✅ 合理
BGM 与音效	5	⚠️ 偏少，建议增至 10
建议：BGM 与音效类别增至 10 条，覆盖更多情绪场景（悲伤、紧张、悬疑、浪漫、史诗等）。

4.2 知识检索 Pipeline
✅ 设计完整

text
用户输入 → RAGQueryBuilder → Embedding → pgvector ANN → Re-ranker → Context Injector → Agent Prompt
建议补充：

Re-ranker 具体方案：使用什么重排序模型？还是基于规则（如 category 匹配）？

python
# 建议的 Re-ranker 策略
class Reranker:
    """多级重排序策略"""
    
    async def rerank(
        self,
        candidates: list[KnowledgeEntry],
        query: RAGQuery,
        top_k: int = 5
    ) -> list[KnowledgeEntry]:
        """
        重排序策略：
        1. 向量相似度分数 (基础)
        2. category 匹配度 (+0.1)
        3. 优先级权重 (priority * 0.05)
        4. 时效性衰减 (旧的 -0.01)
        """
        ...
检索失败降级：当 RAG 检索返回空或低质量结果时，应降级到原始 Prompt（即不注入知识），而不是报错。

4.3 知识注入方式
⚠️ 建议明确注入位置

文档提到 "Agent Prompt RAG 注入"，但未说明注入到哪个 Agent。

建议：

注入目标	注入内容	说明
分镜智能体 (Storyboard Agent)	镜头语言 + 叙事结构	主要注入点
角色智能体 (Character Agent)	经典角色设计案例	次要注入点
场景智能体 (Scene Agent)	场景设计模板	次要注入点
核心注入点：分镜智能体是 RAG 知识注入的主要目标，其他 Agent 可根据需要选择性注入。

5. Memory Middleware 审核
5.1 设计评估
✅ 设计优秀，透明集成理念正确

评估项	状态	说明
透明集成	✅	对 Tool Handler 零侵入
低开销	✅	P95 < 100ms 目标合理
可降级	✅	Memory 不可用不影响核心功能
可观测性	⚠️	需补充日志和监控
5.2 降级策略补充
文档提到 "降级策略 (Memory 不可用)"，但未详细说明。

建议补充：

python
class MemoryMiddleware:
    """降级策略实现"""
    
    async def pre_process(self, tool_name: str, arguments: dict) -> dict:
        try:
            # 正常处理
            return await self._process_with_memory(tool_name, arguments)
        except MemoryUnavailableError:
            # 降级方案1: 记录日志，继续执行
            logger.warning(f"Memory unavailable, continuing without context")
            return arguments
        except MemoryTimeoutError:
            # 降级方案2: 超时降级，使用缓存
            return await self._process_with_cache(tool_name, arguments)
        except Exception as e:
            # 降级方案3: 未知错误，安全降级
            logger.error(f"Memory middleware error: {e}")
            return arguments  # 不影响主流程
5.3 可观测性补充
建议：为 Memory Middleware 增加以下可观测性指标：

指标	类型	用途
memory_middleware_duration_ms	Histogram	监控处理耗时
memory_hit_rate	Gauge	记忆命中率
memory_operation_success	Counter	操作成功率
memory_fallback_total	Counter	降级触发次数
6. MCP Tool 扩展审核
6.1 新增 Tool 评估
Tool	设计	评估
pavo_save_memory	✅ 完整	参数设计合理
pavo_search_memory	✅ 完整	支持分类过滤
pavo_list_memories	✅ 完整	分页设计合理
pavo_delete_memory	✅ 完整	用户隐私合规必需
6.2 context 参数设计
✅ 设计合理，但需明确：

问题：context 参数由 Memory Middleware 自动填充，但 Tool 定义中需要声明这个参数吗？

建议：在 Tool Schema 中声明 context 为可选参数，由 Middleware 注入，用户不传也不影响：

python
# Tool Schema 定义
{
    "name": "pavo_create_project",
    "description": "...",
    "inputSchema": {
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "user_id": {"type": "string"},
            "context": {  # 可选参数，由 Middleware 注入
                "type": "object",
                "description": "系统内部使用，用户无需传入"
            }
        },
        "required": ["input"]  # context 不在 required 中
    }
}
6.3 Tool 使用示例补充
建议：在文档中增加 Tool 调用示例，方便开发者和 AI Client 理解：

python
# pavo_save_memory 示例
{
    "user_id": "alice",
    "memory_type": "style",
    "content": {
        "preferred_genre": "温馨家庭",
        "tone": "温暖治愈",
        "color_palette": "暖色"
    },
    "tags": ["家庭", "温馨", "暖色"],
    "importance": 0.8
}

# pavo_search_memory 示例
{
    "user_id": "alice",
    "query_text": "喜欢的角色风格",
    "memory_types": ["style", "character"],
    "limit": 5
}
7. 数据库与 Schema 审核
7.1 表结构评估
✅ 设计合理，索引配置恰当

表	评估	说明
user_memories	✅	字段完整，索引合理
knowledge_base	✅	含 priority 字段支持优先级
session_contexts	✅	TTL 设计合理
7.2 索引策略
⚠️ 建议补充更多索引

当前只定义了基本索引，建议补充：

sql
-- user_memories 表
CREATE INDEX idx_user_memories_user_type ON user_memories(user_id, memory_type);
CREATE INDEX idx_user_memories_importance ON user_memories(user_id, importance DESC);
CREATE INDEX idx_user_memories_updated ON user_memories(user_id, updated_at DESC);

-- knowledge_base 表
CREATE INDEX idx_knowledge_category_priority ON knowledge_base(category, priority DESC);

-- 向量索引 (IVFFlat)
CREATE INDEX idx_user_memories_embedding ON user_memories 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
CREATE INDEX idx_knowledge_embedding ON knowledge_base 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 50);
7.3 pgvector 索引参数
建议补充：IVFFlat 的 lists 参数选择建议：

数据量	lists 推荐值	说明
< 10,000	10-50	小数据集
10,000 - 100,000	50-100	中等数据集
> 100,000	100-200	大数据集
8. 实施计划审核
8.1 工时评估
Phase	原工时	评估	建议
Phase 2.1	5天	✅ 合理	保持
Phase 2.2	4天	⚠️ 略紧	+0.5天（MCP注册+测试）
Phase 2.3	5天	⚠️ 略紧	+1天（种子数据质量验证）
Phase 2.4	3天	✅ 合理	保持
Phase 2.5	3天	✅ 合理	保持
合计	20天		建议调整为 21.5 天
8.2 任务依赖关系
⚠️ 需明确 Critical Path

当前文档中任务列表清晰，但依赖关系图不够直观。

建议补充：增加 Critical Path 示意图：

text
P2.1.1 (pgvector) ─┬─► P2.1.2 (数据模型) ─┬─► P2.1.3 (Store) ─┬─► P2.2.1 (Tools) ─► P2.2.3 (注册)
                   │                     │                   │
                   └─────────────────────┴───────────────────┴─────────────────────────► P2.4.1 (Middleware)
                                                                                              │
P2.3.1 (种子数据) ──► P2.3.2 (RAG模型) ──► P2.3.3 (Pipeline) ──► P2.3.4 (检索) ──► P2.3.5 (注入)
                                                                                              │
                                                                                              ▼
                                                                                        P2.5.1 (E2E测试)
8.3 Phase 1 依赖确认
⚠️ 需确认 Phase 1 进度

文档第2章列出了 Phase 1 的 7 个强制交付项和 2 个建议交付项。

建议：在 v2.1 启动前，逐项确认 Phase 1 交付状态，确保不阻塞：

yaml
Phase 1 交付确认清单:
  D1: [ ] MCP Server 可启动，list_tools 返回 8 个工具
  D2: [ ] pavo_create_project / pavo_get_project 可用
  D3: [ ] 统一 MCPToolResult 返回格式
  D4: [ ] MCPError 错误码体系
  D5: [ ] pavo_auth_login 提升至 P1
  D6: [ ] 所有 Tool 增加 context 参数
  D7: [ ] Docker Compose 集成 mcp-server 服务
  D8: [ ] (建议) 3 个 Prompt 合并为 2 个
  D9: [ ] (建议) Resources 只读约束
9. 测试策略审核
9.1 测试金字塔
✅ 设计合理

层级	数量预估	评估
单元测试	30-40	✅ 合理
集成测试	15-20	✅ 合理
E2E 测试	5-8	✅ 合理
9.2 关键测试场景补充
建议增加以下测试场景：

场景	类型	验证点
Memory 重要性过滤	集成	min_importance 参数生效
混合检索 (向量+结构化)	集成	同时按 category 和相似度过滤
Middleware 高并发	性能	10 并发下 P95 < 100ms
知识库增量更新	集成	新增知识不覆盖已有
Session TTL 刷新	集成	活跃会话自动续期
Embedding 缓存命中	单元	相同文本不重复调用 API
9.3 性能基准测试
建议：增加性能基准测试章节：

测试场景	目标值	测试方式
Memory 单条查询 (含 Embedding)	< 200ms	10 次平均
Memory 批量查询 (10条)	< 500ms	10 次平均
RAG 检索 (含 Embedding)	< 500ms	10 次平均
Middleware 单次处理	< 100ms	100 次 P95
并发查询 (10 并发)	成功率 > 95%	并发测试
10. 风险识别审核
10.1 现有风险评估
编号	风险	概率	影响	评估
R1	pgvector Windows 安装复杂	高	中	✅ 应对合理
R2	Embedding API 延迟高	中	中	✅ 应对合理
R3	向量检索性能下降	中	低	✅ 应对合理
R4	RAG 知识质量不足	中	高	✅ 应对合理
R5	Middleware 性能瓶颈	低	高	✅ 应对合理
R6	用户隐私合规	中	高	✅ 应对合理
R7	Prompt 注入后输出格式偏离	低	中	✅ 应对合理
R8	知识库版权风险	中	高	✅ 应对合理
10.2 建议补充的风险
编号	风险	概率	影响	应对策略
R9	pgvector 与现有 ORM 兼容性	低	中	Phase 2.1.1 先做 POC 验证；SQLAlchemy 2.0 原生支持 vector 类型
R10	Memory 数据膨胀	中	中	设置存储上限（如 1000 条/用户）；自动清理低重要性记忆
R11	RAG 知识冲突	低	低	知识条目增加版本号；冲突时以新条目为准
11. 审核结论与修改清单
11.1 审核状态总览
模块	状态	说明
架构设计	✅ 通过	设计合理，无需大改
Agent Memory	⚠️ 条件通过	需补充重要性评分策略和 Embedding 细节
RAG 知识库	⚠️ 条件通过	需补充注入目标说明和重排序方案
Memory Middleware	✅ 通过	设计优秀，建议补充可观测性
MCP Tool 扩展	✅ 通过	设计合理，建议增加使用示例
数据库 Schema	✅ 通过	设计合理，建议补充更多索引
实施计划	⚠️ 条件通过	工时建议调整为 21.5 天
测试策略	✅ 通过	建议增加性能基准测试
风险识别	⚠️ 条件通过	建议补充 R9-R11
11.2 必须修改项（前置条件）
序号	修改项	位置	预计工时
1	补充重要性评分策略	第4章	1h
2	补充 Embedding 具体配置（模型、维度、Batch）	第4章	0.5h
3	明确 RAG 注入目标（分镜智能体为主）	第5章	0.5h
4	补充 Re-ranker 具体方案	第5章	1h
5	补充 Session TTL 刷新策略（滑动过期）	第4章	0.5h
6	补充 pgvector 索引创建 SQL	第8章	0.5h
7	确认 Phase 1 交付清单状态	第2章	1h
11.3 建议修改项（推荐完成）
序号	修改项	位置	预计工时
8	增加 Middleware 可观测性指标	第6章	1h
9	增加 MCP Tool 使用示例	第7章	1h
10	增加性能基准测试	第10章	1h
11	补充 BGM 知识条目至 10 条	第5章	1h
12	补充依赖关系 Critical Path 图	第9章	0.5h
13	补充风险 R9-R11	第12章	0.5h
14	工时调整（20→21.5 天）	第9章	0.5h
11.4 最终结论
✅ 方案总体可行，建议在完成必须修改项后进入开发实施。

文档质量：v2.1 文档在 v2.0 基础上有了显著提升，Memory + RAG 的设计完整且务实。Middleware 透明集成是最大亮点，确保了与 v2.0 的完美兼容。

关键修改项：

补充重要性评分策略（Memory 核心机制）

明确 RAG 注入目标（分镜智能体为主）

确认 Phase 1 交付清单（确保不阻塞）

补充 pgvector 索引创建 SQL

整体评估：方案设计质量高，技术选型合理，20 天（建议 21.5 天）工期可接受。完成上述修改后，即可进入开发实施阶段。

建议启动时间：完成必须修改项后（预计 0.5 天），立即启动 Phase 2.1。

审核报告结束
版本：v1.0 | 审核日期：2026-07-13
被审核文档：技术开发计划文档_v2.1_Memory_RAG.md


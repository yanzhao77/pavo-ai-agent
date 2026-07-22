# Pavo AI Agent 前端产品化重构 — 技术开发文档

版本: 3.0
日期: 2026-07-21

---

## 目录

1. [现状分析](#1-现状分析)
2. [架构总览](#2-架构总览)
3. [路由设计](#3-路由设计)
4. [组件树](#4-组件树)
5. [页面级设计](#5-页面级设计)
6. [API 服务层](#6-api-服务层)
7. [状态管理](#7-状态管理)
8. [数据流](#8-数据流)
9. [视觉设计系统](#9-视觉设计系统)
10. [最终验收标准](#10-最终验收标准)
11. [Asset 数据模型](#appendix-asset-数据模型)
12. [分阶段实施计划](#11-分阶段实施计划)

---

## 1. 现状分析

### 1.1 当前文件结构

```
frontend/src/
├── app/
│   ├── globals.css          # 仅 Tailwind 指令
│   ├── layout.tsx           # 基础 HTML 壳
│   └── page.tsx             # 单页面应用：AuthGuard / HomeContent 二分
├── components/
│   ├── AuthGuard.tsx         # 简易登录页（用户名输入）
│   ├── ChatPanel.tsx         # 左侧输入面板 + Agent 进度
│   ├── ConfirmDialog.tsx     # 确认弹窗
│   ├── PreviewPanel.tsx      # 右侧预览面板（5个 tab）
│   ├── Skeleton.tsx          # 骨架屏
│   ├── SortableShot.tsx      # 拖拽镜头
│   ├── Timeline.tsx          # 时间线编辑器
│   ├── Toast.tsx             # 提示组件
│   ├── VideoPanel.tsx        # 视频渲染面板
│   └── WorkflowVisualizer.tsx# Agent 管线可视化
├── lib/
│   └── api.ts               # API 调用层
└── types/
    └── project.ts            # 类型定义
```

### 1.2 当前问题

| 问题 | 描述 |
|------|------|
| 单页面架构 | 所有功能挤在 `/`，无路由划分 |
| 开发工具感 | Agent 执行日志直接暴露，非产品体验 |
| 无登录落地页 | 登录框直接出现在首页 |
| 无视觉叙事 | 纯卡片 + 列表，无动画/渐变/沉浸感 |
| 工作流不可视 | Agent 状态用文字列表展示，非图形化 |
| 状态管理裸写 | 全部 `useState` 散布在各组件 |
| API 调用裸写 | 无 service 层抽象，错误处理分散 |

### 1.3 可复用资产

- **API 接口**：`createProject`, `getProject`, `listProjects`, `updateProject`, `regenerateModule`, `renderProject`（全量保留）
- **类型定义**：`Project`, `Character`, `Scene`, `Prop`, `Storyboard`, `Shot`, `TraceEntry`（全量保留）
- **lucide-react 图标库**：保留升级
- **Tailwind CSS**：保留升级
- **SSE 流式状态更新**：保留机制

### 1.4 向后兼容约束

- 不改后端一行代码
- 所有现有 API 端点不变
- 认证机制不变（token in localStorage）
- SSE `/stream` 端点格式不变

---

## 2. 架构总览

### 2.1 目标架构

```
pages/                    # App Router 页面
├── page.tsx              # Landing Page（公开）
├── studio/page.tsx       # 创作工作室（需登录）
├── projects/page.tsx     # 项目列表（需登录）
├── projects/[id]/page.tsx # 项目详情（需登录）
├── gallery/page.tsx      # AI 作品 Gallery（公开） ← 新增
└── dashboard/page.tsx    # AI 导演控制台（需登录）  ← 新增

components/
├── ui/                   # shadcn/ui 自动生成 (button, card, dialog, toast...)
├── layout/               # 布局组件
│   ├── Navbar.tsx
│   ├── Footer.tsx
│   └── Sidebar.tsx
├── landing/              # Landing Page 组件
│   ├── Hero.tsx
│   ├── PromptInput.tsx
│   ├── FeatureSection.tsx
│   └── GallerySection.tsx         # ← 新增
├── studio/               # 工作室组件
│   ├── CreationPanel.tsx
│   ├── AgentTimeline.tsx
│   ├── WorkflowGraph.tsx          # React Flow
│   ├── StreamingPreview.tsx       # ← 新增
│   └── AgentPipelineProgress.tsx  # ← 新增
├── project/              # 项目详情组件
│   ├── CharacterCard.tsx
│   ├── CharacterImageWall.tsx     # ← 新增
│   ├── SceneCard.tsx
│   ├── ScenePreviewCard.tsx       # ← 新增
│   ├── StoryboardCard.tsx
│   └── StoryboardTimeline.tsx     # ← 新增
├── dashboard/            # 控制台组件         ← 新增
│   ├── Dashboard.tsx
│   ├── ProductionTeam.tsx
│   └── StatsCard.tsx
└── common/               # 跨页面通用组件
    ├── AuthModal.tsx
    ├── GalleryCard.tsx
    ├── LoadingAnimation.tsx
    └── assetGenerator.ts          # ← 新增：Emoji 头像/渐变色生成工具

services/                 # API 服务层
├── api.ts                # HTTP 客户端
├── project.ts            # 项目相关 API
├── workflow.ts           # 工作流相关 API
└── auth.ts               # 认证相关 API

stores/                   # Zustand 状态管理
├── authStore.ts          # 认证状态
├── projectStore.ts       # 轻量：仅当前项目 ID
└── workflowStore.ts      # SSE + Agent 实时状态（含重连机制）

hooks/                    # React Query hooks ← 新增
├── useProject.ts         # 项目查询/缓存
└── useAuth.ts            # 认证相关 hook

types/                    # 类型定义
└── index.ts              # 统一导出
```

### 2.2 技术栈升级

| 当前 | 目标 |
|------|------|
| Next.js 14 | Next.js 14（保持） |
| TypeScript | TypeScript（保持） |
| Tailwind CSS 3 | Tailwind CSS 3 + class-variance-authority |
| - | **shadcn/ui**（Radix UI 原语） |
| - | **Framer Motion**（动画） |
| - | **React Flow**（工作流图） |
| - | **Zustand**（状态管理） |
| - | **Axios**（HTTP） |
| lucide-react | lucide-react（保持） |
| @dnd-kit | @dnd-kit（保持，用于 Timeline） |

### 2.3 依赖安装计划

```bash
# Core
npm install zustand@4.5.0 axios@1.6.0 framer-motion@11.0.0 @xyflow/react@12.0.0
npm install @tanstack/react-query@5.0.0 @tanstack/react-query-devtools@5.0.0

# shadcn/ui (通过 npx 初始化)
npx shadcn@latest init
npx shadcn@latest add button card input dialog toast tabs navigation-menu
```

---

## 3. 路由设计

### 3.1 路由表

| 路由 | 页面 | 访问权限 | 描述 |
|------|------|----------|------|
| `/` | Landing | 公开 | 产品落地页，无需登录即可浏览 |
| `/studio` | 创作工作室 | 需登录 | 输入创意 → 创建工作流 → 查看结果 |
| `/projects` | 项目列表 | 需登录 | 查看/管理所有历史项目 |
| `/projects/[id]` | 项目详情 | 需登录 | 查看/编辑项目所有内容 |

### 3.2 路由守卫

```
请求 → Landing Page（无需登录）
        │
        ├── 点击 "Start Creating"
        │       │
        │       ├── 已登录? → /studio
        │       └── 未登录? → 弹出登录模态框 → /studio
        │
        ├── 直接访问 /studio
        │       │
        │       └── 未登录? → 重定向到 / 并显示登录弹窗
        │
        └── 直接访问 /projects/[id]
                │
                └── 未登录? → 重定向到 /
```

### 3.3 鉴权流程

```
1. 用户访问 Landing Page → 自由浏览
2. 用户尝试创建项目 → localStorage 检查 token
3. 无 token → 显示登录模态框（不离开当前页面）
4. 登录成功 → token 存入 localStorage，关闭模态框
5. 所有 API 请求自动附加 Bearer token
```

---

## 4. 组件树

### 4.1 Landing Page

```
└── LandingPage
    ├── Navbar
    │   ├── Logo
    │   ├── NavLinks (Features, Gallery, Studio)
    │   └── AuthButtons (Sign In / Get Started)
    ├── HeroSection
    │   ├── HeroTitle
    │   ├── HeroSubtitle
    │   ├── PromptInput (核心输入区)
    │   │   ├── TextArea (故事创意输入)
    │   │   ├── ModeSelector (创意模式 / 故事板模式)
    │   │   └── SubmitButton
    │   └── HeroBackground (渐变/粒子动画)
    ├── FeatureSection
    │   ├── FeatureCard (AI Director)
    │   ├── FeatureCard (Character Designer)
    │   ├── FeatureCard (Storyboard Artist)
    │   └── FeatureCard (Scene Creator)
    ├── WorkflowPreview
    │   └── AnimatedPipeline (用展示名称的 7 Agent 流水线)
    ├── GallerySection            ← 新增
    │   ├── GalleryCard (角色示例)
    │   ├── GalleryCard (场景示例)
    │   ├── GalleryCard (分镜示例)
    │   └── GalleryCard (完整作品案例)
    └── Footer
```

### 4.2 Studio Page — 三栏布局

```
┌──────┬──────────────────┬──────────────────┐
│      │                  │                  │
│ Side │   创作输入        │   作品预览       │
│ bar  │   ┌──────────┐   │   ┌──────────┐   │
│      │   │ 故事输入   │   │   │ 角色墙    │   │
│  🆕  │   └──────────┘   │   │          │   │
│      │                  │   ├──────────┤   │
│ Proj │   AI导演工作流    │   │ 场景预览  │   │
│ ects │   ┌──────────┐   │   │          │   │
│      │   │ Agent    │   │   ├──────────┤   │
│  📋  │   │ Graph    │   │   │ 故事板    │   │
│      │   │ (React   │   │   │ 时间线    │   │
│ User │   │  Flow)   │   │   │          │   │
│      │   └──────────┘   │   └──────────┘   │
│      │                  │                  │
│      │   Agent Timeline  │                  │
│      │   [████████░░] 80%│                  │
│      │                  │                  │
└──────┴──────────────────┴──────────────────┘

三栏分工：
  左栏: Sidebar (项目列表 / 用户信息)
  中栏: 创作输入 + AI导演工作流
  右栏: 实时作品预览
```

### 4.3 Project List

```
└── ProjectDetailPage
    ├── ProjectHeader
    │   ├── ProjectTitle
    │   ├── ProjectStatus (Badge)
    │   └── ActionButtons (Edit, Export, Delete)
    ├── ProjectContent
    │   ├── CharactersSection
    │   │   └── CharacterCard[]
    │   ├── ScenesSection
    │   │   └── SceneCard[]
    │   ├── PropsSection
    │   │   └── PropCard[]
    │   └── StoryboardSection
    │       └── StoryboardTimeline
    └── WorkflowHistory
        └── WorkflowGraph (已完成的管线回放)
```

---

## 5. 页面级设计

### 5.1 Landing Page (`/`)

**设计目标**：用户第一眼就知道 "Pavo 能用 AI 做动画故事"

**布局**：

```
┌──────────────────────────────────────┐
│  🦚 Pavo    Features  Studio  [Sign In] │
├──────────────────────────────────────┤
│                                      │
│    Create stories with AI            │
│    Imagine your story,               │
│    AI turns it into animation.       │
│                                      │
│    ┌──────────────────────────┐      │
│    │  Write your story idea... │  ✨  │
│    └──────────────────────────┘      │
│                                      │
│    ┌──────┐ ┌──────┐ ┌──────┐       │
│    │Director│ │Character│ │Storyboard│ │
│    └──────┘ └──────┘ └──────┘       │
│                                      │
│    AI Creation Pipeline              │
│    [🧠 故事导演] → [🎭 角色设计师] → [🌆 场景构建师] │
│    → [🎨 道具师] → [🎬 分镜导演] → ✓              │
│                                      │
├──────────────────────────────────────┤
│              Footer                   │
└──────────────────────────────────────┘
```

**关键交互**：
- 用户在 Hero 区直接输入故事创意
- 点击 Start 若未登录 → 弹出登录模态框（半透明背景）
- 登录后自动创建项目并跳转 /studio

### 5.2 Studio Page (`/studio`)

**设计目标**：用户感受 "AI 在为我创作电影"

**布局**：

```
┌──────┬────────────────────────────────────┐
│      │                                    │
│ Side │  Story Input                        │
│ bar  │  ┌────────────────────────────┐     │
│      │  │ 输入故事创意...              │     │
│  🆕  │  └────────────────────────────┘     │
│      │                                    │
│ Proj │  AI Creation Pipeline               │
│ ects │  [🧠 故事导演] → [🎭 角色设计师] → [🌆 场景构建师] │
│      │  → [🎨 道具师] → [🎬 分镜导演] → [🔍 审查] → [🔧 修复] │
│      │                                    │
│ User │  Result Preview                     │
│      │  ┌────┐ ┌────┐ ┌────┐             │
│      │  │Char│ │Scene│ │Story│            │
│      │  └────┘ └────┘ └────┘             │
│      │                                    │
└──────┴────────────────────────────────────┘
```

**关键交互**：
- 左侧 Sidebar 职责：
  - 显示当前项目信息（标题 + 状态 badge）
  - 最近项目（最多 3 个，点击切换当前 Studio 项目）
  - "查看全部项目" → 跳转 /projects
  - 用户头像 + 退出登录
  - 新项目快速创建按钮
- 中栏：故事输入 → Agent 工作流可视化 → 结果展示
- 工作流用 React Flow 渲染，节点使用 **displayName**（故事导演 / 角色设计师 / 场景构建师...），禁止展示内部标识
- 右栏渲染逻辑（**新增 H-03 澄清**）：

```tsx
// Studio 右栏渲染伪代码
const RightPanel = () => {
  const { isRunning, agents, overallProgress } = useWorkflowStore();

  if (isRunning) {
    return (
      <>
        <AgentPipelineProgress agents={agents} overallProgress={overallProgress} />
        <StreamingPreview agents={agents} />
      </>
    );
  }

  return <ResultPanel />; // 完成后展示完整结果
};
```

- StreamingPreview 在生成中增量展示已完成 Agent 的结果
- ResultPanel 在工作流完成后展示完整内容（含所有 Tab）

### 5.3 移动端响应式方案

Studio 三栏布局在移动端需要适配：

| 断点 | 布局策略 |
|------|----------|
| ≥1200px | 三栏完整布局（Sidebar + 中栏 + 右栏） |
| 768–1199px | 两栏布局（左侧窄栏 + 右侧主内容） |
| <768px | 单栏布局，底部 Tab 切换 |

移动端 Tab 设计：
```
┌──────────────────────┐
│  🦚 Pavo    [≡]      │ ← 顶部导航
├──────────────────────┤
│                      │
│   当前 Tab 内容       │ ← 根据底部 Tab 切换
│                      │
├──────────────────────┤
│  ✍️  📊  👁️  │ ← 底部 Tab (输入/工作流/预览)
└──────────────────────┘
```

### 5.4 Gallery / Dashboard 数据源说明

| 数据需求 | 实现方案 |
|----------|----------|
| Gallery 作品列表 | 复用 `listProjects` + 前端过滤 `status === 'completed'` |
| Dashboard 统计 | 复用 `listProjects` 做前端聚合计算 |
| 项目封面图 | 从 storyboard 第一帧描述生成 SVG 占位图 |
| 预览缩略图 | 角色 → Emoji 头像；场景 → 渐变色背景（工具函数见 `common/assetGenerator.ts`） |

**无新增后端 API 需求。** 所有数据基于现有接口在前端聚合和衍生。

**降级策略（M-09 补充）**：

| 项目数量 | 策略 | 用户体验 |
|----------|------|----------|
| < 50 | 全量加载 + 前端过滤 | 即时响应 |
| 50 - 100 | 全量加载 + 前端过滤 + 加载骨架屏 | 可接受延迟（< 1s） |
| > 100 | 降级：仅展示最近 20 个 + 提示"查看更多请访问项目列表" | 告知用户边界 |

Gallery 组件需在初始化时检测项目总数，超过 100 时自动切换降级模式，并在前端埋点记录项目数用于后续决策。

### 5.5 Project List (`/projects`)

**设计目标**：干净的项目管理界面

- 网格布局展示项目卡片
- 每张卡片显示：标题、状态 badge、创建时间
- 点击进入 `/projects/[id]`
- 空状态展示引导创建

### 5.4 Project Detail (`/projects/[id]`)

**设计目标**：完整的内容浏览和编辑体验

- 使用现有 `PreviewPanel`、`Timeline`、`VideoPanel` 组件
- 但重新包装在统一的产品界面中
- 顶部导航显示项目名称和面包屑

---

## 6. API 服务层

### 6.1 目录结构

```
frontend/src/services/
├── api.ts           # Axios 实例 + 拦截器
├── auth.ts          # 认证 API
├── project.ts       # 项目 CRUD
└── workflow.ts      # 工作流相关（SSE）
```

### 6.2 Axios 实例设计

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:18080/api',
  timeout: 30000,
});

// 请求拦截器：自动附加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pavo_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('pavo_token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 6.3 项目 API

```typescript
// services/project.ts
import api from './api';
import { Project } from '@/types';

export const projectService = {
  create: (input: string, userId?: string) =>
    api.post('/projects', { input, user_id: userId || '' }),

  get: (id: string) =>
    api.get(`/projects/${id}`),

  list: (userId?: string) =>
    api.get('/projects', { params: { user_id: userId } }),

  update: (id: string, data: Partial<Project>) =>
    api.patch(`/projects/${id}`, data),

  delete: (id: string) =>
    api.delete(`/projects/${id}`),

  regenerate: (id: string, module: string) =>
    api.post(`/projects/${id}/regenerate`, { module }),

  render: (id: string) =>
    api.post(`/projects/${id}/render`),

  subscribeSSE: (id: string, token: string): EventSource => {
    const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:18080/api';
    return new EventSource(`${base}/projects/${id}/stream?token=${token}`);
  },
};
```

### 6.4 保留的现有 API 兼容

现有 `lib/api.ts` 中的函数在新 service 层中全部重新实现，确保：
- 接口签名兼容（输入输出一致）
- 旧组件逐步迁移到新 service
- 过渡期两套共存

### 6.5 SSE 事件协议规范

前端通过 SSE 接收 Agent 执行状态。统一事件协议格式：

```typescript
// Backend → Frontend SSE 事件协议
interface SSEAgentEvent {
  event: 'agent_status';
  data: {
    agent: string;            // 内部名称 (planner, character, ...)
    displayName: string;      // 展示名称 (故事导演, 角色设计师, ...)
    status: 'idle' | 'running' | 'completed' | 'failed' | 'retry';
    progress: number;         // 0-100
    message: string;          // 当前状态描述
    timestamp: string;        // ISO 8601
  };
}

// 示例事件
{
  "event": "agent_status",
  "agent": "storyboard",
  "displayName": "分镜导演",
  "status": "running",
  "progress": 60,
  "message": "正在生成第三幕分镜",
  "timestamp": "2026-07-21T12:00:00"
}
```

前端处理逻辑：
```
收到 SSE 事件 → workflowStore 更新对应 agent 状态
               → AgentNode 响应式更新 (颜色/动画/进度)
               → AgentTimeline 进度条更新
               → idle: 灰色半透明
               → running: 蓝色脉冲动画
               → completed: 绿色 + 对勾
               → failed: 红色 + 错误图标
               → retry: 橙色闪烁 + 连线流动
```

### 6.6 Agent Node 显示名称映射

**内部名称禁止展示给普通用户。** 所有 Agent 节点必须使用面向用户的展示名称。

```typescript
// AgentNode 显示名称映射表
// 内部名称 → 对用户展示的名称 + 图标 + 描述
const AGENT_DISPLAY: Record<string, { name: string; icon: string; desc: string }> = {
  planner:    { name: '故事导演',   icon: '🧠', desc: '分析故事结构，制定创作计划' },
  character:  { name: '角色设计师', icon: '🎭', desc: '创造人物形象与性格特征' },
  scene:      { name: '场景构建师', icon: '🌆', desc: '设计环境氛围与光影色调' },
  prop:       { name: '道具师',     icon: '🎨', desc: '配置道具细节与交互方式' },
  storyboard: { name: '分镜导演',   icon: '🎬', desc: '将故事转化为视觉镜头语言' },
  reviewer:   { name: '质量审查官', icon: '🔍', desc: '检查内容质量与叙事一致性' },
  fixer:      { name: '修复专家',   icon: '🔧', desc: '修正问题，优化最终输出' },
};
```

**原则**：用户看到的是 AI 制作团队，不是代码模块。
所有 WorkflowGraph 渲染必须使用 `displayName` 和 `icon`，用户界面上不能出现 `planner`、`character` 等内部标识符。

**Fallback 处理**：如果后端返回的 `agent` 字段不在映射表中，使用兜底策略：

```typescript
const getAgentDisplay = (agentKey: string) => {
  const display = AGENT_DISPLAY[agentKey];
  if (display) return display;
  console.warn(`Unknown agent: ${agentKey}`);
  return {
    name: agentKey.charAt(0).toUpperCase() + agentKey.slice(1),
    icon: '🤖',
    desc: '处理中...',
  };
};
```

---

## 7. 状态管理

### 7.1 分层策略

| 层 | 工具 | 职责 |
|----|------|------|
| 实时状态 | **Zustand** | workflow 运行状态、SSE 连接、用户在线状态 |
| 服务端数据 | **React Query (TanStack Query)** | 项目查询、作品列表、历史记录、缓存与刷新 |
| 本地状态 | **React useState** | UI 状态（tab 切换、弹窗、表单输入） |

**原则**：
- Zustand 负责**实时、频繁变化**的状态（workflow agents、SSE 连接）
- React Query 负责**服务端数据**的获取、缓存、重试（projects、characters、storyboards）
- 避免 Zustand 变成全局数据仓库

### 7.2 Zustand Store 设计

```typescript
// stores/authStore.ts
// 认证状态 — Zustand 管理
// ⚠️ 当前后端仅需 username，无密码验证（演示模式）
// 后续如需密码 / OAuth，在此扩展接口签名
interface AuthState {
  token: string | null;
  userId: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}

// stores/projectStore.ts
// ⚡ 轻量 — 仅管理当前选中的项目 ID
// 项目数据通过 React Query 获取和缓存，避免 Zustand 变成数据仓库
interface ProjectState {
  currentProjectId: string | null;
  setCurrentProjectId: (id: string | null) => void;
  createProject: (input: string) => Promise<string>;
}

// stores/workflowStore.ts
// ⚡ 实时状态 — SSE 连接 + Agent 运行状态
type AgentStatus = 'idle' | 'running' | 'completed' | 'failed' | 'retry';

interface AgentState {
  internalName: string;       // backend 内部名称 (planner, character...)
  displayName: string;        // 用户可见名称 (故事导演, 角色设计师...)
  icon: string;               // Emoji 图标
  description: string;        // 职责描述
  status: AgentStatus;
  progress: number;           // 0-100
  message: string;            // 当前状态描述
}

interface WorkflowState {
  agents: AgentState[];       // 7 个 Agent 的实时状态
  isRunning: boolean;
  overallProgress: number;    // 总进度百分比

  // SSE 连接管理
  sseConnection: EventSource | null;
  sseStatus: 'idle' | 'connecting' | 'connected' | 'disconnected';
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectDelay: number;     // 指数退避起始值 (ms)

  // Actions
  connectSSE: (projectId: string) => void;
  disconnectSSE: () => void;
  handleAgentEvent: (event: SSEAgentEvent) => void;
  syncStateFromAPI: (projectId: string) => Promise<void>;  // 重连后同步策略（见下方说明）
  resetWorkflow: () => void;
}
```

**⛓️ syncStateFromAPI 行为边界（M-08 澄清）**

`syncStateFromAPI(projectId)` 被设计为重连后从 REST API 拉取状态恢复，但 **REST API 不返回 Agent 中间运行状态**（`projectService.get` 返回的是 Project 对象，包含 characters/scenes 等结果数据，不含 agents 数组）。因此实际策略为：

```typescript
// 重连后不恢复中间态，仅判断项目最终状态
syncStateFromAPI: async (projectId: string) => {
  const project = await projectService.get(projectId);
  if (project.status === 'completed' || project.status === 'failed') {
    // 已完成：直接结束工作流，展示最终结果
    workflowStore.setState({ isRunning: false });
  } else {
    // 仍在生成中：重置 agents → idle，等待新的 SSE 事件
    workflowStore.resetWorkflow();
    workflowStore.connectSSE(projectId);
  }
}
```
```

SSE 连接状态机：

```
IDLE → CONNECTING → CONNECTED → (断开) → RECONNECTING → CONNECTED
                                               ↓ (超过重试次数)
                                            DISCONNECTED
```

重连机制：
- 使用指数退避：`delay = min(reconnectDelay * 2^attempt, 30000)`
- 最多重试 `maxReconnectAttempts` 次
- 重连成功后调用 `syncStateFromAPI()` 通过 REST API 拉取当前 project 状态
- 避免 SSE 断开后状态永久丢失

### 7.3 React Query Hooks（替代 projectStore 的数据获取）

```typescript
// hooks/useProject.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectService } from '@/services/project';

export const useProject = (id: string | null) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectService.get(id!),
    enabled: !!id,                        // id 为空时不请求
    refetchInterval: (query) => {          // 生成中轮询
      const data = query.state.data;
      if (data?.status === 'generating') return 2000;
      return false;
    },
  });
};

export const useProjects = (userId?: string) => {
  return useQuery({
    queryKey: ['projects', userId],
    queryFn: () => projectService.list(userId),
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: string) => projectService.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};
```

### 7.4 状态流转

```
用户输入故事
    ↓
workflowStore.createProject()
    ↓
projectStore 更新 currentProject (status: generating)
    ↓
workflowStore.connectSSE(projectId)
    ↓
SSE 事件 → workflowStore 更新 agents 状态
    ↓
projectStore 轮询 /projects/{id} 获取完整数据
    ↓
projectStore 更新 currentProject (status: completed)
    ↓
展示结果
```

---

## 8. 数据流

### 8.1 创作流程数据流

```
[用户] → 输入故事创意
    │
    ▼
[Landing / Studio] → POST /api/projects { input }
    │
    ▼
[Backend] → 创建 Project → 返回 projectId
    │
    ▼
[Frontend] → 连接 SSE /api/projects/{id}/stream
    │
    ▼
[SSE Event] → agent:progress → workflowStore 更新节点
    │         → agent:complete → projectStore 获取完整数据
    │
    ▼
[Components] → 根据 workflowStore 渲染管线状态
              → 根据 projectStore 渲染结果
```

### 8.2 组件数据流

```
Landing Page
  │
  ├── PromptInput → onSubmit → authStore.checkAuth()
  │                              ├── 已登录 → workflowStore.createProject()
  │                              └── 未登录 → 弹登录模态框 → authStore.login()
  │                                                              ↓
  │                                                     workflowStore.createProject()
  │
  └── HeroSection → FeatureCard (静态内容)

Studio Page
  │
  ├── CreationPanel → StoryInput → workflowStore.createProject()
  │                    │
  │                    ├── AgentWorkflow ← workflowStore.agents
  │                    │    └── WorkflowGraph ← workflowStore.agents (每个节点状态)
  │                    │
  │                    └── AgentTimeline ← workflowStore.progress
  │
  └── ResultPanel ← projectStore.currentProject
       ├── CharactersTab → project.characters[]
       ├── ScenesTab → project.scenes[]
       ├── PropsTab → project.props[]
       └── StoryboardTab → project.storyboard
```

---

## 9. 视觉设计系统

### 9.1 明暗主题

**深色模式**（默认）：

```
Background:   #0a0a0a 至 #111111 渐变
Surface:      #1a1a1a
Border:       #2a2a2a
Text Primary: #ffffff
Text Secondary:#888888
Accent:       #6366f1 (indigo)
Success:      #10b981 (emerald)
Warning:      #f59e0b (amber)
Error:        #ef4444 (red)
```

**浅色模式**（备选）：

```
Background:   #fafafa
Surface:      #ffffff
Border:       #e5e5e5
Text Primary: #171717
Text Secondary:#737373
Accent:       #6366f1
```

### 9.2 设计 Token（Tailwind 扩展）

```javascript
// tailwind.config.js 扩展
colors: {
  surface: {
    DEFAULT: '#1a1a1a',
    hover: '#242424',
    active: '#2e2e2e',
  },
  border: {
    DEFAULT: '#2a2a2a',
    light: '#1f1f1f',
  },
  accent: {
    DEFAULT: '#6366f1',
    hover: '#5558e6',
    light: 'rgba(99, 102, 241, 0.1)',
  },
}
```

### 9.3 核心视觉元素

| 元素 | 规范 |
|------|------|
| Border Radius | `sm: 6px`, `md: 8px`, `lg: 12px`, `xl: 16px` |
| Shadow | `sm`, `md`, `lg`, `xl` 层级 |
| Glass | `backdrop-blur-xl bg-white/5 border border-white/10` |
| Typography | `Inter` 英文 / `Noto Sans SC` 中文 |
| Spacing | 4px 基准，8px 步进 |
| Transition | `duration-200 ease-out` |

### 9.4 视觉红线（禁止项）

**以下设计风格严格禁止：**

| 禁止项 | 原因 |
|--------|------|
| 后台管理系统风格（Admin Dashboard） | 用户感知为 "运维工具" |
| 数据表格（`<table>` / `datatable`） | 非消费级体验 |
| JSON 原始输出 | 暴露技术细节 |
| 日志窗口 / Terminal 样式 | 开发工具感 |
| 默认 HTML 控件（裸 `<input>`、`<select>`） | 粗糙感 |
| 灰色 Bootstrap 卡片 | 过时视觉语言 |

**必须采用的风格（参考标准）：**

| 参考产品 | 学习要点 |
|----------|----------|
| Pavo AI (app.pavo-ai.work) | 产品定位、色彩体系 |
| Runway (runwayml.com) | 深色 AI 风格、动画 |
| Midjourney (midjourney.com) | 沉浸感、展示方式 |
| Cursor (cursor.com) | 专业感、状态管理 |

### 9.5 动画规范

| 场景 | 动画 | 时长 |
|------|------|------|
| 页面切换 | fade + slide up | 300ms |
| Agent 节点状态变化 | scale + glow | 400ms |
| 工作流连线 | stroke-dashoffset | 1.5s |
| 卡片悬浮 | translateY(-2px) + shadow | 200ms |
| 输入框聚焦 | ring + border | 150ms |
| 提示框 | slide in from right | 300ms |

---

## 10. 最终验收标准

### 10.1 用户体验验收

| 测试场景 | 预期结果 |
|----------|----------|
| 新用户打开首页 | 5 秒内理解 "Pavo 能帮我用 AI 做动画故事" |
| 未登录试用 | 可在 Landing 页输入创意，触发登录后继续 |
| 创作流程 | 输入故事 → 看到 AI 工作流执行 → 看到角色/场景/分镜 |
| 作品感知 | 用户看到的是角色和场景，不是 Agent 日志 |

### 10.2 功能验收清单

```
□ Landing Page — Hero 区可直接输入创意
□ Landing Page — GallerySection 展示作品案例
□ Studio — 三栏布局（输入 | 工作流 | 预览）
□ Studio — React Flow 工作流图（展示名称，非内部标识）
□ Studio — SSE 实时状态更新
□ Studio — 流式生成预览（边生成边展示）
□ Studio — Agent 完成动画与进度展示
□ Project Detail — 角色视觉墙
□ Project Detail — 场景沉浸预览卡
□ Project Detail — 故事板横向时间线
□ Gallery — 作品展示卡片网格
□ Dashboard — 导演控制台（统计 + 制作团队）
□ 全局 — 深色 AI 风格
□ 全局 — 无 JSON/日志/表格暴露
□ 全局 — 无 Admin Dashboard 风格
```

### 10.3 技术要求验收

```
□ 后端 API 不变（0 行后端改动）
□ Agent 逻辑不变
□ SSE 协议兼容
□ Zustand 仅负责实时状态
□ React Query 负责服务端数据
□ Agent 节点使用 displayName 渲染
□ 移动端响应式
```

### 10.4 开发优先级

| 优先级 | 内容 | 估算 |
|--------|------|------|
| P0 | 新版页面架构 + React Flow Workflow + SSE + 三栏 Studio | 4-5 天 |
| P1 | Gallery 作品展示 + Asset 管理 + Director Dashboard | 3-4 天 |
| P2 | 动画优化 + 主题打磨 + 商业化功能 | 2-3 天 |

---

## 11. 分阶段实施计划

### Phase 1: 基础设施 + Landing Page（预估 2-3 天）

**目标**：搭建新架构骨架，实现产品级 Landing Page

```
Tasks:
├── 初始化 shadcn/ui
├── 安装新依赖 (zustand, axios, framer-motion, @xyflow/react, @tanstack/react-query)
├── 初始化 React Query Provider (app/providers.tsx)
├── 建立目录结构 (services/, stores/, hooks/, components/landing/)
├── 创建 assetGenerator.ts（Emoji 头像 / 渐变色生成工具）
├── 配置 Tailwind 设计 Token + 深色主题
├── 创建 Layout (Navbar, Footer)
├── 实现 HeroSection
│   ├── 渐变背景 + 粒子动画
│   ├── PromptInput（创意输入框）
│   └── ModeSelector
├── 实现 FeatureSection
├── 实现 WorkflowPreview（静态管线展示）
└── 实现 AuthModal（登录模态框，不离开页面）
```

**交付物**：`/` 路由展示完整的 Landing Page，可输入创意触发登录

### Phase 2: Studio 页面（预估 2-3 天）

**目标**：创作工作室核心功能

```
Tasks:
├── 创建 /studio 路由和页面框架
├── 实现 StudioSidebar（当前项目 + 最近项目 + 跳转 /projects）
├── 实现 CreationPanel
│   ├── StoryInput（复用/升级 Landing 的输入组件）
│   └── AgentWorkflow
│       ├── 接入 React Flow
│       ├── 定义 7 个 Agent 节点（使用 displayName）
│       ├── SSE 连接与状态更新
│       ├── 节点动画（运行中/完成/失败）
│       └── AgentPipelineProgress（管线进度条，中栏底部）
├── 实现 ResultPanel
│   ├── 4 个 Tab：Characters / Scenes / Props / Storyboard
│   └── 卡片式展示（复用现有渲染函数，重写样式）
├── 实现 StreamingPreview（右栏，生成中增量展示内容）
├── 实现 Zustand stores (auth, project, workflow)
├── 实现 hooks/useProject.ts（React Query 获取项目详情）
├── 实现 hooks/useProjects.ts（React Query 获取项目列表）
├── 迁移 projectStore 数据读取 → React Query hooks
└── 补充 projectStore 边界说明（仅存 currentProjectId）
```

**交付物**：`/studio` 可完整走通创作流程

### Phase 3: 项目列表 + 详情（预估 1-2 天）

**目标**：项目管理能力

```
Tasks:
├── 创建 /projects 路由
├── 实现项目列表页（网格卡片布局）
│   └── 支持状态过滤 + 前端分页（项目数 > 50 需后端支持分页）
├── 创建 /projects/[id] 路由
├── 实现项目详情页
│   ├── 复用现有的 PreviewPanel 渲染逻辑
│   ├── 但包装在新的统一布局中
│   └── 集成 Timeline 和 VideoPanel
├── Gallery 集成：复用 useProjects + 前端 status 过滤
│   └── ⚠️ 数据量 < 100 时内存过滤可行，超过需后端扩展
├── Gallery 降级检测：初始化时检测项目总数，> 100 时自动切换降级模式
├── 前端埋点：记录项目总数，用于后续后端分页决策
└── 空状态 / 加载状态 / 错误状态
```

**交付物**：完整的项目管理闭环

### Phase 4: 工作流可视化升级（预估 2-3 天）

**目标**：产品级 Agent 工作流可视化

```
Tasks:
├── 重新设计 WorkflowGraph
├── 实现自定义 AgentNode
│   ├── 节点状态（idle/running/completed/failed）
│   ├── 节点动画（脉冲/发光/粒子）
│   └── 节点详情面板
├── 实现连线动画（流动粒子效果）
├── 实现进度条和时间线
├── 添加 Agent 执行详情查看
└── 优化移动端适配
```

**交付物**：媲美 Runway/Midjourney 的工作流可视化

### Phase 5: 打磨（预估 1-2 天）

**目标**：产品级体验优化

```
Tasks:
├── Framer Motion 页面过渡动画
├── 加载状态骨架屏
├── 错误处理和重试机制
├── 移动端响应式适配
├── 性能优化（组件懒加载、图片优化）
├── 深色模式完善
└── 边缘情况处理（空项目、长时间生成、断线重连）
```

**交付物**：完整的 AI 创作平台前端

### 总预估：10-16 天

### Phase 6: AI Visual Creation Experience（预估 2-3 天）

**目标**：用户看到的不是 Agent 执行日志，而是作品的诞生过程。

#### 6.1 AI 作品 Gallery

**路由**：`/gallery`

展示平台上所有公开/示例作品的视觉效果画廊，让新用户直观感受 Pavo 的能力。

```
Layout:
┌───────────────────────────────────────────┐
│  🖼️  Gallery           [Filter] [Search]   │
├──────┬──────┬──────┬──────┬──────┬──────┤
│      │      │      │      │      │      │
│ Card │ Card │ Card │ Card │ Card │ Card │
│      │      │      │      │      │      │
├──────┴──────┴──────┴──────┴──────┴──────┤
│  Project Name · Status · Duration         │
│  [Character] [Scene] [Storyboard]         │
└──────────────────────────────────────────┘
```

每张卡片展示：
- 项目封面（从 storyboard 自动生成的抽象视觉）
- 标题和简短描述
- 角色数量、场景数量、镜头数量
- 生成状态 badge
- 交互：点击进入项目详情

#### 6.2 Character Image Wall

**位置**：Studio ResultPanel / 项目详情页

将角色从文字卡片升级为视觉卡片墙：

```
┌─────────────────────────────────────┐
│  🎭 Characters         [+ Add]      │
│                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐        │
│  │  🧑  │ │  👩  │ │  👴  │        │
│  │李  明 │ │王小美 │ │张爷爷 │        │
│  │25岁   │ │24岁   │ │68岁   │        │
│  │外卖员 │ │护士   │ │退休教师│        │
│  │      │ │      │ │      │        │
│  │善良   │ │温柔   │ │慈祥   │        │
│  │孤独   │ │坚强   │ │固执   │        │
│  └──────┘ └──────┘ └──────┘        │
└─────────────────────────────────────┘
```

每张角色卡片：
- 头像区域（圆形，带角色首字母/表情符号 fallback）
- 名称、年龄、职业
- 性格标签（彩色 chip）
- 统一卡片风格，grid 布局
- 悬停效果：轻微上浮 + 阴影加深
- 点击展开角色详情弹窗

#### 6.3 Scene Preview

**位置**：Studio ResultPanel

场景从信息卡片升级为沉浸式场景预览卡：

```
┌──────────────────────────────────────┐
│  🌆 Scenes                           │
│                                       │
│  ┌─────────────────────────┐         │
│  │  场景视觉卡片             │         │
│  │  [渐变色背景 / 氛围]      │         │
│  │                         │         │
│  │  雨夜城市街道             │         │
│  │  🕐 夜晚  🌧️ 雨天       │         │
│  │  💡 冷蓝调  🎭 孤独      │         │
│  └─────────────────────────┘         │
│                                       │
│  每张卡片展示：                        │
│  - 场景大标题                          │
│  - 时间/天气/光照标签                   │
│  - 氛围描述                           │
│  - 渐变色背景（根据 mood 自动生成）      │
│  - 场景序号 badge                      │
└──────────────────────────────────────┘
```

场景卡片增强：
- 根据场景 mood 自动生成渐变色背景（如 "lonely" → 冷蓝灰，"romantic" → 暖粉）
- 场景信息用标签化展示（时间、天气、灯光）
- 卡片点击可展开/收起详细描述
- 场景之间用视觉分割线区分

#### 6.4 Storyboard Image Timeline

**位置**：Studio ResultPanel → Storyboard Tab

故事板从下拉列表升级为横向视觉时间线：

```
┌────────────────────────────────────────────┐
│  🎬 Storyboard Timeline                    │
│                                             │
│  Scene 1: 雨中相遇                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │Shot 1│→│Shot 2│→│Shot 3│→│Shot 4│     │
│  │ 远景  │ │ 中景  │ │ 特写  │ │ 全景  │     │
│  │ 5s    │ │ 3s    │ │ 4s    │ │ 6s    │     │
│  │       │ │       │ │       │ │       │     │
│  │描述.. │ │描述.. │ │描述.. │ │描述.. │     │
│  └──────┘ └──────┘ └──────┘ └──────┘     │
│                                             │
│  ◀ Scene 1/3 ▶                            │
│                                             │
│  每张 Shot 卡片：                            │
│  - 镜头类型标签（远景/中景/特写）               │
│  - 时长                                  │
│  - 摄影机运动（tracking/pan/tilt）           │
│  - 对话（如果有）                           │
│  - 视觉描述                               │
└────────────────────────────────────────────┘
```

关键交互：
- 场景级导航（上一场景/下一场景）
- 每个场景内镜头横向滚动
- 镜头卡片可点击展开详情
- 镜头编号 + 类型 badge
- 镜头时长显示在卡片底部
- 对话用引用样式突出显示

#### 6.5 AI Director Dashboard

**路由**：`/dashboard`

**目标**：给用户一种 "我是导演，AI 是我的制作团队" 的体验。

```
Layout:
┌─────────────────────────────────────────────┐
│  🎬 Director Dashboard                      │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Total    │ │  Active   │ │  Recent   │   │
│  │ Projects  │ │ Projects  │ │ Activity  │   │
│  │    12     │ │     2     │ │  5m ago   │   │
│  └──────────┘ └──────────┘ └──────────┘    │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │  Recent Projects                    │     │
│  │  ┌──────────────────────────────┐  │     │
│  │  │ 📽️ 外卖员 (生成中...)         │  │     │
│  │  │    Planner ✓  Character ✓    │  │     │
│  │  │    Scene ◉  Props ◯ ...      │  │     │
│  │  ├──────────────────────────────┤  │     │
│  │  │ 📽️ 樱花雨 (已完成)           │  │     │
│  │  │    4 Characters · 3 Scenes   │  │     │
│  │  │    12 Shots · 2:30 Total    │  │     │
│  │  └──────────────────────────────┘  │     │
│  └────────────────────────────────────┘     │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │  AI Production Team                │     │
│  │  [🧠 故事导演] [🎭 角色设计师]    │     │
│  │  [🌆 场景构建师] [🎬 分镜导演]    │     │
│  │  每个 Agent 用展示名称 + 统计     │     │
│  └────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

Dashboard 组件：
- 统计卡片：总项目数、进行中、今日创建
- 最近项目列表：每个项目显示进度条 + Agent 完成状态
- AI Production Team：将 7 个 Agent 拟人化为 "制作团队成员"
  - 使用 displayName 和 icon 展示
  - 每个成员有从属项目数
  - 当前状态（工作中/空闲）
  - 点击可查看该 Agent 的历史处理项目

#### 6.6 Streaming Generation Preview

**位置**：Studio 创作面板

**职责边界（M-07 澄清）**：

| 组件 | 位置 | 职责 | 类型 |
|------|------|------|------|
| **AgentPipelineProgress** | 中栏底部（工作流图下方） | 整体进度百分比 + 7 Agent 紧凑状态 | 进度指示器："到哪了？" |
| **StreamingPreview** | 右栏顶部（生成中） | 已完成 Agent 的具体产出内容 | 内容展示器："生成了什么？" |

AgentPipelineProgress = 进度指示器，展示整体管线进度。
StreamingPreview = 内容展示器，展示已生成的角色/场景/分镜列表。

**目标**：在 Agent 生成过程中，实时预览已生成的内容，而不是等全部完成才看到结果。

```
┌──────────────────────────────────────────┐
│  Streaming Preview                        │
│                                           │
│  ┌──────────── Generated ────────────┐   │
│  │                                    │   │
│  │  ✅ Planner — 分析完成              │   │
│  │     ├ 故事主题: 父子温情             │   │
│  │     └ 核心冲突: 工作与家庭            │   │
│  │                                    │   │
│  │  ✅ Character — 已生成 3 角色        │   │
│  │     ├ 👨 李明 25岁 外卖员           │   │
│  │     ├ 👩 王芳 24岁 妻子             │   │
│  │     └ 👦 李小天 5岁 儿子            │   │
│  │                                    │   │
│  │  ◉ Scene — 场景生成中...            │   │
│  │     ├ 场景1: 夜晚的街道 ✓           │   │
│  │     └ 场景2: 温馨的家 ◉ 生成中      │   │
│  │                                    │   │
│  └────────────────────────────────────┘   │
│                                           │
│  每完成一个 Agent，右侧实时更新内容        │
│  用户无需等待全部完成，即可看到部分结果      │
└──────────────────────────────────────────┘
```

实现方式：
- SSE 事件监听 `agent:progress`
- 每个 Agent 完成后立即更新 ResultPanel 对应区块
- 新增 AgentPipelineProgress 组件，展示管线全景
  - 已完成节点 → 显示完成标志 + 摘要
  - 进行中节点 → 显示进度动画
  - 未开始节点 → 灰色等待
- 用户可以在 Agent 还在工作时，就浏览已生成的角色和场景
- 右侧 ResultPanel 随 SSE 事件逐步渲染，而非一次性刷新

#### 6.7 视觉体验组件清单

| 组件 | 位置 | 描述 |
|------|------|------|
| GalleryCard | `components/common/GalleryCard.tsx` | 作品展示卡片 |
| CharacterImageWall | `components/project/CharacterImageWall.tsx` | 角色视觉墙 |
| ScenePreviewCard | `components/project/ScenePreviewCard.tsx` | 场景沉浸预览卡 |
| StoryboardTimeline | `components/project/StoryboardTimeline.tsx` | 故事板横向时间线 |
| Dashboard | `components/dashboard/Dashboard.tsx` | 导演控制台 |
| ProductionTeam | `components/dashboard/ProductionTeam.tsx` | AI 制作团队展示 |
| StreamingPreview | `components/studio/StreamingPreview.tsx` | 流式生成预览 |
| AgentPipelineProgress | `components/studio/AgentPipelineProgress.tsx` | 管线进度全景 |

#### 6.8 路由新增

| 路由 | 页面 | 权限 | 描述 |
|------|------|------|------|
| `/gallery` | Gallery | 公开 | AI 作品展示画廊 |
| `/dashboard` | Dashboard | 需登录 | AI 导演控制台 |

### 总预估：12-19 天

| 旧组件 | 迁移方式 | 目标位置 |
|--------|----------|----------|
| AuthGuard.tsx | 重写 → AuthModal | `components/common/AuthModal.tsx` |
| ChatPanel.tsx | 分解 → StoryInput + AgentWorkflow | `components/studio/` |
| PreviewPanel.tsx | 保留渲染逻辑，重写包装 | `components/project/` |
| WorkflowVisualizer.tsx | 重写 → WorkflowGraph (React Flow) | `components/studio/WorkflowGraph.tsx` |
| Timeline.tsx | 保留，包装在新布局中 | `components/project/` |
| Toast.tsx | 升级为 shadcn/ui Toast | `components/ui/` |
| SortableShot.tsx | 保留 | `components/project/` |
| VideoPanel.tsx | 保留，包装在新布局中 | `components/project/` |
| Skeleton.tsx | 升级为 shadcn/ui Skeleton | `components/ui/` |
| api.ts | 保持兼容，新建 service 层覆盖 | `services/` |
| types/project.ts | 保持，新增类型补充 | `types/index.ts` |

## 附录：Asset 数据模型

为支持 AI 漫剧体验和 Gallery 展示，前端新增 Asset 类型：

```typescript
// types/asset.ts
interface Asset {
  id: string;
  type: 'character' | 'scene' | 'storyboard' | 'project';
  title: string;
  imageUrl?: string;         // 自动生成的抽象视觉封面
  thumbnailUrl?: string;     // 缩略图
  description?: string;
  tags?: string[];
  metadata: {
    projectId?: string;
    characterCount?: number;
    sceneCount?: number;
    shotCount?: number;
    duration?: string;        // 总时长
    mood?: string;
    generatedAt?: string;
  };
}

// Gallery 用
interface GalleryProject {
  id: string;
  title: string;
  description: string;
  coverUrl?: string;
  characters: number;
  scenes: number;
  shots: number;
  status: 'completed' | 'generating';
  createdAt: string;
  previews: {
    characters: Asset[];
    scenes: Asset[];
    storyboard: Asset[];
  };
}
```

Asset 用于：
- Gallery 作品展示卡片
- Character Image Wall 的图片占位
- Scene Preview 的渐变背景参数
- Dashboard 中的作品摘要

### assetGenerator.ts 接口定义（L-05 补充）

```typescript
// common/assetGenerator.ts
// 纯前端工具函数，不依赖后端 API

/** 根据角色名和特征生成 Emoji 头像 + 背景色 */
export const generateCharacterAvatar = (
  name: string,
  traits?: string[]
): { emoji: string; bgGradient: string } => {
  // 示例：name="李明" traits=["善良","孤独"]
  // → { emoji: "🧑", bgGradient: "linear-gradient(135deg, #667eea, #764ba2)" }
};

/** 根据氛围和环境生成场景缩略渐变色 */
export const generateSceneThumbnail = (
  mood: string,
  setting: string
): { gradient: string; tags: string[] } => {
  // 示例：mood="lonely" setting="rainy street"
  // → { gradient: "linear-gradient(180deg, #1a1a2e, #16213e)", tags: ["夜晚","雨天"] }
};

/** 从故事板和角色中提取视觉元素，生成封面配色方案 */
export const generateProjectCover = (
  storyboard: Shot[],
  characters: Character[]
): { colorPalette: string[]; composition: string } => {
  // 防御（L-06）：新项目可能 storyboard 为空
  if (!storyboard?.length) {
    return {
      colorPalette: ['#6366f1', '#111111'],
      composition: '默认抽象构图'
    };
  }
  // 正常逻辑：从首镜头描述和角色特征推断封面
};
```

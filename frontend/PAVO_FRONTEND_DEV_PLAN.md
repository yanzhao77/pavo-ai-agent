# Pavo AI Agent 前端重构 — 技术开发计划

版本: 1.0
日期: 2026-07-22
基于: PAVO_FRONTEND_REDESIGN_TECH_DOC.md v3.0

---

## 目录

- [Phase 依赖关系](#phase-依赖关系)
- [前置准备](#前置准备)
- [Phase 1: 基础设施 + Landing Page](#phase-1-基础设施--landing-page)
- [Phase 2: Studio 页面](#phase-2-studio-页面)
- [Phase 3: 项目列表 + 详情 + Gallery](#phase-3-项目列表--详情--gallery)
- [Phase 4: 工作流可视化升级](#phase-4-工作流可视化升级)
- [Phase 5: Director Dashboard](#phase-5-director-dashboard)
- [Phase 6: AI Visual Creation Experience](#phase-6-ai-visual-creation-experience)
- [Phase 7: 打磨与优化](#phase-7-打磨与优化)

---

## Phase 依赖关系

```
Phase 1 (基础设施) ─────────────────────────────────────────────┐
    │                                                          │
    ├── Phase 2 (Studio) ──→ Phase 4 (工作流动画) ──→ Phase 7 │
    │                                                          │
    ├── Phase 3 (项目+Gallery) ────────────────────────────────┤
    │                                                          │
    └── Phase 5 (Dashboard) ──→ Phase 6 (视觉体验) ────────────┘
```

**可并行**:
- Phase 2 和 Phase 3 可并行（不同路由，不同组件）
- Phase 4 依赖 Phase 2 完成（WorkflowGraph 基础上加动画）
- Phase 5 和 Phase 6 可并行（Dashboard 和视觉体验独立）
- Phase 7 必须在所有 Phase 完成后进行（最后的打磨）

**多人协作建议**：
- 开发 A: Phase 2 → Phase 4
- 开发 B: Phase 3 + Phase 6
- 开发 C: Phase 5
- 全员: Phase 7

---

## 前置准备

### 1. 环境确认

```bash
node -v  # ≥ 18
npm -v   # ≥ 9
```

### 2. 停止旧服务

```bash
# 如果已有 dev server 在运行
pkill -f "next dev" 2>/dev/null
```

### 3. 安装依赖

```bash
cd frontend

npm install zustand@4.5.0 axios@1.6.0 framer-motion@11.0.0 @xyflow/react@12.0.0
npm install @tanstack/react-query@5.0.0 @tanstack/react-query-devtools@5.0.0

# shadcn/ui
npx shadcn@latest init
npx shadcn@latest add button card input dialog toast tabs navigation-menu
```

### 4. 目录结构初始化

```bash
mkdir -p src/components/{ui,layout,landing,studio,project,dashboard,common}
mkdir -p src/services src/stores src/hooks src/types
```

---

## Phase 1: 基础设施 + Landing Page

**预估**: 2-3 天
**目标**: 搭建新架构骨架，实现产品级 Landing Page

---

### 1.0 视觉红线确认（编码前必读）

**以下设计风格严格禁止，Code Review 中一旦发现直接打回：**

| 禁止项 | 原因 | 替代方案 |
|--------|------|----------|
| 后台管理系统风格（Admin Dashboard） | 用户感知为"运维工具" | 参考 Runway / Midjourney 深色 AI 风格 |
| 数据表格（`<table>` / datatable） | 非消费级体验 | 卡片网格 + Flexbox 布局 |
| JSON 原始输出 | 暴露技术细节 | 结构化卡片展示 |
| 日志窗口 / Terminal 样式 | 开发工具感 | Agent 状态节点 + 进度条 |
| 默认 HTML 控件（裸 `<input>`、`<select>`） | 粗糙感 | shadcn/ui 组件 |
| 灰色 Bootstrap 卡片 | 过时视觉语言 | 深色 Glassmorphism 卡片 |

**必须采用的风格参考**：Pavo AI (app.pavo-ai.work)、Runway (runwayml.com)、Midjourney (midjourney.com)、Cursor (cursor.com)

---

### 1.1 设计 Token 配置

**文件**: `tailwind.config.js`

```javascript
// 深色 AI 主题色
colors: {
  surface: { DEFAULT: '#1a1a1a', hover: '#242424', active: '#2e2e2e' },
  border: { DEFAULT: '#2a2a2a', light: '#1f1f1f' },
  accent: { DEFAULT: '#6366f1', hover: '#5558e6', light: 'rgba(99, 102, 241, 0.1)' },
  cream: '#f8f7f5',
}
```

**测试**:
- [ ] Tailwind 编译通过，无未定义颜色警告
- [ ] 自定义类名 `.btn-primary` `.input-base` `.card` 在 JSX 中可用

### 1.2 全局样式

**文件**: `src/app/globals.css`

```css
/* 保留现有 Tailwind 指令 */
/* 新增组件类：.card .input-base .btn-primary .btn-ghost .tab-btn */
/* 滚动条样式 */
/* ::selection */
```

**测试**:
- [ ] 浏览器中 body 背景色为深色/cream
- [ ] 滚动条样式生效
- [ ] 选中文本时背景色变化

### 1.3 React Query Provider

**文件**: `src/app/providers.tsx`

```typescript
'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 2 } },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

**文件**: `src/app/layout.tsx` — 包裹 `<Providers>`

**测试**:
- [ ] 页面加载后 React Query Devtools 可打开（Ctrl+Shift+Q）
- [ ] Provider 无控制台报错

### 1.4 API 服务层

**文件**: `src/services/api.ts`

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
  timeout: 30000,
});

// 请求拦截器：自动附加 Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('pavo_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 响应拦截器：401 时清除 token
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('pavo_token');
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

export default api;
```

**文件**: `src/services/auth.ts`
**文件**: `src/services/project.ts`
**文件**: `src/services/workflow.ts`

**测试**:
- [ ] `api.ts` 正确读取 `NEXT_PUBLIC_API_BASE`
- [ ] 有 token 时请求头包含 `Authorization: Bearer xxx`
- [ ] 401 响应时自动清除 localStorage 并跳转
- [ ] `projectService.create('test input')` 返回 projectId
- [ ] `projectService.get(id)` 返回 Project 对象

### 1.5 Zustand Stores

**文件**: `src/stores/authStore.ts`

```typescript
interface AuthState {
  token: string | null;
  userId: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}
```

**文件**: `src/stores/projectStore.ts`

```typescript
// 轻量 — 仅管理当前选中的项目 ID
interface ProjectState {
  currentProjectId: string | null;
  setCurrentProjectId: (id: string | null) => void;
  createProject: (input: string) => Promise<string>;
}
```

**文件**: `src/stores/workflowStore.ts`

```typescript
// 实时状态 — SSE 连接 + Agent 运行状态（含重连机制）
interface WorkflowState {
  agents: AgentState[];
  isRunning: boolean;
  overallProgress: number;
  sseConnection: EventSource | null;
  sseStatus: 'idle' | 'connecting' | 'connected' | 'disconnected';
  reconnectAttempts: number;
  maxReconnectAttempts: number;   // 5
  reconnectDelay: number;         // 1000ms
  connectSSE: (projectId: string) => void;
  disconnectSSE: () => void;
  handleAgentEvent: (event: SSEAgentEvent) => void;
  syncStateFromAPI: (projectId: string) => Promise<void>;
  resetWorkflow: () => void;
}
```

**Agent 状态机**:

```
IDLE → CONNECTING → CONNECTED → (断开) → RECONNECTING → CONNECTED
                                               ↓ (超过重试次数)
                                            DISCONNECTED
```

**指数退避**: `delay = Math.min(reconnectDelay * Math.pow(2, attempt), 30000)`

**syncStateFromAPI 策略**:
- 已完成/失败 → 直接结束工作流
- 生成中 → 重置 agents 为 idle，重新连接 SSE

**测试**:
- [ ] `authStore.login('test')` 设置 token 和 userId
- [ ] `authStore.logout()` 清除所有状态
- [ ] `projectStore.setCurrentProjectId('xxx')` 只存 ID
- [ ] `workflowStore.connectSSE` 创建 EventSource 连接
- [ ] SSE 断开后自动触发指数退避重连
- [ ] 重连超过 5 次后状态变为 DISCONNECTED
- [ ] `handleAgentEvent` 正确更新对应 agent 的状态和进度

### 1.6 assetGenerator.ts

**文件**: `src/common/assetGenerator.ts`

```typescript
export const generateCharacterAvatar = (
  name: string,
  traits?: string[]
): { emoji: string; bgGradient: string };

export const generateSceneThumbnail = (
  mood: string,
  setting: string
): { gradient: string; tags: string[] };

export const generateProjectCover = (
  storyboard: Shot[],
  characters: Character[]
): { colorPalette: string[]; composition: string };
```

**测试**:
- [ ] `generateCharacterAvatar('李明', ['善良'])` 返回 emoji + bgGradient
- [ ] `generateSceneThumbnail('lonely', 'rainy')` 返回渐变色 + 标签
- [ ] `generateProjectCover([], [])` 返回默认配色（空 storyboard 防御）
- [ ] `generateProjectCover([shot1, shot2], [char1])` 正常返回

### 1.7 Navbar 组件

**文件**: `src/components/layout/Navbar.tsx`

```
Props: 无（读取 authStore）
渲染: Logo | NavLinks (Features, Gallery, Studio) | AuthButtons
交互: 未登录 → 显示 Sign In / Get Started
      已登录 → 显示用户头像 + 退出
```

**测试**:
- [ ] Navbar 固定在页面顶部
- [ ] 未登录时显示 "Sign In" 按钮
- [ ] 已登录时显示用户名首字母头像
- [ ] 点击 NavLinks 路由跳转正确
- [ ] 移动端导航可折叠/汉堡菜单

### 1.8 HeroSection

**文件**: `src/components/landing/Hero.tsx`

```
渲染: 
  ├── HeroBackground（渐变 + 粒子动画）
  ├── HeroTitle: "Create stories with AI"
  ├── HeroSubtitle: "AI turns it into animation"
  └── PromptInput（创意输入框 + 提交按钮）
```

**PromptInput 交互**:
- 用户输入文字
- 未输入时按钮 disabled
- 点击提交 → 检查 auth → 未登录弹出模态框 / 已登录调用 `createProject`
- 提交后跳转 `/studio`

**测试**:
- [ ] 输入框 placeholder 显示提示文字
- [ ] 空输入时提交按钮 disabled
- [ ] 输入内容后按钮可点击
- [ ] 点击提交 → 未登录显示 AuthModal
- [ ] 点击提交 → 已登录调用 createProject
- [ ] 加载状态显示 spinner
- [ ] 粒子背景动画正常运行（不卡顿）

### 1.9 FeatureSection

**文件**: `src/components/landing/FeatureSection.tsx`

```
内容: 4 张 Feature 卡片
  ├── 🧠 故事导演 — 分析故事结构
  ├── 🎭 角色设计师 — 创造人物形象
  ├── 🎬 分镜导演 — 转化为镜头语言
  └── 🌆 场景构建师 — 设计环境氛围
```

**测试**:
- [ ] 4 张卡片网格布局
- [ ] 鼠标悬浮时卡片微上浮 + 阴影加深（动画 200ms）
- [ ] 卡片内容完整显示

### 1.10 AuthModal 登录模态框

**文件**: `src/components/common/AuthModal.tsx`

```
Props: isOpen, onClose, onAuth
渲染: 半透明遮罩 | 弹窗 | 用户名输入 | 提交按钮
交互: 不离开当前页面，模态框覆盖
     登录成功后关闭模态框
```

**测试**:
- [ ] 模态框打开时背景内容不可滚动
- [ ] 点击遮罩区域关闭模态框
- [ ] 输入用户名后按 Enter 可提交
- [ ] 登录成功后自动关闭并触发回调
- [ ] 登录失败显示错误提示

### 1.11 Landing Page 集成

**文件**: `src/app/page.tsx`

```
渲染顺序:
  Navbar
  HeroSection
  FeatureSection
  WorkflowPreview（静态 7 Agent 流水线）
  GallerySection（占位：展示作品案例卡片）
  Footer
```

**测试**:
- [ ] 页面完整滚动显示所有 Section
- [ ] Hero 区的 PromptInput 可交互
- [ ] 未登录 + 提交创意 → 弹出 AuthModal
- [ ] 登录后 → 跳转 /studio
- [ ] 移动端响应式正常

### Phase 1 完整测试清单

```
□ Tailwind 编译通过
□ 所有组件无控制台错误
□ authStore login/logout 正常
□ projectStore 仅存 ID，不存数据
□ workflowStore SSE 连接 + 重连验证
□ api.ts 请求拦截器 + 401 处理
□ 启动后端服务后，projectService.create('test') 返回真实 projectId
□ process.env.NEXT_PUBLIC_API_BASE 未配置时自动 fallback 到 localhost:18080
□ 网络错误时 axios 超时 30s 自动触发
□ Navbar 固定 + 响应式
□ Hero 粒子动画流畅（60fps）
□ AuthModal 不跳转登录
□ Landing 全页面滚动
□ assetGenerator 3 个函数 + 空 storyboard 防御
□ 移动端 < 768px 布局不崩
```

---

## Phase 2: Studio 页面

**预估**: 2-3 天
**目标**: 创作工作室核心功能 — 三栏布局 + SSE 工作流 + 结果预览

---

### 2.1 React Query Hooks

**文件**: `src/hooks/useProject.ts`

```typescript
export const useProject = (id: string | null) => useQuery({
  queryKey: ['project', id],
  queryFn: () => projectService.get(id!),
  enabled: !!id,
  refetchInterval: (query) => {
    const data = query.state.data;
    if (data?.status === 'generating') return 2000;
    return false;
  },
});

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: string) => projectService.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  });
};
```

**文件**: `src/hooks/useProjects.ts`

```typescript
export const useProjects = (userId?: string) => useQuery({
  queryKey: ['projects', userId],
  queryFn: () => projectService.list(userId),
});

export const useGalleryProjects = (limit = 20) => useQuery({
  queryKey: ['gallery'],
  queryFn: async () => {
    const all = await projectService.list();
    const completed = all.filter((p: any) => p.status === 'completed');
    return completed.slice(0, limit);
  },
});
```

**测试**:
- [ ] `useProject('xxx')` 首次加载显示 skeleton
- [ ] 项目 status='generating' 时每 2s 轮询
- [ ] 项目 status='completed' 时停止轮询
- [ ] `useCreateProject` mutate 成功后 invalidate projects 缓存
- [ ] `useGalleryProjects` 只返回 completed 项目

### 2.2 Studio 路由

**文件**: `src/app/studio/page.tsx`

```
路由守卫: 未登录 → 重定向 /
三栏布局:
  ┌──────┬──────────────────┬──────────────────┐
  │ Side │   创作输入        │   作品预览       │
  │ bar  │  StoryInput       │  ResultPanel     │
  │      │  WorkflowGraph    │  (或              │
  │      │  AgentTimeline    │   StreamingPreview) │
  └──────┴──────────────────┴──────────────────┘
```

**交互逻辑**:
- 初始状态：中栏显示 StoryInput，右栏为空或引导提示
- 提交后：中栏切换为 WorkflowGraph，右栏显示 StreamingPreview
- 完成后：右栏切换为 ResultPanel（完整 Tab 内容）
- 右侧渲染条件见 2.6

**测试**:
- [ ] 未登录访问 /studio → 跳转 /
- [ ] 三栏结构正确渲染
- [ ] 初始状态无项目时显示引导提示
- [ ] 提交创意后切换到工作流视图

### 2.3 StudioSidebar

**文件**: `src/components/studio/StudioSidebar.tsx`

```
职责:
├── 当前项目信息（标题 + 状态 badge）
├── 最近项目（最多 3 个，点击切换）
├── "查看全部项目" → 跳转 /projects
├── 用户头像 + 退出登录
└── 新项目快速创建按钮
```

**测试**:
- [ ] 当前项目标题和状态 badge 正确显示
- [ ] 最近 3 个项目列表
- [ ] 点击最近项目 → 切换当前 Studio 项目
- [ ] "查看全部项目" → 跳转 /projects
- [ ] 退出登录 → 清除 token → 跳转 /

### 2.4 StoryInput + AgentWorkflow

**文件**: `src/components/studio/CreationPanel.tsx`

```
┌─────────────────────────┐
│  故事输入                │
│  ┌─────────────────┐    │
│  │ 输入创意...       │    │
│  └─────────────────┘    │
│  [✨ 开始创作]          │
├─────────────────────────┤
│  AI 创作管线             │
│  ┌───┐ → ┌───┐ → ┌───┐ │
│  │故事│ → │角色│ → │场景│ │
│  │导演│   │设计师│ │构建师│ │
│  └───┘   └───┘   └───┘ │
│  → ┌───┐ → ┌───┐ → ...  │
├─────────────────────────┤
│  AgentPipelineProgress   │
│  [████████░░░░] 60%      │
└─────────────────────────┘
```

**测试**:
- [ ] 输入区域 placeholder 正常
- [ ] 提交后清空输入框
- [ ] 提交后输入框 disabled（loading）
- [ ] Agent 节点使用 displayName（故事导演/角色设计师/...）
- [ ] 禁止出现 planner/character 等内部名称
- [ ] 节点状态颜色正确（idle灰/running蓝/completed绿/failed红）

### 2.5 WorkflowGraph（React Flow 基础版）

**文件**: `src/components/studio/WorkflowGraph.tsx`

```typescript
// 7 个节点线性排列，带箭头连线
const AGENTS = [
  { id: 'planner',    displayName: '故事导演',   icon: '🧠', pos: { x: 0, y: 0 } },
  { id: 'character',  displayName: '角色设计师', icon: '🎭', pos: { x: 180, y: 0 } },
  { id: 'scene',      displayName: '场景构建师', icon: '🌆', pos: { x: 360, y: 0 } },
  { id: 'prop',       displayName: '道具师',     icon: '🎨', pos: { x: 540, y: 0 } },
  { id: 'storyboard', displayName: '分镜导演',   icon: '🎬', pos: { x: 720, y: 0 } },
  { id: 'reviewer',   displayName: '质量审查官', icon: '🔍', pos: { x: 900, y: 0 } },
  { id: 'fixer',      displayName: '修复专家',   icon: '🔧', pos: { x: 1080, y: 0 } },
];
```

每个 AgentNode 渲染:
- Emoji 图标
- displayName
- 状态色圈（idle→gray, running→blue pulse, completed→green, failed→red）
- 进度数字（如 60%）
- 节点 click → 展开详情

**测试**:
- [ ] 7 个节点在 React Flow 画布上水平排列
- [ ] 节点之间有箭头连线
- [ ] 节点状态响应 workflowStore 更新
- [ ] `running` 状态有脉冲动画
- [ ] `failed` 状态显示错误图标
- [ ] 点击节点展开详情面板
- [ ] 禁止显示 planner/character 等内部标识

### 2.6 AgentPipelineProgress

**文件**: `src/components/studio/AgentPipelineProgress.tsx`

```
位置: 中栏底部（工作流图下方）
职责: 进度指示器 — "到哪了？"
渲染: 
├── 整体进度条 [████████░░] 60%
├── 7 Agent 紧凑状态行
│   ✅ 故事导演 · ✅ 角色设计师 · ◉ 场景构建师 · ◯ 道具师 · ◯ 分镜导演 · ◯ 审查 · ◯ 修复
└── 预计完成时间
```

**测试**:
- [ ] 进度条百分比与 workflowStore.overallProgress 一致
- [ ] 已完成 Agent 显示 ✅
- [ ] 运行中 Agent 显示 ◉ 脉冲动画
- [ ] 未开始 Agent 显示 ◯ 灰色
- [ ] 点击 Agent 名称可跳转到 StreamingPreview 对应位置

### 2.7 ResultPanel（现有组件升级版）

**文件**: `src/components/studio/ResultPanel.tsx`

```
位置: 右栏（工作流完成后）
职责: 内容展示器 — "生成了什么？"
布局:
├── Tab 栏: 角色 | 场景 | 道具 | 故事板
├── CharactersTab → CharacterCard[]
├── ScenesTab → SceneCard[]
├── PropsTab → PropCard[]
└── StoryboardTab → StoryboardTimeline
```

使用 React Query 获取数据：`useProject(projectStore.currentProjectId)`

**测试**:
- [ ] 4 个 Tab 切换正常
- [ ] CharactersTab 展示角色卡片网格
- [ ] ScenesTab 展示场景卡片
- [ ] PropsTab 展示道具卡片
- [ ] StoryboardTab 展示分镜头时间线
- [ ] 数据加载中显示 Skeleton

### 2.8 StreamingPreview

**文件**: `src/components/studio/StreamingPreview.tsx`

```
位置: 右栏（工作流运行中）
职责: 内容展示器 — "生成了什么？"
渲染: 已完成 Agent 的产出内容增量展示
├── ✅ 故事导演 — 分析完成
│   ├ 故事主题: 父子温情
│   └ 核心冲突: 工作与家庭
├── ✅ 角色设计师 — 已生成 3 角色
│   ├ 👨 李明 25岁 外卖员
│   ├ 👩 王芳 24岁 妻子
│   └ 👦 李小天 5岁 儿子
├── ◉ 场景构建师 — 场景生成中...
│   ├ 场景1: 夜晚的街道 ✓
│   └ 场景2: 温馨的家 ◉ 生成中
└── ...
```

**数据来源**: workflowStore.agents 中已完成 agent 的产出摘要
**刷新机制**: SSE `agent:progress` 事件驱动

**测试**:
- [ ] Agent 完成后立即在 StreamingPreview 中展示
- [ ] 进行中 Agent 显示进度动画
- [ ] 滚动浏览已生成内容
- [ ] 所有 Agent 完成后自动切换为 ResultPanel
- [ ] 组件卸载时清理 SSE 监听

### 2.9 右栏渲染逻辑集成

**位置**: `src/app/studio/page.tsx`

```typescript
const RightPanel = () => {
  const { isRunning } = useWorkflowStore();

  if (isRunning) {
    return (
      <>
        <AgentPipelineProgress />
        <StreamingPreview />
      </>
    );
  }

  return <ResultPanel />;
};
```

**测试**:
- [ ] 提交创意后右栏显示 StreamingPreview
- [ ] 所有 Agent 完成后右栏切换为 ResultPanel
- [ ] 切换过程无闪烁/卡顿

### 2.10 SSE 连接集成

**位置**: `src/app/studio/page.tsx` (useEffect)

```typescript
useEffect(() => {
  const projectId = projectStore.currentProjectId;
  if (!projectId) return;

  workflowStore.connectSSE(projectId);

  return () => {
    workflowStore.disconnectSSE();
  };
}, [projectStore.currentProjectId]);
```

**测试**:
- [ ] 组件挂载时连接 SSE
- [ ] 组件卸载时断开 SSE
- [ ] 切换项目时断开旧连接 + 建立新连接
- [ ] SSE 断开后自动重连（指数退避）
- [ ] 重连成功后重置 agents 重新接收事件

### Phase 2 完整测试清单

```
□ Studio 路由守卫（未登录跳转 /）
□ app/providers.tsx 正确包裹 layout.tsx
□ React Query Devtools 在开发环境可打开 (Ctrl+Shift+Q)
□ useProject 查询在 Network tab 中可见
□ 三栏布局正确渲染（Sidebar | 中栏 | 右栏）
□ StoryInput 提交触发生成
□ WorkflowGraph 7 节点 + displayName（无内部标识）
□ Agent 节点状态随 SSE 实时更新
□ running 状态蓝色脉冲动画
□ failed 状态红色错误提示
□ AgentPipelineProgress 进度条正确
□ StreamingPreview 增量展示产出内容
□ 完成后自动切换 ResultPanel
□ ResultPanel 4 个 Tab 正常切换
□ 所有数据通过 React Query 获取
□ projectStore 仅存 ID，不重复存数据
□ SSE 连接建立 + 断开 + 重连
□ 指数退避重连（最多 5 次）
□ 重连策略（已完成→结束 / 生成中→重置）
□ 未登录访问 /studio → 跳转 /
□ 移动端两栏布局正常
```

---

## Phase 3: 项目列表 + 详情 + Gallery

**预估**: 2-3 天
**目标**: 项目管理能力 + 作品画廊

---

### 3.1 Projects 路由

**文件**: `src/app/projects/page.tsx`

```
路由守卫: 未登录 → 重定向 /
布局:
├── Navbar
├── 页面标题 + 新建项目按钮
├── 项目网格卡片列表
│   ├── ProjectCard × N
│   │   ├── 标题
│   │   ├── 状态 badge（draft/generating/completed）
│   │   ├── 创建时间
│   │   └── 角色数 / 场景数 / 镜头数
│   └── 空状态: "还没有项目，开始创作"
├── 分页（> 20 条时）
└── Footer
```

**数据**: `useProjects(authStore.userId)`

**测试**:
- [ ] 项目列表网格展示
- [ ] 每张卡片显示标题、状态、时间
- [ ] 空状态显示引导
- [ ] 点击卡片跳转 `/projects/[id]`
- [ ] 点击"新建项目"跳转 `/studio`
- [ ] 超过 20 个项目时分页

### 3.2 ProjectCard

**文件**: `src/components/project/ProjectCard.tsx`

```
Props: project: Project
渲染:
├── 封面区（assetGenerator 生成抽象封面）
├── 标题
├── 状态 badge（颜色编码）
├── 角色数 · 场景数 · 镜头数
└── 创建时间（相对时间 "3小时前"）
```

**测试**:
- [ ] 封面色块正常显示（默认配色）
- [ ] 状态颜色正确（draft=灰, generating=蓝, completed=绿）
- [ ] 相对时间显示正确
- [ ] 鼠标悬浮上浮动画

### 3.3 Project Detail 路由

**文件**: `src/app/projects/[id]/page.tsx`

```
布局:
├── 返回按钮 ← /projects
├── 项目标题 + 状态 badge
├── 操作按钮（导出、渲染、删除）
├── 内容 Tab: 角色 | 场景 | 道具 | 故事板 | 视频
│   ├── CharactersTab → CharacterCard[]
│   ├── ScenesTab → SceneCard[]
│   ├── PropsTab → PropCard[]
│   ├── StoryboardTab → StoryboardTimeline
│   └── VideoTab → VideoPanel
└── WorkflowHistory（已完成的管线回放）
```

**数据**: `useProject(id)`

**测试**:
- [ ] 返回按钮正常跳转
- [ ] 项目标题正确显示
- [ ] 5 个 Tab 切换正常
- [ ] 导出按钮下载 Markdown
- [ ] 渲染按钮调用 renderProject API

### 3.4 Gallery 路由

**文件**: `src/app/gallery/page.tsx`

```
公开访问（无需登录）
布局:
├── Navbar
├── 页面标题 "AI 作品展示"
├── 筛选器: 全部 | 角色 | 场景 | 分镜
├── 作品卡片网格
└── Footer
```

**数据**: `useGalleryProjects(limit=20)`

**降级检测**:
- 项目数 < 50: 全量展示
- 50-100: 加载骨架屏
- > 100: 展示最近 20 个 + 提示"查看更多请访问项目列表"

**测试**:
- [ ] 未登录用户可访问
- [ ] 只展示 status='completed' 的项目
- [ ] 筛选器切换正确
- [ ] 项目数超 100 时显示降级提示
- [ ] 点击项目卡片跳转详情

### 3.5 GalleryCard

**文件**: `src/components/common/GalleryCard.tsx`

```
渲染:
├── 封面区（抽象渐变或 SVG）
├── 项目标题
├── 简短描述（截断）
├── 角色数 · 场景数 · 镜头数
└── 标签: 角色 / 场景 / 分镜
```

**测试**:
- [ ] 封面渲染正常
- [ ] 文字截断不超过 2 行
- [ ] 标签颜色不同
- [ ] 点击跳转 /projects/[id]

### Phase 3 完整测试清单

```
□ /projects 路由守卫（未登录跳转 /）
□ 项目网格列表
□ ProjectCard 封面 + 状态 badge
□ 空状态引导
□ 分页（> 20 条）
□ /projects/[id] 详情页
□ 5 个 Tab 切换
□ 导出 Markdown
□ 渲染视频
□ WorkflowHistory 回放
□ /gallery 公开访问
□ 只展示 completed 项目
□ > 100 项目降级提示
□ 筛选器
□ GalleryCard 封面 + 描述截断
□ 移动端适配
```

---

## Phase 4: 工作流可视化升级

**预估**: 2-3 天
**目标**: 产品级 Agent 工作流可视化

---

### 4.1 自定义 AgentNode

**文件**: `src/components/studio/AgentNode.tsx`

```typescript
interface AgentNodeProps {
  data: {
    internalName: string;
    displayName: string;
    icon: string;
    description: string;
    status: AgentStatus;
    progress: number;
    message: string;
  };
}

// 状态视觉映射
const STATUS_STYLES = {
  idle:      { bg: '#2a2a2a', pulse: false, opacity: 0.5 },
  running:   { bg: '#3b82f6', pulse: true,  opacity: 1.0 },
  completed: { bg: '#10b981', pulse: false, opacity: 1.0 },
  failed:    { bg: '#ef4444', pulse: false, opacity: 1.0 },
  retry:     { bg: '#f59e0b', pulse: true,  opacity: 1.0 },
};
```

**动画效果**:
- running: 蓝色呼吸脉冲（scale 1→1.05→1 循环 2s）
- completed: 绿色 + 对勾 + 轻微翻转
- failed: 红色 + 错误图标 + 抖动
- retry: 橙色闪烁 + 连线 dash 动画

**测试**:
- [ ] 5 种状态颜色正确
- [ ] running 脉冲动画流畅
- [ ] completed 翻转动画
- [ ] failed 抖动动画
- [ ] retry 闪烁动画
- [ ] hover 时显示 description

### 4.2 连线动画

**文件**: `src/components/studio/WorkflowGraph.tsx`（升级）

```typescript
// 使用 animated edges + markerEnd
// 连线样式:
//   idle: 灰色虚线
//   running: 蓝色实线 + dash 流动动画
//   completed: 绿色实线
//   failed: 红色实线
```

**测试**:
- [ ] 连线颜色随上游节点状态变化
- [ ] running 状态连线有流动粒子效果
- [ ] 动画不卡顿（60fps）

### 4.3 Agent 详情面板

**文件**: `src/components/studio/AgentDetailPanel.tsx`

```
点击 AgentNode 展开:
├── Agent 名称 + icon
├── 当前状态（带颜色标识）
├── 状态描述 — 来自 SSE message 字段
│   示例: "正在生成第三幕分镜"
├── 执行时间（秒）
└── 错误信息（红色区域，仅 failed 状态显示）
```

**数据来源**: `workflowStore.agents[i].message`（SSE 事件中的 message 字段），不包含结构化的"输入摘要/输出摘要"（后端不提供此数据）。

```typescript
// AgentDetailPanel.tsx 实现
const AgentDetailPanel = ({ agent }: { agent: AgentState }) => {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2">
        <span>{agent.icon}</span>
        <span className="font-semibold">{agent.displayName}</span>
        <StatusBadge status={agent.status} />
      </div>
      <p className="text-sm text-gray-400 mt-2">{agent.message}</p>
      {agent.durationMs > 0 && (
        <p className="text-xs text-gray-500 mt-1">
          执行时间: {(agent.durationMs / 1000).toFixed(1)}s
        </p>
      )}
      {agent.status === 'failed' && agent.message && (
        <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-400">
          {agent.message}
        </div>
      )}
    </div>
  );
};
```

**测试**:
- [ ] 点击节点展开详情
- [ ] 点击外部关闭详情
- [ ] 详情内容与 workflowStore 对应 agent 一致
- [ ] 错误信息以红色区域突出显示

### 4.4 进度条和时间线

**升级 AgentPipelineProgress**:

```
新增:
├── 单个 Agent 耗时条（横向条形图）
├── 总耗时显示
└── 每个 Agent 耗时比例
```

**测试**:
- [ ] 耗时条与 agent.durationMs 一致
- [ ] 总耗时累加正确
- [ ] 条形图颜色与状态一致

### Phase 4 完整测试清单

```
□ AgentNode 5 种状态正确
□ running 脉冲动画
□ completed 翻转 + 对勾
□ failed 抖动 + 红色
□ retry 闪烁
□ hover 显示 description
□ 连线颜色随上游变化
□ running 连线 dash 流动动画
□ 动画 60fps 不卡顿
□ 节点点击展开详情
□ 详情内容正确
□ 耗时条正确
□ 总耗时累加
```

---

## Phase 5: Director Dashboard

**预估**: 1-2 天
**目标**: "我是导演，AI 是我的制作团队"

---

### 5.1 Dashboard 路由

**文件**: `src/app/dashboard/page.tsx`

```
路由守卫: 未登录 → 重定向 /
布局:
├── Navbar
├── 统计卡片行
│   ├── 总项目数
│   ├── 进行中项目
│   └── 今日创建
├── 最近项目列表（带进度条）
├── AI Production Team
└── Footer
```

**数据**: `useProjects()` → 前端聚合统计

**测试**:
- [ ] 路由守卫
- [ ] 3 张统计卡片数据正确
- [ ] 最近项目列表
- [ ] 项目进度条

### 5.2 StatsCard

**文件**: `src/components/dashboard/StatsCard.tsx`

```
Props: label, value, icon, trend?
渲染: icon + 数字 + 标签
```

**测试**:
- [ ] 数字格式化（12 → "12", 1234 → "1.2k"）
- [ ] 图标正确
- [ ] 悬浮上浮动画

### 5.3 ProductionTeam

**文件**: `src/components/dashboard/ProductionTeam.tsx`

```
渲染: 7 个团队成员卡片
├── 🧠 故事导演 — 3 个项目
├── 🎭 角色设计师 — 3 个项目
├── 🌆 场景构建师 — 2 个项目
├── 🎨 道具师 — 2 个项目
├── 🎬 分镜导演 — 2 个项目
├── 🔍 质量审查官 — 3 个项目
└── 🔧 修复专家 — 1 个项目

交互: 点击成员查看其处理过的项目列表
```

**数据**: 从 projects 数据中聚合计算各 Agent 参与数

**测试**:
- [ ] 7 个成员卡片展示
- [ ] icon + displayName（禁止内部名称）
- [ ] 参与项目数正确
- [ ] 点击成员展开项目列表
- [ ] 空闲/工作中状态指示

### Phase 5 完整测试清单

```
□ /dashboard 路由守卫
□ 3 张统计卡片
□ 最近项目列表 + 进度条
□ ProductionTeam 7 成员
□ 成员使用 displayName
□ 参与项目数正确
□ 点击查看成员历史
□ 移动端适配
```

---

## Phase 6: AI Visual Creation Experience

**预估**: 2-3 天
**目标**: 用户看到的不只是数据，而是作品视觉呈现

---

### 6.1 CharacterImageWall

**文件**: `src/components/project/CharacterImageWall.tsx`

```
渲染: 角色卡片墙（网格）
每张卡片:
├── 头像区（圆形，assetGenerator 生成 Emoji + 背景渐变色）
├── 名称
├── 年龄 / 职业
└── 性格标签（彩色 chip）
```

**assetGenerator 集成**（M-04 补充）：

```typescript
// CharacterImageWall.tsx
import { generateCharacterAvatar } from '@/common/assetGenerator';

const CharacterCard = ({ character }: { character: Character }) => {
  const { emoji, bgGradient } = generateCharacterAvatar(
    character.name,
    character.personality  // traits 参数
  );

  return (
    <div className="card p-4 hover:-translate-y-1 transition-all duration-200">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center text-2xl mx-auto mb-3"
        style={{ background: bgGradient }}
      >
        {emoji}
      </div>
      <h3 className="font-semibold text-center">{character.name}</h3>
      <p className="text-xs text-gray-400 text-center">{character.age}岁 · {character.role}</p>
      {character.personality?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2 justify-center">
          {character.personality.map((trait, i) => (
            <span key={i} className="text-[11px] bg-accent-light text-accent rounded px-1.5 py-0.5">
              {trait}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
```

**测试**:
- [ ] 角色卡片网格布局
- [ ] Emoji 头像 + 渐变色背景
- [ ] 性格标签不同颜色
- [ ] 悬浮上浮动画
- [ ] 点击展开角色详情弹窗

### 6.2 ScenePreviewCard

**文件**: `src/components/project/ScenePreviewCard.tsx`

```
渲染: 场景沉浸式卡片
├── 渐变色背景（按 mood 生成）
├── 场景标题
├── 标签: 🕐 夜晚  🌧️ 雨天  💡 冷蓝调
└── 氛围描述
```

**测试**:
- [ ] 渐变色背景与 mood 对应
- [ ] 标签正确显示
- [ ] 可展开/收起详细描述
- [ ] 场景之间的视觉分割线

### 6.3 StoryboardTimeline

**文件**: `src/components/project/StoryboardTimeline.tsx`

```
渲染: 横向时间线
├── 场景导航（◀ Scene 1/3 ▶）
├── 镜头横向滚动列表
│   ├── Shot 卡片
│   │   ├── 镜头类型 badge
│   │   ├── 时长
│   │   ├── 摄影机运动
│   │   ├── 描述
│   │   └── 对话（引用样式）
│   └── 卡片间有箭头连接
└── 操作: 复制、导出
```

**测试**:
- [ ] 场景导航切换
- [ ] 镜头卡片水平滚动
- [ ] 镜头编号 + 类型 badge
- [ ] 对话引用样式
- [ ] 复制功能正常
- [ ] 滚动流畅

### Phase 6 完整测试清单

```
□ CharacterImageWall Emoji 头像
□ 性格标签彩色 chip
□ ScenePreviewCard mood 渐变色
□ 场景标签 + 可展开
□ StoryboardTimeline 横向滚动
□ 场景导航
□ 镜头卡片全部信息
□ 复制功能
□ 6.1 + 6.2 + 6.3 集成到 Studio ResultPanel
□ 6.1 + 6.2 + 6.3 集成到 Project Detail
```

---

## Phase 7: 打磨与优化

**预估**: 2-3 天
**目标**: 产品级体验

---

### 7.1 Framer Motion 页面过渡

```typescript
// 页面切换动画
<AnimatePresence mode="wait">
  <motion.div
    key={router.pathname}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.3 }}
  >
    {children}
  </motion.div>
</AnimatePresence>
```

**测试**:
- [ ] 页面切换有过渡动画
- [ ] 动画时长 300ms
- [ ] 不触发额外 re-render

### 7.2 加载状态骨架屏

| 组件 | 骨架屏 |
|------|--------|
| ProjectCard | 灰色矩形脉动 |
| CharacterCard | 圆形 + 文字线条 |
| SceneCard | 矩形 + 标签线条 |
| GalleryCard | 矩形 + 文字线条 |
| WorkflowGraph | 7 个圆点排列 |

**测试**:
- [ ] 首次加载显示骨架屏
- [ ] 数据到达后平滑替换
- [ ] 骨架屏脉动动画

### 7.3 错误处理

```
统一错误边界:
├── ErrorBoundary 组件包裹每个路由
├── 网络错误 → 重试按钮
├── API 错误 → 提示 + 详细错误（可折叠）
├── 404 → 自定义页面
└── 空数据 → 引导提示
```

**测试**:
- [ ] API 500 时显示错误提示 + 重试
- [ ] 网络断开时显示提示
- [ ] 404 路由显示自定义页面
- [ ] 空项目列表显示引导

### 7.4 深色模式完善

```typescript
// 使用 tailwind dark: 变体
// or CSS 变量切换
const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  // localStorage 持久化
  // 监听系统偏好
};
```

**测试**:
- [ ] 默认深色模式
- [ ] 切换主题时无闪烁
- [ ] 所有页面主题一致

### 7.5 响应式适配

| 断点 | 布局 |
|------|------|
| ≥1200px | 完整三栏 |
| 768-1199px | 两栏（隐藏 Sidebar） |
| <768px | 单栏 + 底部 Tab |

**移动端 Tab 设计**:

```
┌──────────────────────┐
│  Pavo        [≡]     │
├──────────────────────┤
│                      │
│   当前 Tab 内容       │
│                      │
├──────────────────────┤
│  ✍️  📊  👁️   │
└──────────────────────┘
```

**测试**:
- [ ] 768px 断点切换到两栏
- [ ] 375px 断点切换到单栏 + 底部 Tab
- [ ] 所有交互在触摸屏上可用
- [ ] 无水平滚动

### 7.6 性能优化

```typescript
// 组件懒加载
const StudioPage = dynamic(() => import('@/app/studio/page'), {
  loading: () => <LoadingAnimation />,
});

const WorkflowGraph = dynamic(() => import('@/components/studio/WorkflowGraph'), {
  ssr: false, // React Flow 需要浏览器环境
});
```

**性能验收标准（M-05 补充）**：

```
├── Lighthouse Performance Score > 80
├── Lighthouse Accessibility Score > 90
├── First Contentful Paint (FCP) < 1.5s
├── Largest Contentful Paint (LCP) < 2.5s
├── Total Blocking Time (TBT) < 200ms
└── Cumulative Layout Shift (CLS) < 0.1
```

**优化清单**:
- [ ] 路由级懒加载
- [ ] React Flow 组件 ssr: false
- [ ] 图片懒加载
- [ ] 长列表虚拟滚动（如果 > 50 items）

### Phase 7 完整测试清单

```
□ Framer Motion 页面过渡
□ 骨架屏所有组件
□ 错误边界
□ 网络错误重试
□ 404 页面
□ 深色/浅色切换
□ 768px 响应式
□ 375px 响应式 + 底部 Tab
□ 路由懒加载
□ React Flow ssr: false
□ Lighthouse 性能 > 70
□ 控制台无错误/警告
```

---

## 整体交付清单

```
□ Phase 1: Landing Page（公开访问 + AuthModal + 基础架构）
□ Phase 2: Studio（三栏 + SSE + WorkflowGraph + 结果预览）
□ Phase 3: Projects + Project Detail + Gallery
□ Phase 4: 工作流动画升级（节点 + 连线 + 详情）
□ Phase 5: Director Dashboard
□ Phase 6: 视觉体验（角色墙 + 场景卡 + 故事板时间线）
□ Phase 7: 打磨（动画 + 骨架屏 + 错误处理 + 响应式 + 性能）
```

## 每个 Phase 的测试原则

```
1. 编码时同步写测试
2. 每个组件至少覆盖：正常渲染、空状态、加载状态、错误状态
3. 交互组件覆盖：点击、输入、键盘事件
4. 路由组件覆盖：权限守卫、参数变化
5. 状态管理覆盖：初始化、更新、重置、销毁
6. 每次提交前跑通当前 Phase 的所有测试
```

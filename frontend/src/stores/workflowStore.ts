import { create } from 'zustand';
import { workflowService } from '@/services/workflow';
import { projectService } from '@/services/project';

export type AgentStatus = 'idle' | 'running' | 'completed' | 'failed' | 'retry';

export interface AgentState {
  internalName: string;
  displayName: string;
  icon: string;
  description: string;
  status: AgentStatus;
  progress: number;
  message: string;
  durationMs: number;
}

export interface SSEAgentEvent {
  agent: string;
  displayName: string;
  status: AgentStatus;
  progress: number;
  message: string;
  timestamp?: string;
}

const AGENT_INITIALS: AgentState[] = [
  { internalName: 'planner',    displayName: '故事导演',   icon: '🧠', description: '分析故事结构，制定创作计划',       status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'character',  displayName: '角色设计师', icon: '🎭', description: '创造人物形象与性格特征',           status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'scene',      displayName: '场景构建师', icon: '🌆', description: '设计环境氛围与光影色调',           status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'prop',       displayName: '道具师',     icon: '🎨', description: '配置道具细节与交互方式',           status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'storyboard', displayName: '分镜导演',   icon: '🎬', description: '将故事转化为视觉镜头语言',         status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'reviewer',   displayName: '质量审查官', icon: '🔍', description: '检查内容质量与叙事一致性',         status: 'idle', progress: 0, message: '', durationMs: 0 },
  { internalName: 'fixer',      displayName: '修复专家',   icon: '🔧', description: '修正问题，优化最终输出',           status: 'idle', progress: 0, message: '', durationMs: 0 },
];

interface WorkflowState {
  agents: AgentState[];
  isRunning: boolean;
  overallProgress: number;
  sseConnection: EventSource | null;
  sseStatus: 'idle' | 'connecting' | 'connected' | 'disconnected';
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  reconnectDelay: number;

  connectSSE: (projectId: string) => void;
  disconnectSSE: () => void;
  handleAgentEvent: (event: SSEAgentEvent) => void;
  syncStateFromAPI: (projectId: string) => Promise<void>;
  resetWorkflow: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  agents: AGENT_INITIALS,
  isRunning: false,
  overallProgress: 0,
  sseConnection: null,
  sseStatus: 'idle',
  reconnectAttempts: 0,
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,

  connectSSE: (projectId: string) => {
    const token = localStorage.getItem('pavo_token') || '';
    const store = get();
    store.disconnectSSE();

    set({ sseStatus: 'connecting', isRunning: true });
    const es = workflowService.subscribeSSE(projectId, token);

    es.onopen = () => {
      set({ sseStatus: 'connected', reconnectAttempts: 0 });
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'agent:progress') {
          get().handleAgentEvent({
            agent: data.agent || '',
            displayName: data.displayName || '',
            status: (data.status === 'passed' ? 'completed' : data.status) as AgentStatus,
            progress: data.progress || 0,
            message: data.action || '',
          });
        }
        if (data.type === 'agent:complete') {
          set({ isRunning: false });
          es.close();
        }
      } catch {}
    };

    es.onerror = () => {
      es.close();
      const { reconnectAttempts, maxReconnectAttempts } = get();
      if (reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(get().reconnectDelay * Math.pow(2, reconnectAttempts), 30000);
        set({ sseStatus: 'disconnected', reconnectAttempts: reconnectAttempts + 1 });
        setTimeout(() => get().connectSSE(projectId), delay);
      } else {
        set({ sseStatus: 'disconnected', isRunning: false });
        // 重连耗尽，尝试 REST API 同步
        get().syncStateFromAPI(projectId);
      }
    };

    set({ sseConnection: es });
  },

  disconnectSSE: () => {
    const { sseConnection } = get();
    if (sseConnection) {
      sseConnection.close();
    }
    set({ sseConnection: null, sseStatus: 'idle', reconnectAttempts: 0 });
  },

  handleAgentEvent: (event: SSEAgentEvent) => {
    const { agents } = get();
    const updated = agents.map((a) => {
      if (a.internalName === event.agent) {
        return {
          ...a,
          status: event.status,
          progress: event.progress,
          message: event.message,
          displayName: event.displayName || a.displayName,
        };
      }
      // 如果当前 agent 是 running，其上游已完成
      if (a.internalName === event.agent) {
        return a;
      }
      return a;
    });

    const completed = updated.filter((a) => a.status === 'completed').length;
    const overallProgress = Math.round((completed / updated.length) * 100);

    set({ agents: updated, overallProgress });
  },

  syncStateFromAPI: async (projectId: string) => {
    try {
      const project = await projectService.get(projectId);
      if (project.status === 'completed' || project.status === 'failed') {
        set({ isRunning: false });
      } else {
        get().resetWorkflow();
        get().connectSSE(projectId);
      }
    } catch {
      set({ isRunning: false });
    }
  },

  resetWorkflow: () => {
    set({
      agents: AGENT_INITIALS.map((a) => ({ ...a })),
      isRunning: false,
      overallProgress: 0,
      sseConnection: null,
      sseStatus: 'idle',
      reconnectAttempts: 0,
    });
  },
}));

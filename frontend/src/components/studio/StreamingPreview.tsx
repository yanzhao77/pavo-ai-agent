'use client';

import { useWorkflowStore, type AgentState } from '@/stores/workflowStore';

const STATUS_DOT: Record<string, string> = {
  idle: '○', running: '◉', completed: '✅', failed: '❌', retry: '⟳',
};

function AgentBlock({ agent }: { agent: AgentState }) {
  if (agent.status === 'idle') return null;
  const isRunning = agent.status === 'running';

  return (
    <div className={`p-3 rounded-lg border ${isRunning ? 'border-indigo-500/20 bg-indigo-500/5' : 'border-white/5 bg-white/[0.02]'}`}>
      <div className="flex items-center gap-2">
        <span>{STATUS_DOT[agent.status]}</span>
        <span className="text-xs font-medium text-gray-300">{agent.icon} {agent.displayName}</span>
        {isRunning && (
          <span className="text-[10px] text-indigo-400 animate-pulse">生成中...</span>
        )}
        {agent.status === 'completed' && (
          <span className="text-[10px] text-green-400">完成</span>
        )}
        {agent.status === 'failed' && (
          <span className="text-[10px] text-red-400">失败</span>
        )}
      </div>
      {agent.message && (
        <p className="text-xs text-gray-500 mt-1 ml-5">{agent.message}</p>
      )}
      {agent.progress > 0 && (
        <div className="ml-5 mt-1 h-1 bg-white/5 rounded-full overflow-hidden w-24">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all duration-500"
            style={{ width: `${agent.progress}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function StreamingPreview() {
  const { agents, isRunning } = useWorkflowStore();
  const activeAgents = agents.filter((a) => a.status !== 'idle');

  if (activeAgents.length === 0) return null;

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      <h3 className="text-[10px] text-gray-600 uppercase tracking-wider mb-3">
        {isRunning ? 'AI 创作中...' : '创作完成'}
      </h3>
      {activeAgents.map((a) => (
        <AgentBlock key={a.internalName} agent={a} />
      ))}
    </div>
  );
}

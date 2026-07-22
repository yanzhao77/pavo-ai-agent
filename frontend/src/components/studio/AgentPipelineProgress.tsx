'use client';

import type { AgentState } from '@/stores/workflowStore';

interface Props {
  agents: AgentState[];
  overallProgress: number;
  isRunning: boolean;
}

const STATUS_ICONS: Record<string, string> = {
  idle: '◯', running: '◉', completed: '✅', failed: '❌', retry: '⟳',
};
const STATUS_COLORS: Record<string, string> = {
  idle: '#333', running: '#6366f1', completed: '#10b981', failed: '#ef4444', retry: '#f59e0b',
};

export function AgentPipelineProgress({ agents, overallProgress, isRunning }: Props) {
  if (!isRunning && overallProgress === 0) return null;

  return (
    <div className="mt-4 p-3 rounded-lg bg-white/[0.02] border border-white/5">
      {/* Progress bar */}
      <div className="flex items-center gap-2 mb-2">
        <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        <span className="text-[10px] text-gray-500 w-8 text-right">{overallProgress}%</span>
      </div>

      {/* Agent status row */}
      <div className="flex flex-wrap gap-1.5">
        {agents.map((a) => (
          <span
            key={a.internalName}
            className="text-[10px] flex items-center gap-1 px-1.5 py-0.5 rounded"
            style={{ background: `${STATUS_COLORS[a.status]}15`, color: STATUS_COLORS[a.status] }}
          >
            <span>{STATUS_ICONS[a.status]}</span>
            {a.displayName}
          </span>
        ))}
      </div>
    </div>
  );
}

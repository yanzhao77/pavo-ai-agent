'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { useWorkflowStore } from '@/stores/workflowStore';
import { WorkflowGraph } from '@/components/studio/WorkflowGraph';
import { AgentPipelineProgress } from '@/components/studio/AgentPipelineProgress';

export function CreationPanel() {
  const [input, setInput] = useState('');
  const { isAuthenticated } = useAuthStore();
  const { currentProjectId, setCurrentProjectId, createProject } = useProjectStore();
  const { connectSSE, isRunning, agents, overallProgress } = useWorkflowStore();
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async () => {
    if (!input.trim() || loading) return;
    if (!isAuthenticated) { router.push('/'); return; }

    setLoading(true);
    try {
      const userId = localStorage.getItem('pavo_user_id') || '';
      const projectId = await createProject(input.trim(), userId);
      connectSSE(projectId);
      setInput('');
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="w-[420px] flex-shrink-0 flex flex-col border-r border-white/10 bg-white/[0.01]">
      {/* Input area */}
      <div className="p-4 border-b border-white/10">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder="输入想法或剧本，和Pavo一起创作..."
            className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-gray-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 pr-12"
            disabled={loading || isRunning}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || isRunning || !input.trim()}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-md flex items-center justify-center transition-colors"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" /> : <ArrowRight className="w-3.5 h-3.5 text-white" />}
          </button>
        </div>
      </div>

      {/* Workflow Graph */}
      <div className="flex-1 overflow-y-auto p-4">
        {currentProjectId ? (
          <>
            <WorkflowGraph agents={agents} />
            <AgentPipelineProgress agents={agents} overallProgress={overallProgress} isRunning={isRunning} />
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="w-8 h-8 text-gray-700 mb-3" />
            <p className="text-gray-500 text-sm">Enter a story idea above</p>
            <p className="text-gray-600 text-xs mt-1">AI agents will create your storyboard</p>
          </div>
        )}
      </div>
    </div>
  );
}

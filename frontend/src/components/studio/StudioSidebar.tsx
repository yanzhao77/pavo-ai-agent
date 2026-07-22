'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { useWorkflowStore } from '@/stores/workflowStore';
import { useProjects } from '@/hooks/useProject';
import { Sparkles, Plus, LogOut } from 'lucide-react';

export function StudioSidebar() {
  const { username, logout } = useAuthStore();
  const { currentProjectId, setCurrentProjectId, createProject } = useProjectStore();
  const { resetWorkflow } = useWorkflowStore();
  const { data: projects } = useProjects();

  const handleNewProject = async () => {
    resetWorkflow();
    setCurrentProjectId(null);
  };

  return (
    <nav className="w-56 flex-shrink-0 bg-white/[0.02] border-r border-white/10 flex flex-col">
      <div className="p-4 border-b border-white/10">
        <Link href="/" className="flex items-center gap-2 text-white font-semibold text-sm">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          Pavo
        </Link>
      </div>

      <div className="p-3">
        <button
          onClick={handleNewProject}
          className="w-full flex items-center gap-2 px-3 py-2 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-500/30 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Project
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 space-y-1">
        <p className="text-[10px] text-gray-600 uppercase tracking-wider px-2 mb-2">Recent</p>
        {(projects || []).slice(0, 3).map((p: any) => (
          <button
            key={p.id}
            onClick={() => setCurrentProjectId(p.id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
              currentProjectId === p.id
                ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
                : 'text-gray-400 hover:bg-white/5 hover:text-gray-300'
            }`}
          >
            <p className="truncate font-medium">{p.title || 'Untitled'}</p>
            <p className="text-[10px] text-gray-600 mt-0.5 capitalize">{p.status}</p>
          </button>
        ))}
        {(projects?.length || 0) > 3 && (
          <Link href="/projects" className="block px-3 py-1.5 text-xs text-gray-600 hover:text-gray-400">
            View all projects →
          </Link>
        )}
      </div>

      <div className="p-3 border-t border-white/10">
        <Link href="/dashboard" className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors">
          <Sparkles className="w-3.5 h-3.5" />
          Dashboard
        </Link>
        <div className="flex items-center justify-between mt-2 px-3 py-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center text-[9px] font-medium text-white shrink-0">
              {(username || 'U').charAt(0).toUpperCase()}
            </div>
            <span className="text-xs text-gray-500 truncate">{username}</span>
          </div>
          <button onClick={() => { logout(); window.location.href = '/'; }} className="text-gray-600 hover:text-gray-400">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </nav>
  );
}

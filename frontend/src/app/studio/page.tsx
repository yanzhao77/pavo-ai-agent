'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { useWorkflowStore } from '@/stores/workflowStore';
import { StudioSidebar } from '@/components/studio/StudioSidebar';
import { CreationPanel } from '@/components/studio/CreationPanel';
import { StreamingPreview } from '@/components/studio/StreamingPreview';
import { ResultPanel } from '@/components/studio/ResultPanel';

export default function StudioPage() {
  const { isAuthenticated, checkAuth, logout } = useAuthStore();
  const { currentProjectId } = useProjectStore();
  const { isRunning } = useWorkflowStore();
  const router = useRouter();

  useEffect(() => {
    if (!checkAuth()) {
      router.push('/');
    }
  }, []);

  if (!isAuthenticated) return null;

  return (
    <div className="h-screen bg-black flex overflow-hidden">
      {/* Left: Sidebar */}
      <StudioSidebar />

      {/* Center: Creation Panel */}
      <CreationPanel />

      {/* Right: Preview */}
      <div className="flex-1 flex flex-col min-w-0 border-l border-white/10">
        {currentProjectId && isRunning ? (
          <StreamingPreview />
        ) : currentProjectId ? (
          <ResultPanel />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-500 text-sm">Enter a story idea to begin</p>
              <p className="text-gray-600 text-xs mt-1">AI will generate characters, scenes, and storyboard</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

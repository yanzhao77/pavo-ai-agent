'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useProjects } from '@/hooks/useProject';
import { Navbar } from '@/components/layout/Navbar';
import { ProjectCard } from '@/components/studio/ProjectCard';
import { Plus, Loader2, Sparkles } from 'lucide-react';

const ITEMS_PER_PAGE = 20;

export default function ProjectsPage() {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();
  const [ready, setReady] = useState(false);
  const [page, setPage] = useState(0);

  // Auth guard
  useEffect(() => {
    const authed = checkAuth();
    if (!authed) {
      router.replace('/');
    } else {
      setReady(true);
    }
  }, []);

  const { data: projects, isLoading, error } = useProjects();

  if (!ready) return null;

  const allProjects = projects || [];
  const totalPages = Math.max(1, Math.ceil(allProjects.length / ITEMS_PER_PAGE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = allProjects.slice(
    safePage * ITEMS_PER_PAGE,
    (safePage + 1) * ITEMS_PER_PAGE,
  );

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">My Projects</h1>
            <p className="text-sm text-gray-500 mt-1">
              {allProjects.length > 0
                ? `共 ${allProjects.length} 个项目`
                : '管理你的 AI 创作项目'}
            </p>
          </div>
          <button
            onClick={() => router.push('/studio')}
            className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            <span className="text-sm text-gray-500">加载项目中...</span>
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="text-center py-20">
            <p className="text-red-400 text-sm">加载失败，请稍后重试</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && paged.length === 0 && (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-7 h-7 text-gray-500" />
            </div>
            <p className="text-gray-400 text-sm mb-4">还没有项目，开始创作</p>
            <button
              onClick={() => router.push('/studio')}
              className="px-5 py-2 bg-indigo-500 hover:bg-indigo-600 rounded-lg text-sm font-medium transition-colors"
            >
              开始创作
            </button>
          </div>
        )}

        {/* Grid */}
        {!isLoading && paged.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {paged.map((p: any) => (
                <ProjectCard key={p.id} project={p} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={safePage === 0}
                  className="px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  上一页
                </button>
                {Array.from({ length: totalPages }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setPage(i)}
                    className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                      i === safePage
                        ? 'bg-indigo-500 text-white'
                        : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {i + 1}
                  </button>
                ))}
                <button
                  onClick={() =>
                    setPage((p) => Math.min(totalPages - 1, p + 1))
                  }
                  disabled={safePage === totalPages - 1}
                  className="px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 px-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>Pavo AI Agent</span>
          <span>AI-powered storyboard generation</span>
        </div>
      </footer>
    </div>
  );
}

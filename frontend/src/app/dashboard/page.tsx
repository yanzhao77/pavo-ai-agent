'use client';

import { useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  FolderOpen,
  PlayCircle,
  CalendarPlus,
  ArrowRight,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useProjects } from '@/hooks/useProject';
import { Navbar } from '@/components/layout/Navbar';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { ProductionTeam } from '@/components/dashboard/ProductionTeam';
import type { Project } from '@/types/project';

function isToday(dateStr: string): boolean {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();
  const { data: projects = [], isLoading } = useProjects();

  // Auth guard
  useEffect(() => {
    const authed = checkAuth();
    if (!authed) {
      router.replace('/');
    }
  }, []);

  // Stats derived from projects
  const stats = useMemo(() => {
    const projList: Project[] = Array.isArray(projects) ? projects : [];
    return {
      total: projList.length,
      inProgress: projList.filter((p) => p.status === 'generating').length,
      todayCreated: projList.filter((p) => {
        try {
          return p.createdAt && isToday(p.createdAt);
        } catch {
          return false;
        }
      }).length,
    };
  }, [projects]);

  // Recent projects (last 5)
  const recentProjects: Project[] = useMemo(() => {
    const projList: Project[] = Array.isArray(projects) ? projects : [];
    return [...projList]
      .sort(
        (a, b) =>
          new Date(b.createdAt || 0).getTime() -
          new Date(a.createdAt || 0).getTime(),
      )
      .slice(0, 5);
  }, [projects]);

  if (!isAuthenticated) {
    return null; // will redirect via useEffect
  }

  const progressPercent = (p: Project): number => {
    if (p.status === 'completed') return 100;
    if (p.status === 'generating') return 65;
    return 10;
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Director Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            AI is your production team — overview at a glance
          </p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <StatsCard
            label="总项目数"
            value={stats.total}
            icon={<FolderOpen className="w-5 h-5" />}
          />
          <StatsCard
            label="进行中"
            value={stats.inProgress}
            icon={<PlayCircle className="w-5 h-5" />}
            trend={stats.inProgress > 0 ? 'up' : null}
            trendLabel={
              stats.inProgress > 0
                ? `${stats.inProgress} 个项目正在生成`
                : undefined
            }
          />
          <StatsCard
            label="今日创建"
            value={stats.todayCreated}
            icon={<CalendarPlus className="w-5 h-5" />}
            trend={stats.todayCreated > 0 ? 'up' : null}
          />
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <svg
                className="animate-spin w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Loading dashboard...
            </div>
          </div>
        )}

        {/* Recent Projects */}
        {!isLoading && (
          <section className="mb-10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">
                最近项目
              </h2>
              <a
                href="/projects"
                className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors"
              >
                查看全部 <ArrowRight className="w-3 h-3" />
              </a>
            </div>

            <div className="space-y-2">
              {recentProjects.length === 0 && (
                <div className="rounded-xl border border-dashed border-white/10 p-8 text-center">
                  <FolderOpen className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">
                    还没有项目，开始创作你的第一个故事吧
                  </p>
                </div>
              )}

              {recentProjects.map((p) => {
                const pct = progressPercent(p);
                return (
                  <a
                    key={p.id}
                    href={`/studio?id=${p.id}`}
                    className="block p-4 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/20 transition-all duration-200"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${
                          p.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : p.status === 'generating'
                              ? 'bg-indigo-500/10 text-indigo-400'
                              : 'bg-gray-500/10 text-gray-400'
                        }`}
                      >
                        {p.status === 'completed'
                          ? '已完成'
                          : p.status === 'generating'
                            ? '生成中'
                            : '草稿'}
                      </span>
                      <span className="text-sm text-white truncate">
                        {p.title || p.input?.slice(0, 60) || '未命名项目'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            p.status === 'completed'
                              ? 'bg-emerald-500'
                              : p.status === 'generating'
                                ? 'bg-indigo-500'
                                : 'bg-gray-600'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-gray-600 w-8 text-right">
                        {pct}%
                      </span>
                    </div>
                  </a>
                );
              })}
            </div>
          </section>
        )}

        {/* Production Team */}
        {!isLoading && (
          <ProductionTeam
            projects={Array.isArray(projects) ? projects : []}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>Pavo AI Agent</span>
          <span>AI-powered storyboard generation</span>
        </div>
      </footer>
    </div>
  );
}

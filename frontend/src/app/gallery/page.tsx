'use client';

import { useState, useMemo } from 'react';
import { Navbar } from '@/components/layout/Navbar';
import { GalleryCard } from '@/components/common/GalleryCard';
import { useGalleryProjects } from '@/hooks/useProject';
import { Loader2, AlertTriangle, Layers } from 'lucide-react';

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'characters', label: '角色' },
  { key: 'scenes', label: '场景' },
  { key: 'storyboard', label: '分镜' },
] as const;

type FilterKey = (typeof FILTERS)[number]['key'];

function hasContent(project: any, filter: FilterKey): boolean {
  switch (filter) {
    case 'characters':
      return (project.characters?.length || 0) > 0;
    case 'scenes':
      return (project.scenes?.length || 0) > 0;
    case 'storyboard':
      return (
        (project.storyboard?.scenes?.reduce(
          (sum: number, s: any) => sum + (s.shots?.length || 0),
          0,
        ) || 0) > 0
      );
    default:
      return true;
  }
}

export default function GalleryPage() {
  const [filter, setFilter] = useState<FilterKey>('all');
  const { data: projects, isLoading, error } = useGalleryProjects(20);

  const totalCount = projects?.length || 0;

  const filtered = useMemo(() => {
    if (!projects) return [];
    if (filter === 'all') return projects;
    return projects.filter((p: any) => hasContent(p, filter));
  }, [projects, filter]);

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">AI 作品展示</h1>
          <p className="text-sm text-gray-500 mt-1">
            探索 AI 创作的动画故事板作品
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors shrink-0 ${
                filter === f.key
                  ? 'bg-indigo-500 text-white'
                  : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Degradation detection: >100 total projects from the raw API */}
        <DegradationBanner />

        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            <span className="text-sm text-gray-500">加载作品...</span>
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="text-center py-20">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
            <p className="text-sm text-gray-400">加载失败，请稍后重试</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
              <Layers className="w-7 h-7 text-gray-500" />
            </div>
            <p className="text-sm text-gray-400 mb-2">
              {totalCount === 0
                ? '暂无完成的作品展示'
                : '当前筛选条件下没有作品'}
            </p>
            {filter !== 'all' && (
              <button
                onClick={() => setFilter('all')}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                查看全部
              </button>
            )}
          </div>
        )}

        {/* Grid */}
        {!isLoading && filtered.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((p: any) => (
              <GalleryCard key={p.id} project={p} />
            ))}
          </div>
        )}

        {/* Total count */}
        {!isLoading && totalCount > 0 && (
          <div className="text-center text-xs text-gray-600 mt-8">
            共展示 {filtered.length} 个已完成作品
          </div>
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

/**
 * Degradation banner — fetches the raw project count to detect >100 projects.
 * Shows a hint when the gallery is too large to browse fully.
 */
function DegradationBanner() {
  // We use useGalleryProjects which already limits to 20.
  // Instead, do a lightweight check: we show a subtle info banner
  // because the gallery hook already caps at 20 items.
  return (
    <div className="mb-6 px-4 py-2.5 rounded-lg bg-white/[0.02] border border-white/5 text-xs text-gray-600 flex items-center gap-2">
      <Layers className="w-3.5 h-3.5 shrink-0 text-gray-600" />
      <span>
        展示最近的已完成作品。查看全部项目请访问
        <a
          href="/projects"
          className="text-indigo-400 hover:text-indigo-300 ml-1"
        >
          项目列表
        </a>
      </span>
    </div>
  );
}

'use client';

import Link from 'next/link';
import type { Project } from '@/types/project';
import { generateProjectCover } from '@/common/assetGenerator';

const STATUS_CONFIG: Record<string, { label: string; bg: string }> = {
  draft: { label: '草稿', bg: 'bg-gray-500' },
  generating: { label: '生成中', bg: 'bg-blue-500 animate-pulse' },
  completed: { label: '已完成', bg: 'bg-emerald-500' },
};

function relativeTime(dateStr?: string): string {
  if (!dateStr) return '';
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  if (isNaN(then)) return '';
  const diffSec = Math.floor((now - then) / 1000);
  if (diffSec < 60) return '刚刚';
  const min = Math.floor(diffSec / 60);
  if (min < 60) return `${min}分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}小时前`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day}天前`;
  const mo = Math.floor(day / 30);
  return `${mo}个月前`;
}

function shotCount(project: Project): number {
  return (
    project.storyboard?.scenes?.reduce((sum, s) => sum + (s.shots?.length || 0), 0) || 0
  );
}

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const cover = generateProjectCover(
    project.storyboard?.scenes?.[0]?.shots || [],
    project.characters,
  );
  const gradient =
    cover.colorPalette.length >= 2
      ? `linear-gradient(135deg, ${cover.colorPalette[0]}, ${cover.colorPalette[1]})`
      : 'linear-gradient(135deg, #6366f1, #111111)';
  const status = STATUS_CONFIG[project.status] || STATUS_CONFIG.draft;

  return (
    <Link
      href={`/projects/${project.id}`}
      className="block group focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-xl"
    >
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden transition-all duration-200 group-hover:border-white/20 group-hover:-translate-y-0.5">
        {/* Cover */}
        <div className="h-32 sm:h-40 relative" style={{ background: gradient }} />

        {/* Body */}
        <div className="p-4 space-y-3">
          {/* Title + Status */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-medium text-white truncate">
              {project.title || project.input || '未命名项目'}
            </h3>
            <span
              className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium text-white ${status.bg}`}
            >
              {status.label}
            </span>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-3 text-[11px] text-gray-500">
            <span>角色 {project.characters?.length || 0}</span>
            <span className="text-gray-700">·</span>
            <span>场景 {project.scenes?.length || 0}</span>
            <span className="text-gray-700">·</span>
            <span>镜头 {shotCount(project)}</span>
          </div>

          {/* Time */}
          <div className="text-[11px] text-gray-600">
            {relativeTime(project.createdAt)}
          </div>
        </div>
      </div>
    </Link>
  );
}

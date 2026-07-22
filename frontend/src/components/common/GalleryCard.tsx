'use client';

import Link from 'next/link';
import type { Project } from '@/types/project';

interface Props {
  project: Project;
}

const STATUS_BADGE: Record<string, string> = {
  completed: 'bg-green-500/10 text-green-400',
  generating: 'bg-blue-500/10 text-blue-400',
  draft: 'bg-gray-500/10 text-gray-400',
};

export function GalleryCard({ project }: Props) {
  return (
    <Link
      href={`/projects/${project.id}`}
      className="block p-4 rounded-xl bg-white/[0.02] border border-white/10 hover:bg-white/[0.05] hover:border-white/20 transition-all duration-200 hover:-translate-y-0.5"
    >
      {/* Cover placeholder */}
      <div className="h-24 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 mb-3 flex items-center justify-center">
        <span className="text-3xl">🎬</span>
      </div>

      <h3 className="text-sm font-medium text-white truncate">{project.title || 'Untitled'}</h3>
      <div className="flex items-center gap-2 mt-1.5">
        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${STATUS_BADGE[project.status] || STATUS_BADGE.draft}`}>
          {project.status}
        </span>
        <span className="text-[10px] text-gray-600">
          {project.characters?.length || 0} chars · {project.scenes?.length || 0} scenes
        </span>
      </div>
    </Link>
  );
}

'use client';

import type { Project, StoryboardScene } from '@/types/project';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface Props {
  storyboard: Project['storyboard'];
}

export function StoryboardTimeline({ storyboard }: Props) {
  const [sceneIdx, setSceneIdx] = useState(0);
  const scenes = storyboard?.scenes || [];

  if (!scenes.length) return null;

  const scene = scenes[sceneIdx];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setSceneIdx(Math.max(0, sceneIdx - 1))}
          disabled={sceneIdx === 0}
          className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-gray-500"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-xs text-gray-400 font-medium">{scene.title || `Scene ${sceneIdx + 1}`}</span>
        <span className="text-[10px] text-gray-600">({scene.shots?.length || 0} shots)</span>
        <button
          onClick={() => setSceneIdx(Math.min(scenes.length - 1, sceneIdx + 1))}
          disabled={sceneIdx >= scenes.length - 1}
          className="p-1 rounded hover:bg-white/5 disabled:opacity-30 text-gray-500"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <div className="flex-1" />
        <span className="text-[10px] text-gray-600">{sceneIdx + 1}/{scenes.length}</span>
      </div>

      {/* Shot cards horizontal scroll */}
      <div className="overflow-x-auto pb-2">
        <div className="flex gap-3 min-w-min">
          {scene.shots?.map((shot, i) => (
            <div key={i} className="w-56 shrink-0 p-3 rounded-xl bg-white/[0.02] border border-white/10">
              <div className="flex items-center gap-1.5 mb-2">
                <span className="text-[10px] font-medium text-indigo-400">#{shot.shotNumber}</span>
                {shot.shotType && (
                  <span className="text-[9px] bg-indigo-500/10 text-indigo-300 rounded px-1.5 py-0.5">{shot.shotType}</span>
                )}
                {shot.cameraMove && (
                  <span className="text-[9px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{shot.cameraMove}</span>
                )}
                <span className="text-[9px] text-gray-600 ml-auto">{shot.duration}</span>
              </div>
              <p className="text-xs text-gray-300 line-clamp-3">{shot.description}</p>
              {shot.dialogue && shot.dialogue !== '-' && (
                <p className="text-[10px] text-gray-500 mt-1 italic border-l-2 border-indigo-500/20 pl-1.5">
                  &ldquo;{shot.dialogue}&rdquo;
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

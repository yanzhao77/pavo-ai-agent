'use client';

import type { Scene } from '@/types/project';
import { generateSceneThumbnail } from '@/common/assetGenerator';
import { useState } from 'react';

interface Props {
  scenes: Scene[];
}

export function ScenePreviewCard({ scenes }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!scenes?.length) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Scenes</h3>
      <div className="space-y-3">
        {scenes.map((s, i) => {
          const { gradient, tags } = generateSceneThumbnail(s.atmosphere || '', s.environment?.style || '');
          const isOpen = expanded === i;
          return (
            <div
              key={i}
              onClick={() => setExpanded(isOpen ? null : i)}
              className="rounded-xl overflow-hidden border border-white/10 cursor-pointer transition-all duration-200 hover:border-white/20"
            >
              {/* Gradient header */}
              <div className="h-20 relative" style={{ background: gradient }}>
                <div className="absolute inset-0 bg-black/30" />
                <div className="absolute bottom-2 left-3">
                  <p className="text-white font-semibold text-sm drop-shadow-lg">{s.name}</p>
                </div>
                <span className="absolute top-2 right-2 text-[10px] bg-black/40 text-white px-2 py-0.5 rounded-full">
                  #{i + 1}
                </span>
              </div>

              {/* Tags */}
              <div className="px-3 py-2 flex flex-wrap gap-1.5">
                <span className="text-[10px] text-gray-400 bg-white/5 rounded px-1.5 py-0.5">🕐 {s.timeOfDay}</span>
                {tags.map((t, j) => (
                  <span key={j} className="text-[10px] text-gray-400 bg-white/5 rounded px-1.5 py-0.5">{t}</span>
                ))}
                <span className="text-[10px] text-indigo-300 bg-indigo-500/10 rounded px-1.5 py-0.5">💡 {s.lighting?.type}</span>
              </div>

              {isOpen && (
                <div className="px-3 pb-3 border-t border-white/10 pt-2 text-xs text-gray-400 space-y-1">
                  <p><span className="text-gray-500">Atmosphere:</span> {s.atmosphere}</p>
                  {s.environment?.style && <p><span className="text-gray-500">Style:</span> {s.environment.style}</p>}
                  {s.lighting?.mood && <p><span className="text-gray-500">Light mood:</span> {s.lighting.mood}</p>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import type { Character } from '@/types/project';
import { generateCharacterAvatar } from '@/common/assetGenerator';

interface Props {
  characters: Character[];
}

export function CharacterImageWall({ characters }: Props) {
  const [selected, setSelected] = useState<Character | null>(null);

  if (!characters?.length) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Characters</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {characters.map((c, i) => {
          const { emoji, bgGradient } = generateCharacterAvatar(c.name, c.personality);
          return (
            <button
              key={i}
              onClick={() => setSelected(c)}
              className="group p-4 rounded-xl bg-white/[0.02] border border-white/10 hover:bg-white/[0.05] hover:border-white/20 transition-all duration-200 hover:-translate-y-0.5 text-left"
            >
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center text-xl mx-auto mb-3"
                style={{ background: bgGradient }}
              >
                {emoji}
              </div>
              <h4 className="font-medium text-white text-sm text-center">{c.name}</h4>
              <p className="text-[10px] text-gray-500 text-center mt-0.5">{c.age}岁 · {c.role}</p>
              {c.personality?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 justify-center">
                  {c.personality.map((t, j) => (
                    <span key={j} className="text-[9px] bg-indigo-500/10 text-indigo-300 rounded px-1.5 py-0.5">{t}</span>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Detail modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setSelected(null)}>
          <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl p-6 w-full max-w-sm mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center text-2xl"
                style={{ background: generateCharacterAvatar(selected.name, selected.personality).bgGradient }}
              >
                {generateCharacterAvatar(selected.name, selected.personality).emoji}
              </div>
              <div>
                <h3 className="text-white font-semibold">{selected.name}</h3>
                <p className="text-xs text-gray-500">{selected.role} · {selected.age}岁</p>
              </div>
            </div>
            <div className="space-y-2 text-sm text-gray-400">
              {selected.appearance?.build && <p><span className="text-gray-500">Build:</span> {selected.appearance.build}</p>}
              {selected.appearance?.face && <p><span className="text-gray-500">Face:</span> {selected.appearance.face}</p>}
              {selected.appearance?.clothing && <p><span className="text-gray-500">Clothing:</span> {selected.appearance.clothing}</p>}
              {selected.voice && <p><span className="text-gray-500">Voice:</span> {selected.voice}</p>}
              {selected.relationship && <p><span className="text-gray-500">Relation:</span> {selected.relationship}</p>}
            </div>
            {selected.personality?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {selected.personality.map((t, j) => (
                  <span key={j} className="text-[10px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{t}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

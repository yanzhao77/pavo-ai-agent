'use client';

import { useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { useProject } from '@/hooks/useProject';
import { Film, Users, MapPin, Package, Video, ChevronDown, ChevronUp, Copy, Check, Loader2, Download } from 'lucide-react';
import { projectService } from '@/services/project';
import type { Project, StoryboardScene, Character, Scene, Prop } from '@/types/project';

export function ResultPanel() {
  const { currentProjectId } = useProjectStore();
  const { data: project, isLoading } = useProject(currentProjectId);
  const [tab, setTab] = useState('storyboard');
  const [expandedScene, setExpandedScene] = useState<number | null>(0);
  const [copied, setCopied] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);

  if (isLoading) return <div className="flex-1 flex items-center justify-center"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>;
  if (!project) return <div className="flex-1 flex items-center justify-center"><p className="text-gray-500 text-sm">No project data</p></div>;

  const handleExport = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api'}/projects/${project.id}/export?format=markdown`);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${project.title || 'storyboard'}.md`;
      a.click();
    } catch {}
  };

  const handleRender = async () => {
    setRendering(true);
    try {
      await projectService.render(project.id);
    } catch {}
    setRendering(false);
  };

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const tabs = [
    { id: 'storyboard', label: 'Storyboard', icon: Film },
    { id: 'characters', label: 'Characters', icon: Users, count: project.characters?.length },
    { id: 'scenes', label: 'Scenes', icon: MapPin, count: project.scenes?.length },
    { id: 'props', label: 'Props', icon: Package, count: project.props?.length },
    { id: 'video', label: 'Video', icon: Video, count: project.videos?.length },
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Tab bar */}
      <div className="flex items-center gap-0.5 px-4 py-2 border-b border-white/10 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              tab === t.id ? 'bg-indigo-500/10 text-indigo-300' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span className="text-[10px] bg-white/5 text-gray-500 rounded-full px-1.5">{t.count}</span>
            )}
          </button>
        ))}
        <div className="flex-1" />
        <button onClick={handleExport} className="btn-ghost text-[10px] flex items-center gap-1 text-gray-500">
          <Download className="w-3 h-3" /> Export
        </button>
        <button onClick={handleRender} disabled={rendering} className="px-3 py-1 text-[10px] bg-indigo-500/20 text-indigo-300 rounded-lg hover:bg-indigo-500/30 disabled:opacity-50">
          {rendering ? 'Rendering...' : 'Render Video'}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tab === 'storyboard' && renderStoryboard(project, expandedScene, setExpandedScene, copyText, copied)}
        {tab === 'characters' && renderCharacters(project.characters)}
        {tab === 'scenes' && renderScenes(project.scenes)}
        {tab === 'props' && renderProps(project.props)}
        {tab === 'video' && (
          <div className="text-center text-gray-500 text-sm py-12">
            <Video className="w-8 h-8 mx-auto mb-2 text-gray-600" />
            <p>Video rendering available</p>
            <button onClick={handleRender} disabled={rendering} className="mt-3 px-4 py-2 bg-indigo-500 text-white rounded-lg text-xs">
              {rendering ? 'Rendering...' : 'Start Render'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function renderStoryboard(project: Project, expandedScene: number | null, setExpandedScene: (i: number|null) => void, copyText: (t: string, i: string) => void, copied: string|null) {
  const sb = project.storyboard;
  if (!sb?.scenes?.length) return <div className="text-center text-gray-500 text-sm py-12">Waiting for storyboard...</div>;

  return (
    <div className="space-y-3 max-w-3xl">
      <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
        <h2 className="font-semibold text-white text-sm">{sb.projectName || 'Untitled'}</h2>
        {sb.globalBGM && <p className="text-xs text-gray-500 mt-1">BGM: {sb.globalBGM}</p>}
      </div>
      {sb.scenes.map((scene: StoryboardScene, i: number) => (
        <div key={i} className="rounded-xl bg-white/[0.02] border border-white/10 overflow-hidden">
          <button onClick={() => setExpandedScene(expandedScene === i ? null : i)}
            className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors">
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-medium text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded">{scene.duration}</span>
              <span className="font-medium text-white text-sm">{scene.title}</span>
            </div>
            {expandedScene === i ? <ChevronUp className="w-4 h-4 text-gray-600" /> : <ChevronDown className="w-4 h-4 text-gray-600" />}
          </button>
          {expandedScene === i && (
            <div className="px-4 pb-4 space-y-3 border-t border-white/10 pt-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-[10px] text-gray-500 uppercase">Mood</span><p className="text-gray-300 mt-0.5">{scene.mood}</p></div>
                <div><span className="text-[10px] text-gray-500 uppercase">Music</span><p className="text-gray-300 mt-0.5">{scene.music}</p></div>
              </div>
              {scene.keyframe && (
                <div className="bg-white/[0.02] rounded-lg p-3">
                  <span className="text-[10px] text-gray-500 uppercase">Key Frame</span>
                  <p className="text-sm text-gray-300 mt-1">{scene.keyframe}</p>
                </div>
              )}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-gray-500 uppercase">Shots ({scene.shots?.length || 0})</span>
                  <button onClick={() => copyText(JSON.stringify(scene.shots, null, 2), `s-${i}`)}
                    className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300">
                    {copied === `s-${i}` ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />} Copy
                  </button>
                </div>
                <div className="space-y-2">
                  {scene.shots?.map((shot: any, j: number) => (
                    <div key={j} className="bg-white/[0.02] rounded-lg p-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-medium text-indigo-400">#{shot.shotNumber}</span>
                        {shot.shotType && <span className="text-[10px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{shot.shotType}</span>}
                        {shot.cameraMove && <span className="text-[10px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{shot.cameraMove}</span>}
                        <span className="text-[10px] text-gray-600 ml-auto">{shot.duration}</span>
                      </div>
                      <p className="text-sm text-gray-300 mt-1.5">{shot.description}</p>
                      {shot.dialogue && shot.dialogue !== '-' && (
                        <p className="text-gray-400 text-sm mt-1 italic border-l-2 border-indigo-500/30 pl-2">&ldquo;{shot.dialogue}&rdquo;</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function renderCharacters(characters?: Character[]) {
  if (!characters?.length) return <div className="text-center text-gray-500 text-sm py-12">No characters</div>;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {characters.map((c, i) => (
        <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
          <div className="flex items-center gap-2"><h3 className="font-semibold text-white text-sm">{c.name}</h3>
            <span className="text-[10px] text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded">{c.role}</span></div>
          <div className="mt-3 space-y-1 text-sm text-gray-400"><p><span className="text-gray-500">Age:</span> {c.age}</p>
            <p><span className="text-gray-500">Voice:</span> {c.voice}</p></div>
          {c.personality?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {c.personality.map((p, j) => (
                <span key={j} className="text-[10px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{p}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function renderScenes(scenes?: Scene[]) {
  if (!scenes?.length) return <div className="text-center text-gray-500 text-sm py-12">No scenes</div>;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {scenes.map((s, i) => (
        <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
          <h3 className="font-semibold text-white text-sm">{s.name}</h3>
          <span className="text-[10px] text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded mt-1 inline-block">{s.timeOfDay}</span>
          <div className="mt-3 space-y-1 text-sm text-gray-400">
            <p><span className="text-gray-500">Style:</span> {s.environment?.style}</p>
            <p><span className="text-gray-500">Lighting:</span> {s.lighting?.type} ({s.lighting?.mood})</p>
            <p><span className="text-gray-500">Atmosphere:</span> {s.atmosphere}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function renderProps(props?: Prop[]) {
  if (!props?.length) return <div className="text-center text-gray-500 text-sm py-12">No props</div>;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {props.map((p, i) => (
        <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white text-sm">{p.name}</h3>
            <span className="text-[10px] bg-white/5 text-gray-400 rounded px-1.5 py-0.5">{p.type}</span>
          </div>
          <div className="mt-3 space-y-1 text-sm text-gray-400">
            <p><span className="text-gray-500">Appearance:</span> {p.appearance}</p>
            {p.interaction && <p><span className="text-gray-500">Interaction:</span> {p.interaction}</p>}
            {p.significance && <p className="text-gray-600 italic mt-1 text-xs">{p.significance}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

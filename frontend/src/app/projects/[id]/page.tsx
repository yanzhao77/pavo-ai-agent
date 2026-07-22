'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useProject } from '@/hooks/useProject';
import { projectService } from '@/services/project';
import { Navbar } from '@/components/layout/Navbar';
import {
  ArrowLeft,
  Download,
  Video,
  Trash2,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  MapPin,
  Package,
  Film,
  Play,
} from 'lucide-react';
import type { Character, Scene, Prop, Storyboard, StoryboardScene, Shot } from '@/types/project';

/* ─── helpers ─────────────────────────────────────────────────── */

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'bg-gray-500' },
  generating: { label: '生成中', color: 'bg-blue-500' },
  completed: { label: '已完成', color: 'bg-emerald-500' },
};

const TABS = [
  { key: 'characters', label: '角色', icon: User },
  { key: 'scenes', label: '场景', icon: MapPin },
  { key: 'props', label: '道具', icon: Package },
  { key: 'storyboard', label: '故事板', icon: Film },
  { key: 'videos', label: '视频', icon: Play },
] as const;

type TabKey = (typeof TABS)[number]['key'];

/* ─── sub-components ─────────────────────────────────────────── */

function EmptyTab({ label }: { label: string }) {
  return (
    <div className="text-center py-16">
      <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-3">
        <Clock className="w-5 h-5 text-gray-600" />
      </div>
      <p className="text-sm text-gray-500">暂无{label}</p>
    </div>
  );
}

function CharactersTab({ characters }: { characters?: Character[] }) {
  if (!characters?.length) return <EmptyTab label="角色" />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {characters.map((c, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
              {c.name.charAt(0)}
            </div>
            <div>
              <h4 className="text-sm font-medium text-white">{c.name}</h4>
              <p className="text-[11px] text-gray-500">
                {c.role} · {c.age}岁
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            {c.appearance?.clothing || ''}
            {c.appearance?.distinctive ? ` · ${c.appearance.distinctive}` : ''}
          </p>
          {c.personality?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {c.personality.map((t, j) => (
                <span
                  key={j}
                  className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ScenesTab({ scenes }: { scenes?: Scene[] }) {
  if (!scenes?.length) return <EmptyTab label="场景" />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {scenes.map((s, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3"
        >
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-white">{s.name}</h4>
            <span className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full">
              {s.timeOfDay}
            </span>
          </div>
          <p className="text-xs text-gray-400">
            {s.environment?.type} · {s.environment?.style}
          </p>
          <div className="flex items-center gap-3 text-[11px] text-gray-500">
            <span>灯光: {s.lighting?.type}</span>
            <span>氛围: {s.atmosphere}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function PropsTab({ props: propsList }: { props?: Prop[] }) {
  if (!propsList?.length) return <EmptyTab label="道具" />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {propsList.map((p, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3"
        >
          <h4 className="text-sm font-medium text-white">{p.name}</h4>
          <span className="inline-block text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full">
            {p.type}
          </span>
          <p className="text-xs text-gray-400 leading-relaxed">
            {p.appearance}
          </p>
          {p.interaction && (
            <p className="text-xs text-gray-500">
              <span className="text-gray-600">交互: </span>
              {p.interaction}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function StoryboardTab({ storyboard }: { storyboard?: Storyboard | null }) {
  if (!storyboard?.scenes?.length) return <EmptyTab label="故事板" />;

  const allShots: { scene: StoryboardScene; shot: Shot }[] = [];
  storyboard.scenes.forEach((sc) => {
    sc.shots?.forEach((sh) => {
      allShots.push({ scene: sc, shot: sh });
    });
  });

  return (
    <div className="space-y-6">
      {storyboard.globalBGM && (
        <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 flex items-center gap-2 text-sm">
          <span className="text-gray-500">全局 BGM:</span>
          <span className="text-gray-300">{storyboard.globalBGM}</span>
        </div>
      )}

      {/* Shots as timeline cards */}
      <div className="space-y-3">
        {allShots.map(({ scene, shot }, i) => (
          <div
            key={i}
            className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2"
          >
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-indigo-400 font-medium">
                  #{shot.shotNumber}
                </span>
                <span className="text-gray-500">{shot.shotType}</span>
                <span className="text-gray-600">·</span>
                <span className="text-gray-500">{shot.cameraAngle}</span>
                {shot.cameraMove && (
                  <>
                    <span className="text-gray-600">·</span>
                    <span className="text-gray-500">{shot.cameraMove}</span>
                  </>
                )}
              </div>
              <span className="text-gray-600">{shot.duration}</span>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              {shot.description}
            </p>
            {shot.dialogue && (
              <p className="text-xs text-indigo-400/80 italic">
                &ldquo;{shot.dialogue}&rdquo;
              </p>
            )}
            {shot.characters?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {shot.characters.map((ch, j) => (
                  <span
                    key={j}
                    className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full"
                  >
                    {ch}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function VideosTab({ videos }: { videos?: any[] }) {
  if (!videos?.length) return <EmptyTab label="视频" />;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {videos.map((v, i) => (
        <div
          key={i}
          className="bg-white/5 border border-white/10 rounded-xl overflow-hidden"
        >
          {v.url && (
            <video
              src={v.url}
              controls
              className="w-full aspect-video bg-black"
              preload="metadata"
            />
          )}
          <div className="p-3 text-xs text-gray-500">
            {v.name || `视频 ${i + 1}`}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── page ───────────────────────────────────────────────────── */

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params?.id as string;

  const { checkAuth, isAuthenticated } = useAuthStore();
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState<TabKey>('characters');
  const [deleting, setDeleting] = useState(false);
  const [rendering, setRendering] = useState(false);

  // Auth guard
  useEffect(() => {
    const authed = checkAuth();
    if (!authed) {
      router.replace('/');
    } else {
      setReady(true);
    }
  }, []);

  const { data: project, isLoading, error } = useProject(ready ? id : null);

  const handleExport = useCallback(async () => {
    if (!project) return;
    const lines = [
      `# ${project.title || '项目导出'}`,
      `\n## 基本信息`,
      `状态: ${STATUS_LABEL[project.status]?.label || project.status}`,
      `创建时间: ${project.createdAt || ''}`,
      `\n## 角色`,
      ...(project.characters || []).map(
        (c: Character) => `- ${c.name} (${c.role}, ${c.age}岁) — ${c.personality?.join(', ') || ''}`,
      ),
      `\n## 场景`,
      ...(project.scenes || []).map(
        (s: Scene) => `- ${s.name} — ${s.environment?.type} / ${s.lighting?.type}`,
      ),
      `\n## 道具`,
      ...(project.props || []).map((p: Prop) => `- ${p.name} (${p.type})`),
      `\n## 故事板`,
      ...(project.storyboard?.scenes || []).flatMap((sc: StoryboardScene) =>
        (sc.shots || []).map(
          (sh: Shot) =>
            `- [${sh.shotNumber}] ${sh.shotType} — ${sh.description}`,
        ),
      ),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project.title || 'project'}_export.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [project]);

  const handleRender = useCallback(async () => {
    if (!id || rendering) return;
    setRendering(true);
    try {
      await projectService.render(id);
    } catch {
      // toast would go here
    }
    setRendering(false);
  }, [id, rendering]);

  const handleDelete = useCallback(async () => {
    if (!id || deleting) return;
    if (!confirm('确定要删除这个项目吗？此操作不可撤销。')) return;
    setDeleting(true);
    try {
      await projectService.delete(id);
      router.push('/projects');
    } catch {
      // toast would go here
    }
    setDeleting(false);
  }, [id, deleting]);

  if (!ready || isLoading) {
    return (
      <div className="min-h-screen bg-black text-white">
        <Navbar />
        <div className="flex items-center justify-center pt-32">
          <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-black text-white">
        <Navbar />
        <div className="text-center pt-32">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
          <p className="text-sm text-gray-400">项目加载失败</p>
          <button
            onClick={() => router.push('/projects')}
            className="mt-4 text-sm text-indigo-400 hover:text-indigo-300"
          >
            返回项目列表
          </button>
        </div>
      </div>
    );
  }

  const status = STATUS_LABEL[project.status] || STATUS_LABEL.draft;

  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 pt-24 pb-16">
        {/* Back + Title + Actions */}
        <div className="space-y-4">
          <button
            onClick={() => router.push('/projects')}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            返回项目列表
          </button>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">
                {project.title || project.input || '未命名项目'}
              </h1>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium text-white ${status.color}`}
              >
                {status.label}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleExport}
                className="px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 flex items-center gap-1.5 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                导出
              </button>
              <button
                onClick={handleRender}
                disabled={rendering}
                className="px-3 py-1.5 rounded-lg text-xs bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-700 disabled:cursor-wait text-white flex items-center gap-1.5 transition-colors"
              >
                {rendering ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Video className="w-3.5 h-3.5" />
                )}
                渲染
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-3 py-1.5 rounded-lg text-xs bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 disabled:opacity-40 flex items-center gap-1.5 transition-colors"
              >
                {deleting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
                删除
              </button>
            </div>
          </div>

          {/* Project stats */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>角色 {project.characters?.length || 0}</span>
            <span className="text-gray-700">·</span>
            <span>场景 {project.scenes?.length || 0}</span>
            <span className="text-gray-700">·</span>
            <span>道具 {project.props?.length || 0}</span>
            <span className="text-gray-700">·</span>
            <span>
              镜头{' '}
              {project.storyboard?.scenes?.reduce(
                (sum: number, s: any) => sum + (s.shots?.length || 0),
                0,
              ) || 0}
            </span>
            <span className="text-gray-700">·</span>
            <span>创建于 {project.createdAt ? new Date(project.createdAt).toLocaleDateString('zh-CN') : '—'}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-8 border-b border-white/10">
          <div className="flex gap-1 overflow-x-auto">
            {TABS.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors shrink-0 ${
                    tab === t.key
                      ? 'text-white border-indigo-500'
                      : 'text-gray-500 border-transparent hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab content */}
        <div className="mt-6">
          {tab === 'characters' && <CharactersTab characters={project.characters} />}
          {tab === 'scenes' && <ScenesTab scenes={project.scenes} />}
          {tab === 'props' && <PropsTab props={project.props} />}
          {tab === 'storyboard' && <StoryboardTab storyboard={project.storyboard} />}
          {tab === 'videos' && <VideosTab videos={project.videos} />}
        </div>
      </main>
    </div>
  );
}

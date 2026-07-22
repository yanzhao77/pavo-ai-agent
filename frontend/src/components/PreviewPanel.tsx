"use client";

import { useState } from "react";
import { Film, Users, MapPin, Package, Video, ListOrdered, ChevronDown, ChevronUp, Copy, Check, Loader2, Download } from "lucide-react";
import type { Project, StoryboardScene, Character, Scene, Prop } from "@/types/project";
import { VideoPanel } from "./VideoPanel";
import { Timeline } from "./Timeline";
import { renderProject as apiRenderProject, API_BASE, ApiError } from "@/lib/api";
import { useToast } from "./Toast";

interface PreviewPanelProps {
  project: Project | null;
  onProjectUpdate?: (p: Project) => void;
}

export function PreviewPanel({ project, onProjectUpdate }: PreviewPanelProps) {
  const handleExport = async () => {
    if (!project?.id) return;
    try {
      const res = await fetch(`${API_BASE}/projects/${project.id}/export?format=markdown`);
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${project.title || "storyboard"}.md`;
      a.click();
      addToast("success", "Exported as Markdown");
    } catch { addToast("error", "Export failed"); }
  };
  const [expandedScene, setExpandedScene] = useState<number | null>(0);
  const [copied, setCopied] = useState<string | null>(null);
  const [tab, setTab] = useState<"characters" | "scenes" | "props" | "storyboard" | "video" | "timeline">("storyboard");
  const [rendering, setRendering] = useState(false);
  const { addToast } = useToast();

  const handleRender = async () => {
    if (!project?.id) return;
    setRendering(true);
    try {
      const result = await apiRenderProject(project.id);
      if (onProjectUpdate) {
        onProjectUpdate({ ...project, videos: result.videos || [] });
      }
      addToast("success", `Video rendering complete: ${result.videos?.length || 0} shots`);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to render video";
      addToast("error", msg);
    }
    setRendering(false);
  };

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!project) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Film className="w-12 h-12 text-pavo-300 mx-auto mb-3" />
          <p className="text-pavo-400 text-sm">Enter a story idea to begin</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "storyboard" as const, label: "Storyboard", icon: Film },
    { id: "timeline" as const, label: "Timeline", icon: ListOrdered },
    { id: "characters" as const, label: "Characters", icon: Users, count: project.characters?.length },
    { id: "scenes" as const, label: "Scenes", icon: MapPin, count: project.scenes?.length },
    { id: "props" as const, label: "Props", icon: Package, count: project.props?.length },
    { id: "video" as const, label: "Video", icon: Video, count: project.videos?.length },
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Tab bar */}
      <div className="bg-white border-b border-pavo-100 px-4 lg:px-6 py-2 flex items-center gap-0.5 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              tab === t.id
                ? "bg-pavo-100 text-warm"
                : "text-pavo-400 hover:text-warm/70 hover:bg-pavo-50"
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span className="text-[10px] bg-pavo-200 text-warm/60 rounded-full px-1.5">{t.count}</span>
            )}
          </button>
        ))}
        <div className="flex-1" />
        {project.storyboard && (
          <>
            <button onClick={handleExport} className="btn-ghost text-xs flex items-center gap-1">
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export</span>
            </button>
            <button
              onClick={() => copyText(JSON.stringify(project.storyboard, null, 2), "all")}
              className="btn-ghost text-xs"
            >
              {copied === "all" ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        {tab === "storyboard" && renderStoryboard(project.storyboard, expandedScene, setExpandedScene, copyText, copied)}
        {tab === "characters" && renderCharacters(project.characters)}
        {tab === "scenes" && renderScenes(project.scenes)}
        {tab === "props" && renderProps(project.props)}
        {tab === "timeline" && project && (
          <Timeline
            project={project}
            onSave={async (updatedStoryboard) => {
              try {
                const res = await fetch(`${API_BASE}/projects/${project.id}`, {
                  method: "PATCH",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ storyboard: updatedStoryboard }),
                });
                if (!res.ok) throw new Error("Save failed");
                if (onProjectUpdate) onProjectUpdate({ ...project, storyboard: updatedStoryboard });
                addToast("success", "Timeline saved");
              } catch { addToast("error", "Failed to save timeline"); }
            }}
          />
        )}
        {tab === "video" && (
          <VideoPanel
            project={project}
            onRender={handleRender}
            rendering={rendering}
          />
        )}
      </div>
    </div>
  );
}

function renderStoryboard(
  storyboard: any,
  expandedScene: number | null,
  setExpandedScene: (i: number | null) => void,
  copyText: (text: string, id: string) => void,
  copied: string | null
) {
  if (!storyboard?.scenes?.length) {
    return <div className="text-center text-pavo-400 text-sm py-12">Waiting for storyboard generation...</div>;
  }

  return (
    <div className="space-y-3 max-w-3xl">
      <div className="card p-4">
        <h2 className="font-semibold text-warm">{storyboard.projectName || "Untitled"}</h2>
        {storyboard.globalBGM && (
          <p className="text-xs text-pavo-400 mt-1">BGM: {storyboard.globalBGM}</p>
        )}
      </div>
      {storyboard.scenes.map((scene: StoryboardScene, i: number) => (
        <div key={i} className="card overflow-hidden">
          <button
            onClick={() => setExpandedScene(expandedScene === i ? null : i)}
            className="w-full flex items-center justify-between p-4 hover:bg-pavo-50 transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-[11px] font-medium text-warm bg-pavo-100 px-2 py-0.5 rounded shrink-0">
                {scene.duration}
              </span>
              <span className="font-medium text-warm text-sm truncate">{scene.title}</span>
            </div>
            {expandedScene === i ? (
              <ChevronUp className="w-4 h-4 text-pavo-300 shrink-0" />
            ) : (
              <ChevronDown className="w-4 h-4 text-pavo-300 shrink-0" />
            )}
          </button>
          {expandedScene === i && (
            <div className="px-4 pb-4 space-y-3 border-t border-pavo-100 pt-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-[11px] font-medium text-pavo-400 uppercase">Mood</span>
                  <p className="text-warm mt-0.5">{scene.mood}</p>
                </div>
                <div>
                  <span className="text-[11px] font-medium text-pavo-400 uppercase">Music</span>
                  <p className="text-warm mt-0.5">{scene.music}</p>
                </div>
              </div>
              {scene.keyframe && (
                <div className="bg-pavo-50 rounded-lg p-3">
                  <span className="text-[11px] font-medium text-pavo-400 uppercase">Key Frame</span>
                  <p className="text-sm text-warm mt-1">{scene.keyframe}</p>
                </div>
              )}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-medium text-pavo-400 uppercase">
                    Shots ({scene.shots?.length || 0})
                  </span>
                  <button
                    onClick={() => copyText(JSON.stringify(scene.shots, null, 2), `scene-${i}`)}
                    className="flex items-center gap-1 text-xs text-pavo-400 hover:text-warm/70"
                  >
                    {copied === `scene-${i}` ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                    Copy
                  </button>
                </div>
                <div className="space-y-2">
                  {scene.shots?.map((shot: any, j: number) => (
                    <div key={j} className="bg-pavo-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-medium text-pavo-500">#{shot.shotNumber}</span>
                        {shot.shotType && (
                          <span className="text-[11px] bg-white text-warm/70 rounded px-1.5 py-0.5 border border-pavo-200">
                            {shot.shotType}
                          </span>
                        )}
                        {shot.cameraMove && (
                          <span className="text-[11px] bg-white text-warm/70 rounded px-1.5 py-0.5 border border-pavo-200">
                            {shot.cameraMove}
                          </span>
                        )}
                        {shot.cameraAngle && (
                          <span className="text-[11px] bg-white text-warm/70 rounded px-1.5 py-0.5 border border-pavo-200">
                            {shot.cameraAngle}
                          </span>
                        )}
                        <span className="text-[11px] text-pavo-400 ml-auto">{shot.duration}</span>
                      </div>
                      <p className="text-sm text-warm mt-1.5">{shot.description}</p>
                      {shot.dialogue && shot.dialogue !== "-" && (
                        <p className="text-warm/70 text-sm mt-1 italic border-l-2 border-pavo-300 pl-2">
                          &ldquo;{shot.dialogue}&rdquo;
                        </p>
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
  if (!characters?.length) {
    return <div className="text-center text-pavo-400 text-sm py-12">No characters generated yet</div>;
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {characters.map((c, i) => (
        <div key={i} className="card p-4">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-warm text-sm">{c.name}</h3>
            <span className="text-[11px] text-warm bg-pavo-100 px-2 py-0.5 rounded">{c.role}</span>
          </div>
          <div className="mt-3 space-y-1 text-sm text-warm/70">
            <p><span className="font-medium text-warm/90">Age:</span> {c.age}</p>
            <p><span className="font-medium text-warm/90">Voice:</span> {c.voice}</p>
          </div>
          {c.personality?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {c.personality.map((p, j) => (
                <span key={j} className="text-[11px] bg-pavo-100 text-warm/70 rounded px-1.5 py-0.5">{p}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function renderScenes(scenes?: Scene[]) {
  if (!scenes?.length) return <div className="text-center text-pavo-400 text-sm py-12">No scenes generated yet</div>;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {scenes.map((s, i) => (
        <div key={i} className="card p-4">
          <h3 className="font-semibold text-warm text-sm">{s.name}</h3>
          <span className="text-[11px] text-warm bg-pavo-100 px-2 py-0.5 rounded mt-1 inline-block">{s.timeOfDay}</span>
          <div className="mt-3 space-y-1 text-sm text-warm/70">
            <p><span className="font-medium text-warm/90">Style:</span> {s.environment?.style}</p>
            <p><span className="font-medium text-warm/90">Lighting:</span> {s.lighting?.type} ({s.lighting?.mood})</p>
            <p><span className="font-medium text-warm/90">Atmosphere:</span> {s.atmosphere}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function renderProps(props?: Prop[]) {
  if (!props?.length) return <div className="text-center text-pavo-400 text-sm py-12">No props generated yet</div>;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
      {props.map((p, i) => (
        <div key={i} className="card p-4">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-warm text-sm">{p.name}</h3>
            <span className="text-[11px] bg-pavo-100 text-warm/70 rounded px-1.5 py-0.5">{p.type}</span>
          </div>
          <div className="mt-3 space-y-1 text-sm text-warm/70">
            <p><span className="font-medium text-warm/90">Appearance:</span> {p.appearance}</p>
            {p.interaction && <p><span className="font-medium text-warm/90">Interaction:</span> {p.interaction}</p>}
            {p.significance && <p className="text-pavo-400 italic mt-1 text-xs">{p.significance}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

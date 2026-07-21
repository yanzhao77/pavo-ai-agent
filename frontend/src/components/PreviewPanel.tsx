"use client";

import { useState } from "react";
import { Film, Users, MapPin, Package, Video, ChevronDown, ChevronUp, Copy, Check, Loader2 } from "lucide-react";
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
  const [tab, setTab] = useState<"characters" | "scenes" | "props" | "storyboard" | "video">("storyboard");
  const [rendering, setRendering] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
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
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Film className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Enter a story idea to begin</p>
          <p className="text-gray-400 text-xs mt-1">The AI agent will generate characters, scenes, props, and a full storyboard</p>
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
    <div className="flex-1 flex flex-col bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
              tab === t.id ? "bg-blue-100 text-blue-700" : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
            {t.count !== undefined && t.count > 0 && (
              <span className="text-xs bg-gray-200 text-gray-600 rounded-full px-1.5">{t.count}</span>
            )}
          </button>
        ))}
        <div className="flex-1" />
        {project.storyboard && (
          <button
            onClick={() => copyText(JSON.stringify(project.storyboard, null, 2), "all")}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {copied === "all" ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            Copy All
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
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
    return <div className="text-center text-gray-400 text-sm py-12">Waiting for storyboard generation...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
        <h2 className="font-semibold text-gray-900">{storyboard.projectName || "Untitled"}</h2>
        <p className="text-sm text-gray-500 mt-1">BGM: {storyboard.globalBGM || "Not specified"}</p>
      </div>
      {storyboard.scenes.map((scene: StoryboardScene, i: number) => (
        <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <button
            onClick={() => setExpandedScene(expandedScene === i ? null : i)}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{scene.duration}</span>
              <span className="font-medium text-gray-900">{scene.title}</span>
            </div>
            {expandedScene === i ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>
          {expandedScene === i && (
            <div className="px-4 pb-4 space-y-3">
              <p className="text-sm text-gray-600"><span className="font-medium">Mood:</span> {scene.mood}</p>
              <p className="text-sm text-gray-600"><span className="font-medium">Music:</span> {scene.music}</p>
              {scene.keyframe && (
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">Key Frame</p>
                  <p className="text-sm text-gray-700">{scene.keyframe}</p>
                </div>
              )}
              <div className="space-y-2 mt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-500 uppercase">Shots ({scene.shots?.length || 0})</span>
                  <button
                    onClick={() => copyText(JSON.stringify(scene.shots, null, 2), `scene-${i}`)}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
                  >
                    {copied === `scene-${i}` ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                    Copy
                  </button>
                </div>
                {scene.shots?.map((shot: any, j: number) => (
                  <div key={j} className="bg-gray-50 rounded p-3 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-500">#{shot.shotNumber}</span>
                      <span className="text-xs bg-gray-200 text-gray-700 rounded px-1.5">{shot.shotType}</span>
                      <span className="text-xs bg-gray-200 text-gray-700 rounded px-1.5">{shot.cameraMove}</span>
                      <span className="text-xs bg-gray-200 text-gray-700 rounded px-1.5">{shot.cameraAngle}</span>
                      <span className="text-xs text-gray-400 ml-auto">{shot.duration}</span>
                    </div>
                    <p className="text-gray-700 mt-1">{shot.description}</p>
                    {shot.dialogue && shot.dialogue !== "-" && (
                      <p className="text-blue-600 mt-1 italic">&ldquo;{shot.dialogue}&rdquo;</p>
                    )}
                  </div>
                ))}
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
    return <div className="text-center text-gray-400 text-sm py-12">No characters generated yet</div>;
  }
  return (
    <div className="grid grid-cols-2 gap-4">
      {characters.map((c, i) => (
        <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <h3 className="font-semibold text-gray-900">{c.name}</h3>
          <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded mt-1 inline-block">{c.role} | {c.age}</span>
          <div className="mt-3 space-y-1 text-sm text-gray-600">
            <p><span className="font-medium">Build:</span> {c.appearance?.build}</p>
            <p><span className="font-medium">Face:</span> {c.appearance?.face}</p>
            <p><span className="font-medium">Clothing:</span> {c.appearance?.clothing}</p>
            <p><span className="font-medium">Voice:</span> {c.voice}</p>
          </div>
          {c.personality?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {c.personality.map((p, j) => (
                <span key={j} className="text-xs bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">{p}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function renderScenes(scenes?: Scene[]) {
  if (!scenes?.length) return <div className="text-center text-gray-400 text-sm py-12">No scenes generated yet</div>;
  return (
    <div className="grid grid-cols-2 gap-4">
      {scenes.map((s, i) => (
        <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <h3 className="font-semibold text-gray-900">{s.name}</h3>
          <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded mt-1 inline-block">{s.timeOfDay}</span>
          <div className="mt-3 space-y-1 text-sm text-gray-600">
            <p><span className="font-medium">Style:</span> {s.environment?.style}</p>
            <p><span className="font-medium">Lighting:</span> {s.lighting?.type} ({s.lighting?.mood})</p>
            <p><span className="font-medium">Atmosphere:</span> {s.atmosphere}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function renderProps(props?: Prop[]) {
  if (!props?.length) return <div className="text-center text-gray-400 text-sm py-12">No props generated yet</div>;
  return (
    <div className="grid grid-cols-2 gap-4">
      {props.map((p, i) => (
        <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{p.name}</h3>
            <span className="text-xs bg-purple-50 text-purple-600 rounded px-1.5 py-0.5">{p.type}</span>
          </div>
          <div className="mt-3 space-y-1 text-sm text-gray-600">
            <p><span className="font-medium">Appearance:</span> {p.appearance}</p>
            {p.interaction && <p><span className="font-medium">Interaction:</span> {p.interaction}</p>}
            {p.significance && <p className="text-gray-500 italic mt-2">{p.significance}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

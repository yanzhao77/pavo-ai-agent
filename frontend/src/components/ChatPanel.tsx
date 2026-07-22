"use client";

import { useState } from "react";
import { Send, Loader2, Sparkles, Wand2 } from "lucide-react";
import type { TraceEntry } from "@/types/project";

interface ChatPanelProps {
  onSend: (input: string) => void;
  loading: boolean;
  traceLog: TraceEntry[];
  hasProject: boolean;
}

const AGENT_LABELS: Record<string, string> = {
  planner: "Planning analysis",
  character: "Character design",
  scene: "Scene design",
  prop: "Prop design",
  storyboard: "Storyboard generation",
  reviewer: "Quality review",
  fixer: "Fixing issues",
  system: "System",
};

const MODES = [
  { id: "creative", label: "创意生成", icon: Sparkles },
  { id: "storyboard", label: "故事板", icon: Wand2 },
];

const EXAMPLES = [
  "A father comes home from work, his 5-year-old son brings him a foot basin",
  "A cyberpunk detective walks through neon-lit streets in the rain",
  "Time-lapse of a cherry blossom tree blooming over four seasons",
];

export function ChatPanel({ onSend, loading, traceLog, hasProject }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("creative");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
  };

  return (
    <div className="flex flex-col w-[400px] min-w-[320px] border-r border-pavo-100 bg-white">
      {/* Mode tabs */}
      {!hasProject && (
        <div className="flex gap-1 p-3 border-b border-pavo-100">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                mode === m.id
                  ? "bg-warm text-white"
                  : "text-warm/50 hover:text-warm/80 hover:bg-pavo-50"
              }`}
            >
              <m.icon className="w-3.5 h-3.5" />
              {m.label}
            </button>
          ))}
        </div>
      )}

      {/* Agent progress */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {!hasProject && !loading && traceLog.length === 0 && (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-pavo-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Wand2 className="w-6 h-6 text-warm/50" />
            </div>
            <p className="text-sm text-warm/60">Describe your video idea</p>
            <p className="text-xs text-pavo-400 mt-1">
              AI will generate characters, scenes, and storyboard
            </p>

            <div className="mt-6 space-y-2 text-left">
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setInput(ex)}
                  className="w-full text-left text-xs text-pavo-400 bg-pavo-50 rounded-lg px-3 py-2 hover:bg-pavo-100 transition-colors leading-relaxed"
                >
                  &ldquo;{ex}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}

        {traceLog.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-pavo-400 uppercase tracking-wider">
              Agent Progress
            </p>
            {traceLog.map((t, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 text-sm bg-pavo-50 rounded-lg p-3"
              >
                {t.status === "failed" ? (
                  <span className="w-2 h-2 rounded-full bg-red-400 mt-1.5 shrink-0" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-green-400 mt-1.5 shrink-0" />
                )}
                <div className="min-w-0">
                  <span className="font-medium text-warm text-xs">
                    {AGENT_LABELS[t.agent] || t.agent}
                  </span>
                  <p className="text-pavo-400 text-xs mt-0.5 truncate">{t.action}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-pavo-400 px-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                AI agents working...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-pavo-100">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={hasProject ? "New idea..." : "输入想法或剧本，和Pavo一起创作..."}
            className="input-base pr-12"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 w-9 h-9 bg-warm text-white rounded-lg hover:bg-warm/90 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

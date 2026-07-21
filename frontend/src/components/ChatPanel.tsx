"use client";

import { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import type { TraceEntry } from "@/types/project";

interface ChatPanelProps {
  onSend: (input: string) => void;
  loading: boolean;
  traceLog: TraceEntry[];
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

export function ChatPanel({ onSend, loading, traceLog }: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
  };

  return (
    <div className="flex flex-col w-[420px] min-w-[320px] border-r border-gray-200 bg-white">
      <div className="p-4 border-b border-gray-100">
        <h1 className="text-lg font-semibold text-gray-900">Pavo AI Agent</h1>
        <p className="text-sm text-gray-500 mt-0.5">AI Video Storyboard Generator</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-700">
          Describe your video idea. For example: <br />
          <span className="text-blue-500 mt-1 block">
            &ldquo;A father comes home from work, his 5-year-old son brings him a foot basin&rdquo;
          </span>
        </div>

        {traceLog.length > 0 && (
          <div className="space-y-2 mt-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Agent Progress</p>
            {traceLog.map((t, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                {t.status === "failed" ? (
                  <span className="w-2 h-2 rounded-full bg-red-400 mt-1.5 shrink-0" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-green-400 mt-1.5 shrink-0" />
                )}
                <div>
                  <span className="font-medium text-gray-700">{AGENT_LABELS[t.agent] || t.agent}</span>
                  <p className="text-gray-500 text-xs">{t.action}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your video story..."
            className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </form>
    </div>
  );
}

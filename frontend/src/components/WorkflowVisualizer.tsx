"use client";

import { useState, useEffect, useRef } from "react";

interface AgentState {
  name: string;
  displayName: string;
  status: "idle" | "running" | "completed" | "failed" | "skipped";
  durationMs: number;
  inputSummary: string;
  outputSummary: string;
  error: string | null;
}

const AGENTS: AgentState[] = [
  { name:"planner", displayName:"规划师", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"character", displayName:"角色", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"scene", displayName:"场景", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"prop", displayName:"道具", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"storyboard", displayName:"分镜", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"reviewer", displayName:"审查", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
  { name:"fixer", displayName:"修复", status:"idle", durationMs:0, inputSummary:"", outputSummary:"", error:null },
];

const STATUS_COLORS: Record<string, string> = {
  idle: "#9CA3AF", running: "#3B82F6", completed: "#10B981",
  failed: "#EF4444", skipped: "#D1D5DB",
};

const STATUS_LABELS: Record<string, string> = {
  idle: "等待中", running: "执行中", completed: "已完成",
  failed: "失败", skipped: "已跳过",
};

export default function WorkflowVisualizer({ traceLog, onProjectUpdate }: { traceLog: any[]; onProjectUpdate?: any }) {
  const [agents, setAgents] = useState<AgentState[]>(AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<AgentState | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!traceLog || traceLog.length === 0) return;
    const lastTrace = traceLog[traceLog.length - 1];
    if (lastTrace?.agent) {
      setAgents(prev => prev.map(a => {
        if (a.name === lastTrace.agent) {
          return {
            ...a,
            status: lastTrace.status === "passed" ? "completed" : "failed",
            durationMs: lastTrace.duration_ms || 0,
            inputSummary: lastTrace.input_summary || "",
            outputSummary: lastTrace.output_summary || "",
            error: lastTrace.error || null,
          };
        }
        return a;
      }));
    }
  }, [traceLog]);

  const totalDuration = agents.reduce((s, a) => s + a.durationMs, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Agent 管线执行状态</h3>

      {/* Pipeline Graph */}
      <div className="flex items-center justify-center gap-1 overflow-x-auto py-4">
        {AGENTS.map((agent, idx) => {
          const state = agents.find(a => a.name === agent.name)!;
          return (
            <div key={agent.name} className="flex items-center">
              {/* Node */}
              <button
                onClick={() => setSelectedAgent(state)}
                className="flex flex-col items-center gap-1 p-2 rounded-lg transition-all hover:shadow-md cursor-pointer min-w-[72px]"
                style={{ background: `${STATUS_COLORS[state.status]}15` }}
              >
                {/* Status icon */}
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                  style={{ background: STATUS_COLORS[state.status] }}
                >
                  {state.status === "completed" ? "✓" :
                   state.status === "running" ? "◉" :
                   state.status === "failed" ? "✗" :
                   state.status === "skipped" ? "—" : `${idx + 1}`}
                </div>
                <span className="text-xs font-medium text-gray-600">{agent.displayName}</span>
                {state.durationMs > 0 && (
                  <span className="text-[10px] text-gray-400">{(state.durationMs / 1000).toFixed(1)}s</span>
                )}
              </button>
              {/* Arrow */}
              {idx < AGENTS.length - 1 && (
                <div className="w-6 h-0.5 bg-gray-300 relative mx-1">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 border-4 border-transparent border-l-gray-300" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Timeline */}
      {totalDuration > 0 && (
        <div className="mt-3 space-y-1">
          <p className="text-[10px] text-gray-400">总耗时: {(totalDuration / 1000).toFixed(1)}s</p>
          <div className="h-4 bg-gray-100 rounded-full overflow-hidden flex">
            {agents.filter(a => a.durationMs > 0).map((a, i) => (
              <div
                key={a.name}
                className="h-full transition-all duration-500 first:rounded-l-full last:rounded-r-full"
                style={{
                  width: `${(a.durationMs / totalDuration) * 100}%`,
                  background: STATUS_COLORS[a.status],
                  opacity: 0.8,
                }}
                title={`${a.displayName}: ${(a.durationMs / 1000).toFixed(1)}s`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Detail Panel */}
      {selectedAgent && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg text-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="font-semibold text-gray-700">{selectedAgent.displayName} ({selectedAgent.name})</p>
              <p className="text-gray-500 mt-0.5">
                状态: {STATUS_LABELS[selectedAgent.status]}
                {selectedAgent.durationMs > 0 && ` · ${(selectedAgent.durationMs / 1000).toFixed(1)}s`}
              </p>
            </div>
            <button onClick={() => setSelectedAgent(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          {selectedAgent.inputSummary && (
            <p className="mt-2 text-gray-600">输入: {selectedAgent.inputSummary}</p>
          )}
          {selectedAgent.outputSummary && (
            <p className="text-gray-600">输出: {selectedAgent.outputSummary}</p>
          )}
          {selectedAgent.error && (
            <p className="mt-2 text-red-500 bg-red-50 p-1.5 rounded">错误: {selectedAgent.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

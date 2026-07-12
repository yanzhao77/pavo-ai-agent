"use client";

import { useState } from "react";
import { Film, Play, Loader2, AlertCircle } from "lucide-react";
import type { Project } from "@/types/project";

interface VideoPanelProps {
  project: Project;
  onRender: () => void;
  rendering: boolean;
}

export function VideoPanel({ project, onRender, rendering }: VideoPanelProps) {
  const videos = project.videos || [];

  return (
    <div className="space-y-4">
      {!project.storyboard && (
        <div className="text-center text-gray-400 text-sm py-12">
          Generate a storyboard first before rendering video
        </div>
      )}

      {project.storyboard && videos.length === 0 && !rendering && (
        <div className="text-center py-12">
          <Film className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Ready to render video</p>
          <p className="text-gray-400 text-xs mt-1">
            {project.storyboard?.scenes?.length || 0} scenes,{" "}
            {project.storyboard?.scenes?.reduce((a: number, s: any) => a + (s.shots?.length || 0), 0) || 0} shots
          </p>
          <button
            onClick={onRender}
            disabled={rendering}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
          >
            {rendering ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Rendering...</>
            ) : (
              <><Play className="w-4 h-4" /> Render Video</>
            )}
          </button>
        </div>
      )}

      {rendering && videos.length === 0 && (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Rendering video shots...</p>
          <p className="text-gray-400 text-xs mt-1">This may take a few minutes</p>
        </div>
      )}

      {videos.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-900">Generated Shots ({videos.length})</h3>
          {videos.map((v: any, i: number) => (
            <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Shot #{v.shot_number}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  v.status === "completed" ? "bg-green-50 text-green-600" :
                  v.status === "failed" ? "bg-red-50 text-red-600" :
                  "bg-yellow-50 text-yellow-600"
                }`}>
                  {v.status}
                </span>
              </div>
              {v.result?.url && (
                <video controls className="w-full rounded-lg bg-black max-h-48">
                  <source src={v.result.url} type="video/mp4" />
                </video>
              )}
              {v.error && (
                <p className="text-xs text-red-500 mt-1">{v.error}</p>
              )}
              {v.result && !v.result.url && (
                <pre className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded overflow-auto max-h-20">
                  {JSON.stringify(v.result, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useRef, useEffect } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { PreviewPanel } from "@/components/PreviewPanel";
import { ToastProvider, useToast } from "@/components/Toast";
import { CardSkeleton, StoryboardSkeleton } from "@/components/Skeleton";
import { AuthGuard, type AuthState } from "@/components/AuthGuard";
import { createProject, getProject as apiGetProject, API_BASE, ApiError } from "@/lib/api";
import type { Project } from "@/types/project";

function HomeContent({ auth }: { auth: AuthState }) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const { addToast } = useToast();

  const handleCreateProject = async (input: string) => {
    setLoading(true);
    try {
      const data = await createProject(input, auth.token, auth.userId);
      const projectId = data.projectId;
      setProject({
        id: projectId, status: "generating", input,
        characters: [], scenes: [], props: [], storyboard: null, traceLog: [],
      });
      connectSSE(projectId);
      addToast("success", "Project created! AI agents are working...");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to create project";
      addToast("error", msg);
      setLoading(false);
    }
  };

  const connectSSE = (projectId: string) => {
    if (eventSourceRef.current) eventSourceRef.current.close();
    const es = new EventSource(`${API_BASE}/projects/${projectId}/stream?token=${auth.token}`);
    eventSourceRef.current = es;
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "agent:complete") {
          es.close();
          fetchProject(projectId);
          addToast("info", "Generation complete!");
        }
      } catch {}
    };
    es.onerror = () => {
      es.close();
      setTimeout(() => fetchProject(projectId), 1000);
    };
  };

  const fetchProject = async (projectId: string) => {
    try {
      const data = await apiGetProject(projectId);
      setProject(data);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to fetch project";
      addToast("error", msg);
    }
    setLoading(false);
  };

  return (
        <div className="flex h-screen">
          <ChatPanel onSend={handleCreateProject} loading={loading} traceLog={project?.traceLog || []} />
          <PreviewPanel project={project} onProjectUpdate={setProject} />
        </div>
  );
}

export default function Home() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("pavo_token");
    const userId = localStorage.getItem("pavo_user_id");
    const username = localStorage.getItem("pavo_username");
    if (token && userId && username) {
      setAuth({ token, userId, username });
    }
    setChecking(false);
  }, []);

  if (checking) return null;
  if (!auth) return <AuthGuard onAuth={setAuth} />;

  return (
    <ToastProvider>
      <HomeContent auth={auth} />
    </ToastProvider>
  );
}

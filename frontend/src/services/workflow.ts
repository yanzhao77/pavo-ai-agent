const BASE = (typeof window !== 'undefined'
  ? process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api'
  : 'http://localhost:8000/api');

export const workflowService = {
  subscribeSSE: (projectId: string, token: string): EventSource =>
    new EventSource(`${BASE}/projects/${projectId}/stream?token=${token}`),

  getStatus: (projectId: string) =>
    fetch(`${BASE}/projects/${projectId}/tasks`).then((r) => r.json()),
};

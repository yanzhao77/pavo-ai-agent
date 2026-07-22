import api from './api';

export const projectService = {
  create: (input: string, userId?: string) =>
    api.post('/projects', { input, user_id: userId || '' }).then((r) => r.data),

  get: (id: string) =>
    api.get(`/projects/${id}`).then((r) => r.data),

  list: (userId?: string) =>
    api.get('/projects', { params: { user_id: userId } }).then((r) => r.data),

  update: (id: string, data: any) =>
    api.patch(`/projects/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/projects/${id}`).then((r) => r.data),

  regenerate: (id: string, module: string) =>
    api.post(`/projects/${id}/regenerate`, { module }).then((r) => r.data),

  render: (id: string) =>
    api.post(`/projects/${id}/render`).then((r) => r.data),
};

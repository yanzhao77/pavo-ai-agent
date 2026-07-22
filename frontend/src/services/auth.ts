import api from './api';

export const authService = {
  login: (username: string) =>
    api.post('/auth/login', { username }).then((r) => r.data),

  me: (token?: string) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    return api.get('/auth/me', { headers }).then((r) => r.data);
  },
};

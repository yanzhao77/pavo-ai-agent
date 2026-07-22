import axios from 'axios';

const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('pavo_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('pavo_token');
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

export default api;

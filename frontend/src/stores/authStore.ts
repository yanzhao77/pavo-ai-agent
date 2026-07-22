import { create } from 'zustand';
import { authService } from '@/services/auth';

interface AuthState {
  token: string | null;
  userId: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  userId: null,
  username: null,
  isAuthenticated: false,

  login: async (username: string) => {
    const data = await authService.login(username);
    localStorage.setItem('pavo_token', data.token);
    localStorage.setItem('pavo_user_id', data.user_id);
    localStorage.setItem('pavo_username', username);
    set({ token: data.token, userId: data.user_id, username, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('pavo_token');
    localStorage.removeItem('pavo_user_id');
    localStorage.removeItem('pavo_username');
    set({ token: null, userId: null, username: null, isAuthenticated: false });
  },

  checkAuth: () => {
    const token = localStorage.getItem('pavo_token');
    const userId = localStorage.getItem('pavo_user_id');
    const username = localStorage.getItem('pavo_username');
    if (token && userId && username) {
      set({ token, userId, username, isAuthenticated: true });
      return true;
    }
    return false;
  },
}));

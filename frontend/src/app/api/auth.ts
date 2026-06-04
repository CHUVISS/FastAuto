import { api } from './client';

export interface Token {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
}

export interface UserPublic {
  id: string;
  full_name: string;
  email: string;
  role: 'admin' | 'manager' | 'support' | 'user';
  status: 'active' | 'inactive' | 'banned';
  phone: string | null;
  created_at: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<Token>('/auth/login', { email, password }),

  register: (email: string, password: string, full_name: string) =>
    api.post<UserPublic>('/auth/register', { email, password, full_name }),

  me: () => api.get<UserPublic>('/auth/me'),

  logout: (refresh_token?: string) =>
    api.post<{ message: string }>('/auth/logout', refresh_token ? { refresh_token } : {}),

  refresh: (refresh_token: string) =>
    api.post<Token>('/auth/refresh', { refresh_token }),
};

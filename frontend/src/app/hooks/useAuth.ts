import { useState, useEffect, useCallback } from 'react';
import { authApi, type UserPublic } from '../api/auth';
import { dispatchFavoritesReload } from '../contexts/FavoritesContext';

export function useAuth() {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    authApi.me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token ?? '');
    const me = await authApi.me();
    setUser(me);
    dispatchFavoritesReload(); // загрузить избранное этого пользователя
    return me;
  }, []);

  const register = useCallback(async (email: string, password: string, full_name: string) => {
    await authApi.register(email, password, full_name);
    return login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    const refresh_token = localStorage.getItem('refresh_token') ?? '';
    await authApi.logout(refresh_token).catch(() => {});
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    dispatchFavoritesReload(); // очистить избранное (нет токена → setIds([]))
  }, []);

  return { user, loading, login, register, logout };
}
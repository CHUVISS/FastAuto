import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, HttpError } from '../api/client';

interface FavoritesContextValue {
  ids: string[];
  loading: boolean;
  isFavorite: (id: string) => boolean;
  toggle: (id: string) => void;
  clear: () => void;
}

const FavoritesContext = createContext<FavoritesContextValue>({
  ids: [],
  loading: false,
  isFavorite: () => false,
  toggle: () => {},
  clear: () => {},
});

/** Dispatch this event after login / logout to reload favorites from the server. */
export function dispatchFavoritesReload() {
  window.dispatchEvent(new Event('favorites:reload'));
}

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const [ids, setIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  /** Загружает избранное с сервера. Если пользователь не авторизован — очищает список. */
  const load = useCallback(async () => {
    if (!localStorage.getItem('access_token')) {
      setIds([]);
      return;
    }
    setLoading(true);
    try {
      const listings = await api.get<{ id: string }[]>('/favorites');
      setIds(listings.map(l => l.id));
    } catch {
      setIds([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // Перезагружаем при смене пользователя (после логина / логаута)
    window.addEventListener('favorites:reload', load);
    return () => window.removeEventListener('favorites:reload', load);
  }, [load]);

  const toggle = useCallback((id: string) => {
    if (!localStorage.getItem('access_token')) return;

    setIds(prev => {
      const wasFav = prev.includes(id);
      const next = wasFav ? prev.filter(x => x !== id) : [...prev, id];

      if (wasFav) {
        api.delete(`/favorites/${id}`).catch(() => {
          // Откат: возвращаем ID обратно
          setIds(cur => (cur.includes(id) ? cur : [...cur, id]));
        });
      } else {
        api.post('/favorites', { listing_id: id }).catch(err => {
          // При 404 листинг больше не существует — не откатываем
          const is404 = err instanceof HttpError && err.status === 404;
          if (!is404) {
            setIds(cur => cur.filter(x => x !== id));
          }
        });
      }

      return next;
    });
  }, []);

  const clear = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIds(current => {
        current.forEach(id => api.delete(`/favorites/${id}`).catch(() => {}));
        return [];
      });
    } else {
      setIds([]);
    }
  }, []);

  const isFavorite = useCallback((id: string) => ids.includes(id), [ids]);

  return (
    <FavoritesContext.Provider value={{ ids, loading, isFavorite, toggle, clear }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  return useContext(FavoritesContext);
}

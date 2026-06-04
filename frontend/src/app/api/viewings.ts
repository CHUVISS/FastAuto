import { api } from './client';

export interface ViewingWindow {
  id: string;
  listing_id: string;
  window_date: string;
  time_from: string;
  time_to: string;
  is_available: boolean;
  created_at: string;
}

export const viewingsApi = {
  /** Получить окна просмотра для объявления */
  getAvailableSlots: (listingId: string) =>
    api.get<ViewingWindow[]>(`/listings/${listingId}/viewing-windows`),

  /** Создать окно просмотра (для продавца при создании объявления) */
  createWindow: (
    listingId: string,
    body: { window_date: string; time_from: string; time_to: string }
  ) => api.post<ViewingWindow>(`/listings/${listingId}/viewing-windows`, body),

  /** Удалить окно просмотра */
  deleteWindow: (listingId: string, windowId: string) =>
    api.delete<{ deleted: boolean }>(
      `/listings/${listingId}/viewing-windows/${windowId}`
    ),

  /** Установить расписание просмотров (template-based) */
  setSchedule: (
    listingId: string,
    body: {
      template: { weekday: number; time_from: string; time_to: string }[];
      repeat_weekly: boolean;
    }
  ) => api.put<{ generated: number }>(`/listings/${listingId}/viewing-schedule`, body),
};

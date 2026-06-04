import { api } from './client';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export const notificationsApi = {
  list: (unreadOnly = false) =>
    api.get<Notification[]>(`/notifications${unreadOnly ? '?unread=true' : ''}`),

  markRead: (id: string) =>
    api.post<{ read: boolean }>(`/notifications/${id}/read`, {}),

  markAllRead: () =>
    api.post<{ marked_read: number }>('/notifications/read-all', {}),
};

const LABELS: Record<string, string> = {
  reservation_outcome_marked:    'Результат сделки отмечен',
  reservation_cancelled_by_buyer:'Покупатель отменил бронь',
  reservation_declined_by_seller:'Продавец отклонил бронь',
};

export function notificationText(n: Notification): string {
  const base = LABELS[n.type] ?? n.type.replace(/_/g, ' ');
  const outcome = n.payload?.outcome as string | undefined;
  if (n.type === 'reservation_outcome_marked' && outcome) {
    return outcome === 'sold' ? 'Сделка состоялась' : 'Сделка не состоялась';
  }
  const reason = n.payload?.reason as string | undefined;
  if (n.type === 'reservation_declined_by_seller' && reason) {
    return `${base}: ${reason}`;
  }
  return base;
}

export function notificationHref(_n: Notification): string {
  return '/profile?tab=reservations';
}

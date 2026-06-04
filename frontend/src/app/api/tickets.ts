import { api } from './client';

export type TicketType =
  | 'purchase_dispute'    // Спор по сделке
  | 'listing_report'      // Жалоба на объявление
  | 'moderation_appeal'   // Апелляция модерации
  | 'support_inquiry';    // Общий вопрос поддержки

export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed';

export const TICKET_TYPE_LABELS: Record<TicketType, string> = {
  purchase_dispute: 'Спор по сделке',
  listing_report: 'Жалоба на объявление',
  moderation_appeal: 'Апелляция модерации',
  support_inquiry: 'Вопрос поддержки',
};

export const TICKET_STATUS_LABELS: Record<TicketStatus, string> = {
  open: 'Открыт',
  in_progress: 'В работе',
  resolved: 'Решён',
  closed: 'Закрыт',
};

export const TICKET_STATUS_COLORS: Record<TicketStatus, string> = {
  open: 'bg-primary/10 text-primary',
  in_progress: 'bg-yellow-500/10 text-yellow-600',
  resolved: 'bg-accent/10 text-accent',
  closed: 'bg-muted text-muted-foreground',
};

export interface Ticket {
  id: string;
  type: TicketType;
  status: TicketStatus;
  creator_id: string;
  assignee_id: string | null;
  listing_id: string | null;
  reservation_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_id: string;
  body: string;
  created_at: string;
}

export interface TicketDetail {
  ticket: Ticket;
  messages: TicketMessage[];
}

export interface TicketCreateData {
  type: TicketType;
  title: string;
  listing_id?: string;
  reservation_id?: string;
}

export const ticketsApi = {
  /** Создать тикет */
  create: (data: TicketCreateData) =>
    api.post<Ticket>('/tickets', data),

  /** Мои тикеты */
  my: () =>
    api.get<Ticket[]>('/tickets/my'),

  /** Тикет с сообщениями */
  get: (id: string) =>
    api.get<TicketDetail>(`/tickets/${id}`),

  /** Добавить сообщение в тикет */
  addMessage: (ticket_id: string, body: string) =>
    api.post<TicketMessage>(`/tickets/${ticket_id}/messages`, { body }),
};

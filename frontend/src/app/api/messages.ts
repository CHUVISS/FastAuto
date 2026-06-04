import { api } from './client';

export type MessageType = 'inquiry' | 'callback' | 'general';

export interface MessageCreate {
  name: string;
  email: string;
  phone?: string;
  subject?: string;
  body: string;
  message_type?: MessageType;
  car_id?: string;
}

export interface MessagePublic {
  id: string;
  type: string;
  status: string;
  title: string;
  listing_id: string | null;
  created_at: string;
}

export const messagesApi = {
  send: (data: MessageCreate) =>
    api.post<MessagePublic>('/tickets', {
      type: 'support_inquiry',
      title: data.subject || data.body.slice(0, 200),
      listing_id: data.car_id || undefined,
    }),
};

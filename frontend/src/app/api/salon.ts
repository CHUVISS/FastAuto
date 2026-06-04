import { api } from './client';

export interface WorkingHoursEntry {
  days: string;
  hours: string;
}

export interface SalonInfo {
  address: string;
  working_hours: WorkingHoursEntry[];
  phone: string;
  map_url?: string;
}

const DEFAULT_SALON_INFO: SalonInfo = {
  address: 'г. Москва, ул. Автомобильная, д. 1',
  phone: '+7 (900) 123-45-67',
  working_hours: [
    { days: 'Пн–Пт', hours: '9:00–20:00' },
    { days: 'Сб–Вс', hours: '10:00–18:00' },
  ],
};

export const salonApi = {
  // TODO: подключить endpoint когда бэк будет готов — GET /salon/info
  getInfo: async (): Promise<SalonInfo> => {
    try {
      return await api.get<SalonInfo>('/salon/info');
    } catch {
      return DEFAULT_SALON_INFO;
    }
  },
};

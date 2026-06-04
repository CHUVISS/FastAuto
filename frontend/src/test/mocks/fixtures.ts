import type { Notification } from '../../app/api/notifications';
import type { Reservation } from '../../app/api/reservations';
import type { Car } from '../../app/api/cars';

export const mockUser = {
  id: 'user-1',
  full_name: 'Иван Иванов',
  email: 'ivan@example.com',
  role: 'user' as const,
  status: 'active' as const,
  phone: '+79001234567',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockSeller = {
  id: 'seller-2',
  full_name: 'Пётр Продавцов',
  email: 'seller@example.com',
  role: 'user' as const,
  status: 'active' as const,
  phone: '+79009876543',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockNotifications: Notification[] = [
  {
    id: 'notif-1',
    user_id: 'user-1',
    type: 'reservation_outcome_marked',
    payload: { outcome: 'sold' },
    read_at: null,
    created_at: '2024-01-10T12:00:00Z',
  },
  {
    id: 'notif-2',
    user_id: 'user-1',
    type: 'reservation_cancelled_by_buyer',
    payload: {},
    read_at: '2024-01-11T08:00:00Z',
    created_at: '2024-01-11T07:00:00Z',
  },
  {
    id: 'notif-3',
    user_id: 'user-1',
    type: 'reservation_declined_by_seller',
    payload: { reason: 'Автомобиль уже продан' },
    read_at: null,
    created_at: '2024-01-12T09:00:00Z',
  },
];

export const mockReservation: Reservation = {
  id: 'res-1',
  listing_id: 'listing-1',
  buyer_id: 'user-1',
  seller_id: 'seller-2',
  deposit_amount: 5000,
  yk_payment_id: null,
  status: 'pending_payment',
  outcome: null,
  outcome_set_by: null,
  outcome_set_at: null,
  cancel_reason: null,
  payment_deadline: '2024-01-20T12:00:00Z',
  hold_deadline: '2024-01-27T12:00:00Z',
  correction_deadline: null,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
};

export const mockActiveReservation: Reservation = {
  ...mockReservation,
  id: 'res-2',
  status: 'active',
  yk_payment_id: 'yk-pay-123',
  seller_phone: '+79009876543',
  sale_address: 'г. Москва, ул. Ленина, 1',
};

export const mockCar: Car = {
  id: 'listing-1',
  brand: 'Toyota',
  model: 'Camry',
  year: 2022,
  price: 2500000,
  mileage: 30000,
  vin: 'JT2BF22K1W0122497',
  color: 'white',
  fuel_type: 'petrol',
  transmission: 'automatic',
  body_type: 'sedan',
  engine_volume: '2.5',
  engine_power: 181,
  description: 'Хорошее состояние, один владелец',
  condition: 'used',
  city_name: 'Москва',
  city_id: 'moscow',
  status: 'available',
  created_at: '2024-01-01T00:00:00Z',
  images: [
    {
      id: 'img-1',
      url: 'http://localhost:8000/uploads/cars/img-1.jpg',
      thumbnail_url: 'http://localhost:8000/uploads/cars/img-1-thumb.jpg',
      is_primary: true,
      sort_order: 0,
    },
  ],
  seller_name: 'Пётр Продавцов',
  seller_phone: '+79009876543',
  sale_address: 'г. Москва, ул. Ленина, 1',
  viewing_enabled: true,
  accepts_cash: true,
  accepts_transfer: false,
};

export const mockCarNoImages: Car = {
  ...mockCar,
  id: 'listing-2',
  brand: 'BMW',
  model: 'X5',
  year: 2020,
  price: 4500000,
  images: [],
  seller_phone: null,
  sale_address: null,
};

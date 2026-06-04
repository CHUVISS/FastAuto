/**
 * Unit: notificationText
 * Mirrors: test_reservation_model_short.py — domain model text derivation
 */
import { describe, it, expect } from 'vitest';
import { notificationText, type Notification } from '../../app/api/notifications';

function makeNotif(overrides: Partial<Notification>): Notification {
  return {
    id: 'n-1',
    user_id: 'user-1',
    type: 'reservation_outcome_marked',
    payload: {},
    read_at: null,
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('notificationText', () => {
  it('returns "Сделка состоялась" for outcome sold', () => {
    const n = makeNotif({ type: 'reservation_outcome_marked', payload: { outcome: 'sold' } });
    expect(notificationText(n)).toBe('Сделка состоялась');
  });

  it('returns "Сделка не состоялась" for outcome not_sold', () => {
    const n = makeNotif({ type: 'reservation_outcome_marked', payload: { outcome: 'not_sold' } });
    expect(notificationText(n)).toBe('Сделка не состоялась');
  });

  it('returns base label for buyer cancellation', () => {
    const n = makeNotif({ type: 'reservation_cancelled_by_buyer', payload: {} });
    expect(notificationText(n)).toBe('Покупатель отменил бронь');
  });

  it('appends reason for seller decline', () => {
    const n = makeNotif({
      type: 'reservation_declined_by_seller',
      payload: { reason: 'Уже продан' },
    });
    expect(notificationText(n)).toBe('Продавец отклонил бронь: Уже продан');
  });

  it('falls back to humanised type for unknown notification types', () => {
    const n = makeNotif({ type: 'some_new_event', payload: {} });
    expect(notificationText(n)).toBe('some new event');
  });

  it('returns base label for seller decline without reason', () => {
    const n = makeNotif({ type: 'reservation_declined_by_seller', payload: {} });
    expect(notificationText(n)).toBe('Продавец отклонил бронь');
  });
});

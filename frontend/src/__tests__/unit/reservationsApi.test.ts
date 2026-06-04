/**
 * Unit: reservationsApi
 * Mirrors: test_booking_service_short.py — booking/reservation service calls
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { reservationsApi } from '../../app/api/reservations';

describe('reservationsApi', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  it('my() returns an array of reservations', async () => {
    const result = await reservationsApi.my();
    expect(Array.isArray(result)).toBe(true);
    expect(result[0]).toMatchObject({ id: 'res-1', status: 'pending_payment' });
  });

  it('get() returns a single reservation by id', async () => {
    const result = await reservationsApi.get('res-1');
    expect(result.id).toBe('res-1');
    expect(result.buyer_id).toBe('user-1');
  });

  it('reserve() returns reservation_id and payment_url', async () => {
    const result = await reservationsApi.reserve('listing-1');
    expect(result.reservation_id).toBe('res-1');
    expect(result.payment_url).toContain('yookassa.ru');
  });

  it('markOutcome() sends outcome and returns updated status', async () => {
    const result = await reservationsApi.markOutcome('res-1', 'sold');
    expect(result.outcome).toBe('sold');
  });
});

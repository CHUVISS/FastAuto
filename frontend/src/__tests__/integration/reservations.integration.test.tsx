/**
 * Integration: reservations API
 * Mirrors: test_dashboard_integration_short.py — reservation listing and state transitions
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { reservationsApi } from '../../app/api/reservations';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

const BASE = 'http://localhost:8000/api/v1';

describe('Reservations integration', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  it('my() returns reservations list for authenticated user', async () => {
    const result = await reservationsApi.my();
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]).toMatchObject({
      id: 'res-1',
      buyer_id: 'user-1',
      status: 'pending_payment',
    });
  });

  it('active reservation includes seller_phone and sale_address', async () => {
    const result = await reservationsApi.get('res-2');
    expect(result.status).toBe('active');
    expect(result.seller_phone).toBeTruthy();
    expect(result.sale_address).toBeTruthy();
  });

  it('markOutcome() transitions reservation to settling status', async () => {
    server.use(
      http.post(`${BASE}/reservations/:id/outcome`, () =>
        HttpResponse.json({ status: 'settling', outcome: 'sold' })
      )
    );
    const result = await reservationsApi.markOutcome('res-2', 'sold');
    expect(result.status).toBe('settling');
    expect(result.outcome).toBe('sold');
  });
});

/**
 * Business process: Viewing booking and outcome marking flow
 * Mirrors: test_viewing_process_short.py
 *
 * Flow: active reservation → both parties mark outcome → reservation completes
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { reservationsApi } from '../../app/api/reservations';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

const BASE = 'http://localhost:8000/api/v1';

describe('Viewing booking process', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  it('buyer marks outcome "sold" → reservation moves to settling', async () => {
    server.use(
      http.post(`${BASE}/reservations/:id/outcome`, () =>
        HttpResponse.json({ status: 'settling', outcome: 'sold' })
      )
    );
    const result = await reservationsApi.markOutcome('res-2', 'sold');
    expect(result.status).toBe('settling');
    expect(result.outcome).toBe('sold');
  });

  it('second party marks same outcome → reservation completes', async () => {
    server.use(
      http.post(`${BASE}/reservations/:id/outcome`, () =>
        HttpResponse.json({ status: 'completed', outcome: 'sold' })
      ),
      http.get(`${BASE}/reservations/:id`, () =>
        HttpResponse.json({
          id: 'res-2',
          listing_id: 'listing-1',
          buyer_id: 'user-1',
          seller_id: 'seller-2',
          deposit_amount: 5000,
          yk_payment_id: 'yk-pay-123',
          status: 'completed',
          outcome: 'sold',
          outcome_set_by: null,
          outcome_set_at: '2024-02-01T10:00:00Z',
          cancel_reason: null,
          payment_deadline: '2024-01-20T12:00:00Z',
          hold_deadline: '2024-01-27T12:00:00Z',
          correction_deadline: null,
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-02-01T10:00:00Z',
          seller_phone: '+79009876543',
          sale_address: 'г. Москва, ул. Ленина, 1',
        })
      )
    );

    await reservationsApi.markOutcome('res-2', 'sold');
    const final = await reservationsApi.get('res-2');
    expect(final.status).toBe('completed');
    expect(final.outcome).toBe('sold');
  });
});

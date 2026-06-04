/**
 * Business process: Reservation purchase flow
 * Mirrors: test_reservation_purchase_process_short.py
 *
 * Flow: User browses catalog → views listing → creates reservation → pays deposit
 * Tests the full happy-path through API layer with MSW intercepts.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { carsApi } from '../../app/api/cars';
import { reservationsApi } from '../../app/api/reservations';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

const BASE = 'http://localhost:8000/api/v1';

describe('Reservation purchase process', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  it('buyer can view listing details before booking', async () => {
    const car = await carsApi.get('listing-1');
    expect(car.status).toBe('available');
    expect(car.price).toBeGreaterThan(0);
    expect(car.images.length).toBeGreaterThan(0);
  });

  it('buyer creates reservation and receives payment URL', async () => {
    const response = await reservationsApi.reserve('listing-1');
    expect(response.reservation_id).toBeTruthy();
    expect(response.payment_url).toContain('yookassa.ru');
  });

  it('after payment, active reservation exposes seller contacts', async () => {
    server.use(
      http.post(`${BASE}/reservations`, () =>
        HttpResponse.json({ reservation_id: 'res-2', payment_url: null })
      )
    );
    const reserve = await reservationsApi.reserve('listing-1');
    const detail = await reservationsApi.get(reserve.reservation_id);

    expect(detail.status).toBe('active');
    expect(detail.seller_phone).toBeTruthy();
    expect(detail.sale_address).toBeTruthy();
  });
});

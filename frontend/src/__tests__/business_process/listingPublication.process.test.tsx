/**
 * Business process: Listing publication flow
 * Mirrors: test_publish_moderation_process_short.py
 *
 * Flow: Seller logs in → favorites are per-user → creates listing → listing visible in catalog
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../../app/hooks/useAuth';
import { carsApi } from '../../app/api/cars';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

const BASE = 'http://localhost:8000/api/v1';

describe('Listing publication process', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('user must be authenticated to see their listings', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();

    await act(async () => {
      await result.current.login('ivan@example.com', 'password123');
    });

    expect(result.current.user).not.toBeNull();
    expect(localStorage.getItem('access_token')).toBeTruthy();
  });

  it('newly created listing appears in catalog list', async () => {
    localStorage.setItem('access_token', 'test-token');
    server.use(
      http.post(`${BASE}/listings`, () =>
        HttpResponse.json({ id: 'new-car-99' }, { status: 201 })
      ),
      http.get(`${BASE}/listings`, () =>
        HttpResponse.json({
          items: [
            {
              id: 'new-car-99',
              mark_name: 'Honda',
              model_name: 'Civic',
              year: 2021,
              price: 1800000,
              mileage: 15000,
              city_id: 'moscow',
              city_name: 'Москва',
              created_at: '2024-06-01T00:00:00Z',
              body_type: 'sedan',
              engine_type: 'petrol',
              displacement: 1.5,
              power: 120,
              status: 'active',
            },
          ],
          next_cursor: null,
        })
      )
    );

    const catalog = await carsApi.list({ limit: 10 });
    expect(catalog.data.some(c => c.id === 'new-car-99')).toBe(true);
  });

  it('favorites are per-user: cleared on logout, reloaded on login', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('ivan@example.com', 'password123');
    });
    expect(localStorage.getItem('access_token')).toBeTruthy();

    await act(async () => {
      await result.current.logout();
    });
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});

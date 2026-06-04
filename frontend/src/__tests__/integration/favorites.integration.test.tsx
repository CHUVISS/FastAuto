/**
 * Integration: favorites CRUD
 * Mirrors: test_favorites_integration_short.py — add/remove favorites via API
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FavoritesProvider, useFavorites } from '../../app/contexts/FavoritesContext';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

const BASE = 'http://localhost:8000/api/v1';

function FavoritesWidget() {
  const { ids, toggle, loading } = useFavorites();
  return (
    <div>
      {loading && <span data-testid="loading">loading</span>}
      <span data-testid="ids">{ids.join(',')}</span>
      <button onClick={() => toggle('car-123')}>toggle car-123</button>
    </div>
  );
}

describe('Favorites integration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('loads favorites from server on mount when authenticated', async () => {
    localStorage.setItem('access_token', 'test-token');
    server.use(
      http.get(`${BASE}/favorites`, () =>
        HttpResponse.json([{ id: 'car-abc' }, { id: 'car-xyz' }])
      )
    );

    render(
      <FavoritesProvider>
        <FavoritesWidget />
      </FavoritesProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('ids').textContent).toContain('car-abc');
    });
    expect(screen.getByTestId('ids').textContent).toContain('car-xyz');
  });

  it('toggle adds car then removes it, reflecting server round-trip', async () => {
    localStorage.setItem('access_token', 'test-token');

    render(
      <FavoritesProvider>
        <FavoritesWidget />
      </FavoritesProvider>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('loading')).toBeNull();
    });

    // Add
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle car-123' }));
    });
    expect(screen.getByTestId('ids').textContent).toContain('car-123');

    // Remove
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle car-123' }));
    });
    expect(screen.getByTestId('ids').textContent).not.toContain('car-123');
  });
});

/**
 * Unit: FavoritesContext
 * Mirrors: test_favorites_model_short.py — favorites state management
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FavoritesProvider, useFavorites } from '../../app/contexts/FavoritesContext';

function TestConsumer() {
  const { ids, isFavorite, toggle, clear } = useFavorites();
  return (
    <div>
      <span data-testid="count">{ids.length}</span>
      <span data-testid="is-fav-car1">{isFavorite('car-1') ? 'yes' : 'no'}</span>
      <button onClick={() => toggle('car-1')}>toggle</button>
      <button onClick={() => clear()}>clear</button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <FavoritesProvider>
      <TestConsumer />
    </FavoritesProvider>
  );
}

describe('FavoritesContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts with empty favorites when not authenticated', async () => {
    renderWithProvider();
    await waitFor(() => {
      expect(screen.getByTestId('count').textContent).toBe('0');
    });
  });

  it('optimistically adds a favorite on toggle (authenticated)', async () => {
    localStorage.setItem('access_token', 'test-token');
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId('is-fav-car1').textContent).toBe('no');
    });

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
    });

    expect(screen.getByTestId('is-fav-car1').textContent).toBe('yes');
  });

  it('toggle removes an existing favorite', async () => {
    localStorage.setItem('access_token', 'test-token');
    renderWithProvider();

    // Add
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
    });
    expect(screen.getByTestId('is-fav-car1').textContent).toBe('yes');

    // Remove
    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
    });
    expect(screen.getByTestId('is-fav-car1').textContent).toBe('no');
  });

  it('clear empties all favorites', async () => {
    localStorage.setItem('access_token', 'test-token');
    renderWithProvider();

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
    });
    expect(screen.getByTestId('count').textContent).toBe('1');

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'clear' }));
    });
    expect(screen.getByTestId('count').textContent).toBe('0');
  });

  it('does not toggle when not authenticated', async () => {
    renderWithProvider();

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'toggle' }));
    });
    expect(screen.getByTestId('is-fav-car1').textContent).toBe('no');
  });
});

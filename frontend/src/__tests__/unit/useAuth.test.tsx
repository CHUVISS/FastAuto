/**
 * Unit: useAuth hook
 * Mirrors: test_reservation_service_short.py — service-layer state management
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../../app/hooks/useAuth';

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts with user=null and loading=false when no token', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
  });

  it('fetches user on mount when token exists', async () => {
    localStorage.setItem('access_token', 'test-access-token');
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).not.toBeNull();
    expect(result.current.user?.email).toBe('ivan@example.com');
  });

  it('login stores tokens and sets user', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('ivan@example.com', 'password123');
    });

    expect(localStorage.getItem('access_token')).toBe('test-access-token');
    expect(result.current.user?.email).toBe('ivan@example.com');
  });

  it('logout clears tokens and sets user to null', async () => {
    localStorage.setItem('access_token', 'test-access-token');
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user).not.toBeNull());

    await act(async () => {
      await result.current.logout();
    });

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it('clears token if /auth/me returns error on mount', async () => {
    // Set an invalid token — the mock /auth/me will still return mockUser,
    // but this test validates the cleanup path using server.use override.
    localStorage.setItem('access_token', 'stale-token');
    const { server } = await import('../../test/mocks/server');
    const { http, HttpResponse } = await import('msw');
    server.use(
      http.get('http://localhost:8000/api/v1/auth/me', () =>
        new HttpResponse(null, { status: 401 })
      )
    );

    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });
});

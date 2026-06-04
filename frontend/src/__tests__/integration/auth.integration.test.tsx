/**
 * Integration: auth flow
 * Mirrors: test_auth_integration_short.py — registration, login, protected access
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../../app/hooks/useAuth';

describe('Auth integration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('login flow: stores token and returns user profile', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    let me;
    await act(async () => {
      me = await result.current.login('ivan@example.com', 'password123');
    });

    expect(localStorage.getItem('access_token')).toBe('test-access-token');
    expect(result.current.user).not.toBeNull();
    expect((me as any).email).toBe('ivan@example.com');
  });

  it('logout flow: clears tokens and user', async () => {
    localStorage.setItem('access_token', 'test-access-token');
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user).not.toBeNull());

    await act(async () => {
      await result.current.logout();
    });

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it('auto-restores session from stored token on mount', async () => {
    localStorage.setItem('access_token', 'test-access-token');
    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user?.email).toBe('ivan@example.com');
  });
});

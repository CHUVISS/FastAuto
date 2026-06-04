/**
 * Unit: api client
 * Mirrors: test_yookassa_hold_short.py — HTTP layer and error handling
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';
import { api, HttpError } from '../../app/api/client';

const BASE = 'http://localhost:8000/api/v1';

describe('api client', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('GET request returns parsed JSON', async () => {
    server.use(
      http.get(`${BASE}/test-get`, () => HttpResponse.json({ hello: 'world' }))
    );
    const result = await api.get<{ hello: string }>('/test-get');
    expect(result.hello).toBe('world');
  });

  it('POST request sends JSON body and returns response', async () => {
    server.use(
      http.post(`${BASE}/test-post`, async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        return HttpResponse.json({ echo: body.name });
      })
    );
    const result = await api.post<{ echo: string }>('/test-post', { name: 'test' });
    expect(result.echo).toBe('test');
  });

  it('attaches Authorization header when token is present', async () => {
    localStorage.setItem('access_token', 'my-test-token');
    server.use(
      http.get(`${BASE}/auth-check`, ({ request }) => {
        const auth = request.headers.get('Authorization');
        return HttpResponse.json({ auth });
      })
    );
    const result = await api.get<{ auth: string }>('/auth-check');
    expect(result.auth).toBe('Bearer my-test-token');
  });

  it('throws HttpError with status 404 for not-found responses', async () => {
    server.use(
      http.get(`${BASE}/not-found`, () =>
        HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      )
    );
    await expect(api.get('/not-found')).rejects.toMatchObject({
      status: 404,
      name: 'HttpError',
    });
  });

  it('DELETE request returns undefined for 204 No Content', async () => {
    server.use(
      http.delete(`${BASE}/items/1`, () => new HttpResponse(null, { status: 204 }))
    );
    const result = await api.delete('/items/1');
    expect(result).toBeUndefined();
  });

  it('HttpError carries both status and message', () => {
    const err = new HttpError(422, 'Validation error');
    expect(err.status).toBe(422);
    expect(err.message).toBe('Validation error');
    expect(err instanceof Error).toBe(true);
  });
});

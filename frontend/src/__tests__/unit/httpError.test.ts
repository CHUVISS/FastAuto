/**
 * Unit: HttpError
 * Mirrors: test_yookassa_hold_short.py — domain-specific error class behaviour
 */
import { describe, it, expect } from 'vitest';
import { HttpError } from '../../app/api/client';

describe('HttpError', () => {
  it('stores status code and message', () => {
    const err = new HttpError(404, 'Not found');
    expect(err.status).toBe(404);
    expect(err.message).toBe('Not found');
  });

  it('is an instance of Error', () => {
    const err = new HttpError(500, 'Server error');
    expect(err).toBeInstanceOf(Error);
  });

  it('has name "HttpError"', () => {
    const err = new HttpError(401, 'Unauthorized');
    expect(err.name).toBe('HttpError');
  });
});

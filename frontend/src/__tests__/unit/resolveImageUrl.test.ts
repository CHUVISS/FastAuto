/**
 * Unit: resolveImageUrl
 * Mirrors: test_masking_short.py — pure transformation logic
 */
import { describe, it, expect } from 'vitest';
import { resolveImageUrl } from '../../app/api/client';

describe('resolveImageUrl', () => {
  it('returns empty string for null/undefined', () => {
    expect(resolveImageUrl(null)).toBe('');
    expect(resolveImageUrl(undefined)).toBe('');
  });

  it('returns absolute https URL unchanged', () => {
    const url = 'https://cdn.example.com/photo.jpg';
    expect(resolveImageUrl(url)).toBe(url);
  });

  it('returns absolute http URL unchanged', () => {
    const url = 'http://localhost:9000/uploads/cars/photo.jpg';
    expect(resolveImageUrl(url)).toBe(url);
  });

  it('resolves relative path starting with slash', () => {
    // VITE_API_URL = 'http://localhost:8000/api/v1' → BACKEND_ORIGIN = 'http://localhost:8000'
    const result = resolveImageUrl('/uploads/cars/photo.jpg');
    expect(result).toBe('http://localhost:8000/uploads/cars/photo.jpg');
  });

  it('resolves relative path without leading slash', () => {
    const result = resolveImageUrl('uploads/cars/photo.jpg');
    expect(result).toBe('http://localhost:8000/uploads/cars/photo.jpg');
  });
});

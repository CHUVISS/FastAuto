/**
 * Integration: catalog API + data mapping
 * Mirrors: test_listings_integration_short.py — catalog list and detail fetching
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { carsApi } from '../../app/api/cars';

describe('Catalog integration', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-token');
  });

  it('list() returns mapped Car objects with brand/model fields', async () => {
    const result = await carsApi.list({ limit: 10 });
    expect(result.data.length).toBeGreaterThan(0);
    const car = result.data[0];
    expect(car).toHaveProperty('id');
    expect(car).toHaveProperty('brand');
    expect(car).toHaveProperty('model');
    expect(car).toHaveProperty('price');
    expect(car).toHaveProperty('status');
    expect(car.images).toBeInstanceOf(Array);
  });

  it('get() returns full car detail including images and seller info', async () => {
    const car = await carsApi.get('listing-1');
    expect(car.id).toBe('listing-1');
    expect(car.brand).toBeTruthy();
    expect(car.images.length).toBeGreaterThan(0);
    expect(car.images[0]).toHaveProperty('url');
    expect(car.images[0]).toHaveProperty('is_primary');
    // resolveImageUrl was applied
    expect(car.images[0].url).toMatch(/^https?:\/\//);
  });
});

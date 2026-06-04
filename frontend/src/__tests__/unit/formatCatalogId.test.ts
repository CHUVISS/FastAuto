/**
 * Unit: formatCatalogId
 * Mirrors: test_listing_service_short.py — brand/model ID normalisation
 */
import { describe, it, expect } from 'vitest';
import { formatCatalogId } from '../../app/api/cars';

describe('formatCatalogId', () => {
  it('maps well-known SCREAMING_SNAKE_CASE brand IDs to display name', () => {
    expect(formatCatalogId('TOYOTA')).toBe('Toyota');
    expect(formatCatalogId('BMW')).toBe('BMW');
    expect(formatCatalogId('MERCEDES_BENZ')).toBe('Mercedes-Benz');
  });

  it('title-cases unknown IDs with underscores', () => {
    expect(formatCatalogId('some_model')).toBe('Some Model');
  });

  it('title-cases unknown IDs with spaces', () => {
    expect(formatCatalogId('grand cherokee')).toBe('Grand Cherokee');
  });

  it('handles single-word unknown IDs', () => {
    expect(formatCatalogId('camry')).toBe('Camry');
  });
});

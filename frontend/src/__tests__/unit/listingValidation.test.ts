/**
 * Unit: listing form validation helpers
 * Mirrors: test_listing_service_short.py — input validation rules
 *
 * The CreateListingPage validates: year, price, mileage, required fields.
 * We extract these rules as pure functions and test them in isolation.
 */
import { describe, it, expect } from 'vitest';

const currentYear = new Date().getFullYear();

function validateYear(value: string): string | null {
  const n = Number(value);
  if (!value || isNaN(n)) return 'Укажите год';
  if (n < 1900 || n > currentYear) return `Год должен быть от 1900 до ${currentYear}`;
  return null;
}

function validatePrice(value: string): string | null {
  const n = Number(value.replace(/\s/g, ''));
  if (!value || isNaN(n) || n <= 0) return 'Укажите цену';
  if (n > 1_000_000_000) return 'Цена слишком большая';
  return null;
}

function validateMileage(value: string): string | null {
  const n = Number(value.replace(/\s/g, ''));
  if (value === '' || isNaN(n) || n < 0) return 'Укажите пробег';
  if (n > 10_000_000) return 'Пробег слишком большой';
  return null;
}

describe('listing form validation', () => {
  it('validateYear accepts valid current year', () => {
    expect(validateYear(String(currentYear))).toBeNull();
  });

  it('validateYear rejects year before 1900', () => {
    expect(validateYear('1899')).not.toBeNull();
  });

  it('validateYear rejects empty string', () => {
    expect(validateYear('')).not.toBeNull();
  });

  it('validatePrice accepts positive value', () => {
    expect(validatePrice('2500000')).toBeNull();
  });

  it('validatePrice rejects zero', () => {
    expect(validatePrice('0')).not.toBeNull();
  });

  it('validateMileage accepts zero (new car)', () => {
    expect(validateMileage('0')).toBeNull();
  });

  it('validateMileage rejects negative value', () => {
    expect(validateMileage('-1')).not.toBeNull();
  });

  it('validateMileage handles spaced input format', () => {
    expect(validateMileage('30 000')).toBeNull();
  });
});

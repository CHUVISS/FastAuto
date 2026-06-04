/**
 * Unit: translations
 * Mirrors: test_deposit_settings_short.py — configuration/constants correctness
 */
import { describe, it, expect } from 'vitest';
import { translations } from '../../app/i18n/translations';

const ru = translations.ru;
const en = translations.en;

describe('translations', () => {
  it('ru and en have the same top-level keys', () => {
    const ruKeys = Object.keys(ru).sort();
    const enKeys = Object.keys(en).sort();
    expect(ruKeys).toEqual(enKeys);
  });

  it('fuel labels exist in both languages for expected values', () => {
    const fuelKeys = ['petrol', 'diesel', 'electric', 'hybrid', 'gas'];
    for (const key of fuelKeys) {
      expect(ru.fuel).toHaveProperty(key);
      expect(en.fuel).toHaveProperty(key);
    }
  });

  it('status labels cover all car statuses', () => {
    const statuses = ['available', 'reserved', 'sold', 'inactive'];
    for (const s of statuses) {
      expect(ru.status).toHaveProperty(s);
      expect(en.status).toHaveProperty(s);
    }
  });

  it('nav keys exist for main navigation items', () => {
    expect(ru.nav).toHaveProperty('catalog');
    expect(ru.nav).toHaveProperty('profile');
    expect(ru.nav).toHaveProperty('signIn');
    expect(en.nav).toHaveProperty('catalog');
  });
});

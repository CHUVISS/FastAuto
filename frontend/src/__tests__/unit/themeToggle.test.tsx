/**
 * Unit: ThemeToggle component
 * Tests UI rendering and theme switching behaviour
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeToggle } from '../../app/components/ThemeToggle';

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('renders a button with accessible aria-label', () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute('aria-label');
  });

  it('shows "тёмную тему" label in light mode', async () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');
    // After mount effect fires, theme resolves to light (no saved pref)
    expect(btn.getAttribute('aria-label')).toContain('тёмную тему');
  });

  it('toggles to dark mode on click', async () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');

    await act(async () => {
      await userEvent.click(btn);
    });

    expect(localStorage.getItem('app_theme')).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('toggles back to light mode on second click', async () => {
    render(<ThemeToggle />);
    const btn = screen.getByRole('button');

    await act(async () => {
      await userEvent.click(btn); // → dark
      await userEvent.click(btn); // → light
    });

    expect(localStorage.getItem('app_theme')).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});

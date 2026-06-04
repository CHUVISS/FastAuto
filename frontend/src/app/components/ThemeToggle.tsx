import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className = '' }: ThemeToggleProps) {
  const { isDark, toggle } = useTheme();

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? 'Включить светлую тему' : 'Включить тёмную тему'}
      title={isDark ? 'Светлая тема' : 'Тёмная тема'}
      className={`relative p-2 rounded-lg transition-colors hover:bg-secondary text-foreground ${className}`}
    >
      <Sun
        className={`w-5 h-5 transition-all duration-300 ${
          isDark ? 'opacity-0 rotate-90 scale-0 absolute' : 'opacity-100 rotate-0 scale-100'
        }`}
      />
      <Moon
        className={`w-5 h-5 transition-all duration-300 ${
          isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-0 absolute'
        }`}
      />
    </button>
  );
}
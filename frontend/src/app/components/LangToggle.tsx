import { useLanguage } from '../i18n/LanguageContext';

export function LangToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <button
      onClick={() => setLang(lang === 'ru' ? 'en' : 'ru')}
      className="flex items-center gap-0.5 px-2 py-1.5 rounded-lg text-sm font-medium border border-border hover:bg-secondary transition-colors select-none"
      title={lang === 'ru' ? 'Switch to English' : 'Переключить на русский'}
      aria-label="Toggle language"
    >
      <span className={lang === 'ru' ? 'text-foreground' : 'text-muted-foreground'}>RU</span>
      <span className="text-muted-foreground mx-0.5">/</span>
      <span className={lang === 'en' ? 'text-foreground' : 'text-muted-foreground'}>EN</span>
    </button>
  );
}

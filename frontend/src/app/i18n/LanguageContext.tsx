import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { translations, type Lang } from './translations';


type T = typeof translations['ru'];

interface LanguageContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  T: T;
}


const LanguageContext = createContext<LanguageContextValue>({
  lang: 'ru',
  setLang: () => {},
  T: translations.ru,
});


const STORAGE_KEY = 'fa_lang';

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Lang | null;
    return saved === 'en' ? 'en' : 'ru';
  });

  const setLang = (next: Lang) => {
    setLangState(next);
    localStorage.setItem(STORAGE_KEY, next);
  };

  // Update <html lang="…"> attribute
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, T: translations[lang] }}>
      {children}
    </LanguageContext.Provider>
  );
}


export function useLanguage() {
  return useContext(LanguageContext);
}

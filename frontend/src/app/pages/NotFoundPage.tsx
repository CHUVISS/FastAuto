import { useEffect } from 'react';
import { Link } from 'react-router';
import { Home } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

export function NotFoundPage() {
  const { T } = useLanguage();
  useEffect(() => { window.scrollTo(0, 0); }, []);
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-6xl font-semibold text-primary mb-4">404</h1>
        <h2 className="text-2xl font-semibold mb-4">{T.notFound.title}</h2>
        <p className="text-muted-foreground mb-8">{T.notFound.desc}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
        >
          <Home className="w-5 h-5" />
          <span>{T.notFound.home}</span>
        </Link>
      </div>
    </div>
  );
}

import { Link } from 'react-router';
import { Car, Phone, Mail, MapPin } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

export function Footer() {
  const { T } = useLanguage();
  return (
    <footer className="bg-foreground text-background mt-auto dark:bg-card dark:text-foreground dark:border-t dark:border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Car className="w-8 h-8" />
              <span className="text-xl font-semibold">FastAuto</span>
            </div>
            <p className="text-sm opacity-70">{T.footer.tagline}</p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{T.footer.navigation}</h4>
            <nav className="flex flex-col gap-2">
              <Link to="/catalog" className="text-sm opacity-70 hover:opacity-100 transition-opacity">{T.footer.catalog}</Link>
              <Link to="/catalog?isNew=true" className="text-sm opacity-70 hover:opacity-100 transition-opacity">{T.footer.newCars}</Link>
              <Link to="/catalog?isNew=false" className="text-sm opacity-70 hover:opacity-100 transition-opacity">{T.footer.usedCars}</Link>
              <Link to="/about" className="text-sm opacity-70 hover:opacity-100 transition-opacity">{T.nav.about}</Link>
            </nav>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{T.footer.contacts}</h4>
            <div className="flex flex-col gap-3">
              <a href="tel:+79001234567" className="flex items-center gap-2 text-sm opacity-70 hover:opacity-100 transition-opacity">
                <Phone className="w-4 h-4" />
                <span>+7 (900) 123-45-67</span>
              </a>
              <a href="mailto:info@autosalon.ru" className="flex items-center gap-2 text-sm opacity-70 hover:opacity-100 transition-opacity">
                <Mail className="w-4 h-4" />
                <span>info@autosalon.ru</span>
              </a>
              <div className="flex items-center gap-2 text-sm opacity-70">
                <MapPin className="w-4 h-4" />
                <span>Москва, ул. Примерная, д. 1</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{T.footer.hours}</h4>
            <div className="text-sm opacity-70 space-y-1">
              <p>{T.footer.weekdays}</p>
              <p>{T.footer.weekend}</p>
            </div>
          </div>
        </div>

        <div className="border-t border-current/20 mt-8 pt-8 text-center text-sm opacity-70">
          <p>{T.footer.copyright}</p>
        </div>
      </div>
    </footer>
  );
}

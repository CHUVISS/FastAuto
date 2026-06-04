import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Heart, Trash2, ShoppingBag, AlertTriangle } from 'lucide-react';
import { carsApi, type Car } from '../api/cars';
import { useFavorites } from '../hooks/useFavorites';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { CarImagePlaceholder } from '../components/CarImagePlaceholder';
import { useLanguage } from '../i18n/LanguageContext';

function formatPrice(p: string | number): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB',
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(Number(p));
}
function formatMileage(m: number, lang: string): string {
  return `${new Intl.NumberFormat(lang === 'ru' ? 'ru-RU' : 'en-US').format(m)} км`;
}

const STATUS_COLORS: Record<string, string> = {
  available: 'bg-accent/10 text-accent',
  reserved: 'bg-primary/10 text-primary',
  sold: 'bg-muted text-muted-foreground',
  inactive: 'bg-secondary text-muted-foreground',
};

export function FavoritesPage() {
  useEffect(() => { window.scrollTo(0, 0); }, []);
  const { ids, toggle, clear } = useFavorites();
  const { lang, T } = useLanguage();
  const [cars, setCars] = useState<Car[]>([]);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState<string[]>([]);

  useEffect(() => {
    if (ids.length === 0) { setCars([]); return; }
    setLoading(true);
    Promise.allSettled(ids.map(id => carsApi.get(id)))
      .then(results => {
        const loaded: Car[] = [];
        const missing: string[] = [];
        results.forEach((r, i) => {
          if (r.status === 'fulfilled') loaded.push(r.value);
          else missing.push(ids[i]);
        });
        setCars(loaded);
        setNotFound(missing);
      })
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(',')]);

  const FUEL_LABELS: Record<string, string> = T.fuel;
  const TRANSMISSION_LABELS: Record<string, string> = T.transmission;
  const STATUS_LABELS: Record<string, string> = {
    available: T.status.available,
    reserved: T.status.reserved,
    sold: T.status.sold,
    inactive: T.status.inactive,
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-foreground">{T.favorites.title}</h2>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-card border border-border rounded-xl p-4 flex gap-4 animate-pulse">
              <div className="w-36 h-24 bg-secondary rounded-lg flex-shrink-0" />
              <div className="flex-1 space-y-2 py-1">
                <div className="h-5 bg-secondary rounded w-1/2" />
                <div className="h-4 bg-secondary rounded w-1/3" />
                <div className="h-6 bg-secondary rounded w-1/4 mt-4" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (ids.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-12 text-center">
        <div className="w-20 h-20 bg-secondary rounded-full flex items-center justify-center mx-auto mb-5">
          <Heart className="w-10 h-10 text-muted-foreground opacity-40" />
        </div>
        <h3 className="text-xl font-semibold text-foreground mb-2">{T.favorites.empty}</h3>
        <p className="text-muted-foreground mb-6 max-w-sm mx-auto">{T.favorites.emptyDesc}</p>
        <Link
          to="/catalog"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25"
        >
          <ShoppingBag className="w-5 h-5" />
          {T.favorites.toCatalog}
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-foreground">
          {T.favorites.title}{' '}
          <span className="text-muted-foreground text-lg font-normal">({cars.length})</span>
        </h2>
        {cars.length > 0 && (
          <button
            onClick={() => { if (confirm(T.favorites.clearConfirm)) clear(); }}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-destructive transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            {T.favorites.clearAll}
          </button>
        )}
      </div>

      {/* Предупреждение об удалённых авто */}
      {notFound.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-400">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{notFound.length} {T.favorites.unavailableWarning}</span>
          </div>
          <button
            onClick={() => notFound.forEach(id => toggle(id))}
            className="text-xs text-yellow-600 dark:text-yellow-400 underline hover:no-underline flex-shrink-0"
          >
            {T.favorites.removeUnavailable}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {cars.map(car => {
          const primaryImg = car.images.find(img => img.is_primary) ?? car.images[0];
          return (
            <div
              key={car.id}
              className="bg-card border border-border rounded-xl overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25 group"
            >
              <div className="flex">
                {/* Фото */}
                <Link to={`/car/${car.id}`} className="flex-shrink-0 w-36 sm:w-48">
                  <div className="h-full min-h-[100px] bg-secondary">
                    {primaryImg ? (
                      <ImageWithFallback
                        src={primaryImg.url}
                        alt={`${car.brand} ${car.model}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <CarImagePlaceholder />
                    )}
                  </div>
                </Link>

                {/* Инфо */}
                <div className="flex-1 min-w-0 p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <Link to={`/car/${car.id}`} className="hover:text-primary transition-colors">
                        <h3 className="font-semibold text-lg text-foreground leading-tight">
                          {car.brand} {car.model}
                        </h3>
                      </Link>
                      <button
                        onClick={() => toggle(car.id)}
                        className="flex-shrink-0 p-1.5 hover:bg-destructive/10 rounded-lg transition-colors"
                        title={T.favorites.removeFavorite}
                      >
                        <Heart className="w-5 h-5 fill-destructive text-destructive" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span className="text-sm text-muted-foreground">
                        {car.year} г. • {formatMileage(car.mileage, lang)}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[car.status] ?? 'bg-secondary text-muted-foreground'}`}>
                        {STATUS_LABELS[car.status] ?? car.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground mb-3">
                      {car.engine_volume && <span>{car.engine_volume} л</span>}
                      {car.engine_power && <span>{car.engine_power} л.с.</span>}
                      {car.transmission && <span>{TRANSMISSION_LABELS[car.transmission] ?? car.transmission}</span>}
                      {car.fuel_type && <span>{FUEL_LABELS[car.fuel_type] ?? car.fuel_type}</span>}
                      {car.color && <span>{car.color}</span>}
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xl font-semibold text-primary">
                      {formatPrice(car.price)}
                    </p>
                    <Link
                      to={`/car/${car.id}`}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25 flex-shrink-0"
                    >
                      {T.favorites.moreDetails}
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

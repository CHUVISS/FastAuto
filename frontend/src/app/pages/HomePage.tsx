import { Link, useNavigate } from 'react-router';
import { Search, Shield, Wallet, Headset, Heart } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { CarImagePlaceholder } from '../components/CarImagePlaceholder';
import { carsApi, type Car, formatCatalogId } from '../api/cars';
import { catalogApi, type CatalogMark } from '../api/catalog';
import { useLanguage } from '../i18n/LanguageContext';
import { useFavorites } from '../hooks/useFavorites';

function formatPrice(p: number) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(p);
}
function formatMileage(m: number) {
  return `${new Intl.NumberFormat('ru-RU').format(m)} км`;
}
function markLabel(m: CatalogMark) {
  return m.name ?? m.cyrillic_name ?? formatCatalogId(m.id);
}

/** Карточка авто для главной страницы (использует CarType.images напрямую) */
function HomeCarCard({ car }: { car: Car }) {
  const { isFavorite, toggle } = useFavorites();
  const fav = isFavorite(car.id);
  const img = car.images.find(i => i.is_primary) ?? car.images[0];
  const isSoldOrInactive = car.status === 'sold' || car.status === 'inactive';

  return (
    <Link
      to={`/car/${car.id}`}
      className="group block bg-card rounded-lg border border-border overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25"
    >
      <div className="relative aspect-[4/3] bg-secondary overflow-hidden">
        {img ? (
          <ImageWithFallback
            src={img.url}
            alt={`${car.brand} ${car.model}`}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${isSoldOrInactive ? 'brightness-75' : ''}`}
          />
        ) : (
          <CarImagePlaceholder />
        )}
        <button
          onClick={e => { e.preventDefault(); toggle(car.id); }}
          className="absolute top-2.5 right-2.5 p-1.5 bg-card/90 rounded-full hover:bg-card transition-colors"
        >
          <Heart className={`w-4 h-4 ${fav ? 'fill-destructive text-destructive' : 'text-foreground'}`} />
        </button>
        {car.images.length > 1 && (
          <span className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/60 text-white text-[10px] rounded backdrop-blur-sm">
            {car.images.length} фото
          </span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-foreground mb-0.5">{car.brand} {car.model}</h3>
        <p className="text-sm text-muted-foreground mb-3">
          {car.year} • {formatMileage(car.mileage)}
          {car.engine_volume ? ` • ${car.engine_volume}л` : ''}
        </p>
        <p className="text-xl font-semibold text-foreground">{formatPrice(Number(car.price))}</p>
      </div>
    </Link>
  );
}


export function HomePage() {
  useEffect(() => { window.scrollTo(0, 0); }, []);
  const navigate = useNavigate();
  const { T } = useLanguage();

  // ─── Поиск ────────────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('');
  const [marks, setMarks] = useState<CatalogMark[]>([]);
  const [suggestions, setSuggestions] = useState<CatalogMark[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Загружаем все марки один раз
  useEffect(() => {
    catalogApi.searchMarks('').then(setMarks).catch(() => {});
  }, []);

  // Фильтруем подсказки по вводу
  useEffect(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) { setSuggestions([]); return; }
    setSuggestions(
      marks.filter(m => markLabel(m).toLowerCase().includes(q)).slice(0, 8)
    );
  }, [searchQuery, marks]);

  // Закрываем подсказки при клике снаружи
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) { navigate('/catalog'); return; }
    // Ищем точное совпадение или первую подсказку
    const match = marks.find(m => markLabel(m).toLowerCase() === q.toLowerCase()) ?? suggestions[0];
    if (match) {
      navigate(`/catalog?brands=${encodeURIComponent(markLabel(match))}`);
    } else {
      navigate(`/catalog`);
    }
  };

  const selectSuggestion = (m: CatalogMark) => {
    setSearchQuery(markLabel(m));
    setShowSuggestions(false);
    navigate(`/catalog?brands=${encodeURIComponent(markLabel(m))}`);
  };

  // ─── Машины ───────────────────────────────────────────────────────────────
  const [cars, setCars] = useState<Car[]>([]);
  const [loadingCars, setLoadingCars] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingCars(true);
    carsApi.list({ limit: 6 })
      .then(async res => {
        if (cancelled) return;
        setCars(res.data);
        setLoadingCars(false);
        // Подгружаем фото в фоне
        const details = await Promise.allSettled(res.data.map(c => carsApi.get(c.id)));
        if (cancelled) return;
        setCars(res.data.map((c, i) => {
          const r = details[i];
          return r.status === 'fulfilled' && r.value.images.length > 0
            ? { ...c, images: r.value.images }
            : c;
        }));
      })
      .catch(() => { if (!cancelled) setLoadingCars(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Герой */}
      <section className="relative bg-primary text-primary-foreground group">
        <div className="absolute inset-0 overflow-hidden">
          <ImageWithFallback
            src="https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=1600&q=80"
            alt="Автомобили"
            className="w-full h-full object-cover opacity-20 transition-transform duration-500 group-hover:scale-105"
          />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-20 lg:py-32">
          <div className="max-w-2xl">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold mb-4 transition-transform duration-300 group-hover:scale-105">
              {T.home.heroTitle}
            </h1>
            <p className="text-lg opacity-90 mb-8 transition-transform duration-300 group-hover:scale-105 origin-left">
              {T.home.heroSubtitle}
            </p>

            {/* Поиск */}
            <form
              onSubmit={handleSearch}
              className="bg-card rounded-lg p-4 shadow-lg border border-border transition-all duration-300 group-hover:shadow-[0_0_24px_6px_hsl(var(--primary)/0.25)]"
            >
              <div className="flex flex-col md:flex-row gap-3">
                <div ref={searchRef} className="flex-1 relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => { setSearchQuery(e.target.value); setShowSuggestions(true); }}
                    onFocus={() => setShowSuggestions(true)}
                    placeholder={T.home.allBrands}
                    className="w-full px-4 py-3 bg-secondary text-foreground placeholder:text-muted-foreground rounded-lg outline-none focus:ring-2 focus:ring-primary border border-border transition-all duration-200"
                  />
                  {showSuggestions && suggestions.length > 0 && (
                    <ul className="absolute z-50 left-0 right-0 top-full mt-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
                      {suggestions.map(m => (
                        <li key={m.id}>
                          <button
                            type="button"
                            onMouseDown={() => selectSuggestion(m)}
                            className="w-full text-left px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
                          >
                            {markLabel(m)}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <button
                  type="submit"
                  className="px-8 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-all duration-200 flex items-center justify-center gap-2 hover:scale-105 active:scale-95"
                >
                  <Search className="w-5 h-5" />
                  <span>{T.home.findBtn}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Популярные модели */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 group">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-semibold text-foreground transition-transform duration-300 group-hover:scale-105">
            {T.home.popularModels}
          </h2>
          <Link to="/catalog" className="text-primary hover:underline transition-transform duration-300 group-hover:scale-105">
            {T.home.seeAll}
          </Link>
        </div>
        {loadingCars ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-card rounded-lg border border-border overflow-hidden">
                <div className="aspect-[4/3] bg-secondary animate-pulse" />
                <div className="p-4 space-y-3">
                  <div className="h-5 bg-secondary rounded animate-pulse" />
                  <div className="h-4 bg-secondary rounded animate-pulse w-2/3" />
                  <div className="h-7 bg-secondary rounded animate-pulse w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {cars.map(car => <HomeCarCard key={car.id} car={car} />)}
          </div>
        )}
      </section>

      {/* Преимущества */}
      <section className="bg-secondary border-y border-border py-16 group">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-semibold text-center text-foreground mb-12 transition-transform duration-300 group-hover:scale-105">
            {T.home.advantages}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {[
              { icon: Shield,  title: T.home.qualityTitle, desc: T.home.qualityDesc },
              { icon: Wallet,  title: T.home.dealsTitle,   desc: T.home.dealsDesc },
              { icon: Headset, title: T.home.supportTitle, desc: T.home.supportDesc },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="text-center group/adv cursor-default">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4
                  transition-all duration-300
                  group-hover/adv:scale-110 group-hover/adv:bg-primary/20
                  group-hover/adv:shadow-[0_0_18px_4px_hsl(var(--primary)/0.35)]
                  group-hover/adv:ring-2 group-hover/adv:ring-primary/30">
                  <Icon className="w-8 h-8 text-primary transition-transform duration-300 group-hover/adv:scale-110" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2 transition-transform duration-300 group-hover/adv:scale-105">
                  {title}
                </h3>
                <p className="text-muted-foreground transition-transform duration-300 group-hover/adv:scale-105">
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, Loader2, Car } from 'lucide-react';
import { carsApi, type Car as CarType } from '../api/cars';
import { useLanguage } from '../i18n/LanguageContext';

interface CarSearchProps {
  onSelect?: (car: CarType) => void;
  placeholder?: string;
  className?: string;
  variant?: 'catalog' | 'admin';
}

const STATUS_COLORS: Record<string, string> = {
  available: 'bg-accent/10 text-accent',
  reserved: 'bg-primary/10 text-primary',
  sold: 'bg-muted text-muted-foreground',
  inactive: 'bg-secondary text-muted-foreground',
};

export function CarSearch({
  onSelect,
  placeholder,
  className = '',
  variant = 'catalog',
}: CarSearchProps) {
  const { T, lang } = useLanguage();
  const A = T.admin;

  const formatPrice = (p: string | number) =>
    new Intl.NumberFormat(lang === 'ru' ? 'ru-RU' : 'en-US', {
      style: 'currency', currency: 'RUB',
      minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(Number(p));

  const formatMileage = (m: number) =>
    `${new Intl.NumberFormat(lang === 'ru' ? 'ru-RU' : 'en-US').format(m)} ${lang === 'ru' ? 'км' : 'km'}`;

  const resolvedPlaceholder = placeholder ?? A.carSearchPlaceholder;

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CarType[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<CarType | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    setLoading(true);
    try {
      const res = await carsApi.list({ limit: 20 });
      const lq = q.toLowerCase().trim();
      const filtered = res.data.filter(c =>
        c.brand.toLowerCase().includes(lq) ||
        c.model.toLowerCase().includes(lq) ||
        `${c.brand} ${c.model}`.toLowerCase().includes(lq)
      );
      setResults(filtered.slice(0, 8));
      setOpen(true);
      setActiveIndex(-1);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      setLoading(false);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(() => search(query), 350);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, search]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current && !inputRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSelect = (car: CarType) => {
    setSelected(car);
    setQuery(`${car.brand} ${car.model} ${car.year}`);
    setOpen(false);
    onSelect?.(car);
  };

  const handleClear = () => {
    setQuery('');
    setSelected(null);
    setResults([]);
    setOpen(false);
    onSelect?.(null as unknown as CarType);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && results[activeIndex]) handleSelect(results[activeIndex]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  const isAdmin = variant === 'admin';
  void selected; // suppress unused var warning

  return (
    <div className={`relative ${className}`}>
      {/* Input */}
      <div className={`flex items-center gap-2 border rounded-xl px-3 transition-all ${
        open
          ? 'border-foreground shadow-sm'
          : 'border-border hover:border-foreground/40'
      } bg-white`}>
        {loading
          ? <Loader2 className="w-4 h-4 text-muted-foreground animate-spin flex-shrink-0" />
          : <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        }
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => { setQuery(e.target.value); setSelected(null); }}
          onFocus={() => { if (results.length > 0) setOpen(true); }}
          onKeyDown={handleKeyDown}
          placeholder={resolvedPlaceholder}
          className="flex-1 py-2.5 text-sm bg-transparent outline-none placeholder:text-muted-foreground"
        />
        {query && (
          <button onClick={handleClear} className="p-0.5 hover:bg-secondary rounded-md transition-colors flex-shrink-0">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {open && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-border rounded-xl shadow-lg z-50 overflow-hidden"
        >
          {results.length === 0 && !loading ? (
            <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
              <Car className="w-8 h-8 text-muted-foreground mb-2 opacity-40" />
              <p className="text-sm text-muted-foreground">{A.carSearchEmpty}</p>
              <p className="text-xs text-muted-foreground mt-1">{A.carSearchEmptyHint}</p>
            </div>
          ) : (
            <ul className="py-1 max-h-80 overflow-y-auto">
              {results.map((car, i) => {
                const primaryImg = car.images.find(img => img.is_primary) ?? car.images[0];
                const isActive = i === activeIndex;
                return (
                  <li key={car.id}>
                    <button
                      onClick={() => handleSelect(car)}
                      onMouseEnter={() => setActiveIndex(i)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 transition-colors text-left ${
                        isActive ? 'bg-secondary' : 'hover:bg-secondary/50'
                      }`}
                    >
                      <div className="w-12 h-9 rounded-lg overflow-hidden flex-shrink-0 bg-secondary">
                        {primaryImg ? (
                          <img
                            src={primaryImg.thumbnail_url}
                            alt={`${car.brand} ${car.model}`}
                            className="w-full h-full object-cover"
                            onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Car className="w-4 h-4 text-muted-foreground opacity-40" />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold truncate">
                            {car.brand} {car.model}
                          </p>
                          <span className="text-xs text-muted-foreground flex-shrink-0">
                            {car.year}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <p className="text-sm font-medium text-primary">
                            {formatPrice(car.price)}
                          </p>
                          <span className="text-xs text-muted-foreground">•</span>
                          <p className="text-xs text-muted-foreground">
                            {formatMileage(car.mileage)}
                          </p>
                          {car.color && (
                            <>
                              <span className="text-xs text-muted-foreground">•</span>
                              <p className="text-xs text-muted-foreground truncate">{car.color}</p>
                            </>
                          )}
                        </div>
                      </div>

                      {isAdmin && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${STATUS_COLORS[car.status]}`}>
                          {A.carStatus[car.status]}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {results.length > 0 && (
            <div className="px-3 py-2 border-t border-border bg-secondary/30">
              <p className="text-xs text-muted-foreground">
                {A.carSearchKeyHint}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

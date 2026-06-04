import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useState, useEffect, useMemo, useRef, useCallback, type KeyboardEvent, type ChangeEvent } from 'react';
import { SlidersHorizontal, X, ChevronDown, Check, Search, LayoutGrid, List, Heart, Plus } from 'lucide-react';
import { carsApi, formatCatalogId } from '../api/cars';
import { catalogApi } from '../api/catalog';
import type { CatalogMark, CatalogModel, CatalogGeneration, CatalogConfiguration, CatalogModification, CatalogColor } from '../api/catalog';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { CarImagePlaceholder } from '../components/CarImagePlaceholder';
import { useFavorites } from '../hooks/useFavorites';
import type { CarFilters, FuelType, Transmission, Car as CarType } from '../api/cars';
import { useLanguage } from '../i18n/LanguageContext';

const PAGE_SIZE = 30;

/** Batch-fetch full listing details to attach images, color, transmission and other detail-only fields. */
async function enrichWithImages(cars: CarType[]): Promise<CarType[]> {
  if (cars.length === 0) return cars;
  const results = await Promise.allSettled(cars.map(c => carsApi.get(c.id)));
  return cars.map((c, i) => {
    const r = results[i];
    if (r.status === 'fulfilled') {
      // Merge all detail fields; preserve brand/model/city_name from list (cleaner values)
      return { ...c, ...r.value, brand: c.brand, model: c.model, city_name: r.value.city_name ?? c.city_name };
    }
    return c;
  });
}
function markLabel(m: CatalogMark) { return m.name ?? m.cyrillic_name ?? formatCatalogId(m.id); }
function modelLabel(m: CatalogModel) { return m.name ?? formatCatalogId(m.id); }

const inputCls = "w-full px-3 py-2 bg-secondary text-foreground placeholder:text-muted-foreground rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary border border-transparent focus:border-primary";

function ColorFilter({ colors, selected, onToggle, onClear }: {
  colors: CatalogColor[];
  selected: string[];
  onToggle: (id: string) => void;
  onClear: () => void;
}) {
  const { lang, T } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const colorLabel = (c: CatalogColor) => {
    if (lang === 'en') {
      return c.name_en ?? c.id.charAt(0).toUpperCase() + c.id.slice(1).replace(/_/g, ' ');
    }
    return c.name_ru;
  };

  const filtered = colors.filter(c => colorLabel(c).toLowerCase().includes(search.toLowerCase()));

  const displayText = selected.length > 0
    ? selected.map(id => { const c = colors.find(x => x.id === id); return c ? colorLabel(c) : id; }).join(', ')
    : (T.common.selectPlaceholder ?? 'Выберите...');

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-foreground">{T.catalog.color}</h3>
        {selected.length > 0 && (
          <button type="button" onClick={e => { e.stopPropagation(); onClear(); }} className="text-xs text-destructive hover:underline flex items-center gap-1">
            <X className="w-3 h-3" />{T.catalog.clearFilter}
          </button>
        )}
      </div>

      <button type="button" onClick={() => setIsOpen(o => !o)}
        className={`w-full flex items-center justify-between px-3 py-2 bg-secondary rounded-lg text-sm text-left hover:bg-secondary/80 transition-colors min-h-[40px] border border-border ${selected.length > 0 ? 'text-primary font-medium' : 'text-muted-foreground'}`}>
        <span className="overflow-hidden text-ellipsis whitespace-nowrap" title={displayText}>{displayText}</span>
        <ChevronDown className={`w-4 h-4 transition-transform flex-shrink-0 ml-2 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="mt-2 bg-card border border-border rounded-lg shadow-sm overflow-hidden">
          <div className="p-2 border-b border-border">
            <input
              type="text"
              placeholder={T.common.searchPlaceholder}
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-secondary text-foreground placeholder:text-muted-foreground rounded outline-none focus:ring-2 focus:ring-primary"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filtered.length > 0 ? filtered.map(c => {
              const isSelected = selected.includes(c.id);
              return (
                <label key={c.id} className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-secondary/50 text-foreground text-sm">
                  <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors flex-shrink-0 ${isSelected ? 'bg-primary border-primary' : 'border-border'}`}>
                    {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
                  </div>
                  <input type="checkbox" className="sr-only" checked={isSelected} onChange={() => onToggle(c.id)} />
                  {c.hex_code && (
                    <span className="w-3.5 h-3.5 rounded-full flex-shrink-0 border border-black/10 dark:border-white/10" style={{ backgroundColor: c.hex_code }} />
                  )}
                  <span>{colorLabel(c)}</span>
                </label>
              );
            }) : (
              <div className="px-3 py-4 text-center text-sm text-muted-foreground">{T.common.noResults}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const BODY_TYPE_LABELS: Record<string, { ru: string; en: string }> = {
  SEDAN: { ru: 'Седан', en: 'Sedan' },
  HATCHBACK: { ru: 'Хэтчбек', en: 'Hatchback' },
  SUV: { ru: 'Внедорожник', en: 'SUV' },
  COUPE: { ru: 'Купе', en: 'Coupe' },
  MINIVAN: { ru: 'Минивэн', en: 'Minivan' },
  PICKUP: { ru: 'Пикап', en: 'Pickup' },
  CONVERTIBLE: { ru: 'Кабриолет', en: 'Convertible' },
  WAGON: { ru: 'Универсал', en: 'Wagon' },
  LIFTBACK: { ru: 'Лифтбэк', en: 'Liftback' },
  VAN: { ru: 'Фургон', en: 'Van' },
  CROSSOVER: { ru: 'Кроссовер', en: 'Crossover' },
  ALLROAD: { ru: 'Вседорожник', en: 'Allroad' },
};

function labelBodyType(id: string, lang: string): string {
  const key = id.split(/[\s_]/)[0].toUpperCase();
  const entry = BODY_TYPE_LABELS[key];
  if (entry) return lang === 'en' ? entry.en : entry.ru;
  return id.charAt(0).toUpperCase() + id.slice(1).toLowerCase();
}

function labelTransmission(id: string, T: { transmission: Record<string, string> }): string {
  const key = id.toLowerCase() as keyof typeof T.transmission;
  return T.transmission[key] ?? (id.charAt(0).toUpperCase() + id.slice(1));
}

function formatPrice(p: number) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(p);
}
function formatMileage(m: number, lang?: string) {
  return `${new Intl.NumberFormat(lang === 'en' ? 'en-US' : 'ru-RU').format(m)} км`;
}
/** Match a DB engine_type string (Russian) against an English filter key. */
function matchesFuel(dbValue: string, filterKey: string): boolean {
  const v = dbValue.toLowerCase();
  switch (filterKey) {
    case 'petrol':   return v.includes('бензин') || v === 'petrol' || v === 'gasoline';
    case 'diesel':   return v.includes('дизел')  || v === 'diesel';
    case 'electric': return v.includes('электр') || v === 'electric';
    case 'hybrid':   return v.includes('гибрид') || v === 'hybrid';
    case 'gas':      return v.includes('газ')    || v === 'gas' || v.includes('lpg') || v.includes('cng');
    default:         return v.includes(filterKey.toLowerCase());
  }
}

// Filter helpers

function SearchableMultiSelect<T extends string>({
  label, options, selected, onToggle, onClear, placeholder, openUp = false,
}: { label: string; options: { value: T; label: string }[]; selected: T[]; onToggle: (v: T) => void; onClear: () => void; placeholder?: string; openUp?: boolean }) {
  const { T } = useLanguage();
  const ph = placeholder ?? T.common.selectPlaceholder;
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) { setIsOpen(false); setSearch(''); } };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const filtered = options.filter(o => o.label.toLowerCase().includes(search.toLowerCase()));
  const displayText = selected.length > 0 ? selected.map(v => options.find(o => o.value === v)?.label ?? v).join(', ') : ph;
  return (
    <div className="relative" ref={ref}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-foreground">{label}</h3>
        {selected.length > 0 && <button type="button" onClick={e => { e.stopPropagation(); onClear(); }} className="text-xs text-destructive hover:underline flex items-center gap-1"><X className="w-3 h-3" />{T.catalog.clearFilter}</button>}
      </div>
      <button type="button" onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between px-3 py-2 bg-secondary rounded-lg text-sm text-left hover:bg-secondary/80 transition-colors min-h-[40px] border border-border ${selected.length > 0 ? 'text-primary font-medium' : 'text-muted-foreground'}`}>
        <span className="overflow-hidden text-ellipsis whitespace-nowrap" title={displayText}>{displayText}</span>
        <ChevronDown className={`w-4 h-4 transition-transform flex-shrink-0 ml-2 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className={`absolute z-20 w-full bg-card border border-border rounded-lg shadow-lg overflow-hidden ${openUp ? 'bottom-full mb-2' : 'mt-2'}`}>
          <div className="p-2 border-b border-border">
            <input type="text" placeholder={T.common.searchPlaceholder} value={search} onChange={e => setSearch(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-secondary text-foreground placeholder:text-muted-foreground rounded outline-none focus:ring-2 focus:ring-primary" autoFocus />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filtered.length > 0 ? filtered.map(opt => (
              <label key={opt.value} className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-secondary/50 text-foreground text-sm">
                <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors flex-shrink-0 ${selected.includes(opt.value) ? 'bg-primary border-primary' : 'border-border'}`}>
                  {selected.includes(opt.value) && <Check className="w-3 h-3 text-primary-foreground" />}
                </div>
                <input type="checkbox" className="sr-only" checked={selected.includes(opt.value)} onChange={() => onToggle(opt.value)} />
                <span>{opt.label}</span>
              </label>
            )) : <div className="px-3 py-4 text-center text-sm text-muted-foreground">{T.common.noResults}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

function fmtNum(s: string) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }


function SortDropdown({ value, onChange }: { value: CarFilters['sort_by']; onChange: (v: CarFilters['sort_by']) => void }) {
  const { T } = useLanguage();
  const SORT_OPTIONS: { value: NonNullable<CarFilters['sort_by']>; label: string }[] = [
    { value: 'date_desc',  label: T.catalog.sortNewest },
    { value: 'date_asc',   label: T.catalog.sortOldest },
    { value: 'price_asc',  label: T.catalog.sortCheapest },
    { value: 'price_desc', label: T.catalog.sortMostExpensive },
  ];
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const current = SORT_OPTIONS.find(o => o.value === value) ?? SORT_OPTIONS[0];
  return (
    <div className="relative flex-shrink-0" ref={ref}>
      <button type="button" onClick={() => setIsOpen(o => !o)}
        className="flex items-center justify-between gap-1.5 min-w-[110px] px-3 py-2.5 bg-secondary border border-border rounded-xl text-sm text-foreground hover:bg-secondary/80 transition-colors whitespace-nowrap">
        <span>{current.label}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="absolute right-0 z-30 mt-1.5 min-w-full bg-card border border-border rounded-lg shadow-lg overflow-hidden">
          {SORT_OPTIONS.map(opt => (
            <button key={opt.value} type="button"
              onClick={() => { onChange(opt.value); setIsOpen(false); }}
              className={`w-full flex items-center justify-between gap-3 px-3 py-2 text-left text-xs transition-colors
                ${opt.value === value ? 'text-primary font-medium bg-secondary/60' : 'text-foreground hover:bg-secondary/50'}`}>
              <span>{opt.label}</span>
              {opt.value === value && <Check className="w-3 h-3 text-primary flex-shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function NumberFilterInput({ placeholder, value, onChange, onConfirm, format = false }: {
  placeholder: string; value: string; onChange: (v: string) => void; onConfirm: (v: string) => void; format?: boolean;
}) {
  return (
    <input type="text" inputMode="numeric" placeholder={placeholder}
      value={format ? fmtNum(value) : value}
      onChange={(e: ChangeEvent<HTMLInputElement>) => { const c = e.target.value.replace(/\D/g, ''); if (c !== value) onChange(c); }}
      onBlur={() => onConfirm(value.trim())}
      onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => { if (e.key === 'Enter') { e.preventDefault(); e.currentTarget.blur(); } }}
      className={inputCls} />
  );
}

// Card components

function GridCard({ car }: { car: CarType }) {
  const { isFavorite, toggle } = useFavorites();
  const { lang, T } = useLanguage();
  const fav = isFavorite(car.id);
  const img = car.images.find(i => i.is_primary) ?? car.images[0];
  const isSoldOrInactive = car.status === 'sold' || car.status === 'inactive';
  const STATUS_LABELS: Record<string, string> = { available: T.status.available, reserved: T.status.reserved, sold: T.status.sold, inactive: T.status.inactive };
  const TRANSMISSION_LABELS: Record<string, string> = T.transmission;
  function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return T.common.today;
    if (days === 1) return T.common.yesterday;
    if (days < 7) return `${days} ${T.common.daysAgo}`;
    return new Date(dateStr).toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', { day: 'numeric', month: 'short' });
  }
  return (
    <Link to={`/car/${car.id}`}
      className="group block bg-card rounded-lg border border-border overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25">
      <div className="relative aspect-[4/3] bg-secondary overflow-hidden">
        {img ? (
          <ImageWithFallback src={img.url} alt={`${car.brand} ${car.model}`}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${isSoldOrInactive ? 'brightness-75' : ''}`} />
        ) : (
          <CarImagePlaceholder />
        )}
        <div className="absolute top-2.5 left-2.5 flex flex-col gap-1">
          {car.mileage === 0 && <span className="px-2 py-0.5 bg-accent text-accent-foreground rounded-full text-xs font-medium">{T.status.new}</span>}
          {car.status && car.status !== 'available' && (
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${car.status === 'reserved' ? 'bg-primary/90 text-primary-foreground' : 'bg-black/60 text-white backdrop-blur-sm'}`}>
              {STATUS_LABELS[car.status] ?? car.status}
            </span>
          )}
        </div>
        <button onClick={e => { e.preventDefault(); toggle(car.id); }}
          className="absolute top-2.5 right-2.5 p-1.5 bg-card/90 rounded-full hover:bg-card transition-colors">
          <Heart className={`w-4 h-4 ${fav ? 'fill-destructive text-destructive' : 'text-foreground'}`} />
        </button>
        {car.images.length > 1 && (
          <span className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/60 text-white text-[10px] rounded backdrop-blur-sm">
            {car.images.length} {T.common.photos}
          </span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-foreground mb-0.5">{car.brand} {car.model}</h3>
        <p className="text-sm text-muted-foreground mb-3">
          {car.year} • {formatMileage(car.mileage, lang)}
          {car.engine_volume ? ` • ${car.engine_volume}л` : ''}
          {car.transmission ? ` • ${TRANSMISSION_LABELS[car.transmission] ?? car.transmission}` : ''}
        </p>
        <div className="flex items-center justify-between">
          <p className="text-xl font-semibold text-foreground">{formatPrice(Number(car.price))}</p>
          <span className="text-xs text-muted-foreground">{timeAgo(car.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

function ListRow({ car }: { car: CarType }) {
  const { isFavorite, toggle } = useFavorites();
  const { lang, T } = useLanguage();
  const fav = isFavorite(car.id);
  const img = car.images.find(i => i.is_primary) ?? car.images[0];
  const isSoldOrInactive = car.status === 'sold' || car.status === 'inactive';
  const STATUS_LABELS: Record<string, string> = { available: T.status.available, reserved: T.status.reserved, sold: T.status.sold, inactive: T.status.inactive };
  const TRANSMISSION_LABELS: Record<string, string> = T.transmission;
  const FUEL_LABELS: Record<string, string> = T.fuel;
  function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return T.common.today;
    if (days === 1) return T.common.yesterday;
    if (days < 7) return `${days} ${T.common.daysAgo}`;
    return new Date(dateStr).toLocaleDateString(lang === 'ru' ? 'ru-RU' : 'en-US', { day: 'numeric', month: 'short' });
  }
  const specs = [
    car.engine_volume && `${car.engine_volume}л`,
    car.engine_power && `${car.engine_power} л.с.`,
    car.transmission && TRANSMISSION_LABELS[car.transmission],
    car.fuel_type && FUEL_LABELS[car.fuel_type],
    car.body_type,
    car.color,
  ].filter(Boolean);

  return (
    <Link to={`/car/${car.id}`}
      className="group flex gap-4 bg-card rounded-lg border border-border overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25 p-3">
      {/* Фото */}
      <div className="relative w-44 flex-shrink-0 rounded-lg overflow-hidden bg-secondary self-stretch min-h-[110px]">
        {img ? (
          <ImageWithFallback src={img.url || img.thumbnail_url} alt={`${car.brand} ${car.model}`}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${isSoldOrInactive ? 'brightness-75' : ''}`} />
        ) : (
          <CarImagePlaceholder />
        )}
        {car.images.length > 1 && (
          <span className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/60 text-white text-[10px] rounded backdrop-blur-sm">
            {car.images.length} {T.common.photos}
          </span>
        )}
      </div>

      {/* Контент */}
      <div className="flex-1 min-w-0 flex flex-col py-1">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-foreground">{car.brand} {car.model} {car.year}</h3>
            {car.mileage === 0 && <span className="px-2 py-0.5 bg-accent text-accent-foreground rounded-full text-xs font-medium">{T.status.new}</span>}
            {car.status && car.status !== 'available' && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                car.status === 'reserved' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
              }`}>
                {STATUS_LABELS[car.status] ?? car.status}
              </span>
            )}
          </div>
          <button onClick={e => { e.preventDefault(); toggle(car.id); }}
            className="p-1.5 rounded-full hover:bg-secondary transition-colors flex-shrink-0">
            <Heart className={`w-4 h-4 ${fav ? 'fill-destructive text-destructive' : 'text-muted-foreground'}`} />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mt-1">{formatMileage(car.mileage, lang)}</p>

        {specs.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {specs.map((s, i) => (
              <span key={i} className="text-xs px-2 py-0.5 bg-secondary rounded-md text-muted-foreground">{s}</span>
            ))}
          </div>
        )}

        {car.description && (
          <p className="text-sm text-muted-foreground mt-2 line-clamp-1">{car.description}</p>
        )}

        <div className="flex items-center justify-between mt-auto pt-2">
          <p className="text-xl font-semibold text-foreground">{formatPrice(Number(car.price))}</p>
          <span className="text-xs text-muted-foreground">{timeAgo(car.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

// Inline search

function BoardSearch({ cars, onSelect }: { cars: CarType[]; onSelect: (car: CarType | null) => void }) {
  const { T } = useLanguage();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [hi, setHi] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) { setIsOpen(false); setHi(-1); } };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const filtered = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return cars.filter(c => c.brand.toLowerCase().includes(q) || c.model.toLowerCase().includes(q) || `${c.brand} ${c.model}`.toLowerCase().includes(q)).slice(0, 8);
  }, [cars, query]);
  const handleSelect = (car: CarType) => { onSelect(car); setQuery(''); setIsOpen(false); setHi(-1); };
  return (
    <div className="relative w-full" ref={ref}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input ref={inputRef} type="text" value={query}
          onChange={e => { setQuery(e.target.value); setIsOpen(true); }}
          onFocus={() => query && setIsOpen(true)}
          onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
            if (e.key === 'ArrowDown') { e.preventDefault(); setHi(i => Math.min(i + 1, filtered.length - 1)); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); setHi(i => Math.max(i - 1, 0)); }
            else if (e.key === 'Enter' && hi >= 0 && filtered[hi]) { e.preventDefault(); handleSelect(filtered[hi]); }
            else if (e.key === 'Escape') { setIsOpen(false); setHi(-1); }
          }}
          placeholder={T.catalog.searchCatalog}
          className="w-full pl-10 pr-10 py-2.5 bg-secondary text-foreground placeholder:text-muted-foreground rounded-xl outline-none focus:ring-2 focus:ring-primary text-sm border border-border focus:border-primary"
        />
        {query && <button type="button" onClick={() => { setQuery(''); onSelect(null); }} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>}
      </div>
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-30 w-full mt-2 bg-card border border-border rounded-xl shadow-lg overflow-hidden">
          {filtered.map((car, i) => {
            const img = car.images.find(x => x.is_primary) ?? car.images[0];
            return (
              <button key={car.id} type="button" onMouseEnter={() => setHi(i)} onClick={() => handleSelect(car)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${hi === i ? 'bg-secondary' : 'hover:bg-secondary/50'}`}>
                <div className="w-12 h-9 bg-secondary rounded overflow-hidden flex-shrink-0 border border-border">
                  {img && (img.url || img.thumbnail_url)
                    ? <ImageWithFallback src={img.url || img.thumbnail_url} alt="" className="w-full h-full object-cover" />
                    : <CarImagePlaceholder />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground truncate">{car.brand} {car.model} {car.year}</p>
                  <p className="text-xs text-muted-foreground">{formatMileage(car.mileage)} • {formatPrice(Number(car.price))}</p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Page

export function CatalogPage() {
  useEffect(() => { window.scrollTo(0, 0); }, []);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { T, lang } = useLanguage();
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(
    () => (localStorage.getItem('catalogViewMode') as 'grid' | 'list') ?? 'grid'
  );

  const handleSetViewMode = useCallback((mode: 'grid' | 'list') => {
    setViewMode(mode);
    localStorage.setItem('catalogViewMode', mode);
  }, []);

  const FUELS = [
    ['petrol', T.fuel.petrol], ['diesel', T.fuel.diesel],
    ['electric', T.fuel.electric], ['hybrid', T.fuel.hybrid], ['gas', T.fuel.gas],
  ] as const;

  const [displayPriceMin, setDisplayPriceMin] = useState('');
  const [displayPriceMax, setDisplayPriceMax] = useState('');
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');
  const [displayMileageMin, setDisplayMileageMin] = useState('');
  const [displayMileageMax, setDisplayMileageMax] = useState('');
  const [mileageMin, setMileageMin] = useState('');
  const [mileageMax, setMileageMax] = useState('');
  const [displayYearMin, setDisplayYearMin] = useState('');
  const [displayYearMax, setDisplayYearMax] = useState('');
  const [yearMin, setYearMin] = useState('');
  const [yearMax, setYearMax] = useState('');
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedTransmissions, setSelectedTransmissions] = useState<Transmission[]>([]);
  const [selectedFuels, setSelectedFuels] = useState<FuelType[]>([]);
  const [selectedColors, setSelectedColors] = useState<string[]>([]);
  const [selectedBodyTypes, setSelectedBodyTypes] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<CarFilters['sort_by']>('date_desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  const [marks, setMarks] = useState<CatalogMark[]>([]);
  const [catalogColors, setCatalogColors] = useState<CatalogColor[]>([]);
  const [availableModels, setAvailableModels] = useState<CatalogModel[]>([]);
  const [selectedGenIds, setSelectedGenIds] = useState<string[]>([]);
  const [selectedConfIds, setSelectedConfIds] = useState<string[]>([]);
  const [selectedModifIds, setSelectedModifIds] = useState<string[]>([]);
  const [availableGens, setAvailableGens] = useState<CatalogGeneration[]>([]);
  const [availableConfs, setAvailableConfs] = useState<CatalogConfiguration[]>([]);
  const [availableModifs, setAvailableModifs] = useState<CatalogModification[]>([]);

  const [allCars, setAllCars] = useState<CarType[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const b = searchParams.get('brands'); if (b) setSelectedBrands(b.split(',').filter(Boolean));
    const md = searchParams.get('models'); if (md) setSelectedModels(md.split(',').filter(Boolean));
    const t = searchParams.get('transmissions'); if (t) setSelectedTransmissions(t.split(',') as Transmission[]);
    const f = searchParams.get('fuels'); if (f) setSelectedFuels(f.split(',') as FuelType[]);
    const c = searchParams.get('colors'); if (c) setSelectedColors(c.split(',').filter(Boolean));
    const bt = searchParams.get('body_types'); if (bt) setSelectedBodyTypes(bt.split(',').filter(Boolean));
    const pMin = searchParams.get('price_min'); if (pMin) { setDisplayPriceMin(pMin); setPriceMin(pMin); }
    const pMax = searchParams.get('price_max'); if (pMax) { setDisplayPriceMax(pMax); setPriceMax(pMax); }
    const mMin = searchParams.get('mileage_min'); if (mMin) { setDisplayMileageMin(mMin); setMileageMin(mMin); }
    const mMax = searchParams.get('mileage_max'); if (mMax) { setDisplayMileageMax(mMax); setMileageMax(mMax); }
    const yMin = searchParams.get('year_min'); if (yMin) { setDisplayYearMin(yMin); setYearMin(yMin); }
    const yMax = searchParams.get('year_max'); if (yMax) { setDisplayYearMax(yMax); setYearMax(yMax); }
    const s = searchParams.get('sort_by'); if (s) setSortBy(s as CarFilters['sort_by']);
    const q = searchParams.get('q'); if (q) setSearchQuery(q);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedBrands.length) params.set('brands', selectedBrands.join(','));
    if (selectedModels.length) params.set('models', selectedModels.join(','));
    if (selectedTransmissions.length) params.set('transmissions', selectedTransmissions.join(','));
    if (selectedFuels.length) params.set('fuels', selectedFuels.join(','));
    if (selectedColors.length) params.set('colors', selectedColors.join(','));
    if (selectedBodyTypes.length) params.set('body_types', selectedBodyTypes.join(','));
    if (priceMin) params.set('price_min', priceMin);
    if (priceMax) params.set('price_max', priceMax);
    if (mileageMin) params.set('mileage_min', mileageMin);
    if (mileageMax) params.set('mileage_max', mileageMax);
    if (yearMin) params.set('year_min', yearMin);
    if (yearMax) params.set('year_max', yearMax);
    if (sortBy && sortBy !== 'date_desc') params.set('sort_by', sortBy);
    if (searchQuery) params.set('q', searchQuery);
    if (params.toString() !== searchParams.toString()) setSearchParams(params);
  }, [selectedBrands, selectedModels, selectedTransmissions, selectedFuels, selectedColors, selectedBodyTypes, priceMin, priceMax, mileageMin, mileageMax, yearMin, yearMax, sortBy, searchQuery]);

  useEffect(() => {
    catalogApi.searchMarks('').then(setMarks).catch(() => {});
    catalogApi.getColors().then(setCatalogColors).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedBrands.length === 0) { setAvailableModels([]); setSelectedModels([]); return; }
    const ids = selectedBrands
      .map(name => marks.find(m => markLabel(m) === name)?.id)
      .filter(Boolean) as string[];
    if (ids.length === 0) return;
    Promise.all(ids.map(id => catalogApi.getModels(id)))
      .then(results => setAvailableModels(results.flat()))
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBrands, marks]);

  useEffect(() => {
    setSelectedGenIds([]); setSelectedConfIds([]); setSelectedModifIds([]);
    setAvailableGens([]); setAvailableConfs([]); setAvailableModifs([]);
    if (selectedModels.length !== 1) return;
    const modelId = availableModels.find(m => modelLabel(m) === selectedModels[0])?.id;
    if (!modelId) return;
    catalogApi.getGenerations(modelId).then(setAvailableGens).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedModels, availableModels]);

  useEffect(() => {
    setSelectedConfIds([]); setSelectedModifIds([]);
    setAvailableConfs([]); setAvailableModifs([]);
    if (selectedGenIds.length === 0) return;
    Promise.all(selectedGenIds.map(id => catalogApi.getConfigurations(id)))
      .then(results => setAvailableConfs(results.flat()))
      .catch(() => {});
  }, [selectedGenIds]);

  useEffect(() => {
    setSelectedModifIds([]);
    setAvailableModifs([]);
    if (selectedConfIds.length === 0) return;
    Promise.all(selectedConfIds.map(id => catalogApi.getModifications(id)))
      .then(results => setAvailableModifs(results.flat()))
      .catch(() => {});
  }, [selectedConfIds]);

  const apiFilters: CarFilters = useMemo(() => {
    const f: CarFilters = { sort_by: sortBy };
    if (priceMin) f.price_from = Number(priceMin);
    if (priceMax) f.price_to = Number(priceMax);
    if (yearMin) f.year_from = Number(yearMin);
    if (yearMax) f.year_to = Number(yearMax);
    return f;
  }, [sortBy, priceMin, priceMax, yearMin, yearMax]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(null); setAllCars([]); setNextCursor(null); setHasMore(false);
    carsApi.list({ ...apiFilters, limit: PAGE_SIZE })
      .then(async res => {
        if (cancelled) return;
        setAllCars(res.data);
        setNextCursor(res.next_cursor);
        setHasMore(res.next_cursor !== null);
        setLoading(false);
        // Enrich with images in the background
        const enriched = await enrichWithImages(res.data);
        if (!cancelled) setAllCars(enriched);
      })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(apiFilters)]);

  const loadMore = useCallback(() => {
    if (loadingMore || !hasMore || !nextCursor) return;
    setLoadingMore(true);
    carsApi.list({ ...apiFilters, cursor: nextCursor, limit: PAGE_SIZE })
      .then(async res => {
        setAllCars(prev => [...prev, ...res.data]);
        setNextCursor(res.next_cursor);
        setHasMore(res.next_cursor !== null);
        setLoadingMore(false);
        // Enrich new page with images
        const enriched = await enrichWithImages(res.data);
        setAllCars(prev => {
          const enrichedIds = new Set(enriched.map(c => c.id));
          return prev.map(c => enrichedIds.has(c.id) ? (enriched.find(e => e.id === c.id) ?? c) : c);
        });
      })
      .catch(() => setLoadingMore(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingMore, hasMore, nextCursor, JSON.stringify(apiFilters)]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || !hasMore || loading) return;
    const observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore(); }, { rootMargin: '400px' });
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore, hasMore, loading]);

  const bodyTypeOptions = useMemo(() => {
    const seen = new Set<string>();
    return allCars
      .filter(c => c.body_type && !seen.has(c.body_type) && !!seen.add(c.body_type))
      .map(c => ({ value: c.body_type!, label: labelBodyType(c.body_type!, lang) }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [allCars, lang]);

  const transmissionOptions = useMemo(() => {
    const seen = new Set<string>();
    return allCars
      .filter(c => c.transmission && !seen.has(c.transmission) && !!seen.add(c.transmission))
      .map(c => ({ value: c.transmission! as Transmission, label: labelTransmission(c.transmission!, T) }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [allCars, T]);

  const filteredCars = useMemo(() => {
    let result = [...allCars];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(c => c.brand.toLowerCase().includes(q) || c.model.toLowerCase().includes(q) || `${c.brand} ${c.model}`.toLowerCase().includes(q) || c.description?.toLowerCase().includes(q));
    }
    if (selectedBrands.length > 0) result = result.filter(c => selectedBrands.includes(c.brand));
    if (selectedModels.length > 0) result = result.filter(c => selectedModels.includes(c.model));
    if (selectedTransmissions.length > 0) result = result.filter(c => c.transmission && selectedTransmissions.includes(c.transmission as Transmission));
    if (selectedFuels.length > 0) result = result.filter(c => !c.fuel_type || selectedFuels.some(f => matchesFuel(c.fuel_type!, f)));
    if (selectedColors.length > 0) {
      result = result.filter(c => c.color && selectedColors.includes(c.color));
    }
    if (selectedBodyTypes.length > 0) result = result.filter(c => c.body_type && selectedBodyTypes.includes(c.body_type));
    const pMin = priceMin ? Number(priceMin) : null;
    const pMax = priceMax ? Number(priceMax) : null;
    const mMin = mileageMin ? Number(mileageMin) : null;
    const mMax = mileageMax ? Number(mileageMax) : null;
    if (pMin !== null || pMax !== null) result = result.filter(c => { const p = Number(c.price); return (pMin === null || p >= pMin) && (pMax === null || p <= pMax); });
    if (mMin !== null || mMax !== null) result = result.filter(c => { const m = Number(c.mileage); return (mMin === null || m >= mMin) && (mMax === null || m <= mMax); });
    if (selectedGenIds.length > 0) {
      result = result.filter(c => selectedGenIds.some(gid => {
        const gen = availableGens.find(g => g.id === gid);
        return gen && (!gen.year_from || c.year >= gen.year_from) && (!gen.year_to || c.year <= gen.year_to);
      }));
    }
    if (selectedConfIds.length > 0) {
      const confBodyTypes = selectedConfIds
        .map(cid => availableConfs.find(cf => cf.id === cid))
        .filter(Boolean)
        .map(cf => cf!.body_type)
        .filter(Boolean);
      if (confBodyTypes.length > 0) result = result.filter(c => confBodyTypes.includes(c.body_type));
    }
    return result;
  }, [allCars, searchQuery, selectedBrands, selectedModels, selectedTransmissions, selectedFuels, selectedColors, selectedBodyTypes, priceMin, priceMax, mileageMin, mileageMax, selectedGenIds, selectedConfIds, availableGens, availableConfs]);

  const resetFilters = () => {
    setSelectedBrands([]); setSelectedModels([]); setSelectedGenIds([]); setSelectedConfIds([]); setSelectedModifIds([]);
    setSelectedTransmissions([]); setSelectedFuels([]); setSelectedColors([]); setSelectedBodyTypes([]);
    setSortBy('date_desc'); setSearchQuery('');
    setPriceMin(''); setPriceMax(''); setMileageMin(''); setMileageMax(''); setYearMin(''); setYearMax('');
    setDisplayPriceMin(''); setDisplayPriceMax(''); setDisplayMileageMin(''); setDisplayMileageMax(''); setDisplayYearMin(''); setDisplayYearMax('');
    setSearchParams({});
  };

  const hasActiveFilters = selectedBrands.length > 0 || selectedModels.length > 0 || selectedGenIds.length > 0 || selectedConfIds.length > 0 || selectedModifIds.length > 0 || selectedTransmissions.length > 0 || selectedFuels.length > 0 || selectedColors.length > 0 || selectedBodyTypes.length > 0 || priceMin || priceMax || mileageMin || mileageMax || yearMin || yearMax;

  const filtersPanel = (
    <div className="bg-card rounded-xl border border-border p-5 space-y-5">
      <div>
        <h3 className="font-semibold text-foreground mb-2">{T.catalog.price}</h3>
        <div className="flex gap-2">
          <NumberFilterInput placeholder={T.common.from} value={displayPriceMin} onChange={setDisplayPriceMin} onConfirm={setPriceMin} format />
          <NumberFilterInput placeholder={T.common.to} value={displayPriceMax} onChange={setDisplayPriceMax} onConfirm={setPriceMax} format />
        </div>
      </div>
      <div>
        <h3 className="font-semibold text-foreground mb-2">{T.catalog.year}</h3>
        <div className="flex gap-2">
          <NumberFilterInput placeholder={T.common.from} value={displayYearMin} onChange={setDisplayYearMin} onConfirm={setYearMin} />
          <NumberFilterInput placeholder={T.common.to} value={displayYearMax} onChange={setDisplayYearMax} onConfirm={setYearMax} />
        </div>
      </div>
      <div>
        <h3 className="font-semibold text-foreground mb-2">{T.catalog.mileage}</h3>
        <div className="flex gap-2">
          <NumberFilterInput placeholder={T.common.from} value={displayMileageMin} onChange={setDisplayMileageMin} onConfirm={setMileageMin} format />
          <NumberFilterInput placeholder={T.common.to} value={displayMileageMax} onChange={setDisplayMileageMax} onConfirm={setMileageMax} format />
        </div>
      </div>
      <SearchableMultiSelect label={T.catalog.brand} options={marks.map(m => ({ value: markLabel(m), label: markLabel(m) }))} selected={selectedBrands} onToggle={v => setSelectedBrands(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])} onClear={() => { setSelectedBrands([]); setSelectedModels([]); }} />
      {selectedBrands.length > 0 && availableModels.length > 0 && (
        <SearchableMultiSelect label={T.catalog.model} options={availableModels.map(m => ({ value: modelLabel(m), label: modelLabel(m) }))} selected={selectedModels} onToggle={v => setSelectedModels(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])} onClear={() => setSelectedModels([])} />
      )}
      {selectedModels.length === 1 && availableGens.length > 0 && (
        <SearchableMultiSelect
          label={T.catalog.generation}
          options={availableGens.map(g => ({ value: g.id, label: g.name ?? `${g.year_from ?? ''}–${g.year_to ?? '...'}` }))}
          selected={selectedGenIds}
          onToggle={v => setSelectedGenIds(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
          onClear={() => setSelectedGenIds([])}
        />
      )}
      {selectedGenIds.length > 0 && availableConfs.length > 0 && (
        <SearchableMultiSelect
          label={T.catalog.configuration}
          options={availableConfs.map(c => ({ value: c.id, label: c.name ?? c.id }))}
          selected={selectedConfIds}
          onToggle={v => setSelectedConfIds(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
          onClear={() => setSelectedConfIds([])}
        />
      )}
      {selectedConfIds.length > 0 && availableModifs.length > 0 && (
        <SearchableMultiSelect
          label={T.catalog.modification}
          options={availableModifs.map(m => ({ value: m.id, label: m.name ?? m.group_name ?? m.id }))}
          selected={selectedModifIds}
          onToggle={v => setSelectedModifIds(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
          onClear={() => setSelectedModifIds([])}
        />
      )}
      <SearchableMultiSelect
        label={T.catalog.transmission}
        options={transmissionOptions}
        selected={selectedTransmissions}
        onToggle={v => setSelectedTransmissions(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
        onClear={() => setSelectedTransmissions([])}
      />
      <SearchableMultiSelect label={T.catalog.fuelType} options={FUELS.map(([v, l]) => ({ value: v as FuelType, label: l }))} selected={selectedFuels} onToggle={v => setSelectedFuels(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])} onClear={() => setSelectedFuels([])} />
      <SearchableMultiSelect
        label={T.catalog.bodyType}
        options={bodyTypeOptions}
        selected={selectedBodyTypes}
        onToggle={v => setSelectedBodyTypes(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
        onClear={() => setSelectedBodyTypes([])}
      />
      <ColorFilter
        colors={catalogColors}
        selected={selectedColors}
        onToggle={v => setSelectedColors(p => p.includes(v) ? p.filter(x => x !== v) : [...p, v])}
        onClear={() => setSelectedColors([])}
      />
      {hasActiveFilters && (
        <button onClick={resetFilters} className="w-full px-4 py-2 text-sm text-destructive hover:bg-destructive/10 rounded-lg transition-colors border border-destructive/30">
          {T.catalog.resetFilters}
        </button>
      )}
    </div>
  );

  const skeletonGrid = (
    <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4' : 'space-y-3'}>
      {Array.from({ length: viewMode === 'grid' ? 6 : 5 }).map((_, i) => (
        viewMode === 'grid' ? (
          <div key={i} className="bg-card rounded-lg border border-border overflow-hidden">
            <div className="aspect-[4/3] bg-secondary animate-pulse" />
            <div className="p-4 space-y-2">
              <div className="h-5 bg-secondary rounded animate-pulse" />
              <div className="h-4 bg-secondary rounded animate-pulse w-2/3" />
              <div className="h-6 bg-secondary rounded animate-pulse w-1/2 mt-3" />
            </div>
          </div>
        ) : (
          <div key={i} className="bg-card rounded-lg border border-border p-3 flex gap-4">
            <div className="w-44 h-28 bg-secondary rounded-lg animate-pulse flex-shrink-0" />
            <div className="flex-1 space-y-2 py-1">
              <div className="h-5 bg-secondary rounded animate-pulse w-3/4" />
              <div className="h-4 bg-secondary rounded animate-pulse w-1/2" />
              <div className="h-4 bg-secondary rounded animate-pulse w-2/3" />
              <div className="h-6 bg-secondary rounded animate-pulse w-1/3 mt-auto" />
            </div>
          </div>
        )
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Title row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">{T.catalog.title}</h1>
            {/* <p className="text-muted-foreground mt-0.5">
              {loading ? T.common.loading : `${filteredCars.length}${hasMore ? '+' : ''}`}
            </p> */}
          </div>
          <Link to="/sell"
            className="hidden sm:flex items-center gap-2 px-4 py-2.5 bg-accent text-accent-foreground rounded-xl hover:opacity-90 transition-opacity text-sm font-medium self-start">
            <Plus className="w-4 h-4" /> {T.catalog.createListing}
          </Link>
        </div>

        <div className="flex gap-6">
          {/* Desktop sidebar — старая боковая панель */}
          <aside className="hidden md:block w-64 flex-shrink-0">
            <div className="sticky top-20">{filtersPanel}</div>
          </aside>

          {/* Mobile filters drawer */}
          {mobileFiltersOpen && (
            <div className="fixed inset-0 z-50 md:hidden">
              <div className="absolute inset-0 bg-black/60" onClick={() => setMobileFiltersOpen(false)} />
              <div className="absolute right-0 top-0 bottom-0 w-80 max-w-full bg-background border-l border-border p-5 overflow-y-auto">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-foreground">{T.catalog.filters}</h2>
                  <button onClick={() => setMobileFiltersOpen(false)} className="p-2 hover:bg-secondary rounded-lg transition-colors">
                    <X className="w-5 h-5 text-foreground" />
                  </button>
                </div>
                <div className="mb-4">
                  <SortDropdown value={sortBy} onChange={setSortBy} />
                </div>
                {filtersPanel}
              </div>
            </div>
          )}

          {/* Listings */}
          <div className="flex-1 min-w-0">
            {/* Search + sort + view — на уровне верхнего края фильтра */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex-1">
                <BoardSearch cars={allCars} onSelect={car => { if (car) navigate(`/car/${car.id}`); }} />
              </div>
              <button onClick={() => setMobileFiltersOpen(true)}
                className="md:hidden flex items-center gap-2 px-3 py-2.5 bg-secondary rounded-xl border border-border hover:bg-secondary/80 transition-colors flex-shrink-0">
                <SlidersHorizontal className="w-4 h-4 text-foreground" />
                {hasActiveFilters && <span className="w-1.5 h-1.5 bg-primary rounded-full" />}
              </button>
              <SortDropdown value={sortBy} onChange={setSortBy} />
              <div className="flex items-center border border-border rounded-lg overflow-hidden flex-shrink-0">
                <button onClick={() => handleSetViewMode('grid')} title="Сетка"
                  className={`p-2.5 transition-colors ${viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'bg-card text-muted-foreground hover:text-foreground'}`}>
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button onClick={() => handleSetViewMode('list')} title="Список"
                  className={`p-2.5 transition-colors ${viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'bg-card text-muted-foreground hover:text-foreground'}`}>
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>

            {error && (
              <div className="text-center py-16">
                <p className="text-destructive mb-4">Ошибка загрузки: {error}</p>
                <button onClick={() => window.location.reload()} className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg hover:opacity-90">{T.common.reset}</button>
              </div>
            )}

            {loading && !error && skeletonGrid}

            {!loading && !error && filteredCars.length > 0 && (
              <>
                {viewMode === 'grid' ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredCars.map(car => <GridCard key={car.id} car={car} />)}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredCars.map(car => <ListRow key={car.id} car={car} />)}
                  </div>
                )}

                {hasMore && (
                  <div ref={sentinelRef} className="mt-4">
                    {loadingMore && (viewMode === 'grid' ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <div key={i} className="bg-card rounded-lg border border-border overflow-hidden">
                            <div className="aspect-[4/3] bg-secondary animate-pulse" />
                            <div className="p-4 space-y-2"><div className="h-5 bg-secondary rounded animate-pulse" /><div className="h-6 bg-secondary rounded animate-pulse w-1/2 mt-2" /></div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <div key={i} className="bg-card rounded-lg border border-border p-3 flex gap-4">
                            <div className="w-44 h-28 bg-secondary rounded-lg animate-pulse flex-shrink-0" />
                            <div className="flex-1 space-y-2 py-1"><div className="h-5 bg-secondary rounded animate-pulse w-3/4" /><div className="h-6 bg-secondary rounded animate-pulse w-1/3 mt-auto" /></div>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}

                {!hasMore && allCars.length > PAGE_SIZE && (
                  <p className="text-center text-sm text-muted-foreground mt-8 pb-4">
                    {allCars.length}
                  </p>
                )}
              </>
            )}

            {!loading && !error && filteredCars.length === 0 && (
              <div className="text-center py-20">
                <p className="text-4xl mb-4">🔍</p>
                <h3 className="text-xl font-semibold text-foreground mb-2">{T.catalog.noResults}</h3>
                <p className="text-muted-foreground mb-6">{T.catalog.noResultsDesc}</p>
                <button onClick={resetFilters} className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg hover:opacity-90">{T.catalog.resetFilters}</button>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

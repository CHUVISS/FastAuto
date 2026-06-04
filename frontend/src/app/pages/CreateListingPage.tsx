import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, Link } from 'react-router';
import { ChevronRight, Upload, X, CheckCircle, Loader2, Search, Trash2, Star } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../hooks/useAuth';
import {
  catalogApi,
  listingsApi,
  type CatalogMark,
  type CatalogModel,
  type CatalogGeneration,
  type CatalogConfiguration,
  type CatalogModification,
  type CatalogColor,
  type GeoCity,
  type MyListingImage,
} from '../api/catalog';
import { viewingsApi } from '../api/viewings';
import { useLanguage } from '../i18n/LanguageContext';

const inputCls = 'w-full px-4 py-2.5 bg-secondary text-foreground placeholder:text-muted-foreground rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary border border-border focus:border-primary transition-colors';
const labelCls = 'block text-sm font-medium text-foreground mb-1.5';

const TIME_SLOTS = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00'];

function SearchSelect<T extends { id: string }>({
  options, value, onChange, getLabel, placeholder, searchPlaceholder, disabled, loading, noResults,
}: {
  options: T[];
  value: string;
  onChange: (id: string, item: T) => void;
  getLabel: (item: T) => string;
  placeholder: string;
  searchPlaceholder?: string;
  disabled?: boolean;
  loading?: boolean;
  noResults?: string;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selected = options.find(o => o.id === value);
  const filtered = q.trim()
    ? options.filter(o => getLabel(o).toLowerCase().includes(q.toLowerCase()))
    : options;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        disabled={disabled || loading}
        onClick={() => { setOpen(o => !o); setQ(''); }}
        className={`${inputCls} flex items-center justify-between gap-2 text-left ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
      >
        <span className={selected ? 'text-foreground' : 'text-muted-foreground'}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin inline-block" /> : selected ? getLabel(selected) : placeholder}
        </span>
        {loading
          ? <Loader2 className="w-4 h-4 animate-spin flex-shrink-0 text-muted-foreground" />
          : <ChevronRight className={`w-4 h-4 flex-shrink-0 text-muted-foreground transition-transform ${open ? 'rotate-90' : ''}`} />
        }
      </button>
      {open && !loading && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg z-50 max-h-64 overflow-hidden flex flex-col">
          {options.length > 6 && (
            <div className="p-2 border-b border-border">
              <div className="flex items-center gap-2 px-2 py-1.5 bg-secondary rounded-md">
                <Search className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                <input
                  autoFocus
                  type="text"
                  value={q}
                  onChange={e => setQ(e.target.value)}
                  placeholder={searchPlaceholder}
                  className="flex-1 text-sm bg-transparent outline-none text-foreground placeholder:text-muted-foreground"
                />
              </div>
            </div>
          )}
          <ul className="overflow-y-auto">
            {filtered.length === 0 ? (
              <li className="px-3 py-3 text-sm text-muted-foreground text-center">{noResults}</li>
            ) : (
              filtered.map(item => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => { onChange(item.id, item); setOpen(false); setQ(''); }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-secondary transition-colors ${item.id === value ? 'text-primary font-medium' : 'text-foreground'}`}
                  >
                    {getLabel(item)}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

export function CreateListingPage() {
  const { id: editId } = useParams<{ id?: string }>();
  const isEdit = Boolean(editId);
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { T } = useLanguage();
  const L = T.listing;

  const STEPS = L.steps;
  const CONDITION_OPTIONS = L.conditionOptions;
  const WEEK_DAYS = L.weekDays;

  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [editLoading, setEditLoading] = useState(isEdit);

  // Step 1 — car selection
  const [marks, setMarks] = useState<CatalogMark[]>([]);
  const [markSearch] = useState('');
  const [marksLoading, setMarksLoading] = useState(false);
  const [selectedMark, setSelectedMark] = useState('');
  const [originalModId, setOriginalModId] = useState('');

  const [models, setModels] = useState<CatalogModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('');

  const [generations, setGenerations] = useState<CatalogGeneration[]>([]);
  const [gensLoading, setGensLoading] = useState(false);
  const [selectedGen, setSelectedGen] = useState('');

  const [configurations, setConfigurations] = useState<CatalogConfiguration[]>([]);
  const [confsLoading, setConfsLoading] = useState(false);
  const [selectedConf, setSelectedConf] = useState('');

  const [modifications, setModifications] = useState<CatalogModification[]>([]);
  const [modsLoading, setModsLoading] = useState(false);
  const [selectedMod, setSelectedMod] = useState('');

  // Step 2 — details
  const [year, setYear] = useState('');
  const [price, setPrice] = useState('');
  const [mileage, setMileage] = useState('');
  const [condition, setCondition] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [vin, setVin] = useState('');
  const [description, setDescription] = useState('');

  const [colors, setColors] = useState<CatalogColor[]>([]);
  const [cities, setCities] = useState<GeoCity[]>([]);

  // Viewing schedule
  const [viewingDays, setViewingDays] = useState<number[]>([]);
  const [viewingFrom, setViewingFrom] = useState('10:00');
  const [viewingTo, setViewingTo] = useState('18:00');
  const [licensePlate, setLicensePlate] = useState('');
  const [saleAddress, setSaleAddress] = useState('');
  const [acceptsCash, setAcceptsCash] = useState(false);
  const [acceptsTransfer, setAcceptsTransfer] = useState(false);

  const toggleDay = (i: number) =>
    setViewingDays(prev => prev.includes(i) ? prev.filter(d => d !== i) : [...prev, i]);

  const viewingEnabled = viewingDays.length > 0;

  // Step 3 — images
  const [images, setImages] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [existingImages, setExistingImages] = useState<MyListingImage[]>([]);
  const [deletingImageId, setDeletingImageId] = useState<string | null>(null);

  // Load marks on mount (always)
  useEffect(() => {
    setMarksLoading(true);
    catalogApi.searchMarks('').then(setMarks).catch(() => setMarks([])).finally(() => setMarksLoading(false));
    if (!isEdit) {
      catalogApi.getColors().then(setColors).catch(() => setColors([]));
      catalogApi.getPopularCities().then(setCities).catch(() => setCities([]));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load edit data
  useEffect(() => {
    if (!editId) return;
    setEditLoading(true);
    Promise.all([
      listingsApi.get(editId),
      catalogApi.getColors(),
      catalogApi.getPopularCities(),
    ]).then(async ([listing, cols, cts]) => {
      setYear(String(listing.year));
      setPrice(String(listing.price));
      setMileage(String(listing.mileage));
      setCondition(listing.condition ?? '');
      setSelectedColor(listing.color_id ?? '');
      setSelectedCity(listing.city_id ?? '');
      setVin(listing.vin ?? '');
      setDescription(listing.description ?? '');
      setLicensePlate(listing.license_plate ?? '');
      setSaleAddress(listing.sale_address ?? '');
      setAcceptsCash(Boolean(listing.accepts_cash));
      setAcceptsTransfer(Boolean(listing.accepts_transfer));
      setColors(cols);
      setCities(cts);
      if (listing.modification_id) setOriginalModId(listing.modification_id);
      if (listing.images && listing.images.length > 0) {
        setExistingImages([...listing.images].sort((a, b) => a.sort_order - b.sort_order));
      }

      setSelectedMark(listing.mark_id);
      try {
        setModelsLoading(true);
        const mods = await catalogApi.getModels(listing.mark_id);
        setModels(mods);
        setSelectedModel(listing.model_id);
        setGensLoading(true);
        const gens = await catalogApi.getGenerations(listing.model_id);
        setGenerations(gens);
      } catch {
        // silently fail
      } finally {
        setModelsLoading(false);
        setGensLoading(false);
      }
    }).catch(() => {
      toast.error(L.errorLoad);
      navigate('/profile?tab=drafts');
    }).finally(() => setEditLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editId]);

  // Mark search debounce
  const markDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (markDebounce.current) clearTimeout(markDebounce.current);
    if (!markSearch.trim() && marks.length > 0) return;
    markDebounce.current = setTimeout(() => {
      setMarksLoading(true);
      catalogApi.searchMarks(markSearch).then(setMarks).catch(() => setMarks([])).finally(() => setMarksLoading(false));
    }, 300);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [markSearch]);

  const handleMarkChange = (id: string) => {
    setSelectedMark(id);
    setSelectedModel(''); setModels([]);
    setSelectedGen(''); setGenerations([]);
    setSelectedConf(''); setConfigurations([]);
    setSelectedMod(''); setModifications([]);
    setOriginalModId('');
    setModelsLoading(true);
    catalogApi.getModels(id).then(setModels).catch(() => setModels([])).finally(() => setModelsLoading(false));
  };

  const handleModelChange = (id: string) => {
    setSelectedModel(id);
    setSelectedGen(''); setGenerations([]);
    setSelectedConf(''); setConfigurations([]);
    setSelectedMod(''); setModifications([]);
    setOriginalModId('');
    setGensLoading(true);
    catalogApi.getGenerations(id).then(setGenerations).catch(() => setGenerations([])).finally(() => setGensLoading(false));
  };

  const handleGenChange = (id: string) => {
    setSelectedGen(id);
    setSelectedConf(''); setConfigurations([]);
    setSelectedMod(''); setModifications([]);
    setOriginalModId('');
    setConfsLoading(true);
    catalogApi.getConfigurations(id).then(setConfigurations).catch(() => setConfigurations([])).finally(() => setConfsLoading(false));
  };

  const handleConfChange = (id: string) => {
    setSelectedConf(id);
    setSelectedMod(''); setModifications([]);
    setOriginalModId('');
    setModsLoading(true);
    catalogApi.getModifications(id).then(setModifications).catch(() => setModifications([])).finally(() => setModsLoading(false));
  };

  const handleExistingImageDelete = async (image: MyListingImage) => {
    if (!editId) return;
    setDeletingImageId(image.id);
    try {
      await listingsApi.deleteImage(editId, image.id);
      setExistingImages(prev => prev.filter(img => img.id !== image.id));
      toast.success(L.photoDeleted);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : L.photoDeleteError);
    } finally {
      setDeletingImageId(null);
    }
  };

  const handleImageAdd = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    const next = [...images, ...files].slice(0, 10);
    setImages(next);
    setPreviews(next.map(f => URL.createObjectURL(f)));
    e.target.value = '';
  };

  const handleImageRemove = (i: number) => {
    const next = images.filter((_, idx) => idx !== i);
    setImages(next);
    setPreviews(next.map(f => URL.createObjectURL(f)));
  };

  const saveViewingWindows = async (listingId: string) => {
    if (viewingDays.length === 0) return;
    const windows: Promise<unknown>[] = [];
    for (let week = 0; week < 4; week++) {
      for (const dayIdx of viewingDays) {
        const d = new Date();
        const jsDay = (dayIdx + 1) % 7;
        const diff = (jsDay - d.getDay() + 7) % 7 || 7;
        d.setDate(d.getDate() + diff + week * 7);
        windows.push(
          viewingsApi.createWindow(listingId, {
            window_date: d.toISOString().slice(0, 10),
            time_from: viewingFrom,
            time_to: viewingTo,
          }).catch(() => null)
        );
      }
    }
    await Promise.all(windows);
  };

  const handleSubmit = async () => {
    const modId = selectedMod || originalModId;
    const hasId = vin.trim().length === 17 || licensePlate.trim().length > 0;
    if (!modId || !year || !price || !mileage || !condition || !selectedColor || !selectedCity || !hasId) {
      toast.error(L.fillRequired);
      return;
    }
    if (!acceptsCash && !acceptsTransfer) {
      toast.error(L.paymentRequired);
      return;
    }
    setSubmitting(true);
    try {
      if (isEdit && editId) {
        await listingsApi.update(editId, {
          year: Number(year),
          price: Number(price),
          mileage: Number(mileage),
          condition: condition as 'excellent' | 'good' | 'fair' | 'poor',
          color_id: selectedColor,
          city_id: selectedCity,
          vin: vin.trim() || undefined,
          license_plate: licensePlate.trim() || undefined,
          description: description.trim() || undefined,
          viewing_enabled: viewingEnabled,
          sale_address: saleAddress.trim() || undefined,
          accepts_cash: acceptsCash,
          accepts_transfer: acceptsTransfer,
        });
        if (images.length > 0) {
          try {
            await listingsApi.uploadImages(editId, images);
          } catch {
            toast.error(L.photosErrorEdit);
          }
        }
        await saveViewingWindows(editId);
        toast.success(L.savedSuccess);
        navigate('/profile?tab=drafts');
      } else {
        const listing = await listingsApi.create({
          modification_id: modId,
          year: Number(year),
          price: Number(price),
          mileage: Number(mileage),
          condition: condition as 'excellent' | 'good' | 'fair' | 'poor',
          color_id: selectedColor,
          city_id: selectedCity,
          vin: vin.trim() || undefined,
          license_plate: licensePlate.trim() || undefined,
          description: description.trim() || undefined,
          viewing_enabled: viewingEnabled,
          sale_address: saleAddress.trim() || undefined,
          accepts_cash: acceptsCash,
          accepts_transfer: acceptsTransfer,
        });
        if (images.length > 0) {
          try {
            await listingsApi.uploadImages(listing.id, images);
          } catch {
            toast.error(L.photosErrorButCreated);
          }
        }
        await saveViewingWindows(listing.id);
        try {
          await listingsApi.publish(listing.id);
          toast.success(L.publishedSuccess);
        } catch {
          toast.success(L.savedToDrafts);
        }
        navigate('/profile');
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : isEdit ? L.errorSave : L.errorCreate);
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading || editLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <h1 className="text-2xl font-semibold text-foreground mb-3">{L.loginRequired}</h1>
          <p className="text-muted-foreground mb-6">{L.loginRequiredDesc}</p>
          <Link to="/profile" className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity">
            {T.profile.signIn}
          </Link>
        </div>
      </div>
    );
  }

  const genLabel = (gen: CatalogGeneration) =>
    gen.name ?? `${gen.year_from ?? ''}–${gen.year_to ?? '...'}`;

  const modLabel = (m: CatalogModification) => m.name ?? m.group_name ?? m.id;

  const canGoNext0 = Boolean(selectedMod || originalModId);
  const hasIdentifier = vin.trim().length === 17 || licensePlate.trim().length > 0;
  const hasPaymentMethod = acceptsCash || acceptsTransfer;
  const canGoNext1 = Boolean(
    year && price && mileage && condition && selectedColor && selectedCity &&
    hasIdentifier && hasPaymentMethod &&
    (!viewingEnabled || saleAddress.trim().length > 0)
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
        <h1 className="text-3xl font-semibold text-foreground mb-8">
          {isEdit ? L.editTitle : L.createTitle}
        </h1>

        {/* Progress steps */}
        <div className="flex items-center gap-2 mb-10">
          {STEPS.map((label, i) => (
            <div key={i} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 transition-colors ${
                i < step ? 'bg-accent text-accent-foreground'
                  : i === step ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-muted-foreground'
              }`}>
                {i < step ? <CheckCircle className="w-4 h-4" /> : i + 1}
              </div>
              <span className={`text-sm hidden sm:block ${i === step ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>{label}</span>
              {i < STEPS.length - 1 && <div className={`flex-1 h-px mx-2 ${i < step ? 'bg-accent' : 'bg-border'}`} />}
            </div>
          ))}
        </div>

        <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">

          {/* Step 1: Car selection */}
          {step === 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                {isEdit ? L.changeCarTitle : L.selectCarTitle}
              </h2>

              {isEdit && originalModId && !selectedMod && (
                <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg text-sm text-muted-foreground">
                  {L.carAlreadySelected}
                </div>
              )}

              <div>
                <label className={labelCls}>{L.mark} *</label>
                <SearchSelect
                  options={marks}
                  value={selectedMark}
                  onChange={(id) => handleMarkChange(id)}
                  getLabel={(m) => m.name ?? m.cyrillic_name ?? m.id}
                  placeholder={L.chooseMark}
                  searchPlaceholder={L.searchPlaceholder}
                  noResults={L.noResults}
                  loading={marksLoading}
                />
              </div>

              <div>
                <label className={labelCls}>{L.model} *</label>
                <SearchSelect
                  options={models}
                  value={selectedModel}
                  onChange={(id) => handleModelChange(id)}
                  getLabel={(m) => m.name ?? m.id}
                  placeholder={selectedMark ? L.chooseModel : L.firstChooseMark}
                  searchPlaceholder={L.searchPlaceholder}
                  noResults={L.noResults}
                  disabled={!selectedMark || modelsLoading}
                  loading={modelsLoading}
                />
              </div>

              <div>
                <label className={labelCls}>{L.generation} *</label>
                <SearchSelect
                  options={generations}
                  value={selectedGen}
                  onChange={(id) => handleGenChange(id)}
                  getLabel={genLabel}
                  placeholder={selectedModel ? L.chooseGeneration : L.firstChooseModel}
                  searchPlaceholder={L.searchPlaceholder}
                  noResults={L.noResults}
                  disabled={!selectedModel || gensLoading}
                  loading={gensLoading}
                />
              </div>

              <div>
                <label className={labelCls}>{L.configuration} *</label>
                <SearchSelect
                  options={configurations}
                  value={selectedConf}
                  onChange={(id) => handleConfChange(id)}
                  getLabel={(c) => c.name ?? c.id}
                  placeholder={selectedGen ? L.chooseConfiguration : L.firstChooseGeneration}
                  searchPlaceholder={L.searchPlaceholder}
                  noResults={L.noResults}
                  disabled={!selectedGen || confsLoading}
                  loading={confsLoading}
                />
              </div>

              <div>
                <label className={labelCls}>{L.modification} *</label>
                <SearchSelect
                  options={modifications}
                  value={selectedMod}
                  onChange={(id) => setSelectedMod(id)}
                  getLabel={modLabel}
                  placeholder={selectedConf ? L.chooseModification : L.firstChooseConfiguration}
                  searchPlaceholder={L.searchPlaceholder}
                  noResults={L.noResults}
                  disabled={!selectedConf || modsLoading}
                  loading={modsLoading}
                />
              </div>
            </div>
          )}

          {/* Step 2: Details */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground mb-4">{L.carDataTitle}</h2>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className={labelCls}>{L.year} *</label>
                  <input type="number" min="1900" max={new Date().getFullYear()} value={year}
                    onChange={e => setYear(e.target.value)} placeholder="2020" className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>{L.price} *</label>
                  <input type="text" inputMode="numeric"
                    value={price.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                    onChange={e => setPrice(e.target.value.replace(/\D/g, ''))}
                    placeholder={L.pricePlaceholder} className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>{L.mileage} *</label>
                  <input type="text" inputMode="numeric"
                    value={mileage.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                    onChange={e => setMileage(e.target.value.replace(/\D/g, ''))}
                    placeholder={L.mileagePlaceholder} className={inputCls} />
                </div>
              </div>

              <div>
                <label className={labelCls}>{L.condition} *</label>
                <div className="grid grid-cols-2 gap-2">
                  {CONDITION_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setCondition(opt.value)}
                      className={`p-3 rounded-lg border text-left transition-colors ${
                        condition === opt.value
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-foreground/30'
                      }`}
                    >
                      <p className="text-sm font-medium text-foreground">{opt.label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{opt.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>{L.color}</label>
                  <SearchSelect
                    options={colors}
                    value={selectedColor}
                    onChange={(id) => setSelectedColor(id)}
                    getLabel={(c) => c.name_ru}
                    placeholder={L.chooseColor}
                    searchPlaceholder={L.searchPlaceholder}
                    noResults={L.noResults}
                  />
                </div>
                <div>
                  <label className={labelCls}>{L.city}</label>
                  <SearchSelect
                    options={cities}
                    value={selectedCity}
                    onChange={(id) => setSelectedCity(id)}
                    getLabel={(c) => c.name_ru}
                    placeholder={L.chooseCity}
                    searchPlaceholder={L.searchPlaceholder}
                    noResults={L.noResults}
                  />
                </div>
              </div>

              <div>
                <label className={labelCls}>{L.vin}</label>
                <input type="text" value={vin} onChange={e => setVin(e.target.value.toUpperCase())}
                  placeholder={L.vinPlaceholder} maxLength={17} className={inputCls} />
                {vin.length > 0 && vin.length < 17 && (
                  <p className="text-xs text-destructive mt-1">{L.vinError} ({vin.length}/17)</p>
                )}
              </div>

              <div>
                <label className={labelCls}>
                  {L.plateMandatory}{!vin.trim() ? ' *' : ''}
                  <span className="text-xs font-normal text-muted-foreground ml-1">{L.plateNote}</span>
                </label>
                <input
                  type="text"
                  value={licensePlate}
                  onChange={e => setLicensePlate(e.target.value.toUpperCase())}
                  placeholder={L.platePlaceholder}
                  maxLength={10}
                  className={inputCls}
                />
                {!hasIdentifier && (vin.length > 0 || licensePlate.length > 0) && (
                  <p className="text-xs text-destructive mt-1">{L.plateIdentifierError}</p>
                )}
              </div>

              <div>
                <label className={labelCls}>{L.description}</label>
                <textarea value={description} onChange={e => setDescription(e.target.value)}
                  rows={4} placeholder={L.descriptionPlaceholder}
                  className={inputCls + ' resize-none'} />
              </div>

              <div className="pt-2 border-t border-border">
                <label className={labelCls}>{L.viewingSchedule}</label>
                <p className="text-xs text-muted-foreground mb-3">{L.viewingDaysDesc}</p>
                <div className="flex gap-1.5 mb-4">
                  {WEEK_DAYS.map((day, i) => (
                    <button key={i} type="button" onClick={() => toggleDay(i)}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${viewingDays.includes(i) ? 'border-primary bg-primary/5 text-primary' : 'border-border hover:border-foreground/30 text-foreground'}`}>
                      {day}
                    </button>
                  ))}
                </div>
                {viewingEnabled && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">{L.timeFrom}</label>
                        <select value={viewingFrom} onChange={e => setViewingFrom(e.target.value)}
                          className={inputCls + ' appearance-none cursor-pointer'}>
                          {TIME_SLOTS.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">{L.timeTo}</label>
                        <select value={viewingTo} onChange={e => setViewingTo(e.target.value)}
                          className={inputCls + ' appearance-none cursor-pointer'}>
                          {TIME_SLOTS.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className={labelCls}>
                        {L.viewingAddress} <span className="text-destructive">*</span>
                      </label>
                      <input
                        type="text"
                        value={saleAddress}
                        onChange={e => setSaleAddress(e.target.value)}
                        placeholder={L.viewingAddressPlaceholder}
                        className={inputCls}
                      />
                      <p className="text-xs text-muted-foreground mt-1">{L.viewingAddressNote}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-border">
                <label className={labelCls}>
                  {L.paymentMethods} <span className="text-destructive">*</span>
                </label>
                <p className="text-xs text-muted-foreground mb-3">{L.paymentMethodsNote}</p>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={acceptsCash}
                      onChange={e => setAcceptsCash(e.target.checked)}
                      className="w-4 h-4 accent-primary rounded"
                    />
                    <span className="text-sm text-foreground">{L.cash}</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={acceptsTransfer}
                      onChange={e => setAcceptsTransfer(e.target.checked)}
                      className="w-4 h-4 accent-primary rounded"
                    />
                    <span className="text-sm text-foreground">{L.transfer}</span>
                  </label>
                </div>
                {!hasPaymentMethod && (
                  <p className="text-xs text-destructive mt-1.5">{L.paymentRequired}</p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Photos */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">{L.photos}</h2>

              {/* Existing photos (edit mode) */}
              {isEdit && existingImages.length > 0 && (
                <div>
                  <label className={labelCls}>{L.existingPhotosLabel} ({existingImages.length})</label>
                  <div className="grid grid-cols-4 gap-2">
                    {existingImages.map((img) => (
                      <div key={img.id} className="relative aspect-square rounded-lg overflow-hidden group bg-secondary">
                        <img
                          src={img.thumbnail_url || img.url}
                          alt=""
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {img.is_primary && (
                          <span className="absolute bottom-1 left-1 flex items-center gap-0.5 text-[10px] bg-black/60 text-yellow-300 px-1.5 py-0.5 rounded">
                            <Star className="w-2.5 h-2.5" /> {L.mainPhotoLabel}
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => handleExistingImageDelete(img)}
                          disabled={deletingImageId === img.id}
                          className="absolute top-1 right-1 w-7 h-7 bg-black/70 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-60"
                          title={L.deletePhoto}
                        >
                          {deletingImageId === img.id
                            ? <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                            : <Trash2 className="w-3.5 h-3.5 text-white" />
                          }
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Upload new photos */}
              <div>
                <label className={labelCls}>
                  {isEdit ? L.addPhotos : L.carsUpTo}
                </label>
                <label className="flex flex-col items-center justify-center gap-3 p-8 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-primary/50 transition-colors group">
                  <Upload className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
                  <div className="text-center">
                    <p className="text-sm font-medium text-foreground">{L.clickToUpload}</p>
                    <p className="text-xs text-muted-foreground">{L.photoTypes}</p>
                  </div>
                  <input type="file" accept="image/*" multiple className="hidden" onChange={handleImageAdd} />
                </label>

                {previews.length > 0 && (
                  <div className="grid grid-cols-4 gap-2 mt-3">
                    {previews.map((src, i) => (
                      <div key={i} className="relative aspect-square rounded-lg overflow-hidden group bg-secondary">
                        <img src={src} alt="" className="w-full h-full object-cover" />
                        <button
                          type="button"
                          onClick={() => handleImageRemove(i)}
                          className="absolute top-1 right-1 w-6 h-6 bg-black/60 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3.5 h-3.5 text-white" />
                        </button>
                        {i === 0 && !isEdit && (
                          <span className="absolute bottom-1 left-1 text-[10px] bg-black/60 text-white px-1.5 py-0.5 rounded">{L.mainPhotoLabel}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {!isEdit && (
                <div className="p-4 bg-secondary/50 rounded-xl border border-border">
                  <p className="text-sm font-medium text-foreground mb-1">{L.afterSubmitTitle}</p>
                  <p className="text-sm text-muted-foreground">{L.afterSubmitDesc}</p>
                </div>
              )}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-border">
            <button
              type="button"
              onClick={() => step === 0 ? navigate(isEdit ? '/profile?tab=drafts' : -1 as never) : setStep(s => s - 1)}
              className="px-5 py-2.5 text-sm text-foreground border border-border rounded-lg hover:bg-secondary transition-colors"
            >
              {step === 0 ? L.cancel : L.prevStep}
            </button>

            {step < 2 ? (
              <button
                type="button"
                onClick={() => setStep(s => s + 1)}
                disabled={step === 0 ? !canGoNext0 : !canGoNext1}
                className="px-6 py-2.5 text-sm bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-40"
              >
                {L.next}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                className="flex items-center gap-2 px-6 py-2.5 text-sm bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                {submitting
                  ? (isEdit ? L.saving : L.publishing)
                  : (isEdit ? L.saveChanges : L.submitBtn)}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

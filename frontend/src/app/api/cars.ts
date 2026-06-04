import { api, resolveImageUrl } from './client';

export type CarStatus = 'available' | 'reserved' | 'sold' | 'inactive';
export type FuelType = 'petrol' | 'diesel' | 'electric' | 'hybrid' | 'gas';
export type Transmission = 'manual' | 'automatic' | 'robot' | 'variator';
export type BodyType = 'sedan' | 'hatchback' | 'suv' | 'coupe' | 'convertible' | 'wagon' | 'minivan' | 'pickup';

export interface CarImage {
  id: string;
  url: string;
  thumbnail_url: string;
  is_primary: boolean;
  sort_order: number;
}

export interface Car {
  id: string;
  brand: string;
  model: string;
  year: number;
  vin: string | null;
  color: string | null;
  mileage: number;
  price: number;
  fuel_type: string | null;
  transmission: string | null;
  body_type: string | null;
  engine_volume: string | null;
  engine_power: number | null;
  description: string | null;
  condition: string | null;
  city_name: string | null;
  city_id?: string | null;
  status: CarStatus;
  created_at: string;
  images: CarImage[];
  // Seller info — populated by GET /listings/:id
  seller_name?: string | null;
  seller_phone?: string | null;
  // Listing settings
  sale_address?: string | null;
  viewing_enabled?: boolean | null;
  accepts_cash?: boolean | null;
  accepts_transfer?: boolean | null;
}

export interface CarsPublic {
  data: Car[];
  next_cursor: string | null;
}

export interface CarFilters {
  sort_by?: 'price_asc' | 'price_desc' | 'year_asc' | 'year_desc' | 'date_desc' | 'date_asc' | 'newest';
  year_from?: number;
  year_to?: number;
  price_from?: number;
  price_to?: number;
  fuel_type?: string;
  body_type?: string;
  city?: string;
  cursor?: string;
  limit?: number;
  // kept for interface compat but not sent to server (no text search in new API)
  brand?: string;
  model?: string;
  color?: string;
  mileage_from?: number;
  mileage_to?: number;
  transmission?: string;
  status?: CarStatus;
  skip?: number;
}

const BRAND_NAMES: Record<string, string> = {
  ACURA: 'Acura', ALFA_ROMEO: 'Alfa Romeo', AUDI: 'Audi',
  BENTLEY: 'Bentley', BMW: 'BMW', BYD: 'BYD',
  CADILLAC: 'Cadillac', CHANGAN: 'Changan', CHERY: 'Chery', CHEVROLET: 'Chevrolet', CHRYSLER: 'Chrysler', CITROEN: 'Citroën',
  DACIA: 'Dacia', DATSUN: 'Datsun', DODGE: 'Dodge', DONGFENG: 'Dongfeng',
  FERRARI: 'Ferrari', FIAT: 'Fiat', FORD: 'Ford',
  GAZ: 'ГАЗ', GEELY: 'Geely', GENESIS: 'Genesis', GREAT_WALL: 'Great Wall',
  HAVAL: 'Haval', HONDA: 'Honda', HYUNDAI: 'Hyundai',
  INFINITI: 'INFINITI', ISUZU: 'Isuzu',
  JAC: 'JAC', JAGUAR: 'Jaguar', JEEP: 'Jeep',
  KIA: 'KIA',
  LAMBORGHINI: 'Lamborghini', LADA: 'Lada', LAND_ROVER: 'Land Rover', LEXUS: 'Lexus', LINCOLN: 'Lincoln',
  MASERATI: 'Maserati', MAZDA: 'Mazda', MERCEDES: 'Mercedes-Benz', MERCEDES_BENZ: 'Mercedes-Benz',
  MINI: 'MINI', MITSUBISHI: 'Mitsubishi', MOSKVICH: 'Москвич',
  NISSAN: 'Nissan',
  OPEL: 'Opel',
  PEUGEOT: 'Peugeot', PORSCHE: 'Porsche',
  RAM: 'RAM', RENAULT: 'Renault', ROLLS_ROYCE: 'Rolls-Royce',
  SEAT: 'SEAT', SKODA: 'Škoda', SMART: 'smart', SUBARU: 'Subaru', SUZUKI: 'Suzuki',
  TESLA: 'Tesla', TOYOTA: 'Toyota',
  UAZ: 'УАЗ',
  VAZ: 'Lada', VOLKSWAGEN: 'Volkswagen', VOLVO: 'Volvo',
  ZOTYE: 'Zotye',
};

export function formatCatalogId(id: string): string {
  const upper = id.toUpperCase().replace(/-/g, '_');
  if (BRAND_NAMES[upper]) return BRAND_NAMES[upper];
  return id.split(/[_\s]/).map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
}

function mapSort(sort_by?: string): string {
  switch (sort_by) {
    case 'price_asc': return 'price_asc';
    case 'price_desc': return 'price_desc';
    default: return 'newest';
  }
}

function mapStatus(status: string): CarStatus {
  switch (status) {
    case 'active': return 'available';
    case 'reserved': return 'reserved';
    case 'sold': return 'sold';
    default: return 'inactive';
  }
}

interface ListingRow {
  id: string;
  year: number;
  price: number;
  mileage: number;
  city_id: string;
  created_at: string;
  body_type: string | null;
  engine_type: string | null;
  mark_name: string | null;
  model_name: string | null;
  city_name: string | null;
  displacement: number | null;
  power: number | null;
  status?: string;
}

interface ListingDetail {
  id: string;
  seller_id: string;
  modification_id: string;
  mark_id: string;
  model_id: string;
  body_type: string | null;
  engine_type: string | null;
  year: number;
  price: number;
  mileage: number;
  color_id: string | null;
  vin: string | null;
  license_plate: string | null;
  description: string | null;
  condition: string | null;
  city_id: string;
  sale_address: string | null;
  viewing_enabled: boolean;
  accepts_cash: boolean;
  accepts_transfer: boolean;
  status: string;
  created_at: string;
  catalog_specs: Record<string, unknown> | null;
  images: {
    id: string;
    url: string;
    thumbnail_url: string;
    is_primary: boolean;
    sort_order: number;
  }[];
}

function mapRow(row: ListingRow): Car {
  return {
    id: row.id,
    brand: row.mark_name ?? '',
    model: row.model_name ?? '',
    year: row.year,
    price: row.price,
    mileage: row.mileage,
    vin: null,
    color: null,
    fuel_type: row.engine_type,
    transmission: null,
    body_type: row.body_type,
    engine_volume: row.displacement != null ? String(row.displacement) : null,
    engine_power: row.power,
    description: null,
    condition: null,
    city_name: row.city_name,
    status: mapStatus(row.status ?? 'active'),
    created_at: row.created_at,
    images: [],
  };
}

function mapDetail(d: ListingDetail): Car {
  const specs = d.catalog_specs ?? {};
  return {
    id: d.id,
    brand: formatCatalogId(d.mark_id),
    model: formatCatalogId(d.model_id),
    year: d.year,
    price: d.price,
    mileage: d.mileage,
    vin: d.vin,
    color: d.color_id,
    fuel_type: d.engine_type,
    transmission: (specs.transmission as string | null) ?? null,
    body_type: d.body_type,
    engine_volume: specs.displacement != null ? String(specs.displacement) : null,
    engine_power: (specs.power as number | null) ?? null,
    description: d.description,
    condition: d.condition,
    city_name: null,
    sale_address: d.sale_address,
    viewing_enabled: d.viewing_enabled,
    accepts_cash: d.accepts_cash,
    accepts_transfer: d.accepts_transfer,
    status: mapStatus(d.status),
    created_at: d.created_at,
    images: d.images.map(img => ({
      id: img.id,
      url: resolveImageUrl(img.url),
      thumbnail_url: resolveImageUrl(img.thumbnail_url),
      is_primary: img.is_primary,
      sort_order: img.sort_order,
    })),
  };
}

function buildQuery(filters: CarFilters): string {
  const params = new URLSearchParams();
  params.set('sort', mapSort(filters.sort_by));
  if (filters.cursor) params.set('cursor', filters.cursor);
  if (filters.limit) params.set('limit', String(filters.limit));
  if (filters.year_from !== undefined) params.set('year_min', String(filters.year_from));
  if (filters.year_to !== undefined) params.set('year_max', String(filters.year_to));
  if (filters.price_from !== undefined) params.set('price_min', String(filters.price_from));
  if (filters.price_to !== undefined) params.set('price_max', String(filters.price_to));
  if (filters.fuel_type) params.set('engine_type', filters.fuel_type);
  if (filters.body_type) params.set('body_type', filters.body_type);
  if (filters.city) params.set('city', filters.city);
  return `?${params.toString()}`;
}

export const carsApi = {
  list: async (filters: CarFilters = {}): Promise<CarsPublic> => {
    const res = await api.get<{ items: ListingRow[]; next_cursor: string | null }>(
      `/listings${buildQuery(filters)}`
    );
    return {
      data: res.items.map(mapRow),
      next_cursor: res.next_cursor,
    };
  },

  get: async (id: string): Promise<Car> => {
    const res = await api.get<ListingDetail>(`/listings/${id}`);
    return mapDetail(res);
  },
};

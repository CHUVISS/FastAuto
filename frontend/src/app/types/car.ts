export type TransmissionType = 'automatic' | 'manual';
export type FuelType = 'petrol' | 'diesel' | 'electric' | 'hybrid';
export type DriveType = 'front' | 'rear' | 'all';
export type BodyType = 'sedan' | 'suv' | 'hatchback' | 'wagon' | 'coupe' | 'minivan';

export interface Car {
  id: string;
  brand: string;
  model: string;
  year: number;
  price: number;
  mileage: number;
  transmission: TransmissionType;
  fuel: FuelType;
  color: string;
  engineVolume: number;
  drive: DriveType;
  body: BodyType;
  images: string[];
  description: string;
  isNew: boolean;
  createdAt: string;
  power: number;
  vin?: string;
}

export interface FilterState {
  price: { min: number; max: number };
  brand: string[];
  year: { min: number; max: number };
  mileage: { min: number; max: number };
  transmission: TransmissionType[];
  fuel: FuelType[];
  color: string[];
  engineVolume: { min: number; max: number };
  drive: DriveType[];
  body: BodyType[];
  isNew?: boolean;
}

export interface Lead {
  id: string;
  name: string;
  phone: string;
  email?: string;
  carId?: string;
  message?: string;
  type: 'viewing' | 'callback' | 'consultation';
  status: 'new' | 'contacted' | 'completed' | 'cancelled';
  createdAt: string;
}

export interface Appointment {
  id: string;
  clientName: string;
  clientPhone: string;
  carId: string;
  date: string;
  time: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  notes?: string;
}

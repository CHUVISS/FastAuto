import { type Car } from '../types/car';

// Моковые данные для автомобилей
export const mockCars: Car[] = [
  {
    id: '1',
    brand: 'Toyota',
    model: 'Camry',
    year: 2023,
    price: 3250000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Белый',
    engineVolume: 2.5,
    drive: 'front',
    body: 'sedan',
    power: 181,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'Новый седан Toyota Camry в максимальной комплектации. Полный пакет опций, гарантия производителя.',
    isNew: true,
    createdAt: '2026-03-25',
    vin: 'JTDKARFP1M3123456'
  },
  {
    id: '2',
    brand: 'BMW',
    model: 'X5',
    year: 2022,
    price: 5890000,
    mileage: 18500,
    transmission: 'automatic',
    fuel: 'diesel',
    color: 'Черный',
    engineVolume: 3.0,
    drive: 'all',
    body: 'suv',
    power: 265,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'BMW X5 в отличном состоянии, один владелец. Полный пакет M Sport, панорама, пневмоподвеска.',
    isNew: false,
    createdAt: '2026-03-24'
  },
  {
    id: '3',
    brand: 'Mercedes-Benz',
    model: 'E-Class',
    year: 2023,
    price: 6200000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'hybrid',
    color: 'Серебристый',
    engineVolume: 2.0,
    drive: 'rear',
    body: 'sedan',
    power: 299,
    images: ['placeholder1', 'placeholder2'],
    description: 'Mercedes-Benz E-Class 300e - гибридный седан премиум класса. Современные технологии и комфорт.',
    isNew: true,
    createdAt: '2026-03-26',
    vin: 'WDD2130361A123456'
  },
  {
    id: '4',
    brand: 'Volkswagen',
    model: 'Tiguan',
    year: 2021,
    price: 2750000,
    mileage: 35000,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Синий',
    engineVolume: 2.0,
    drive: 'all',
    body: 'suv',
    power: 180,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'Volkswagen Tiguan в хорошем состоянии. Регулярное обслуживание у официального дилера.',
    isNew: false,
    createdAt: '2026-03-23'
  },
  {
    id: '5',
    brand: 'Audi',
    model: 'Q7',
    year: 2023,
    price: 7450000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Белый',
    engineVolume: 3.0,
    drive: 'all',
    body: 'suv',
    power: 340,
    images: ['placeholder1', 'placeholder2', 'placeholder3', 'placeholder4'],
    description: 'Новый Audi Q7 с максимальной комплектацией. 7 мест, полный пакет ассистентов, панорамная крыша.',
    isNew: true,
    createdAt: '2026-03-27',
    vin: 'WAUZZZ4M7ED123456'
  },
  {
    id: '6',
    brand: 'Hyundai',
    model: 'Tucson',
    year: 2022,
    price: 2950000,
    mileage: 22000,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Красный',
    engineVolume: 2.0,
    drive: 'all',
    body: 'suv',
    power: 150,
    images: ['placeholder1', 'placeholder2'],
    description: 'Hyundai Tucson в отличной комплектации. Один владелец, все ТО пройдены вовремя.',
    isNew: false,
    createdAt: '2026-03-22'
  },
  {
    id: '7',
    brand: 'Kia',
    model: 'K5',
    year: 2023,
    price: 2650000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Серый',
    engineVolume: 2.5,
    drive: 'front',
    body: 'sedan',
    power: 180,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'Новый Kia K5 - стильный и технологичный седан. Гарантия 5 лет.',
    isNew: true,
    createdAt: '2026-03-28',
    vin: 'KNAGN4A78N5123456'
  },
  {
    id: '8',
    brand: 'Tesla',
    model: 'Model 3',
    year: 2023,
    price: 5200000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'electric',
    color: 'Белый',
    engineVolume: 0,
    drive: 'rear',
    body: 'sedan',
    power: 283,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'Tesla Model 3 Long Range - электрический седан с запасом хода до 602 км.',
    isNew: true,
    createdAt: '2026-03-29',
    vin: 'LRW3E7FK5NC123456'
  },
  {
    id: '9',
    brand: 'Mazda',
    model: 'CX-5',
    year: 2021,
    price: 2450000,
    mileage: 42000,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Красный',
    engineVolume: 2.5,
    drive: 'all',
    body: 'suv',
    power: 194,
    images: ['placeholder1', 'placeholder2'],
    description: 'Mazda CX-5 в хорошем состоянии. Надежный и экономичный кроссовер.',
    isNew: false,
    createdAt: '2026-03-21'
  },
  {
    id: '10',
    brand: 'Skoda',
    model: 'Octavia',
    year: 2022,
    price: 2150000,
    mileage: 28000,
    transmission: 'automatic',
    fuel: 'petrol',
    color: 'Серебристый',
    engineVolume: 1.4,
    drive: 'front',
    body: 'sedan',
    power: 150,
    images: ['placeholder1', 'placeholder2', 'placeholder3'],
    description: 'Skoda Octavia - практичный семейный седан. Просторный салон, экономичный двигатель.',
    isNew: false,
    createdAt: '2026-03-20'
  },
  {
    id: '11',
    brand: 'Lexus',
    model: 'RX',
    year: 2023,
    price: 6850000,
    mileage: 0,
    transmission: 'automatic',
    fuel: 'hybrid',
    color: 'Черный',
    engineVolume: 2.5,
    drive: 'all',
    body: 'suv',
    power: 248,
    images: ['placeholder1', 'placeholder2', 'placeholder3', 'placeholder4'],
    description: 'Lexus RX 350h - премиальный гибридный кроссовер. Непревзойденный комфорт и надежность.',
    isNew: true,
    createdAt: '2026-03-30',
    vin: 'JTJHARKC7N2123456'
  },
  {
    id: '12',
    brand: 'Nissan',
    model: 'Qashqai',
    year: 2021,
    price: 2250000,
    mileage: 31000,
    transmission: 'manual',
    fuel: 'petrol',
    color: 'Синий',
    engineVolume: 1.6,
    drive: 'front',
    body: 'suv',
    power: 117,
    images: ['placeholder1', 'placeholder2'],
    description: 'Nissan Qashqai - компактный городской кроссовер. Экономичный и практичный.',
    isNew: false,
    createdAt: '2026-03-19'
  }
];

// Функция для получения списка автомобилей с фильтрацией
export const getCars = (filters?: Partial<any>): Car[] => {
  let filtered = [...mockCars];

  if (filters) {
    if (filters.brand && filters.brand.length > 0) {
      filtered = filtered.filter(car => filters.brand.includes(car.brand));
    }
    if (filters.price) {
      filtered = filtered.filter(car => 
        car.price >= (filters.price.min || 0) && 
        car.price <= (filters.price.max || Infinity)
      );
    }
    if (filters.year) {
      filtered = filtered.filter(car => 
        car.year >= (filters.year.min || 0) && 
        car.year <= (filters.year.max || Infinity)
      );
    }
    if (filters.transmission && filters.transmission.length > 0) {
      filtered = filtered.filter(car => filters.transmission.includes(car.transmission));
    }
    if (filters.fuel && filters.fuel.length > 0) {
      filtered = filtered.filter(car => filters.fuel.includes(car.fuel));
    }
    if (filters.isNew !== undefined) {
      filtered = filtered.filter(car => car.isNew === filters.isNew);
    }
  }

  return filtered;
};

// Функция для получения автомобиля по ID
export const getCarById = (id: string): Car | undefined => {
  return mockCars.find(car => car.id === id);
};

// Функция для получения популярных брендов
export const getPopularBrands = (): string[] => {
  return ['Toyota', 'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Hyundai', 'Kia', 'Mazda', 'Nissan', 'Skoda'];
};

// Функция для получения всех уникальных брендов
export const getAllBrands = (): string[] => {
  return [...new Set(mockCars.map(car => car.brand))].sort();
};

// Функция для получения всех цветов
export const getAllColors = (): string[] => {
  return [...new Set(mockCars.map(car => car.color))].sort();
};

// Функция для форматирования цены
export const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
};

// Функция для форматирования пробега
export const formatMileage = (mileage: number): string => {
  return `${new Intl.NumberFormat('ru-RU').format(mileage)} км`;
};

// Перевод типов трансмиссии
export const getTransmissionLabel = (type: string): string => {
  const labels: Record<string, string> = {
    automatic: 'Автомат',
    manual: 'Механика'
  };
  return labels[type] || type;
};

// Перевод типов топлива
export const getFuelLabel = (type: string): string => {
  const labels: Record<string, string> = {
    petrol: 'Бензин',
    diesel: 'Дизель',
    electric: 'Электро',
    hybrid: 'Гибрид'
  };
  return labels[type] || type;
};

// Перевод типов привода
export const getDriveLabel = (type: string): string => {
  const labels: Record<string, string> = {
    front: 'Передний',
    rear: 'Задний',
    all: 'Полный'
  };
  return labels[type] || type;
};

// Перевод типов кузова
export const getBodyLabel = (type: string): string => {
  const labels: Record<string, string> = {
    sedan: 'Седан',
    suv: 'Внедорожник',
    hatchback: 'Хэтчбек',
    wagon: 'Универсал',
    coupe: 'Купе',
    minivan: 'Минивэн'
  };
  return labels[type] || type;
};

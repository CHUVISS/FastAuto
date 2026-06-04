import { http, HttpResponse } from 'msw';
import { mockUser, mockNotifications, mockCar, mockCarNoImages, mockReservation, mockActiveReservation } from './fixtures';

const BASE = 'http://localhost:8000/api/v1';

export const handlers = [
  // Auth
  http.post(`${BASE}/auth/login`, () =>
    HttpResponse.json({
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      token_type: 'bearer',
    }),
  ),
  http.post(`${BASE}/auth/register`, () =>
    HttpResponse.json(mockUser, { status: 201 }),
  ),
  http.get(`${BASE}/auth/me`, () =>
    HttpResponse.json(mockUser),
  ),
  http.post(`${BASE}/auth/logout`, () =>
    HttpResponse.json({ message: 'Logged out' }),
  ),

  // Notifications
  http.get(`${BASE}/notifications`, () =>
    HttpResponse.json(mockNotifications),
  ),
  http.post(`${BASE}/notifications/:id/read`, () =>
    HttpResponse.json({ read: true }),
  ),
  http.post(`${BASE}/notifications/read-all`, () =>
    HttpResponse.json({ marked_read: 2 }),
  ),

  // Favorites
  http.get(`${BASE}/favorites`, () =>
    HttpResponse.json([]),
  ),
  http.post(`${BASE}/favorites`, () =>
    HttpResponse.json({ id: 'fav-1' }, { status: 201 }),
  ),
  http.delete(`${BASE}/favorites/:id`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  // Listings
  http.get(`${BASE}/listings`, () =>
    HttpResponse.json({
      items: [
        {
          id: mockCar.id,
          mark_name: mockCar.brand,
          model_name: mockCar.model,
          year: mockCar.year,
          price: mockCar.price,
          mileage: mockCar.mileage,
          city_id: mockCar.city_id ?? 'moscow',
          city_name: mockCar.city_name,
          created_at: mockCar.created_at,
          body_type: mockCar.body_type,
          engine_type: mockCar.fuel_type,
          displacement: 2.5,
          power: mockCar.engine_power,
          status: 'active',
        },
      ],
      next_cursor: null,
    }),
  ),
  http.get(`${BASE}/listings/my`, () =>
    HttpResponse.json([]),
  ),
  http.get(`${BASE}/listings/:id`, ({ params }) => {
    if (params.id === mockCarNoImages.id) {
      return HttpResponse.json({
        id: mockCarNoImages.id,
        seller_id: 'seller-2',
        modification_id: 'mod-1',
        mark_id: 'BMW',
        model_id: 'X5',
        body_type: null,
        engine_type: null,
        year: mockCarNoImages.year,
        price: mockCarNoImages.price,
        mileage: mockCarNoImages.mileage,
        color_id: null,
        vin: null,
        description: null,
        condition: null,
        city_id: 'moscow',
        status: 'active',
        created_at: mockCarNoImages.created_at,
        catalog_specs: {},
        images: [],
      });
    }
    return HttpResponse.json({
      id: mockCar.id,
      seller_id: 'seller-2',
      modification_id: 'mod-1',
      mark_id: 'TOYOTA',
      model_id: 'CAMRY',
      body_type: 'sedan',
      engine_type: 'petrol',
      year: mockCar.year,
      price: mockCar.price,
      mileage: mockCar.mileage,
      color_id: 'white',
      vin: mockCar.vin,
      description: mockCar.description,
      condition: mockCar.condition,
      city_id: 'moscow',
      status: 'active',
      created_at: mockCar.created_at,
      catalog_specs: { transmission: 'automatic', displacement: 2.5, power: 181 },
      images: mockCar.images.map(img => ({
        id: img.id,
        url: img.url,
        thumbnail_url: img.thumbnail_url,
        is_primary: img.is_primary,
        sort_order: img.sort_order,
      })),
    });
  }),
  http.post(`${BASE}/listings`, () =>
    HttpResponse.json({ id: 'new-listing-1' }, { status: 201 }),
  ),

  // Reservations
  http.get(`${BASE}/reservations/my`, () =>
    HttpResponse.json([mockReservation]),
  ),
  http.get(`${BASE}/reservations/:id`, ({ params }) => {
    if (params.id === 'res-2') return HttpResponse.json(mockActiveReservation);
    return HttpResponse.json(mockReservation);
  }),
  http.post(`${BASE}/reservations`, () =>
    HttpResponse.json({
      reservation_id: 'res-1',
      payment_url: 'https://pay.yookassa.ru/test',
    }),
  ),
  http.post(`${BASE}/reservations/:id/outcome`, () =>
    HttpResponse.json({ status: 'settling', outcome: 'sold' }),
  ),
  http.post(`${BASE}/reservations/:id/cancel`, () =>
    HttpResponse.json({ status: 'cancelled' }),
  ),

  // Catalog
  http.get(`${BASE}/catalog/marks`, () =>
    HttpResponse.json([
      { id: 'TOYOTA', name: 'TOYOTA', cyrillic_name: 'Тойота', popular: true },
      { id: 'BMW', name: 'BMW', cyrillic_name: 'БМВ', popular: true },
    ]),
  ),
  http.get(`${BASE}/catalog/colors`, () =>
    HttpResponse.json([
      { id: 'white', name_ru: 'Белый', name_en: 'White', hex_code: '#FFFFFF' },
      { id: 'black', name_ru: 'Чёрный', name_en: 'Black', hex_code: '#000000' },
    ]),
  ),
  http.get(`${BASE}/geo/cities`, () =>
    HttpResponse.json([
      { id: 'moscow', name_ru: 'Москва', name_en: 'Moscow' },
      { id: 'spb', name_ru: 'Санкт-Петербург', name_en: 'Saint Petersburg' },
    ]),
  ),
];

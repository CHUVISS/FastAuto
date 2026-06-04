import { useState, useEffect } from 'react';
import { carsApi, type Car, type CarFilters } from '../api/cars';

export function useCars(filters: CarFilters = {}) {
  const [data, setData] = useState<{ data: Car[]; next_cursor: string | null }>({ data: [], next_cursor: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    carsApi.list(filters)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  return { cars: data.data, nextCursor: data.next_cursor, loading, error };
}

export function useCar(id: string | undefined) {
  const [car, setCar] = useState<Car | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    carsApi.get(id)
      .then(setCar)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  return { car, loading, error };
}

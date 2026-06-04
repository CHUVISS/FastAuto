import { useEffect, useState } from 'react';
import { salonApi, type SalonInfo } from '../api/salon';

export function useSalonInfo() {
  const [info, setInfo] = useState<SalonInfo | null>(null);

  useEffect(() => {
    salonApi.getInfo().then(setInfo);
  }, []);

  return info;
}

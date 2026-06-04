import { RouterProvider } from 'react-router';
import { router } from './routes';
import { Toaster } from 'sonner';
import { LanguageProvider } from './i18n/LanguageContext';
import { FavoritesProvider } from './contexts/FavoritesContext';

export default function App() {
  return (
    <LanguageProvider>
      <FavoritesProvider>
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors />
      </FavoritesProvider>
    </LanguageProvider>
  );
}
import { lazy } from 'react';
import { createBrowserRouter } from 'react-router';
import { Layout } from './components/Layout';
import { NotFoundPage } from './pages/NotFoundPage';
import { ServerErrorPage } from './pages/ServerErrorPage';

const HomePage         = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })));
const CatalogPage      = lazy(() => import('./pages/CatalogPage').then(m => ({ default: m.CatalogPage })));
const CarDetailPage    = lazy(() => import('./pages/CarDetailPage').then(m => ({ default: m.CarDetailPage })));
const ProfilePage      = lazy(() => import('./pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const AdminPage        = lazy(() => import('./pages/AdminPage').then(m => ({ default: m.AdminPage })));
const AboutPage        = lazy(() => import('./pages/AboutPage').then(m => ({ default: m.AboutPage })));
const AiPage           = lazy(() => import('./pages/AiPage').then(m => ({ default: m.AiPage })));
const CreateListingPage  = lazy(() => import('./pages/CreateListingPage').then(m => ({ default: m.CreateListingPage })));
const PaymentReturnPage  = lazy(() => import('./pages/PaymentReturnPage').then(m => ({ default: m.PaymentReturnPage })));

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <ServerErrorPage />,
    children: [
      { index: true,              element: <HomePage /> },
      { path: 'catalog',          element: <CatalogPage /> },
      { path: 'car/:id',          element: <CarDetailPage /> },
      { path: 'profile',          element: <ProfilePage /> },
      { path: 'admin',            element: <AdminPage /> },
      { path: 'about',            element: <AboutPage /> },
      { path: 'ai',               element: <AiPage /> },
      { path: 'sell',             element: <CreateListingPage /> },
      { path: 'listing/:id/edit', element: <CreateListingPage /> },
      { path: 'payment/return',   element: <PaymentReturnPage /> },
      { path: '500',              element: <ServerErrorPage status={500} /> },
      { path: '502',              element: <ServerErrorPage status={502} /> },
      { path: '503',              element: <ServerErrorPage status={503} /> },
      { path: '504',              element: <ServerErrorPage status={504} /> },
      { path: '*',                element: <NotFoundPage /> },
    ],
  },
]);

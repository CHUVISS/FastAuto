import { Link, useNavigate } from 'react-router';
import { Car, Phone, User, Menu, LogOut, Bot, Bell } from 'lucide-react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'sonner';
import { ThemeToggle } from './ThemeToggle';
import { LangToggle } from './LangToggle';
import { useLanguage } from '../i18n/LanguageContext';
import {
  notificationsApi,
  notificationText,
  notificationHref,
  type Notification,
} from '../api/notifications';

// NotificationBell

function NotificationItem({
  n,
  onRead,
}: {
  n: Notification;
  onRead: (id: string) => void;
}) {
  const { lang } = useLanguage();
  const isUnread = !n.read_at;
  return (
    <Link
      to={notificationHref(n)}
      onClick={() => { if (isUnread) onRead(n.id); }}
      className={`flex items-start gap-3 px-4 py-3 hover:bg-secondary transition-colors border-b border-border last:border-0 ${
        isUnread ? 'bg-primary/5' : ''
      }`}
    >
      <span
        className={`mt-1.5 flex-shrink-0 w-2 h-2 rounded-full ${
          isUnread ? 'bg-primary' : 'bg-transparent'
        }`}
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground leading-snug">{notificationText(n)}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {new Date(n.created_at).toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </Link>
  );
}

function NotificationBell() {
  const { T } = useLanguage();
  const [items, setItems] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const data = await notificationsApi.list();
      setItems(data);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const unread = items.filter(n => !n.read_at).length;

  const handleToggle = () => {
    const next = !open;
    setOpen(next);
    if (next) load();
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setItems(prev => prev.map(n => ({ ...n, read_at: new Date().toISOString() })));
    } catch {
      toast.error(T.notifications.error);
    }
  };

  const handleMarkOne = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setItems(prev => prev.map(n => n.id === id ? { ...n, read_at: new Date().toISOString() } : n));
    } catch { /* silent */ }
  };

  return (
    <div ref={wrapRef} className="relative">
      <button
        onClick={handleToggle}
        className="relative p-2 text-foreground hover:text-primary transition-colors"
        aria-label={T.notifications.title}
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[16px] h-4 bg-destructive text-white text-[10px] font-bold rounded-full flex items-center justify-center px-0.5 leading-none">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-1rem)] bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <span className="font-semibold text-sm text-foreground">{T.notifications.title}</span>
            {unread > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-primary hover:underline"
              >
                {T.notifications.markAllRead}
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-72 overflow-y-auto">
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-10">
                {T.notifications.empty}
              </p>
            ) : (
              items.map(n => (
                <NotificationItem key={n.id} n={n} onRead={handleMarkOne} />
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-border text-center">
            <Link
              to="/profile?tab=reservations"
              onClick={() => setOpen(false)}
              className="text-xs text-primary hover:underline"
            >
              {T.notifications.myBookings}
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

// Header

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { T } = useLanguage();

  // Блокируем скролл страницы когда мобильное меню открыто
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileMenuOpen]);

  const handleLogout = async () => {
    await logout();
    toast.success(T.profile.logoutSuccess);
    navigate('/');
    setMobileMenuOpen(false);
  };

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="bg-background border-b border-border sticky top-0 z-50" style={{ paddingTop: 'env(safe-area-inset-top)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <span className="text-xl font-semibold text-foreground">FastAuto</span>
            <Car className="w-8 h-8 text-primary" />
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link to="/catalog" className="text-foreground hover:text-primary transition-colors">{T.nav.listings}</Link>
            <Link to="/ai" className="flex items-center gap-1.5 text-foreground hover:text-primary transition-colors">
              <Bot className="w-4 h-4" />{T.nav.ai}
            </Link>
            <Link to="/about" className="text-foreground hover:text-primary transition-colors">{T.nav.about}</Link>
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <a href="tel:+79001234567" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors">
              <Phone className="w-5 h-5" />
              <span>+7 (900) 123-45-67</span>
            </a>

            <LangToggle />
            <ThemeToggle />

            {user ? (
              <div className="flex items-center gap-2">
                <NotificationBell />
                <Link to="/profile"
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity">
                  <User className="w-5 h-5" />
                  <span>{user.full_name.split(' ')[0]}</span>
                </Link>
                {(user.role === 'admin' || user.role === 'manager') && (
                  <Link to="/admin" className="px-3 py-2 bg-secondary text-foreground rounded-lg hover:bg-secondary/80 text-sm transition-colors">
                    {user.role === 'admin' ? T.nav.admin : T.nav.manager}
                  </Link>
                )}
                <button onClick={handleLogout} className="p-2 text-muted-foreground hover:text-destructive transition-colors">
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <Link to="/profile"
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity">
                <User className="w-5 h-5" />
                <span>{T.nav.signIn}</span>
              </Link>
            )}
          </div>

          {/* Mobile controls */}
          <div className="flex items-center gap-2 md:hidden">
            {user && <NotificationBell />}
            <LangToggle />
            <ThemeToggle />
            <button className="p-2 text-foreground" onClick={() => setMobileMenuOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu — fixed overlay, страница не двигается */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Затемнение */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeMenu} />

          {/* Панель справа */}
          <div className="relative ml-auto w-72 max-w-full h-full bg-card border-l border-border flex flex-col shadow-2xl overflow-y-auto">
            {/* Шапка */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border" style={{ paddingTop: 'calc(env(safe-area-inset-top) + 1rem)' }}>
              <span className="font-semibold text-foreground text-lg">FastAuto</span>
              <button onClick={closeMenu} className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Навигация */}
            <nav className="flex flex-col px-3 py-4 gap-1 flex-1">
              <Link to="/catalog" onClick={closeMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl text-foreground hover:bg-secondary transition-colors font-medium">{T.nav.listings}</Link>
              <Link to="/ai" onClick={closeMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl text-foreground hover:bg-secondary transition-colors font-medium">
                <Bot className="w-5 h-5 text-primary" />{T.nav.ai}
              </Link>
              <Link to="/about" onClick={closeMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl text-foreground hover:bg-secondary transition-colors font-medium">{T.nav.about}</Link>
              <a href="tel:+79001234567" onClick={closeMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl text-foreground hover:bg-secondary transition-colors font-medium">
                <Phone className="w-5 h-5 text-primary" />
                <span>+7 (900) 123-45-67</span>
              </a>
            </nav>

            {/* Блок пользователя */}
            <div className="border-t border-border px-3 py-4 flex flex-col gap-2" style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 1rem)' }}>
              {user ? (
                <>
                  <Link to="/profile" onClick={closeMenu} className="flex items-center gap-3 px-4 py-3 bg-primary text-primary-foreground rounded-xl font-medium">
                    <User className="w-5 h-5" />
                    <span className="truncate">{user.full_name}</span>
                  </Link>
                  {(user.role === 'admin' || user.role === 'manager') && (
                    <Link to="/admin" onClick={closeMenu} className="px-4 py-3 bg-secondary text-foreground rounded-xl text-sm text-center font-medium hover:bg-secondary/80 transition-colors">
                      {user.role === 'admin' ? T.nav.admin : T.nav.manager}
                    </Link>
                  )}
                  <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-3 rounded-xl text-destructive hover:bg-destructive/10 transition-colors font-medium">
                    <LogOut className="w-5 h-5" />
                    <span>{T.nav.signOut}</span>
                  </button>
                </>
              ) : (
                <Link to="/profile" onClick={closeMenu} className="flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-xl font-medium">
                  <User className="w-5 h-5" />
                  <span>{T.nav.signIn}</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

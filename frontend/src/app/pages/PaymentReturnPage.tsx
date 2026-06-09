import { useEffect } from 'react';
import { Link, useSearchParams } from 'react-router';
import { CheckCircle, Clock, XCircle, Ban, Car } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

type PaymentStatus = 'ok' | 'pending' | 'failed' | 'cancelled';

interface StatusConfig {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  bg: string;
}

export function PaymentReturnPage() {
  const [params] = useSearchParams();
  const { T } = useLanguage();
  const P = T.paymentReturn;

  const status = (params.get('status') ?? 'failed') as PaymentStatus;

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const configs: Record<PaymentStatus, StatusConfig> = {
    ok: {
      icon: <CheckCircle className="w-16 h-16" />,
      title: P.okTitle,
      description: P.okDesc,
      color: 'text-accent',
      bg: 'bg-accent/10',
    },
    pending: {
      icon: <Clock className="w-16 h-16" />,
      title: P.pendingTitle,
      description: P.pendingDesc,
      color: 'text-yellow-500',
      bg: 'bg-yellow-500/10',
    },
    failed: {
      icon: <XCircle className="w-16 h-16" />,
      title: P.failedTitle,
      description: P.failedDesc,
      color: 'text-destructive',
      bg: 'bg-destructive/10',
    },
    cancelled: {
      icon: <Ban className="w-16 h-16" />,
      title: P.cancelledTitle,
      description: P.cancelledDesc,
      color: 'text-muted-foreground',
      bg: 'bg-muted',
    },
  };

  const cfg = configs[status] ?? configs.failed;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-2xl p-8 text-center shadow-sm">

          {/* Иконка статуса */}
          <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${cfg.bg} ${cfg.color} mb-6`}>
            {cfg.icon}
          </div>

          {/* Заголовок */}
          <h1 className="text-2xl font-semibold text-foreground mb-3">
            {cfg.title}
          </h1>

          {/* Описание */}
          <p className="text-muted-foreground leading-relaxed mb-8">
            {cfg.description}
          </p>

          {/* Разделитель */}
          <div className="border-t border-border mb-6" />

          {/* Кнопки */}
          <div className="flex flex-col gap-3">
            <Link
              to="/profile"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
              {P.toProfile}
            </Link>
            <Link
              to="/catalog"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-secondary text-foreground rounded-xl font-medium hover:bg-secondary/80 transition-colors"
            >
              <Car className="w-4 h-4" />
              {P.toCatalog}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

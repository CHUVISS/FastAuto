import { useRouteError, isRouteErrorResponse, Link, useNavigate } from 'react-router';
import { AlertTriangle, Home, RefreshCw, ServerCrash, WifiOff, Clock } from 'lucide-react';
import { useState } from 'react';
import { useLanguage } from '../i18n/LanguageContext';

function getIcon(status: number | null) {
  if (status === 503) return WifiOff;
  if (status === 504) return Clock;
  if (status === 502) return ServerCrash;
  return AlertTriangle;
}

interface ServerErrorPageProps {
  /** Pass a status code when rendering outside of router errorElement context */
  status?: number;
  message?: string;
}

export function ServerErrorPage({ status: propStatus, message: propMessage }: ServerErrorPageProps = {}) {
  const routeError = useRouteError?.();
  const navigate = useNavigate();
  const { T } = useLanguage();
  const E = T.serverError;
  const [showDetails, setShowDetails] = useState(false);

  // Detect status and message from router error or props
  let status: number | null = propStatus ?? null;
  let message: string | null = propMessage ?? null;
  let stack: string | null = null;

  if (routeError) {
    if (isRouteErrorResponse(routeError)) {
      status = routeError.status;
      message = routeError.statusText || routeError.data;
    } else if (routeError instanceof Error) {
      message = routeError.message;
      stack = routeError.stack ?? null;
    }
  }

  // Map status to localised code label
  const codeLabel =
    status && status in E.codes
      ? `${status} — ${E.codes[status as keyof typeof E.codes]}`
      : status
      ? `${status}`
      : null;

  const Icon = getIcon(status);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-destructive/5 rounded-full blur-3xl" />
      </div>

      <div className="relative text-center max-w-lg w-full">
        {/* Icon + code */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-destructive/10 flex items-center justify-center mb-6 ring-1 ring-destructive/20">
            <Icon className="w-10 h-10 text-destructive" />
          </div>

          {codeLabel && (
            <span className="inline-block px-3 py-1 rounded-full bg-destructive/10 text-destructive text-sm font-mono font-semibold mb-4 ring-1 ring-destructive/20">
              {codeLabel}
            </span>
          )}

          <h1 className="text-3xl sm:text-4xl font-semibold text-foreground mb-3">
            {E.title}
          </h1>
          <p className="text-muted-foreground leading-relaxed">
            {E.desc}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-8">
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary/25"
          >
            <RefreshCw className="w-4 h-4" />
            {E.retry}
          </button>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-secondary text-foreground rounded-xl font-medium hover:bg-secondary/80 transition-all duration-200 border border-border"
          >
            <Home className="w-4 h-4" />
            {E.home}
          </Link>
        </div>

        {/* Go back */}
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline"
        >
          ← Назад
        </button>

        {/* Collapsible error details (dev / debug) */}
        {(message || stack) && (
          <div className="mt-8 text-left">
            <button
              onClick={() => setShowDetails(v => !v)}
              className="text-xs text-muted-foreground/60 hover:text-muted-foreground transition-colors flex items-center gap-1 mx-auto"
            >
              {E.details} {showDetails ? '▲' : '▼'}
            </button>
            {showDetails && (
              <pre className="mt-3 p-4 rounded-xl bg-secondary border border-border text-xs text-muted-foreground overflow-x-auto whitespace-pre-wrap break-words leading-relaxed max-h-60 overflow-y-auto">
                {message && <span className="text-destructive font-semibold block mb-2">{message}</span>}
                {stack}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

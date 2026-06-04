/**
 * Skeleton placeholder shown while a car photo is loading or unavailable.
 * Renders a pulsing background with a subtle car silhouette.
 */
export function CarImagePlaceholder({ className = '' }: { className?: string }) {
  return (
    <div className={`w-full h-full bg-secondary animate-pulse flex items-center justify-center ${className}`}>
      {/* Minimalist car silhouette */}
      <svg
        viewBox="0 0 80 40"
        xmlns="http://www.w3.org/2000/svg"
        className="w-16 h-8 text-muted-foreground/20"
        fill="currentColor"
      >
        {/* Body */}
        <rect x="4" y="18" width="72" height="16" rx="4" />
        {/* Cabin */}
        <path d="M18 18 L26 6 H54 L62 18 Z" />
        {/* Wheel wells */}
        <circle cx="20" cy="34" r="6" className="fill-secondary" />
        <circle cx="60" cy="34" r="6" className="fill-secondary" />
        {/* Wheels */}
        <circle cx="20" cy="34" r="4" />
        <circle cx="60" cy="34" r="4" />
      </svg>
    </div>
  );
}

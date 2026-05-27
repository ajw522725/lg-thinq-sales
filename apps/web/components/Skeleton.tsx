export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-surface-container ${className}`} />;
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`rounded-xl border border-surface-high bg-white p-6 shadow-soft ${className}`}>
      <SkeletonBlock className="mb-4 h-4 w-24" />
      <SkeletonBlock className="mb-3 h-6 w-3/4" />
      <SkeletonBlock className="mb-2 h-4 w-full" />
      <SkeletonBlock className="h-4 w-5/6" />
    </div>
  );
}

export function SkeletonMetric() {
  return (
    <div className="rounded-xl border border-surface-high bg-white p-6 shadow-soft">
      <SkeletonBlock className="mb-3 h-3 w-28" />
      <SkeletonBlock className="h-10 w-16" />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 border-b border-surface-container py-4">
      <SkeletonBlock className="h-4 w-48" />
      <SkeletonBlock className="h-4 w-24" />
      <SkeletonBlock className="h-4 w-32" />
      <SkeletonBlock className="h-6 w-16 rounded-full" />
    </div>
  );
}

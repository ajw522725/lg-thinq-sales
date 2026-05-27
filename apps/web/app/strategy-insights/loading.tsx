import { SkeletonCard } from "@/components/Skeleton";

export default function StrategyInsightsLoading() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-12 gap-6">
        <SkeletonCard className="col-span-12 lg:col-span-8 h-80" />
        <SkeletonCard className="col-span-12 lg:col-span-4 h-80" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} className="h-40" />)}
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} className="h-56" />)}
      </div>
    </div>
  );
}

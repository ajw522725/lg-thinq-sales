import { SkeletonCard, SkeletonRow } from "@/components/Skeleton";

export default function VocLoading() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-12 gap-6">
        <SkeletonCard className="col-span-12 lg:col-span-8 h-48" />
        <SkeletonCard className="col-span-12 lg:col-span-4 h-48" />
      </div>
      <div className="h-14 animate-pulse rounded-xl bg-surface-container" />
      <div className="rounded-xl border border-surface-high bg-white p-6">
        {Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)}
      </div>
    </div>
  );
}

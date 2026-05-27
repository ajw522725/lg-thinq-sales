import { SkeletonCard, SkeletonMetric, SkeletonRow } from "@/components/Skeleton";

export default function LeadScoringLoading() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 md:col-span-3"><SkeletonMetric /></div>
        <div className="col-span-12 md:col-span-3"><SkeletonMetric /></div>
        <SkeletonCard className="col-span-12 md:col-span-6 h-24" />
      </div>
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-7 rounded-xl border border-surface-high bg-white p-6">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)}
        </div>
        <SkeletonCard className="col-span-12 xl:col-span-5 h-96" />
      </div>
    </div>
  );
}

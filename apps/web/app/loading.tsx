import { SkeletonCard, SkeletonMetric } from "@/components/Skeleton";

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonMetric key={i} />)}
      </div>
      <div className="grid grid-cols-12 gap-6">
        <SkeletonCard className="col-span-12 lg:col-span-8 h-52" />
        <SkeletonCard className="col-span-12 lg:col-span-4 h-52" />
      </div>
      <div className="grid grid-cols-12 gap-6">
        <SkeletonCard className="col-span-12 lg:col-span-7 h-64" />
        <SkeletonCard className="col-span-12 lg:col-span-5 h-64" />
      </div>
    </div>
  );
}

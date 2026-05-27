export function FilterBar() {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-surface-high bg-white p-4">
      <span className="text-sm font-medium text-secondary">Filter by:</span>
      {["Product Category", "Score Range: All", "Date: Last 30 Days"].map((label) => (
        <button key={label} className="rounded-lg bg-surface-low px-4 py-2 text-sm font-medium text-charcoal">
          {label}
        </button>
      ))}
      <button className="ml-auto rounded-lg bg-surface-low px-3 py-2 text-secondary">Filter</button>
    </div>
  );
}

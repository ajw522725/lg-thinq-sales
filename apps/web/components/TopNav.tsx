export function TopNav() {
  const now = new Date().toLocaleDateString("ko-KR", {
    year: "numeric", month: "long", day: "numeric", weekday: "short",
  });

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-surface-high bg-background/90 px-8 backdrop-blur-sm">
      {/* 검색 */}
      <div className="flex w-full max-w-sm items-center gap-2 rounded-xl bg-surface-low px-4 py-2.5 text-secondary ring-1 ring-transparent focus-within:ring-primary/30 transition-all">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" className="shrink-0">
          <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M11 11L14.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          className="w-full border-none bg-transparent text-sm outline-none placeholder:text-secondary/70"
          placeholder="인사이트, 리드, VOC 검색..."
        />
      </div>

      {/* 우측 */}
      <div className="flex items-center gap-5">
        <span className="hidden text-xs text-secondary lg:block">{now}</span>

        <div className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
          <span className="text-xs font-bold text-primary">AI Active</span>
        </div>

        <button className="relative text-secondary hover:text-charcoal transition-colors">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          <span className="absolute -right-0.5 -top-0.5 flex h-3 w-3 items-center justify-center rounded-full bg-primary text-[7px] font-bold text-white">2</span>
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-charcoal text-xs font-bold text-white ring-2 ring-surface-high">
          SK
        </div>
      </div>
    </header>
  );
}

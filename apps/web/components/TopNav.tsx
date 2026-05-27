export function TopNav() {
  return (
    <header className="sticky top-0 z-40 flex h-20 items-center justify-between bg-background/85 px-8 backdrop-blur">
      <div className="flex w-full max-w-xl items-center gap-3 rounded-full bg-surface-low px-5 py-3 text-secondary">
        <span>⌕</span>
        <input className="w-full border-none bg-transparent text-sm outline-none" placeholder="Search insights, leads or VOC..." />
      </div>
      <div className="flex items-center gap-5">
        <button className="font-bold text-primary">✧ AI Assistant</button>
        <button className="text-secondary">Alerts</button>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-charcoal text-xs font-bold text-white">SH</div>
      </div>
    </header>
  );
}

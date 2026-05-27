"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/voc", label: "VOC Analysis", icon: "▤" },
  { href: "/lead-scoring", label: "Lead Scoring", icon: "▥" },
  { href: "/strategy-insights", label: "Strategy Insights", icon: "✧" }
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed left-0 top-0 z-50 flex h-screen w-72 flex-col bg-surface-low px-5 py-5">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-lg font-bold text-white">LG</div>
        <div>
          <h1 className="text-2xl font-bold leading-none text-primary">ThinQ-Sales</h1>
          <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-secondary">Strategic Intelligence</p>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-2">
        {navItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-semibold transition ${
                active ? "border-r-4 border-primary bg-surface-container text-primary" : "text-secondary hover:bg-white/60"
              }`}
            >
              <span className="w-5 text-lg">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
        <div className="mt-auto border-t border-surface-high pt-4">
          <button className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm font-semibold text-secondary">⚙ Settings</button>
        </div>
      </nav>
      <button className="mt-5 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg shadow-primary/20">＋ New Analysis</button>
    </aside>
  );
}

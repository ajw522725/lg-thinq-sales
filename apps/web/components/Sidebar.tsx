"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { NewAnalysisModal } from "./NewAnalysisModal";

const navItems = [
  { href: "/",                   label: "Dashboard",         icon: "◫" },
  { href: "/voc",                label: "VOC Analysis",      icon: "◧" },
  { href: "/lead-scoring",       label: "Lead Scoring",      icon: "◨" },
  { href: "/strategy-insights",  label: "Strategy Insights", icon: "✦" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [showModal, setShowModal] = useState(false);

  return (
    <aside className="fixed left-0 top-0 z-50 flex h-screen w-72 flex-col bg-surface-low px-5 py-6 border-r border-surface-high">
      {/* 로고 */}
      <div className="mb-8 flex items-center gap-3 px-1">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-base font-black tracking-tighter text-white shadow-lg shadow-primary/30">
          LG
        </div>
        <div>
          <h1 className="text-xl font-bold leading-none text-primary">ThinQ-Sales</h1>
          <p className="mt-1 text-[10px] font-semibold uppercase tracking-widest text-secondary">Strategic Intelligence</p>
        </div>
      </div>

      {/* 데모 모드 배지 */}
      <div className="mb-6 flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
        <span className="text-xs font-semibold text-amber-700">DEMO MODE — 샘플 데이터</span>
      </div>

      {/* 네비게이션 */}
      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all duration-150 ${
                active
                  ? "bg-primary text-white shadow-md shadow-primary/20"
                  : "text-secondary hover:bg-white hover:text-charcoal hover:shadow-soft"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
              {active && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-white/60" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* 하단 */}
      <div className="mt-4 space-y-2 border-t border-surface-high pt-4">
        <button className="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-secondary hover:bg-white hover:text-charcoal transition-colors">
          ⚙ Settings
        </button>
        <button
          onClick={() => setShowModal(true)}
          className="w-full rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg shadow-primary/25 hover:bg-primary-strong transition-colors"
        >
          ＋ New Analysis
        </button>
      </div>
      {showModal && <NewAnalysisModal onClose={() => setShowModal(false)} />}
    </aside>
  );
}

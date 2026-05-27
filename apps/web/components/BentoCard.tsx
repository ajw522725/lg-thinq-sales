import type { ReactNode } from "react";

interface BentoCardProps {
  children: ReactNode;
  className?: string;
  ai?: boolean;
}

export function BentoCard({ children, className = "", ai = false }: BentoCardProps) {
  return (
    <section className={`${ai ? "ai-glow" : "bg-surface shadow-soft"} rounded-xl p-8 ${className}`}>
      {children}
    </section>
  );
}

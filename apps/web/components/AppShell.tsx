import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div>
      <Sidebar />
      <div className="ml-72 min-h-screen">
        <TopNav />
        <main className="mx-auto max-w-[1440px] px-8 pb-12">{children}</main>
      </div>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { runCollection } from "@/lib/api";

type Status = "idle" | "running" | "success" | "error";

const SOURCE_OPTIONS = [
  { value: "Reddit", label: "Reddit", note: "Live fallback" },
  { value: "NaverBlog", label: "Naver Blog", note: "API/scrape" },
  { value: "Danawa", label: "Danawa", note: "Cookie 권장" },
  { value: "YouTube", label: "YouTube", note: "API key 필요" },
];

export function CollectionRunButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("Run Collection");
  const [sources, setSources] = useState<string[]>(["Reddit"]);
  const [keywordsText, setKeywordsText] = useState("LG air purifier\nLG ThinQ");
  const [maxPerSource, setMaxPerSource] = useState(10);
  const [live, setLive] = useState(true);
  const [reset, setReset] = useState(false);

  const keywords = useMemo(
    () => keywordsText
      .split(/[\n,]/)
      .map((keyword) => keyword.trim())
      .filter(Boolean),
    [keywordsText],
  );

  const canRun = status !== "running" && sources.length > 0 && keywords.length > 0;

  function toggleSource(source: string) {
    setSources((current) => (
      current.includes(source)
        ? current.filter((item) => item !== source)
        : [...current, source]
    ));
  }

  async function handleRun() {
    if (!canRun) return;
    setStatus("running");
    setMessage("Collecting...");

    try {
      const result = await runCollection({
        keywords,
        sources,
        max_per_source: maxPerSource,
        live,
        reset,
        save: false,
      });

      setStatus("success");
      setMessage(`${result.raw_documents} saved`);
      setOpen(false);
      router.refresh();
    } catch {
      setStatus("error");
      setMessage("Collection failed");
    }
  }

  const tone =
    status === "success"
      ? "bg-emerald-600 hover:bg-emerald-700"
      : status === "error"
        ? "bg-red-600 hover:bg-red-700"
        : "bg-primary hover:bg-primary-strong";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-bold text-white shadow-lg shadow-primary/20 transition-colors ${tone}`}
        title="VOC 수집 설정"
      >
        <span>↻</span>
        <span>{message}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 w-[360px] rounded-xl border border-surface-high bg-white p-4 text-charcoal shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-bold">VOC Collection</p>
              <p className="text-xs text-secondary">Source, keyword, mode</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-secondary hover:bg-surface-low hover:text-charcoal"
              aria-label="Close collection panel"
            >
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-bold uppercase tracking-widest text-secondary">
                Sources
              </label>
              <div className="grid grid-cols-2 gap-2">
                {SOURCE_OPTIONS.map((source) => {
                  const selected = sources.includes(source.value);
                  return (
                    <button
                      key={source.value}
                      type="button"
                      onClick={() => toggleSource(source.value)}
                      className={`rounded-lg border px-3 py-2 text-left transition-colors ${
                        selected
                          ? "border-primary bg-primary/5 text-primary"
                          : "border-surface-high bg-surface-low text-secondary hover:bg-white"
                      }`}
                    >
                      <span className="block text-sm font-bold">{source.label}</span>
                      <span className="block text-[10px] font-semibold">{source.note}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-bold uppercase tracking-widest text-secondary">
                Keywords
              </label>
              <textarea
                value={keywordsText}
                onChange={(event) => setKeywordsText(event.target.value)}
                rows={3}
                className="w-full resize-none rounded-lg border border-surface-high bg-surface-low px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <label className="col-span-1">
                <span className="mb-2 block text-xs font-bold uppercase tracking-widest text-secondary">
                  Max
                </span>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={maxPerSource}
                  onChange={(event) => setMaxPerSource(Math.max(1, Math.min(50, Number(event.target.value) || 1)))}
                  className="h-10 w-full rounded-lg border border-surface-high bg-surface-low px-3 text-sm outline-none focus:border-primary"
                />
              </label>

              <button
                type="button"
                onClick={() => setLive((value) => !value)}
                className={`col-span-1 mt-6 h-10 rounded-lg text-sm font-bold transition-colors ${
                  live ? "bg-primary/10 text-primary" : "bg-surface-low text-secondary"
                }`}
              >
                {live ? "Live" : "Demo"}
              </button>

              <button
                type="button"
                onClick={() => setReset((value) => !value)}
                className={`col-span-1 mt-6 h-10 rounded-lg text-sm font-bold transition-colors ${
                  reset ? "bg-red-50 text-red-700" : "bg-surface-low text-secondary"
                }`}
              >
                {reset ? "Reset" : "Append"}
              </button>
            </div>

            <button
              type="button"
              onClick={handleRun}
              disabled={!canRun}
              className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary text-sm font-bold text-white transition-colors hover:bg-primary-strong disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className={status === "running" ? "animate-spin" : ""}>↻</span>
              <span>{status === "running" ? "Collecting VOC..." : "Run Collection"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

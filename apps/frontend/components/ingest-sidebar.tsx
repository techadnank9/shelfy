"use client";
import { useEffect, useState } from "react";
import { listGuidelines, listPlanograms } from "@/lib/api";

interface Guideline {
  id: string;
  brand_id: string;
  raw_file_url: string;
  created_at: string;
  products_count: number;
}

interface PlanogramItem {
  id: string;
  brand_id: string;
  store_format: string;
  status: string;
  generated_at: string;
}

interface Props {
  selectedPlanogramId: string;
  onSelectPlanogram: (id: string) => void;
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const FORMAT_BADGE: Record<string, string> = {
  SMALL:  "bg-blue-100 text-blue-700",
  MEDIUM: "bg-purple-100 text-purple-700",
  LARGE:  "bg-orange-100 text-orange-700",
};

export function IngestSidebar({ selectedPlanogramId, onSelectPlanogram }: Props) {
  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [planograms, setPlanograms] = useState<PlanogramItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listGuidelines(), listPlanograms()])
      .then(([g, p]) => { setGuidelines(g); setPlanograms(p); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <aside className="w-72 shrink-0 border-r bg-gray-50 h-full overflow-y-auto">
      <div className="p-4 border-b bg-white sticky top-0 z-10">
        <h2 className="font-semibold text-sm text-gray-800">Ingested Data</h2>
        <p className="text-xs text-gray-400 mt-0.5">Click a planogram to audit it</p>
      </div>

      {loading && (
        <div className="p-4 text-xs text-gray-400 animate-pulse">Loading...</div>
      )}

      {/* Guidelines section */}
      {guidelines.length > 0 && (
        <div className="p-3">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">
            Brand Guidelines
          </p>
          <div className="space-y-1.5">
            {guidelines.map((g) => (
              <div
                key={g.id}
                className="rounded-lg border bg-white p-3 text-xs shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-medium text-gray-700 truncate">
                      Brand {g.brand_id.slice(0, 8)}…
                    </p>
                    <p className="text-gray-400 mt-0.5">{g.products_count} products parsed</p>
                  </div>
                  <span className="text-gray-300 shrink-0">{timeAgo(g.created_at)}</span>
                </div>
                {g.raw_file_url && (
                  <a
                    href={g.raw_file_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1.5 inline-block text-blue-500 hover:underline text-[10px]"
                  >
                    View PDF ↗
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Planograms section */}
      {planograms.length > 0 && (
        <div className="p-3 pt-1">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">
            Generated Planograms
          </p>
          <div className="space-y-1.5">
            {planograms.map((p) => {
              const selected = p.id === selectedPlanogramId;
              return (
                <button
                  key={p.id}
                  onClick={() => onSelectPlanogram(p.id)}
                  className={`w-full text-left rounded-lg border p-3 text-xs transition-all shadow-sm ${
                    selected
                      ? "border-black bg-black text-white"
                      : "border-gray-200 bg-white hover:border-gray-400 text-gray-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        selected
                          ? "bg-white/20 text-white"
                          : (FORMAT_BADGE[p.store_format] ?? "bg-gray-100 text-gray-600")
                      }`}
                    >
                      {p.store_format}
                    </span>
                    <span className={selected ? "text-white/60" : "text-gray-300"}>
                      {timeAgo(p.generated_at)}
                    </span>
                  </div>
                  <p className={`font-mono truncate ${selected ? "text-white/80" : "text-gray-400"}`}>
                    {p.id.slice(0, 20)}…
                  </p>
                  {selected && (
                    <p className="mt-1 text-[10px] text-white/60">✓ Selected for audit</p>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {!loading && guidelines.length === 0 && planograms.length === 0 && (
        <div className="p-4 text-xs text-gray-400">
          No ingested data yet. Upload a planogram PDF first.
        </div>
      )}
    </aside>
  );
}

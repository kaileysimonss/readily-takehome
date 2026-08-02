"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { MatchItem } from "@/lib/data";
import MatchRow from "./MatchRow";
import ClaimDetail, { SelectedClaim } from "./ClaimDetail";
import ItemDetail from "./ItemDetail";
import Overview from "./Overview";
import { VERDICT_CONFIG, VERDICT_ORDER, Verdict } from "@/lib/verdict";

type FilterValue = "all" | Verdict;

export default function MatchWorkspace({
  items,
  title,
  unitLabelSingular,
  unitLabelPlural,
  sourceLabel,
}: {
  items: MatchItem[];
  title: string;
  unitLabelSingular: string;
  unitLabelPlural: string;
  sourceLabel: string;
}) {
  const [hasRun, setHasRun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [filter, setFilter] = useState<FilterValue>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<SelectedClaim | null>(null);
  const [loadingChunkId, setLoadingChunkId] = useState<string | null>(null);
  const [chunkCache, setChunkCache] = useState<Record<string, SelectedClaim>>({});

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: items.length };
    for (const m of items) c[m.verdict] = (c[m.verdict] ?? 0) + 1;
    return c;
  }, [items]);

  const filtered = useMemo(
    () => (filter === "all" ? items : items.filter((m) => m.verdict === filter)),
    [items, filter]
  );

  const expandedItem = useMemo(
    () => items.find((m) => m.id === expandedId) ?? null,
    [items, expandedId]
  );

  function toggleRow(id: string) {
    setExpandedId((cur) => (cur === id ? null : id));
    setSelectedClaim(null);
  }

  function handleRun() {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setHasRun(true);
    }, 900);
  }

  async function selectCandidate(chunkId: string) {
    const cached = chunkCache[chunkId];
    if (cached) {
      setSelectedClaim(cached);
      return;
    }
    setLoadingChunkId(chunkId);
    try {
      const res = await fetch(`/api/pp-chunk/${encodeURIComponent(chunkId)}`);
      if (!res.ok) throw new Error("not found");
      const data: SelectedClaim = await res.json();
      setChunkCache((prev) => ({ ...prev, [chunkId]: data }));
      setSelectedClaim(data);
    } catch {
      // leave the current selection as-is; a missing chunk shouldn't happen
      // since every candidate comes from the real P&P index
    } finally {
      setLoadingChunkId(null);
    }
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="flex items-center justify-between border-b border-zinc-200 px-4 py-2.5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-700">
            ← Back
          </Link>
          <h1 className="text-sm font-semibold text-zinc-800">{title}</h1>
        </div>
        <p className="text-xs text-zinc-400">{`${items.length} ${unitLabelPlural} extracted`}</p>
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="w-1/2 border-r border-zinc-200">
          {selectedClaim ? (
            <ClaimDetail
              claim={selectedClaim}
              onBack={() => setSelectedClaim(null)}
              backLabel={unitLabelSingular}
            />
          ) : expandedItem ? (
            <ItemDetail item={expandedItem} />
          ) : hasRun ? (
            <Overview items={items} unitLabelPlural={unitLabelPlural} />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 bg-zinc-50 px-8 text-center">
              <p className="text-sm font-medium text-zinc-600">
                {`${items.length} ${unitLabelPlural} extracted from ${sourceLabel}`}
              </p>
              <p className="max-w-xs text-xs text-zinc-400">
                Click Run to check each one against the plan&apos;s P&amp;P documents. An
                overview will appear here once it&apos;s done.
              </p>
            </div>
          )}
        </div>

        <div className="flex w-1/2 flex-col">
          <div className="flex items-center gap-3 border-b border-zinc-200 px-4 py-3">
            <button
              onClick={handleRun}
              disabled={isRunning}
              className="rounded-md bg-zinc-900 px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:opacity-50"
            >
              {isRunning ? "Running…" : hasRun ? "Re-run" : "Run"}
            </button>
            {hasRun && !isRunning && (
              <div className="flex flex-wrap gap-1.5">
                {(["all", ...VERDICT_ORDER] as FilterValue[]).map((v) => (
                  <button
                    key={v}
                    onClick={() => setFilter(v)}
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset transition ${
                      filter === v
                        ? "bg-zinc-900 text-white ring-zinc-900"
                        : "bg-white text-zinc-600 ring-zinc-200 hover:ring-zinc-400"
                    }`}
                  >
                    {`${v === "all" ? "All" : VERDICT_CONFIG[v].label} ${counts[v] ?? 0}`}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {!hasRun ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-zinc-400">
                <p className="text-sm font-medium">Not started</p>
                <p className="max-w-xs text-xs">
                  {`Click Run to check every ${unitLabelSingular} extracted from ${sourceLabel} against the plan's P&P documents.`}
                </p>
              </div>
            ) : (
              filtered.map((m) => (
                <MatchRow
                  key={m.id}
                  item={m}
                  isExpanded={expandedId === m.id}
                  onToggle={() => toggleRow(m.id)}
                  onSelectCandidate={selectCandidate}
                  selectedChunkId={selectedClaim?.chunkId ?? null}
                  loadingChunkId={loadingChunkId}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

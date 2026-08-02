"use client";

import { useState } from "react";
import type { MatchItem } from "@/lib/data";
import { VERDICT_CONFIG, Verdict } from "@/lib/verdict";

const VISIBLE_CANDIDATES = 5;

export default function MatchRow({
  item,
  isExpanded,
  onToggle,
  onSelectCandidate,
  selectedChunkId,
  loadingChunkId,
  isResolved,
  onToggleResolved,
}: {
  item: MatchItem;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectCandidate: (chunkId: string) => void;
  selectedChunkId: string | null;
  loadingChunkId: string | null;
  isResolved: boolean;
  onToggleResolved: () => void;
}) {
  const [showAll, setShowAll] = useState(false);
  const verdict = VERDICT_CONFIG[item.verdict as Verdict] ?? VERDICT_CONFIG.error;
  const visible = showAll ? item.candidates : item.candidates.slice(0, VISIBLE_CANDIDATES);

  return (
    <div className={`border-b border-zinc-100 ${isResolved ? "bg-zinc-50/60" : ""}`}>
      <button
        onClick={onToggle}
        className="flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-zinc-50"
      >
        <span
          className={`mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full ${verdict.dot}`}
          aria-hidden
        />
        <span className="flex-1 text-sm text-zinc-800">
          {item.number != null && (
            <span className="mr-1.5 font-semibold text-zinc-400">{`Q${item.number}.`}</span>
          )}
          {item.statement}
        </span>
        {isResolved && (
          <span className="mt-0.5 shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
            ✓ Resolved
          </span>
        )}
        {item.citationVerified === false && (
          <span
            className="mt-0.5 shrink-0 text-amber-500"
            title="This citation could not be automatically verified - check manually before trusting it."
          >
            ⚠
          </span>
        )}
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${verdict.badge}`}
        >
          {verdict.label}
        </span>
      </button>

      {isExpanded && (
        <div className="bg-zinc-50 px-4 pb-4 pl-9">
          <button
            onClick={onToggleResolved}
            className={`mb-3 rounded-md px-2.5 py-1 text-xs font-medium ring-1 ring-inset transition ${
              isResolved
                ? "bg-white text-zinc-600 ring-zinc-200 hover:ring-zinc-400"
                : "bg-emerald-600 text-white ring-emerald-600 hover:bg-emerald-700"
            }`}
          >
            {isResolved ? "Unresolve" : "Mark Resolved"}
          </button>

          <p className="mb-3 text-xs text-zinc-500">
            <span className="font-medium text-zinc-600">Why: </span>
            {item.explanation}
          </p>

          {item.citationVerified === false && (
            <p className="mb-3 rounded-md bg-amber-50 px-2.5 py-1.5 text-xs text-amber-700">
              The cited claim below could not be automatically verified as one of the
              excerpts actually reviewed - double-check it manually before relying on it.
            </p>
          )}

          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
            Matched claims checked ({item.candidates.length})
          </p>
          <ul className="space-y-1">
            {visible.map((c) => {
              const isMatch = c.chunkId === item.matchedChunkId;
              const isSelected = c.chunkId === selectedChunkId;
              const isLoading = c.chunkId === loadingChunkId;
              return (
                <li key={c.chunkId}>
                  <button
                    onClick={() => onSelectCandidate(c.chunkId)}
                    className={`flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-xs transition ${
                      isSelected
                        ? "bg-zinc-900 text-white"
                        : "bg-white text-zinc-700 hover:bg-zinc-100"
                    }`}
                  >
                    <span className="flex items-center gap-1.5 truncate">
                      {isMatch && (
                        <span
                          className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                            isSelected ? "bg-white/20" : "bg-zinc-900 text-white"
                          }`}
                        >
                          MATCH
                        </span>
                      )}
                      <span className="truncate">
                        {c.doc} · {c.section}
                      </span>
                    </span>
                    <span className={`shrink-0 ${isSelected ? "text-white/70" : "text-zinc-400"}`}>
                      {isLoading ? "loading…" : c.score.toFixed(2)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          {item.candidates.length > VISIBLE_CANDIDATES && (
            <button
              onClick={() => setShowAll((s) => !s)}
              className="mt-2 text-xs font-medium text-zinc-500 hover:text-zinc-800"
            >
              {showAll ? "Show fewer" : `Show ${item.candidates.length - VISIBLE_CANDIDATES} more`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

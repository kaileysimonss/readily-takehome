"use client";

import { useState } from "react";
import type { Match } from "@/lib/data";
import { VERDICT_CONFIG, Verdict } from "./verdict";

const VISIBLE_CANDIDATES = 5;

export default function ObligationRow({
  match,
  isExpanded,
  onToggle,
  onSelectCandidate,
  selectedChunkId,
  loadingChunkId,
}: {
  match: Match;
  isExpanded: boolean;
  onToggle: () => void;
  onSelectCandidate: (chunkId: string) => void;
  selectedChunkId: string | null;
  loadingChunkId: string | null;
}) {
  const [showAll, setShowAll] = useState(false);
  const verdict = VERDICT_CONFIG[match.verdict as Verdict] ?? VERDICT_CONFIG.error;
  const visible = showAll ? match.candidates : match.candidates.slice(0, VISIBLE_CANDIDATES);

  return (
    <div className="border-b border-zinc-100">
      <button
        onClick={onToggle}
        className="flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-zinc-50"
      >
        <span
          className={`mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full ${verdict.dot}`}
          aria-hidden
        />
        <span className="flex-1 text-sm text-zinc-800">{match.obligation}</span>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${verdict.badge}`}
        >
          {verdict.label}
        </span>
      </button>

      {isExpanded && (
        <div className="bg-zinc-50 px-4 pb-4 pl-9">
          <p className="mb-3 text-xs text-zinc-500">
            <span className="font-medium text-zinc-600">Why: </span>
            {match.explanation}
          </p>

          <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
            Matched claims checked ({match.candidates.length})
          </p>
          <ul className="space-y-1">
            {visible.map((c) => {
              const isMatch = c.chunkId === match.matchedChunkId;
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

          {match.candidates.length > VISIBLE_CANDIDATES && (
            <button
              onClick={() => setShowAll((s) => !s)}
              className="mt-2 text-xs font-medium text-zinc-500 hover:text-zinc-800"
            >
              {showAll ? "Show fewer" : `Show ${match.candidates.length - VISIBLE_CANDIDATES} more`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

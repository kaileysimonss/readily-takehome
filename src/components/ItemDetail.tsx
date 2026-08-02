"use client";

import type { MatchItem } from "@/lib/data";
import { VERDICT_CONFIG, Verdict } from "@/lib/verdict";

export default function ItemDetail({ item }: { item: MatchItem }) {
  const verdict = VERDICT_CONFIG[item.verdict as Verdict] ?? VERDICT_CONFIG.error;

  return (
    <div className="flex h-full flex-col bg-white px-6 py-6">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
          {item.doc} · Page {item.page}
        </p>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${verdict.badge}`}
        >
          {verdict.label}
        </span>
        {item.citationVerified === false && (
          <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
            ⚠ Unverified citation
          </span>
        )}
      </div>

      <p className="mt-3 text-base font-medium leading-relaxed text-zinc-800">
        {item.statement}
      </p>

      {item.reference && (
        <p className="mt-2 text-xs text-zinc-400">Reference: {item.reference}</p>
      )}

      <div className="mt-5 rounded-lg bg-zinc-50 p-4 text-sm text-zinc-600">
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-400">
          Why
        </p>
        {item.explanation}
      </div>

      <p className="mt-auto pt-6 text-xs text-zinc-400">
        Click one of the matched claims on the right to see its cited text here.
      </p>
    </div>
  );
}

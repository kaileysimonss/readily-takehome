"use client";

import type { Match } from "@/lib/data";
import { VERDICT_CONFIG, Verdict } from "./verdict";

export default function ObligationDetail({ match }: { match: Match }) {
  const verdict = VERDICT_CONFIG[match.verdict as Verdict] ?? VERDICT_CONFIG.error;

  return (
    <div className="flex h-full flex-col bg-white px-6 py-6">
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
          {match.doc} · Page {match.page}
        </p>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${verdict.badge}`}
        >
          {verdict.label}
        </span>
      </div>

      <p className="mt-3 text-base font-medium leading-relaxed text-zinc-800">
        {match.obligation}
      </p>

      <div className="mt-5 rounded-lg bg-zinc-50 p-4 text-sm text-zinc-600">
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-zinc-400">
          Why
        </p>
        {match.explanation}
      </div>

      <p className="mt-auto pt-6 text-xs text-zinc-400">
        Click one of the matched claims on the right to see its cited text here.
      </p>
    </div>
  );
}

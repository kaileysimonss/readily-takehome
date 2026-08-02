"use client";

import type { MatchItem } from "@/lib/data";
import { VERDICT_CONFIG, VERDICT_ORDER, Verdict } from "@/lib/verdict";

// Tailwind dot color -> matching solid fill for the proportion bar segments.
const BAR_FILL: Record<Verdict, string> = {
  supports: "bg-emerald-500",
  partial: "bg-amber-500",
  contradicts: "bg-red-500",
  gap: "bg-zinc-400",
  error: "bg-zinc-300",
};

export default function Overview({
  items,
  unitLabelPlural,
}: {
  items: MatchItem[];
  unitLabelPlural: string;
}) {
  const total = items.length;
  const counts = VERDICT_ORDER.reduce((acc, v) => {
    acc[v] = items.filter((m) => m.verdict === v).length;
    return acc;
  }, {} as Record<Verdict, number>);
  const unverifiedCount = items.filter((m) => m.citationVerified === false).length;

  return (
    <div className="flex h-full flex-col bg-white px-6 py-6">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">Overview</p>
      <h2 className="mt-1 text-lg font-semibold text-zinc-800">
        {`${total} ${unitLabelPlural} checked against the plan's P&Ps`}
      </h2>

      <div className="mt-5 grid grid-cols-2 gap-3">
        {VERDICT_ORDER.map((v) => (
          <div
            key={v}
            className="rounded-lg border border-zinc-200 px-4 py-3"
            title={`${counts[v]} ${VERDICT_CONFIG[v].label}`}
          >
            <div className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${VERDICT_CONFIG[v].dot}`} aria-hidden />
              <span className="text-xs font-medium text-zinc-500">{VERDICT_CONFIG[v].label}</span>
            </div>
            <p className="mt-1 text-2xl font-semibold text-zinc-900">{counts[v]}</p>
          </div>
        ))}
      </div>

      <div className="mt-5">
        <p className="mb-1.5 text-xs font-medium text-zinc-500">{`Proportion of all ${unitLabelPlural}`}</p>
        <div className="flex h-3 w-full overflow-hidden rounded-full bg-zinc-100">
          {VERDICT_ORDER.map((v, i) =>
            counts[v] === 0 ? null : (
              <div
                key={v}
                className={`${BAR_FILL[v]} h-full ${i > 0 ? "border-l-2 border-white" : ""}`}
                style={{ width: `${(counts[v] / total) * 100}%` }}
                title={`${VERDICT_CONFIG[v].label}: ${counts[v]} (${Math.round((counts[v] / total) * 100)}%)`}
              />
            )
          )}
        </div>
      </div>

      {unverifiedCount > 0 && (
        <p className="mt-3 text-xs text-amber-600">
          {`⚠ ${unverifiedCount} citation${unverifiedCount === 1 ? "" : "s"} could not be automatically verified - look for the warning icon.`}
        </p>
      )}

      <div className="mt-8 rounded-lg bg-zinc-50 p-4 text-sm text-zinc-500">
        <p className="font-medium text-zinc-600">How to read this</p>
        <ul className="mt-2 space-y-1.5">
          <li>
            <span className="font-medium text-red-700">Conflict</span> — a P&amp;P says
            something that actively contradicts this item. Review first.
          </li>
          <li>
            <span className="font-medium text-zinc-600">Gap</span> — no existing P&amp;P
            language addresses it. Needs new/updated policy.
          </li>
          <li>
            <span className="font-medium text-amber-700">Partial</span> — related P&amp;P
            language exists, but only via inference. Worth a manual check.
          </li>
          <li>
            <span className="font-medium text-emerald-700">Covered</span> — a P&amp;P
            explicitly states the requirement.
          </li>
        </ul>
      </div>

      <p className="mt-auto pt-6 text-xs text-zinc-400">
        {`Expand a row on the right, then click a matched claim to see its citation here.`}
      </p>
    </div>
  );
}

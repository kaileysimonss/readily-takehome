export type Verdict = "supports" | "partial" | "contradicts" | "gap" | "error";

export const VERDICT_CONFIG: Record<
  Verdict,
  { label: string; badge: string; dot: string }
> = {
  supports: {
    label: "Covered",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    dot: "bg-emerald-500",
  },
  partial: {
    label: "Partial",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
    dot: "bg-amber-500",
  },
  contradicts: {
    label: "Conflict",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    dot: "bg-red-500",
  },
  gap: {
    label: "Gap",
    badge: "bg-zinc-100 text-zinc-600 ring-zinc-500/20",
    dot: "bg-zinc-400",
  },
  error: {
    label: "Error",
    badge: "bg-zinc-100 text-zinc-500 ring-zinc-500/20",
    dot: "bg-zinc-400",
  },
};

export const VERDICT_ORDER: Verdict[] = ["contradicts", "gap", "partial", "supports"];

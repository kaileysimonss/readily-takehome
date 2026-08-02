"use client";

export interface SelectedClaim {
  chunkId: string;
  doc: string;
  docTitle: string;
  section: string;
  page: number;
  text: string;
}

export default function ClaimDetail({
  claim,
  onBack,
  backLabel,
}: {
  claim: SelectedClaim;
  onBack: () => void;
  backLabel: string;
}) {
  return (
    <div className="flex h-full flex-col bg-white">
      <div className="border-b border-zinc-200 px-6 py-4">
        <button
          onClick={onBack}
          className="mb-2 text-xs font-medium text-zinc-400 hover:text-zinc-700"
        >
          {`← Back to ${backLabel}`}
        </button>
        <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
          {claim.doc} · Section {claim.section} · Page {claim.page}
        </p>
        <p className="mt-1 text-base font-semibold text-zinc-800">{claim.docTitle}</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
          Cited text
        </p>
        <blockquote className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-relaxed text-zinc-800">
          &ldquo;{claim.text}&rdquo;
        </blockquote>
      </div>
    </div>
  );
}

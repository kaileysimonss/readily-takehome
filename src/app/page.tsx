import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-6 py-16">
      <main className="w-full max-w-3xl">
        <div className="mb-10 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Readily Compliance Module
          </h1>
          <p className="mt-2 text-zinc-500">
            Choose what you want to check the plan&apos;s Policies &amp; Procedures against.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <Link
            href="/ecm"
            className="group flex flex-col rounded-xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-400 hover:shadow-md"
          >
            <span className="text-xs font-medium uppercase tracking-wide text-emerald-600">
              Available
            </span>
            <h2 className="mt-2 text-lg font-semibold text-zinc-900">
              Check P&amp;P against ECM Policy Guide
            </h2>
            <p className="mt-2 flex-1 text-sm text-zinc-500">
              Every obligation extracted from the DHCS ECM Policy Guide, checked against
              the plan&apos;s existing Policy &amp; Procedure documents, with citations.
            </p>
            <span className="mt-4 text-sm font-medium text-zinc-900 group-hover:underline">
              Open →
            </span>
          </Link>

          <div
            aria-disabled="true"
            className="flex cursor-not-allowed flex-col rounded-xl border border-dashed border-zinc-200 bg-zinc-50 p-6 opacity-60"
          >
            <span className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Coming soon
            </span>
            <h2 className="mt-2 text-lg font-semibold text-zinc-500">
              Check P&amp;P against Questionnaire
            </h2>
            <p className="mt-2 flex-1 text-sm text-zinc-400">
              Answer a DHCS Submission Review Form question-by-question, with the exact
              P&amp;P citation that proves compliance.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

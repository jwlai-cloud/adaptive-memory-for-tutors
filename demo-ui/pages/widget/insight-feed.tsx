import { useCallback, useEffect, useState } from "react";
import type { Insight } from "../../lib/api";

function decisionLabel(decision: Insight["decision"]) {
  if (decision === "retire") return "Resolved";
  if (decision === "escalate") return "Needs attention";
  return "Watching";
}

function decisionClass(decision: Insight["decision"]) {
  if (decision === "retire") return "border-teal text-teal";
  if (decision === "escalate") return "border-coral text-coral";
  return "border-amber text-ink";
}

function readParam(name: string, fallback: string) {
  if (typeof window === "undefined") return fallback;
  return new URLSearchParams(window.location.search).get(name) || fallback;
}

const DEFAULT_CONFIG = {
  tenantId: "demo-school",
  studentRef: "demo-student-1",
  pairId: "kana-so-n",
};

export default function InsightFeedWidget() {
  const [feed, setFeed] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState(DEFAULT_CONFIG);

  useEffect(() => {
    setConfig({
      tenantId: readParam("tenantId", "demo-school"),
      studentRef: readParam("studentRef", "demo-student-1"),
      pairId: readParam("pairId", "kana-so-n"),
    });
  }, []);

  const load = useCallback(async () => {
    try {
      setError(null);
      const path = `/v1/insights/${encodeURIComponent(config.pairId)}/history`;
      const query = new URLSearchParams({
        tenant_id: config.tenantId,
        student_ref: config.studentRef,
      });
      const response = await fetch(`/api/backend${path}?${query}`);
      if (!response.ok) throw new Error(`API ${response.status}`);
      const nextFeed = (await response.json()) as Insight[];
      setFeed(nextFeed);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load insights.");
    } finally {
      setLoading(false);
    }
  }, [config]);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 12000);
    return () => window.clearInterval(id);
  }, [load]);

  const latest = feed[feed.length - 1];

  return (
    <main className="min-h-screen bg-white p-4 text-ink">
      <section className="mx-auto max-w-md border border-ink/20 bg-white p-4">
        <div className="flex items-start justify-between gap-4 border-b border-ink/15 pb-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-ink/55">Memory insight</p>
            <h1 suppressHydrationWarning className="mt-1 text-base font-bold">{config.pairId}</h1>
          </div>
          {latest ? (
            <span className={`border px-2 py-1 text-xs font-bold ${decisionClass(latest.decision)}`}>
              {decisionLabel(latest.decision)}
            </span>
          ) : null}
        </div>

        {loading ? (
          <div className="mt-4 space-y-3" aria-busy="true" aria-label="Loading insight feed">
            <div className="h-4 w-2/3 animate-pulse bg-ink/10" />
            <div className="h-4 w-full animate-pulse bg-ink/10" />
            <div className="h-4 w-5/6 animate-pulse bg-ink/10" />
          </div>
        ) : error ? (
          <p role="alert" className="mt-4 border border-coral/40 bg-coral/5 p-3 text-sm text-coral">
            {error}
          </p>
        ) : feed.length ? (
          <ol className="mt-2 divide-y divide-ink/10">
            {[...feed].reverse().slice(0, 5).map((insight) => (
              <li key={`${insight.timestamp}-${insight.decision}`} className="py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className={`border px-2 py-0.5 text-xs font-bold ${decisionClass(insight.decision)}`}>
                    {decisionLabel(insight.decision)}
                  </span>
                  <time suppressHydrationWarning className="text-xs text-ink/55">{new Date(insight.timestamp).toLocaleString()}</time>
                </div>
                <p className="mt-2 text-sm leading-6">{insight.reasoning}</p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-4 border border-dashed border-ink/25 p-3 text-sm text-ink/65">
            No insight entries yet for this pair.
          </p>
        )}
      </section>
    </main>
  );
}

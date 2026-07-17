import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { AsyncPanel } from "../components/AsyncPanel";
import { DecisionBadge } from "../components/DecisionBadge";
import { getPairState, PairState } from "../lib/api";

export default function ComparePage() {
  const [state, setState] = useState<PairState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setError(null); setState(await getPairState("kana-so-n")); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load the student graph."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); const id = window.setInterval(() => void load(), 12000); return () => window.clearInterval(id); }, [load]);
  const insight = state?.latest_insight;

  return (
    <AppShell title="Memory on vs off">
      <section className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-sm font-bold uppercase tracking-wide text-coral">Same prompt, different context</p><h2 className="mt-2 text-2xl font-bold">Why persistent memory changes the next drill</h2></div>
        <button onClick={() => { setLoading(true); void load(); }} className="border border-ink bg-white px-3 py-2 text-sm font-semibold hover:bg-ink hover:text-white">Refresh live state</button>
      </section>
      <div className="grid gap-5 lg:grid-cols-2">
        <article className="border border-ink/20 bg-white p-6">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-ink/60">Memory off · stateless mock</p>
          <h3 className="mt-4 text-xl font-bold">Try another general review.</h3>
          <p className="mt-3 leading-7 text-ink/80">Let&apos;s practise recognizing ソ and ン again. Look carefully at the final stroke before choosing your answer.</p>
          <p className="mt-8 border-t border-ink/10 pt-4 text-sm text-ink/60">Knows neither the pattern nor the progress.</p>
        </article>
        <article className="border-2 border-teal bg-white p-6" aria-live="polite">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-teal">Memory on · live API</p>
          <AsyncPanel loading={loading} error={error}>
            {insight ? <>
              <div className="mt-4"><DecisionBadge decision={insight.decision} /></div>
              <h3 className="mt-4 text-xl font-bold">{insight.reasoning}</h3>
              <p className="mt-3 leading-7 text-ink/80">This recommendation is derived from {state?.recent_facts.length} stored attempts for the same student and concept pair.</p>
              <p className="mt-8 border-t border-ink/10 pt-4 text-sm text-ink/60">Last updated {new Date(insight.timestamp).toLocaleString()}.</p>
            </> : <div className="mt-5"><h3 className="text-xl font-bold">No decision logged yet.</h3><p className="mt-3 leading-7 text-ink/80">The live history is loaded; post one event through the API to create the first GPT-backed insight.</p></div>}
          </AsyncPanel>
        </article>
      </div>
    </AppShell>
  );
}

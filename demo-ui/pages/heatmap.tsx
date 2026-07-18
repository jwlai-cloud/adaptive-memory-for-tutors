import { useCallback, useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { AsyncPanel } from "../components/AsyncPanel";
import { getPairs, getPairState, Pair, PairState } from "../lib/api";

type Tile = { pair: Pair; state: PairState | null };
type Status = "confused" | "improving" | "resolved" | "no_history";
const style: Record<Status, string> = { confused: "border-coral bg-coral/15", improving: "border-sand bg-sand/25", resolved: "border-teal bg-teal/15", no_history: "border-ink/20 bg-white" };

function statusFor(state: PairState | null): Status {
  const outcomes = state?.recent_facts.map((fact) => fact.correct) || [];
  if (!outcomes.length) return "no_history";
  if (outcomes.length >= 3 && outcomes.slice(-3).every(Boolean)) return "resolved";
  if (outcomes.slice(-3).filter(Boolean).length >= 2) return "improving";
  return "confused";
}

export default function HeatmapPage() {
  const [tiles, setTiles] = useState<Tile[]>([]); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    try {
      setError(null); const pairs = (await Promise.all([getPairs("japanese-kana"), getPairs("chemistry-notation")])).flat();
      const states = await Promise.all(pairs.map(async (pair) => { try { return await getPairState(pair.id); } catch { return null; } }));
      setTiles(pairs.map((pair, index) => ({ pair, state: states[index] })));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load the tracked pair grid."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); const id = window.setInterval(() => void load(), 12000); return () => window.clearInterval(id); }, [load]);
  return <AppShell title="Heatmap"><section className="mb-8 flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-bold uppercase tracking-wide text-coral">Schema reused across domains</p><h2 className="mt-2 text-2xl font-bold">Current confusion heatmap</h2><p className="mt-2 max-w-2xl text-ink/70">The same memory engine reads Japanese kana and chemistry notation without domain-specific code.</p></div><button onClick={() => { setLoading(true); void load(); }} className="border border-ink bg-white px-3 py-2 text-sm font-semibold hover:bg-ink hover:text-white">Refresh</button></section><AsyncPanel loading={loading} error={error}><div className="mb-5 flex flex-wrap gap-3 text-sm"><span><i className="mr-1 inline-block h-3 w-3 bg-coral" />confused</span><span><i className="mr-1 inline-block h-3 w-3 bg-sand" />improving</span><span><i className="mr-1 inline-block h-3 w-3 bg-teal" />resolved</span><span><i className="mr-1 inline-block h-3 w-3 border border-ink/30 bg-white" />no history</span></div><div className="grid gap-4 sm:grid-cols-2">{tiles.map(({ pair, state }) => { const status = statusFor(state); return <article key={pair.id} className={`border-l-4 p-5 ${style[status]}`}><div className="flex items-start justify-between gap-3"><p className="text-xs font-bold uppercase tracking-[0.12em] text-ink/65">{pair.domain}</p><span className="text-xs font-bold uppercase">{status.replace("_", " ")}</span></div><h3 className="mt-4 text-lg font-bold">{pair.label_a} / {pair.label_b}</h3><p className="mt-2 text-sm leading-6 text-ink/75">{pair.description}</p><p className="mt-4 text-xs text-ink/60">{state?.recent_facts.length || 0} live events</p></article>; })}</div></AsyncPanel></AppShell>;
}

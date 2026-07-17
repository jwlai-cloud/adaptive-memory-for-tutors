import { useCallback, useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AppShell } from "../components/AppShell";
import { AsyncPanel } from "../components/AsyncPanel";
import { DecisionBadge } from "../components/DecisionBadge";
import { getInsightFeed, getPairState, Insight, PairState } from "../lib/api";

function shortDate(value: string) { return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" }); }

export default function TimelinePage() {
  const [state, setState] = useState<PairState | null>(null);
  const [feed, setFeed] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { setError(null); const [nextState, nextFeed] = await Promise.all([getPairState("kana-so-n"), getInsightFeed("kana-so-n")]); setState(nextState); setFeed(nextFeed); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load the live timeline."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); const id = window.setInterval(() => void load(), 12000); return () => window.clearInterval(id); }, [load]);

  const chartData = useMemo(() => (state?.recent_facts || []).map((fact, index, all) => ({
    label: shortDate(fact.timestamp), accuracy: fact.correct ? 100 : 0,
    checkpoint: index === 0 ? "Flagged" : index === 3 ? "Not improving" : index === all.length - 1 ? "Resolved" : ""
  })), [state]);

  return <AppShell title="Timeline">
    <section className="mb-8"><p className="text-sm font-bold uppercase tracking-wide text-coral">Temporal graph story</p><h2 className="mt-2 text-2xl font-bold">ソ / ン: flagged, adjusted, resolved</h2></section>
    <AsyncPanel loading={loading} error={error}>
      <section className="border border-ink/20 bg-white p-5 sm:p-7">
        <div className="mb-5 flex items-start justify-between gap-4"><div><h3 className="font-bold">Accuracy across stored attempts</h3><p className="mt-1 text-sm text-ink/65">Each point is a live Zep episode; annotations mark the demo checkpoints.</p></div><button onClick={() => { setLoading(true); void load(); }} className="text-sm font-semibold underline underline-offset-4">Refresh</button></div>
        <div className="h-72" aria-label="Accuracy timeline chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 24, right: 16, bottom: 4, left: -18 }}><CartesianGrid stroke="#14213d" strokeOpacity={0.12} vertical={false} /><XAxis dataKey="label" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} ticks={[0, 50, 100]} tickFormatter={(value) => `${value}%`} tickLine={false} axisLine={false} /><Tooltip formatter={(value) => [`${value}%`, "Accuracy"]} /><Line type="stepAfter" dataKey="accuracy" stroke="#2a9d8f" strokeWidth={3} dot={{ r: 5, fill: "#14213d" }} activeDot={{ r: 7 }} /><ReferenceLine y={50} stroke="#e9c46a" strokeDasharray="4 4" /></LineChart></ResponsiveContainer></div>
        <ol className="mt-5 grid gap-3 text-sm sm:grid-cols-3"><li><strong className="text-coral">Flagged</strong><br />Repeated wrong answers establish the confusion.</li><li><strong className="text-coral">Not improving</strong><br />A second session confirms the pattern persists.</li><li><strong className="text-teal">Resolved</strong><br />Three correct answers support retirement.</li></ol>
      </section>
      <section className="mt-7"><div className="mb-4 flex items-end justify-between"><div><p className="text-sm font-bold uppercase tracking-wide text-teal">Live decision feed</p><h3 className="mt-1 text-xl font-bold">Auditable insight log</h3></div><span className="text-xs text-ink/60">Refreshes every 12 seconds</span></div>
        {feed.length ? <ol className="border-t border-ink/20">{[...feed].reverse().map((insight) => <li key={`${insight.timestamp}-${insight.decision}`} className="grid gap-3 border-b border-ink/15 py-4 sm:grid-cols-[11rem_7rem_1fr]"><time className="text-sm text-ink/65">{new Date(insight.timestamp).toLocaleString()}</time><DecisionBadge decision={insight.decision} /><p className="leading-6">{insight.reasoning}</p></li>)}</ol> : <p className="border border-dashed border-ink/30 bg-white p-5 text-sm">No live insight entries yet. Post a new event through the REST API to create a GPT-backed audit entry.</p>}</section>
    </AsyncPanel>
  </AppShell>;
}
